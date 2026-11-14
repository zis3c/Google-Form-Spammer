#!/usr/bin/env python3
"""Local web UI for the Google Forms runner.

Usage: python webapp.py [--host 127.0.0.1] [--port 8000] [--no-browser]
"""
import argparse
import asyncio
import json
import math
import time
import uuid
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

from aiohttp import web

from core import SubmissionEngine, FormParser, is_google_form_url

ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"
MAX_COUNT = 100000
MAX_WORKERS = 200

RUNS = {}


def clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


def _number(value, default=None, floor: float = 0.0):
    """Coerce a JSON number-ish value; anything unusable becomes default."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number >= floor else default


def sanitize_config(config: dict, details) -> dict:
    """Keep only real question ids/options and canonicalise option casing."""
    out = {}
    for qid, qdata in details.questions.items():
        options = qdata.get("options") or []
        canon = {o.lower(): o for o in options}

        pool = config.get(f"{qid}__pool")
        if isinstance(pool, list):
            entries = []
            for item in pool:
                if isinstance(item, str):
                    item = {"value": item}
                if not isinstance(item, dict):
                    continue
                value = str(item.get("value", "")).strip()
                real = canon.get(value.lower()) if options else value
                if not real:
                    continue
                entries.append({
                    "value": real,
                    "weight": _number(item.get("weight"), 1.0, 0.0),
                    "quota": int(_number(item.get("quota")) or 0) or None,
                })
            if entries:
                out[f"{qid}__pool"] = entries

        pick = _number(config.get(f"{qid}__pick"))
        qtype = qdata.get("type") or ""
        if pick and (qtype == "Checkboxes" or qtype.endswith("Grid")):
            out[f"{qid}__pick"] = clamp(int(pick), 1, max(len(options), 1))

        fixed = config.get(qid)
        if fixed not in (None, ""):
            out[qid] = str(fixed)
    return out


async def get_details(url: str):
    if not is_google_form_url(url):
        raise web.HTTPBadRequest(
            content_type="application/json",
            text=json.dumps({"error": "URL bukan Google Forms."}),
        )
    try:
        return await FormParser(url).fetch_details()
    except ValueError as exc:
        raise web.HTTPBadRequest(
            content_type="application/json",
            text=json.dumps({"error": str(exc)}),
        )
    except RuntimeError as exc:
        raise web.HTTPBadGateway(
            content_type="application/json",
            text=json.dumps({"error": str(exc)}),
        )


class RunState:
    def __init__(self, engine, total: int, workers: int):
        self.id = uuid.uuid4().hex[:12]
        self.engine = engine
        self.total = total
        self.workers = workers
        self.done = 0
        self.status = "running"
        self.error = None
        self.started = time.time()
        self.events = asyncio.Queue()
        self.task = None

    def snapshot(self) -> dict:
        stats = self.engine.stats
        return {
            "run_id": self.id,
            "done": self.done,
            "total": self.total,
            "success": stats["success"],
            "failed": stats["failed"],
            "retries": stats["retries"],
            "unverified": stats["unverified"],
            "status": self.status,
            "error": self.error,
            "errors": dict(sorted(stats["errors"].items(), key=lambda kv: -kv[1])[:10]),
        }

    def progress(self, success: bool) -> None:
        self.done += 1
        self.events.put_nowait(self.snapshot())

    def finish(self, status: str, error: str = None) -> None:
        self.status = status
        self.error = error
        self.events.put_nowait(self.snapshot())


async def execute(run: RunState, config: dict) -> None:
    try:
        await run.engine.run(run.total, run.workers, custom_config=config,
                              progress_callback=run.progress)
        run.finish("done")
    except asyncio.CancelledError:
        run.finish("cancelled")
        raise
    except Exception as exc:  # noqa: BLE001 - surfaced to the browser
        run.finish("error", str(exc))

def _json_error(status: int, code: str, message: str = None) -> web.Response:
    payload = {"error": code}
    if message is not None:
        payload["message"] = message
    return web.Response(
        status=status,
        content_type="application/json",
        text=json.dumps(payload),
    )


def _origin_ok(request: web.Request) -> bool:
    origin = request.headers.get("Origin")
    if not origin:
        return True
    try:
        o = urlparse(origin.strip())
    except ValueError:
        return False
    ohost = (o.hostname or "").lower()
    oport = o.port or (443 if o.scheme == "https" else 80)
    hhost = (request.host.split(":")[0] or "").lower()
    # request.host may already include port; compare default ports sensibly.
    hparts = request.host.rsplit(":", 1)
    if len(hparts) == 2 and hparts[1].isdigit():
        hhost = hparts[0].lower()
        hport = int(hparts[1])
    else:
        # Behind the Cloudflare tunnel the origin hop is plain HTTP; the edge
        # terminates TLS and forwards the original scheme.
        scheme = (request.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip().lower()
        if not scheme:
            try:
                scheme = json.loads(request.headers.get("CF-Visitor", "{}")).get("scheme", "")
            except ValueError:
                scheme = ""
        scheme = scheme or request.scheme
        hport = 443 if scheme == "https" else 80
    return ohost == hhost and oport == hport
def _parse_count_workers(body: dict):
    count_raw = body.get("count", 1)
    workers_raw = body.get("workers", 8)
    if isinstance(count_raw, bool) or isinstance(count_raw, float):
        return None, "count"
    try:
        count = int(count_raw)
    except (TypeError, ValueError):
        return None, "count"
    if not math.isfinite(count) or not 1 <= count <= MAX_COUNT:
        return None, "count"
    if isinstance(workers_raw, bool) or isinstance(workers_raw, float):
        return None, "workers"
    try:
        workers = int(workers_raw)
    except (TypeError, ValueError):
        return None, "workers"
    if not math.isfinite(workers) or not 1 <= workers <= MAX_WORKERS:
        return None, "workers"
    config = body.get("config")
    if config is not None and not isinstance(config, dict):
        return None, "config"
    return count, workers, config


async def handle_index(request):

    return web.FileResponse(WEB_ROOT / "index.html")


async def handle_parse(request):
    if not _origin_ok(request):
        return _json_error(403, "cross-origin")
    if request.content_type != "application/json":
        return _json_error(400, "content-type")
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return _json_error(400, "body")
    if not isinstance(body, dict):
        return _json_error(400, "body")
    url = (body.get("url") or "").strip()
    details = await get_details(url)
    return web.json_response({
        "url": url,
        "questions": [
            {"id": qid, "text": q["text"], "type": q["type"],
             "options": q.get("options") or [], "required": q.get("required", False)}
            for qid, q in details.questions.items()
        ],
    })


async def handle_run(request):
    if not _origin_ok(request):
        return _json_error(403, "cross-origin")
    if request.content_type != "application/json":
        return _json_error(400, "content-type")
    try:
        body = await request.json()
    except json.JSONDecodeError:
        return _json_error(400, "body")
    if not isinstance(body, dict):
        return _json_error(400, "body")

    parsed = _parse_count_workers(body)
    if parsed[0] is None:
        return _json_error(400, parsed[1])
    count, workers, config = parsed

    url = (body.get("url") or "").strip()
    details = await get_details(url)

    config = sanitize_config(config or {}, details)

    if any(r.status == "running" for r in RUNS.values()):
        return _json_error(409, "conflict")

    run = RunState(SubmissionEngine(details), count, workers)
    run.task = asyncio.create_task(execute(run, config))
    RUNS[run.id] = run

    for old in list(RUNS.values()):
        if old.status != "running" and len(RUNS) > 50:
            RUNS.pop(old.id, None)

    return web.json_response({"run_id": run.id, "count": count, "workers": workers})


async def handle_events(request):
    run = RUNS.get(request.match_info["run_id"])
    if not run:
        raise web.HTTPNotFound(text="run tidak ditemukan")

    resp = web.StreamResponse(headers={
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    })
    await resp.prepare(request)

    # A finished run whose events were already drained still needs a terminal event.
    if run.status != "running" and run.events.empty():
        await resp.write(f"data: {json.dumps(run.snapshot())}\n\n".encode())
        await resp.write_eof()
        return resp

    while True:
        try:
            payload = await asyncio.wait_for(run.events.get(), timeout=15)
        except asyncio.TimeoutError:
            await resp.write(b": ping\n\n")
            continue
        await resp.write(f"data: {json.dumps(payload)}\n\n".encode())
        if payload["status"] != "running":
            break
    await resp.write_eof()
    return resp


async def handle_cancel(request):
    if not _origin_ok(request):
        return _json_error(403, "cross-origin")
    if request.content_type != "application/json":
        return _json_error(400, "content-type")
    run = RUNS.get(request.match_info["run_id"])
    if not run:
        raise web.HTTPNotFound(text="run tidak ditemukan")
    if run.task and not run.task.done():
        run.task.cancel()
        try:
            await run.task
        except asyncio.CancelledError:
            pass
    return web.json_response({"status": run.status})


def build_app() -> web.Application:
    app = web.Application()
    app.add_routes([
        web.get("/", handle_index),
        web.post("/api/parse", handle_parse),
        web.post("/api/run", handle_run),
        web.get("/api/run/{run_id}/events", handle_events),
        web.post("/api/run/{run_id}/cancel", handle_cancel),
    ])
    return app


def main() -> None:
    parser = argparse.ArgumentParser(description="FormForge web UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    if args.host not in ("127.0.0.1", "localhost", "::1"):
        print(
            "PERINGATAN: server tidak memiliki autentikasi dan dapat diakses oleh "
            "orang lain dalam jaringan."
        )

    async def serve():
        runner = web.AppRunner(build_app())
        await runner.setup()
        site = web.TCPSite(runner, args.host, args.port)
        await site.start()
        port = runner.addresses[0][1]
        url = f"http://{args.host}:{port}"
        print(f"Web UI: {url}")
        if not args.no_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        await asyncio.Event().wait()

    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
