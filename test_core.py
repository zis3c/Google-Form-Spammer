"""Offline checks for submission verification and run reporting.

Run: python test_core.py
Starts a throwaway local aiohttp server; never contacts Google.
"""
import asyncio
import json
import re
import tempfile
from pathlib import Path

import aiohttp
from aiohttp import web

from core import FormDetails, SubmissionEngine, classify_submission, REQUEST_TIMEOUT, _find_regex

CONFIRM = '<div class="freebirdFormviewerViewResponseConfirmationMessage">Your response has been recorded.</div>'
THANK_YOU = (
    '<html><title>Event RSVP</title><body>Thank you for your response.'
    '<script>var FB_PUBLIC_LOAD_DATA_ = [[]];</script></body></html>'
)
CLOSED = '<div class="freebirdFormviewerViewNoLongerAcceptingResponses">This form is no longer accepting responses.</div>'
REJECTED = (
    '<html><script>var FB_PUBLIC_LOAD_DATA_ = [["Nama lengkap"]];</script>'
    '<div class="freebirdFormviewerViewItemsItemErrorMessage">This is a required question</div></html>'
)
LOCALIZED_CONFIRM = (
    '<html><body><div role="heading" aria-level="1">Acara</div>'
    '<div>Terima kasih atas jawapan anda.</div>'
    '<script>var FB_PUBLIC_LOAD_DATA_ = [];</script></body></html>'
)
LOCALIZED_REJECTED = (
    '<html><body><script>var FB_PUBLIC_LOAD_DATA_ = [["Nama lengkap"]];</script>'
    '<div>Wajib diisi</div></body></html>'
)
NO_HEADING_CONFIRM = (
    '<html><body><div>Terima kasih</div>'
    '<script>var FB_PUBLIC_LOAD_DATA_ = [];</script></body></html>'
)
SHORT_REJECTED = '<html><script>var FB_PUBLIC_LOAD_DATA_ = [["Umur"]];</script></html>'
CLOSED_CLASS_ONLY = '<div class="freebirdFormviewerViewNoLongerAcceptingResponses">Ditutup</div>'
UNKNOWN = "<html><body>gateway hiccup</body></html>"

BODIES = {
    "/recorded": CONFIRM,
    "/closed": CLOSED,
    "/rejected": REJECTED,
    "/unknown": UNKNOWN,
}

ATTEMPTS = {}


async def handle_submit(request):
    if request.path == "/closed-redirect":
        raise web.HTTPFound("/closedform")
    if request.path == "/retry":
        ATTEMPTS["/retry"] = ATTEMPTS.get("/retry", 0) + 1
        if ATTEMPTS["/retry"] <= 2:
            return web.Response(status=429, text="rate limited")
        return web.Response(text=CONFIRM, content_type="text/html")
    return web.Response(text=BODIES.get(request.path, UNKNOWN), content_type="text/html")


async def handle_closed(request):
    return web.Response(text="<html><body>Ditutup</body></html>", content_type="text/html")


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
    assert classify_submission(THANK_YOU) == "recorded"
    assert classify_submission(CLOSED) == "closed"
    assert classify_submission(CLOSED_CLASS_ONLY) == "closed"
    assert classify_submission(REJECTED) == "rejected"
    assert classify_submission(UNKNOWN) == "unknown"
    assert classify_submission("") == "unknown"
    # A confirmation page wins even when it also carries the form script marker.
    assert classify_submission(CONFIRM + "FB_PUBLIC_LOAD_DATA_") == "recorded"
    # With the form's questions, classification does not depend on the page language.
    questions = [{"text": "Nama lengkap"}]
    assert classify_submission(REJECTED, questions) == "rejected"
    assert classify_submission(LOCALIZED_REJECTED, questions) == "rejected"
    assert classify_submission(LOCALIZED_CONFIRM, questions) == "recorded"
    assert classify_submission(NO_HEADING_CONFIRM, questions) == "recorded"
    assert classify_submission(SHORT_REJECTED, [{"text": "Umur"}]) == "rejected"


async def check_send(port: int) -> None:
    expected = {
        "/recorded": (True, None, "recorded"),
        "/closed": (False, "Form is no longer accepting responses", "closed"),
        "/rejected": (False, "Answer rejected (not recorded)", "rejected"),
        "/unknown": (True, None, "recorded"),
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


async def check_retry(port: int) -> None:
    ATTEMPTS.clear()
    engine = SubmissionEngine(details_for(port, "/retry"))
    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
        result = await engine._send_request(session, {"entry.1": "Siti"})
    assert result == (True, None, "recorded"), result
    assert engine.stats["retries"] == 2, engine.stats
    assert engine.stats["success"] == 1, engine.stats


async def check_closed(port: int) -> None:
    engine = SubmissionEngine(details_for(port, "/closed-redirect"))
    async with aiohttp.ClientSession(timeout=REQUEST_TIMEOUT) as session:
        result = await engine._send_request(session, {"entry.1": "Siti"})
    assert result == (False, "Form is no longer accepting responses", "closed"), result
    assert engine.stats["failed"] == 1, engine.stats


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


def check_generation() -> None:
    details = FormDetails(
        url="offline",
        form_action_url="offline",
        questions={
            "entry.1": {"text": "Start date", "type": "Date", "options": [],
                        "required": False, "include_time": True, "duration": False},
            "entry.2": {"text": "Focused hours", "type": "Time", "options": [],
                        "required": False, "include_time": False, "duration": True},
            "entry.3": {"text": "Devices", "type": "Multiple Choice Grid",
                        "options": ["A", "B", "C"], "required": False,
                        "include_time": False, "duration": False, "multi": True},
            "entry.4": {"text": "Employee ID", "type": "Short Answer",
                        "options": [], "required": True, "regex": r"^EMP-[0-9]{4}$"},
            "entry.5": {"text": "Work email", "type": "Short Answer",
                        "options": [], "required": True},
            "entry.6": {"text": "Age", "type": "Short Answer",
                        "options": [], "required": True},
            "entry.7": {"text": "Short bio", "type": "Paragraph",
                        "options": [], "required": True},
            "entry.8": {"text": "Tools you use", "type": "Checkboxes",
                        "options": ["A", "B", "C"], "required": True},
        },
        hidden_fields={},
    )
    engine = SubmissionEngine(details)
    for _ in range(20):
        response = engine.generate_response()
        assert response["entry.1_year"] and response["entry.1_month"] and response["entry.1_day"]
        assert response["entry.1_hour"] and response["entry.1_minute"]
        assert response["entry.2_hour"] and response["entry.2_minute"] and response["entry.2_second"]
        assert isinstance(response["entry.3"], list) and response["entry.3"]
        assert re.fullmatch(r"EMP-\d{4}", response["entry.4"]), response["entry.4"]
        assert "@" in response["entry.5"], response["entry.5"]
        assert 18 <= int(response["entry.6"]) <= 65, response["entry.6"]
        assert len(response["entry.7"]) <= 200, len(response["entry.7"])
        assert len(response["entry.8"]) >= 2, response["entry.8"]

    assert _find_regex([[4, 299, ["^EMP-[0-9]{4}$"]]]) == r"^EMP-[0-9]{4}$"
    assert _find_regex(None) is None


async def main() -> None:
    app = web.Application()
    app.router.add_post("/{path:.*}", handle_submit)
    app.router.add_get("/closedform", handle_closed)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = runner.addresses[0][1]
    try:
        check_generation()
        check_classification()
        await check_send(port)
        await check_retry(port)
        await check_closed(port)
        with tempfile.TemporaryDirectory() as tmp:
            await check_recorded_run(port, Path(tmp))
            await check_rejected_run(port, Path(tmp))
    finally:
        await runner.cleanup()

    print("OK: response classification, verification stats, and JSONL report")


if __name__ == "__main__":
    asyncio.run(main())
