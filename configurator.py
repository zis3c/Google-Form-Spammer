import asyncio
import html as html_lib
import webbrowser
from aiohttp import web
from typing import Dict, Any, Tuple
from core import FormDetails

# Premium HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FormForge Configuration</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --card-bg: rgba(30, 41, 59, 0.7);
            --primary: #8b5cf6;
            --primary-hover: #7c3aed;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }

        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 2rem;
            min-height: 100vh;
            display: flex;
            justify-content: center;
        }

        .container { width: 100%; max-width: 800px; }

        .header { text-align: center; margin-bottom: 3rem; }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #8b5cf6, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header p { color: var(--text-muted); }

        form { display: flex; flex-direction: column; gap: 1.5rem; }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: transform 0.2s;
        }

        .card:hover { transform: translateY(-2px); border-color: var(--primary); }

        label { display: block; margin-bottom: 0.75rem; font-weight: 500; color: var(--text-main); }

        .badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            background: rgba(139, 92, 246, 0.2);
            color: #a78bfa;
            margin-bottom: 0.5rem;
        }

        input[type="text"], input[type="date"], input[type="time"], input[type="number"],
        textarea, select {
            width: 100%;
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid var(--border);
            color: white;
            padding: 0.75rem;
            border-radius: 0.5rem;
            font-size: 1rem;
            transition: all 0.2s;
            box-sizing: border-box;
        }

        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2);
        }

        .radio-group, .checkbox-group { display: flex; flex-direction: column; gap: 0.5rem; }

        .option-item { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem; border-radius: 0.375rem; cursor: pointer; }

        .option-item:hover { background: rgba(255, 255, 255, 0.05); }

        input[type="radio"], input[type="checkbox"] { accent-color: var(--primary); width: 1.25rem; height: 1.25rem; cursor: pointer; }

        .pool-row { display: grid; grid-template-columns: 1.75rem 1fr 5.5rem 5.5rem; align-items: center; gap: 0.5rem; padding: 0.25rem 0.5rem; border-radius: 0.375rem; }
        .pool-row:hover { background: rgba(255, 255, 255, 0.05); }
        .pool-row input[type="number"] { padding: 0.35rem 0.5rem; font-size: 0.875rem; }
        .pool-head { display: grid; grid-template-columns: 1.75rem 1fr 5.5rem 5.5rem; gap: 0.5rem; padding: 0 0.5rem; font-size: 0.75rem; color: var(--text-muted); }

        button.submit-btn {
            background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
            color: white;
            border: none;
            padding: 1rem;
            border-radius: 0.75rem;
            font-size: 1.125rem;
            font-weight: 600;
            cursor: pointer;
            margin-top: 2rem;
            transition: opacity 0.2s;
        }

        button.submit-btn:hover { opacity: 0.9; }

        .helper { font-size: 0.875rem; color: var(--text-muted); margin-top: 0.5rem; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>FormForge Configuration</h1>
            <p>Customize specific answers for the target form.</p>
        </div>
        <form action="/submit" method="post">
            {form_content}
            <button type="submit" class="submit-btn" id="startBtn">Start Run</button>
        </form>
    </div>
</body>
</html>
"""

TEXT_TYPES = ["Short Answer", "Paragraph", "Date", "Time", "Open Ended"]
CHOICE_TYPES = ["Multiple Choice", "Dropdown", "Linear Scale", "Multiple Choice Grid"]


def _esc(value: str) -> str:
    return html_lib.escape(value, quote=True)


def _pool_table(q_id: str, options) -> str:
    """Checkbox + weight + quota row per option."""
    rows = []
    for i, opt in enumerate(options):
        rows.append(f"""
            <div class="pool-row">
                <input type="checkbox" name="{q_id}__sel{i}" value="1">
                <span>{_esc(opt)}</span>
                <input type="number" name="{q_id}__w{i}" value="1" min="0" step="0.1" title="Weight">
                <input type="number" name="{q_id}__q{i}" placeholder="-" min="1" title="Quota (max uses)">
            </div>
        """)
    return f"""
        <div class="pool-head"><span></span><span>Option</span><span>Weight</span><span>Quota</span></div>
        {''.join(rows)}
    """


def generate_form_html(questions: Dict[str, Any]) -> str:
    html_parts = []

    for q_id, q_data in questions.items():
        q_text = q_data['text']
        q_type = q_data['type']
        options = q_data.get('options', [])

        field_html = ""

        if q_type in TEXT_TYPES:
            input_type = "text"
            if q_type == "Date":
                input_type = "date"
            if q_type == "Time":
                input_type = "time"

            field_html = f"""
                <input type="{input_type}" name="{q_id}" placeholder="Fixed value (leave empty to use random / weighted list)">
                <div class="helper">Nilai terbalok, satu per baris: <code>nilai|bobot|kuota</code> (bobot dan kuota opsional). Kosongkan untuk acak.</div>
                <textarea name="{q_id}__tl" rows="3" placeholder="nilai|bobot|kuota"></textarea>
            """

        elif q_type in CHOICE_TYPES:
            opts_html = [f"""
                <label class="option-item">
                    <input type="radio" name="{q_id}" value="__RANDOM__" checked>
                    <span>Random (weighted pool below, or all options if empty)</span>
                </label>
            """]
            for opt in options:
                opts_html.append(f"""
                    <label class="option-item">
                        <input type="radio" name="{q_id}" value="{_esc(opt)}">
                        <span>{_esc(opt)}</span>
                    </label>
                """)

            field_html = f"""
                <div class="radio-group">
                    {''.join(opts_html)}
                </div>
                <div class="helper">Tick options to build the weighted random pool:</div>
                <div class="checkbox-group">
                    {_pool_table(q_id, options)}
                </div>
            """

        elif q_type == "Checkboxes":
            field_html = f"""
                <div class="helper">Tick options to build the weighted pool. Leave all unticked to use every option.</div>
                <div class="checkbox-group">
                    {_pool_table(q_id, options)}
                </div>
                <div class="helper">
                    Picks per submission
                    <input type="number" name="{q_id}__pick" min="1" max="{max(len(options), 1)}" value="{max(len(options), 1)}" style="width:6rem">
                </div>
            """

        else:
            field_html = f"""<input type="text" name="{q_id}" placeholder="Custom value">"""

        html_parts.append(f"""
        <div class="card">
            <span class="badge">{q_type}</span>
            <label>{_esc(q_text)}</label>
            {field_html}
        </div>
        """)

    return "\n".join(html_parts)


def _number(value, default=None, floor=1.0):
    """Coerce a form value to a number, falling back instead of raising. floor is the inclusive minimum."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if number >= floor else default


def _is_number(value) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _parse_weighted_lines(text: str):
    entries = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            value = parts[0]
            if not value:
                continue
            weight = _number(parts[1] if len(parts) > 1 else None, 1.0, 0.0)
            quota = None
            if len(parts) > 2 and parts[2]:
                q = _number(parts[2], None, 1.0)
                quota = int(q) if q else None
            entries.append({"value": value, "weight": weight, "quota": quota})
        elif ":" in line:
            chunks = line.rsplit(":", 2)
            if len(chunks) == 3:
                v, w, q = [c.strip() for c in chunks]
                if v and _is_number(w) and _is_number(q):
                    entries.append({"value": v, "weight": float(w), "quota": int(float(q))})
                    continue
            entries.append({"value": line, "weight": 1.0, "quota": None})
        else:
            entries.append({"value": line, "weight": 1.0, "quota": None})
    return entries




def build_config(details: FormDetails, data) -> Dict[str, Any]:
    """Turns the submitted MultiDict into the custom_config consumed by the submission engine."""
    config: Dict[str, Any] = {}

    for q_id, q_data in details.questions.items():
        q_type = q_data['type']
        options = q_data.get('options') or []

        if q_type == "Checkboxes":
            pool = []
            for i, opt in enumerate(options):
                if data.get(f"{q_id}__sel{i}"):
                    weight = _number(data.get(f"{q_id}__w{i}"), 1.0, 0.0)
                    quota_raw = (data.get(f"{q_id}__q{i}") or "").strip()
                    pool.append({
                        "value": opt,
                        "weight": weight,
                        "quota": int(quota_raw) if quota_raw.isdigit() and int(quota_raw) > 0 else None,
                    })
            if pool:
                config[f"{q_id}__pool"] = pool
                pick = (data.get(f"{q_id}__pick") or "").strip()
                config[f"{q_id}__pick"] = max(1, min(int(pick), len(pool))) if pick.isdigit() else len(pool)

        elif q_type in CHOICE_TYPES:
            val = data.get(q_id)
            if val and val != "__RANDOM__":
                config[q_id] = val
                continue
            pool = []
            for i, opt in enumerate(options):
                if data.get(f"{q_id}__sel{i}"):
                    weight = _number(data.get(f"{q_id}__w{i}"), 1.0, 0.0)
                    quota_raw = (data.get(f"{q_id}__q{i}") or "").strip()
                    pool.append({
                        "value": opt,
                        "weight": weight,
                        "quota": int(quota_raw) if quota_raw.isdigit() and int(quota_raw) > 0 else None,
                    })
            if pool:
                config[f"{q_id}__pool"] = pool

        else:
            val = data.get(q_id)
            if val:
                config[q_id] = val
                continue
            pool = _parse_weighted_lines(data.get(f"{q_id}__tl", ""))
            if pool:
                config[f"{q_id}__pool"] = pool

    return config


async def run_configurator(details: FormDetails) -> Tuple[Dict[str, Any], str]:
    """Starts the web server and waits for the user to submit the config."""

    config_future = asyncio.Future()

    async def handle_index(request):
        form_content = generate_form_html(details.questions)
        html = HTML_TEMPLATE.replace("{form_content}", form_content)
        return web.Response(text=html, content_type='text/html')

    async def handle_submit(request):
        origin = request.headers.get("Origin")
        if origin:
            try:
                from urllib.parse import urlparse
                origin_host = urlparse(origin).netloc.lower().split(":")[0]
            except Exception:
                origin_host = None
            own_host = request.host.split(":")[0]
            if origin_host and origin_host != own_host:
                return web.Response(status=403, text="Forbidden: cross-origin request rejected")
        data = await request.post()
        config = build_config(details, data)

        if not config_future.done():
            config_future.set_result(config)

        return web.Response(text="<h1>Konfigurasi dimuat. Anda dapat menutup tab ini; proses berjalan.</h1>", content_type='text/html')

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index),
        web.post('/submit', handle_submit)
    ])

    runner = web.AppRunner(app)
    await runner.setup()
    try:
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
    except OSError:
        site = web.TCPSite(runner, 'localhost', 0)
        await site.start()
    port = runner.addresses[0][1]
    url = f"http://localhost:{port}"

    print(f"Silakan buka: {url}")

    try:
        webbrowser.open(url)
    except Exception:
        pass

    try:
        result = await asyncio.wait_for(config_future, timeout=1800)
    except asyncio.TimeoutError:
        print("No configuration submitted in 30 minutes; keeping random mode.")
        result = {}
    except asyncio.CancelledError:
        result = {}
    finally:
        await runner.cleanup()

    return result, url