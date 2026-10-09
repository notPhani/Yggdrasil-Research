"""FastAPI lightweight dashboard application for inspecting Yggdrasil cases."""
from __future__ import annotations

import json
from pathlib import Path

HTML_VIEWER = """<!DOCTYPE html>
<html>
<head>
    <title>Yggdrasil Forensics Viewer</title>
    <style>
        body { font-family: monospace; background: #0d1117; color: #c9d1d9; padding: 20px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 15px; margin-bottom: 20px; }
        h1, h2 { color: #58a6ff; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #30363d; padding: 8px; text-align: left; }
        th { background: #21262d; }
        .supported { color: #7ee787; }
        .consistent { color: #d29922; }
    </style>
</head>
<body>
    <h1>Yggdrasil Market Event Forensics</h1>
    <div id="content">Loading cases...</div>
    <script>
        fetch('/api/cases')
            .then(res => res.json())
            .then(data => {
                let html = '<div class="card"><h2>Recorded Cases</h2><ul>';
                data.forEach(c => { html += `<li><a href="/case/${c}" style="color:#58a6ff;">Case ${c}</a></li>`; });
                html += '</ul></div>';
                document.getElementById('content').innerHTML = html;
            });
    </script>
</body>
</html>
"""


def create_app(data_dir: Path):
    try:
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse
    except ImportError:
        return None

    app = FastAPI(title="Yggdrasil Forensics")
    data_dir = Path(data_dir)

    @app.get("/", response_class=HTMLResponse)
    def index():
        return HTML_VIEWER

    @app.get("/api/cases")
    def list_cases():
        cases_dir = data_dir / "cases"
        if not cases_dir.exists():
            return []
        return sorted(p.stem for p in cases_dir.glob("*.json") if p.stem != "plan")

    @app.get("/api/cases/{day}")
    def get_case(day: str):
        path = data_dir / "cases" / f"{day}.json"
        if not path.exists():
            return {"error": "Case not found"}
        return json.loads(path.read_text(encoding="utf-8"))

    return app
