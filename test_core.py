"""Offline checks for submission verification and run reporting.

Run: python test_core.py
Starts a throwaway local aiohttp server; never contacts Google.
"""
import asyncio
import json
import tempfile
from pathlib import Path

import aiohttp
from aiohttp import web

from core import FormDetails, SubmissionEngine, classify_submission, REQUEST_TIMEOUT

CONFIRM = '<div class="freebirdFormviewerViewResponseConfirmationMessage">Your response has been recorded.</div>'
CLOSED = '<div class="freebirdFormviewerViewNoLongerAcceptingResponses">This form is no longer accepting responses.</div>'
REJECTED = (
    '<html><script>var FB_PUBLIC_LOAD_DATA_ = [[]];</script>'
    '<div class="freebirdFormviewerViewItemsItemErrorMessage">This is a required question</div></html>'
)
UNKNOWN = "<html><body>gateway hiccup</body></html>"

BODIES = {
    "/recorded": CONFIRM,
    "/closed": CLOSED,
    "/rejected": REJECTED,
    "/unknown": UNKNOWN,
}


async def handle_submit(request):
    return web.Response(text=BODIES.get(request.path, UNKNOWN), content_type="text/html")


def details_for(port: int, path: str) -> FormDetails:
    return FormDetails(
        url=f"http://127.0.0.1:{port}/viewform",
        form_action_url=f"http://127.0.0.1:{port}{path}",
        questions={
            "entry.1": {"text": "Nama lengkap", "type": "Short Answer",
                        "options": [], "required": True},
        },
        hidden_fields={},
    )


def check_classification() -> None:
    assert classify_submission(CONFIRM) == "recorded"
    assert classify_submission("Jawaban Anda telah direkam.") == "recorded"
    assert classify_submission(CLOSED) == "closed"
    assert classify_submission(REJECTED) == "rejected"
    assert classify_submission(UNKNOWN) == "unknown"
    assert classify_submission("") == "unknown"
    # A confirmation page wins even when it also carries the form script marker.
    assert classify_submission(CONFIRM + "FB_PUBLIC_LOAD_DATA_") == "recorded"


async def check_send(port: int) -> None:
    expected = {
        "/recorded": (True, None, "recorded"),
        "/closed": (False, "Form is no longer accepting responses", "closed"),
        "/rejected": (False, "Answer rejected (not recorded)", "rejected"),
        "/unknown": (True, None, "unknown"),
    }
    for path, want in expected.items():
        engine = SubmissionEngine(details_for(port, path))
        async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
            result = await engine._send_request(session, {"entry.1": "Siti"})
        assert result == want, (path, result)
        if want[0]:
            assert engine.stats["success"] == 1, path
            assert engine.stats["unverified"] == (1 if want[2] == "unknown" else 0), path
        else:
            assert engine.stats["failed"] == 1, path
            assert engine.stats["success"] == 0, path


def read_report(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


async def check_recorded_run(port: int, tmp: Path) -> None:
    report_path = tmp / "recorded.jsonl"
    engine = SubmissionEngine(details_for(port, "/recorded"))
    await engine.run(3, 2, report_path=str(report_path))

    assert engine.stats["success"] == 3
    assert engine.stats["failed"] == 0
    assert sum(engine.distributions["entry.1"].values()) == 3

    lines = read_report(report_path)
    assert [line["type"] for line in lines] == ["run_start"] + ["response"] * 3 + ["run_end"]
    responses = [line for line in lines if line["type"] == "response"]
    assert [line["n"] for line in responses] == [1, 2, 3]
    assert all(line["ok"] and line["verified"] == "recorded" for line in responses)
    assert all(line["answers"].get("entry.1") for line in responses)
    assert lines[0]["count"] == 3 and lines[0]["workers"] == 2
    assert lines[-1]["success"] == 3 and lines[-1]["status"] == "done"


async def check_rejected_run(port: int, tmp: Path) -> None:
    """A 200 page without confirmation must not be counted as success."""
    report_path = tmp / "rejected.jsonl"
    engine = SubmissionEngine(details_for(port, "/rejected"))
    await engine.run(2, 2, report_path=str(report_path))

    assert engine.stats["success"] == 0
    assert engine.stats["failed"] == 2
    assert engine.distributions == {}

    responses = [line for line in read_report(report_path) if line["type"] == "response"]
    assert len(responses) == 2
    assert all(not line["ok"] and line["verified"] == "rejected" for line in responses)


async def main() -> None:
    app = web.Application()
    app.router.add_post("/{path:.*}", handle_submit)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = runner.addresses[0][1]
    try:
        check_classification()
        await check_send(port)
        with tempfile.TemporaryDirectory() as tmp:
            await check_recorded_run(port, Path(tmp))
            await check_rejected_run(port, Path(tmp))
    finally:
        await runner.cleanup()

    print("OK: response classification, verification stats, and JSONL report")


if __name__ == "__main__":
    asyncio.run(main())
