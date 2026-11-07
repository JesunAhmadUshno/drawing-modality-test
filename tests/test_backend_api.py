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
