import json
from pathlib import Path
from ygg.dashboard.app import create_app

def test_dashboard_api(tmp_path):
    cases_dir = tmp_path / "cases"
    cases_dir.mkdir(parents=True)
    (cases_dir / "2025-01-27.json").write_text(json.dumps({"case": {"day": "2025-01-27"}}), encoding="utf-8")
    
    app = create_app(tmp_path)
    if app is None:
        return  # FastAPI optional in dev test
        
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    resp = client.get("/api/cases")
    assert resp.status_code == 200
    assert resp.json() == ["2025-01-27"]
    
    case_resp = client.get("/api/cases/2025-01-27")
    assert case_resp.status_code == 200
    assert case_resp.json()["case"]["day"] == "2025-01-27"
