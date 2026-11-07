"""Tests for the Flask backend's /api/submit route. Each test runs in a temp dir so Records/ stays clean.

Run: python -m pytest tests (needs flask and flask-cors on top of requirements-test.txt)
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
pytest.importorskip("flask")
pytest.importorskip("flask_cors")
import backend_api  # noqa: E402

SESSION = ROOT / "Records/session-1772353073240/JSON/session-1772353073240.json"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return backend_api.app.test_client()


def test_submit_with_strokes_saves_report(client, tmp_path):
    data = json.loads(SESSION.read_text())
    r = client.post("/api/submit", json=data)
    assert r.status_code == 200, r.get_json()
    sid = data["sessionId"]
    report = json.loads((tmp_path / "Records" / sid / f"{sid}_report.json").read_text())
    assert "wellness_level" in report["mental_health_assessment"]


PNG = "UFdORUQ="  # base64 of b"PWNED"


@pytest.mark.parametrize("body", [
    {"sessionId": "../escaped", "tasks": {}},
    {"sessionId": "/tmp/abs-session", "tasks": {}},
    {"sessionId": "ok-1", "tasks": {"1": {"pngData": PNG, "pngFileName": "ABS_TARGET"}}},
    {"sessionId": "ok-2", "tasks": {"1": {"pngData": PNG, "pngFileName": "../../out.png"}}},
    {"sessionId": "ok-3", "tasks": {"../../x": {"pngData": PNG}}},
])
def test_submit_rejects_names_that_escape_the_session_folder(client, tmp_path, monkeypatch, body):
    body = json.loads(json.dumps(body).replace("ABS_TARGET", str(tmp_path / "abs_write.txt")))
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)  # Records/ sits one level down, so an escape lands in tmp_path
    r = client.post("/api/submit", json=body)
    assert r.status_code == 400, r.get_json()
    written = sorted(str(p.relative_to(tmp_path)) for p in tmp_path.rglob("*") if p.is_file())
    assert written == [], written
    assert not (tmp_path / "escaped").exists() and not Path("/tmp/abs-session").exists()


def test_read_routes_reject_dot_dot_session_id(client):
    assert client.get("/api/mental-health/..").status_code == 400
