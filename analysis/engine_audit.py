"""Run MentalHealthAssessmentEngine.assess() on every recorded report.

Writes analysis/engine_audit.json. The dashboard build checks its JS port of
the engine against this file, so the two cannot drift apart silently.

Run: python analysis/engine_audit.py   (needs numpy only)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "features"))
from mental_health_assessment import MentalHealthAssessmentEngine  # noqa: E402

engine = MentalHealthAssessmentEngine()
rows = []
for path in sorted(ROOT.glob("Records/*/*_report.json")):
    report = json.loads(path.read_text())
    p = engine.assess(report)
    rows.append({
        "report": path.name,
        "stress": p.stress_score,
        "anxiety": p.anxiety_score,
        "burnout": p.burnout_score,
        "cognitive_load": p.cognitive_load_score,
        "wellness": p.overall_wellness,
        "indicators": {k: round(float(v), 6) for k, v in p.indicators.items()},
    })

out = ROOT / "analysis" / "engine_audit.json"
out.write_text(json.dumps({"engine": "features/mental_health_assessment.py", "reports": rows}, indent=1) + "\n")
stress = sorted({r["stress"] for r in rows})
anxiety = sorted({r["anxiety"] for r in rows})
print(f"{len(rows)} reports; distinct stress {stress}; distinct anxiety {anxiety}")
