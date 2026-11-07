"""Pytest-discoverable smoke tests: re-run the pipeline on recorded sessions and compare with the
reports the backend saved, and keep analysis/engine_audit.json in step with the engine.

Run: python -m pytest tests
"""
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "features"))

from integration_pipeline import DrawingModalityPipeline  # noqa: E402
from mental_health_assessment import MentalHealthAssessmentEngine  # noqa: E402

SCORED = sorted(
    p for p in ROOT.glob("Records/session-*/*_report.json")
    if json.loads(p.read_text()).get("features", {}).get("dynamic", {}).get("speed")
)


def backend_session(session_json):
    """Rebuild the analysis input the way backend_api.py does: all tasks' strokes in one list."""
    raw = json.loads(session_json.read_text())
    strokes = [s for t in raw["tasks"].values() for s in t.get("strokes", [])]
    return {"sessionId": raw["sessionId"], "sessionStartTime": raw["timestamp"], "sessionEndTime": raw["timestamp"],
            "deviceInfo": {}, "strokes": strokes}


def test_recorded_reports_exist():
    assert len(SCORED) >= 20


@pytest.mark.parametrize("report_path", SCORED[:3], ids=lambda p: p.parent.name)
def test_pipeline_reproduces_recorded_report(report_path):
    report = json.loads(report_path.read_text())
    sid = report_path.parent.name
    pipe = DrawingModalityPipeline(canvas_size=(900, 650))
    result = pipe.analyze_session(backend_session(report_path.parent / "JSON" / f"{sid}.json"))
    got, want = result["dynamic_features"], report["features"]["dynamic"]
    for group in ("speed", "acceleration", "pauses", "movement"):
        for key, value in want[group].items():
            assert math.isclose(got[group][key], value, rel_tol=1e-9), f"{group}.{key}"
    a = result["combined_analysis"]["analysis"]
    assert a["drawing_efficiency"] == report["analysis"]["assessment"]["drawing_efficiency"]
    assert a["overall_assessment"]["grade"] == report["analysis"]["assessment"]["overall_assessment"]["grade"]


def test_engine_audit_is_current():
    audit = json.loads((ROOT / "analysis" / "engine_audit.json").read_text())
    engine = MentalHealthAssessmentEngine()
    assert len(audit["reports"]) == len(list(ROOT.glob("Records/*/*_report.json")))
    for row in audit["reports"]:
        report = json.loads(next(ROOT.glob(f"Records/*/{row['report']}")).read_text())
        p = engine.assess(report)
        assert (p.stress_score, p.anxiety_score, p.burnout_score) == (row["stress"], row["anxiety"], row["burnout"])


def test_efficiency_saturates_past_twenty_pauses():
    pipe = DrawingModalityPipeline()
    eff = [pipe._calculate_efficiency({"speed": {"variance": 0.1}, "pauses": {"count": n}}) for n in (20, 40, 80)]
    assert eff[0] == eff[1] == eff[2] == pytest.approx(59.99, abs=0.01)
