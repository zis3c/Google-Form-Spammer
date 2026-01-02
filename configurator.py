import asyncio
import webbrowser
from aiohttp import web
import json
from typing import Dict, Any
from core import FormDetails

# Premium HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Form Attack Configuration</title>
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

        .container {
            width: 100%;
            max-width: 800px;
        }

        .header {
            text-align: center;
            margin-bottom: 3rem;
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(to right, #8b5cf6, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header p {
            color: var(--text-muted);
        }

        form {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .card {
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: transform 0.2s;
        }

        .card:hover {
            transform: translateY(-2px);
            border-color: var(--primary);
        }

        label {
            display: block;
            margin-bottom: 0.75rem;
            font-weight: 500;
            color: var(--text-main);
        }

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

        input[type="text"], 
        input[type="date"], 
        input[type="time"],
        textarea,
        select {
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

        .radio-group, .checkbox-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .option-item {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem;
            border-radius: 0.375rem;
            cursor: pointer;
        }

        .option-item:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        input[type="radio"], input[type="checkbox"] {
            accent-color: var(--primary);
            width: 1.25rem;
            height: 1.25rem;
            cursor: pointer;
        }

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

        button.submit-btn:hover {
            opacity: 0.9;
        }

        .helper {
            font-size: 0.875rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Attack Configuration</h1>
            <p>Customize specific answers for the target form.</p>
        </div>
        
        <form action="/submit" method="post">
            {form_content}
            <button type="submit" class="submit-btn" id="startBtn">🚀 Launch Attack</button>
        </form>
    </div>
</body>
</html>
"""

def generate_form_html(questions: Dict[str, Any]) -> str:
    html_parts = []
    
    for q_id, q_data in questions.items():
        q_text = q_data['text']
        q_type = q_data['type']
        options = q_data.get('options', [])
        
        field_html = ""
        
        if q_type in ["Short Answer", "Paragraph", "Date", "Time", "Open Ended"]:
            input_type = "text"
            if q_type == "Date": input_type = "date"
            if q_type == "Time": input_type = "time"
            
            field_html = f"""
                <input type="{input_type}" name="{q_id}" placeholder="Enter value for random (leave empty)">
                <div class="helper">Leave empty to use random generation.</div>
            """
            
        elif q_type in ["Multiple Choice", "Dropdown", "Linear Scale", "Multiple Choice Grid"]:
            opts_html = []
            # Add a "Random" option first
            opts_html.append(f"""
                <label class="option-item">
                    <input type="radio" name="{q_id}" value="__RANDOM__" checked>
                    <span>Random (Default)</span>
                </label>
            """)
            
            for opt in options:
                # Escape quotes in value
                safe_val = opt.replace('"', '&quot;')
                opts_html.append(f"""
                    <label class="option-item">
                        <input type="radio" name="{q_id}" value="{safe_val}">
                        <span>{opt}</span>
                    </label>
                """)
            
            field_html = f"""
                <div class="radio-group">
                    {''.join(opts_html)}
                </div>
            """
            
        elif q_type == "Checkboxes":
            opts_html = []
            for opt in options:
                safe_val = opt.replace('"', '&quot;')
                opts_html.append(f"""
                    <label class="option-item">
                        <input type="checkbox" name="{q_id}" value="{safe_val}">
                        <span>{opt}</span>
                    </label>
                """)
                
            field_html = f"""
                <div class="checkbox-group">
                    {''.join(opts_html)}
                </div>
                <div class="helper">Select none for random selection.</div>
            """

        else:
            # Fallback
            field_html = f"""<input type="text" name="{q_id}" placeholder="Custom value">"""

        card = f"""
        <div class="card">
            <span class="badge">{q_type}</span>
            <label>{q_text}</label>
            {field_html}
        </div>
        """
        html_parts.append(card)
        
    return "\n".join(html_parts)

async def run_configurator(details: FormDetails) -> Dict[str, Any]:
    """Starts the web server and waits for the user to submit the config."""
    
    # Create a Future to hold the result
    config_future = asyncio.Future()
    
    async def handle_index(request):
        form_content = generate_form_html(details.questions)
        # Use replace instead of format to avoid issues with CSS curly braces
        html = HTML_TEMPLATE.replace("{form_content}", form_content)
        return web.Response(text=html, content_type='text/html')

    async def handle_submit(request):
        data = await request.post()
        config = {}
        
        # Process the MultiDict
        # Checkboxes can have multiple values for same key
        for q_id, q_data in details.questions.items():
            if q_id not in data:
                continue
                
            if q_data['type'] == "Checkboxes":
                # Get all values for this key
                values = data.getall(q_id)
                # Filter out empty or placeholders if any (though logic below handles valid opts)
                if values:
                    config[q_id] = values
            else:
                val = data.get(q_id)
                if val and val != "__RANDOM__": 
                    config[q_id] = val
                    
        # Set the result
        if not config_future.done():
            config_future.set_result(config)
            
        return web.Response(text="<h1>Configuration Loaded! You can close this tab. Attack Starting...</h1>", content_type='text/html')

    app = web.Application()
    app.add_routes([
        web.get('/', handle_index),
        web.post('/submit', handle_submit)
    ])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    
    print("Please open: http://localhost:8080")
    
    # Auto-open browser
    try:
        webbrowser.open("http://localhost:8080")
    except:
        pass
    
    # Wait for the future to be set
    try:
        result = await config_future
    except asyncio.CancelledError:
        result = {}
    finally:
        await runner.cleanup()
        
    return result
