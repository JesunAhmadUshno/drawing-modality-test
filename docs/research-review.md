# Research review: PulseKey drawing-modality prototype

Reviewed 7 November 2026 against a doctoral-level research rubric plus an engineering-rigor check.
Every figure below can be regenerated: `python analysis/engine_audit.py`, `python -m pytest tests`,
and `cd site && npm run build` (which runs `site/src/pipeline.check.mjs`). The live dashboard computes
the same figures from `Records/` at build time.

**Overall grade: D (2 out of 5).** The capture and feature-engineering code is solid and now regression-tested
against its own saved output. The research claims are not supported: there is no validity evidence, the
dataset is small and mostly duplicated, and the paper's results section reports numbers the code and
records do not produce.

## Scorecard

| Criterion | Grade | Finding |
| :--- | :---: | :--- |
| Research question | C | Clear aim ("drawing dynamics as a psychomotor signal of stress, anxiety, burnout, cognitive load"), but stated as a capability, not as a falsifiable question. |
| Hypotheses | F | None are written down or pre-registered. The paper's section 4.4 correlations read as confirmations, not tests. |
| Method and construct validity | F | No ground-truth labels (no PHQ-9, GAD-7, PSS or burnout inventory, no induced-stress condition). The four scores are hand-set weightings, not measurements. |
| Measurement correctness | D | Dynamic features are correct and reproducible (the JS port matches the saved reports to 1e-9). The engine is broken: `_extract_indicators` reads `features.dynamic.temporal.acceleration_profile`, `features.dynamic.motion.avg_speed_per_stroke`, `features.dynamic.rhythm.rhythm_regularity` and `features.dynamic.timing.pause_events`, none of which the pipeline writes, and `_calculate_pressure_stability` expects `raw_session_data.tasks` as a list. Stress is therefore 5.0 and anxiety 12.5 in all 29 reports. |
| Scoring design | D | Efficiency = 0.6·(1 − speed variance / 1000) + 0.4·(1 − pauses / 20). Speed variance is far below 1 px²/ms², so the first term is always about 60; pauses are every gap between strokes with no duration threshold, so any drawing with more than 20 strokes zeroes the second term. Every substantive session scores about 60 efficiency and grades F (scores 29.59 to 45.51). |
| Unit of analysis | D | `backend_api.py` concatenates all seven tasks into one stroke list before analysis. Geometry (bounding box, compactness, symmetry) is computed over overlapping unrelated drawings, and the six inter-task gaps count as pauses. The dashboard's per-task view shows the size of the effect. |
| Data | F | 35 session JSON files hold 12 distinct stroke payloads (23 resubmissions, one empty); 8 have at least 500 points; they appear to come from one participant. Every one of the 151,656 recorded pressure values is 0.5 (mouse input), so pressure features carry no information. |
| Baselines | F | No baseline (for example a random or constant scorer, or a simple speed-only model) and no comparison condition. |
| Statistics and uncertainty | F | No intervals, no test-retest reliability, no left- vs right-hand comparison although tasks 6 and 7 were designed for it. Correlations between constants are reported as r = 0.62. |
| Reproducibility | C | Now good for the code path: pinned `requirements-test.txt`, 14/14 integration tests plus 6 pytest smoke tests that re-run the pipeline against saved reports, a build-time parity check, and a committed engine audit. Weak for the paper: section 4 cannot be regenerated from anything in the repo. Stroke frequency cannot be reproduced because the saved JSON drops the session start and end times. |
| Threats to validity | D | The paper's section 6 lists generic limitations but not the specific defects above. The dashboard and this review now list them. |
| Related work | D | Citations are thin and two look misplaced: Viterbi (1967) on convolutional codes has no evident role, and "Ramirez-Mahaluf et al. (2018), Tremor and Parkinson's disease, Nature Reviews Disease Primers" could not be matched to a known article and should be verified or removed. |
| Limitations and honesty | C | The README already frames the project as a research prototype. The paper and `mental_health_assessment.py` still present the scores as assessments and recommendations. |
| Engineering rigor | C | Readable modules and a working capture app. Weaknesses: committed `__pycache__/*.pyc` files, a custom test harness that used to pass silently when data was missing, unpinned `>=` ranges in `requirements.txt`, many overlapping setup documents, and every frontend analysis call hard-coded to `http://localhost:5000`. |

## Fixed in this pass (cheap)

- Engine audit script `analysis/engine_audit.py` and its output `analysis/engine_audit.json` (29 reports, stress 5.0 and anxiety 12.5 for each).
- Dated reproducibility notes appended to the README results table and to the start of the paper's section 4. Nothing was deleted.
- `tests/integration_tests.py` now fails when tests are skipped, so a missing `test_data/` can no longer pass as green.
- `tests/test_smoke.py` (pytest): re-runs the pipeline on recorded sessions and checks the saved dynamic features, efficiency and grade; keeps the engine audit current; pins the efficiency saturation.
- `requirements-test.txt` with the exact versions the suite was run with.
- `.gitignore` for `__pycache__/`, `*.pyc` and the dashboard build output.
- A live dashboard (`site/`, published at `/dashboard/`) with a JS port of the pipeline that `npm run build` checks against every saved report.

## Remaining gaps and exactly what each needs

| Gap | What closes it | Cost |
| :--- | :--- | :--- |
| Engine reads keys that do not exist | Change `_extract_indicators` to read the keys the pipeline writes (or compute from raw strokes), add a test that two different sessions give different stress, then regenerate the 29 reports. Changes product behaviour and makes stored reports stale, so it needs the Owner's decision; keep it in its own commit. | About 2 hours of code, no compute. |
| Pause definition and efficiency saturation | Add a pause duration threshold (for example 250 ms, chosen before looking at outcomes) and rescale the variance term to the observed range. Also a product change needing sign-off. | About 1 hour. |
| Per-task analysis | Analyse each task separately in `backend_api.py` and store per-task features. | About half a day; existing reports would need regenerating. |
| Construct validity | Collect a validated questionnaire (PHQ-9, GAD-7, PSS-10, or a burnout inventory) alongside each session, ideally with an induced-stress condition (for example a timed arithmetic task) against a rest condition. | Ethics approval; at least 30 to 50 participants for a first correlation study, more for anything predictive. No GPU needed. |
| Pressure features | Re-collect with a stylus or pen tablet that reports real pressure. | Hardware (a pressure-sensitive tablet) and new sessions. |
| Reliability | Test-retest: each participant repeats the battery on two days; report ICCs per feature. | Same participants twice; analysis is minutes on a laptop. |
| Baselines and statistics | Pre-register hypotheses, compare against a constant and a speed-only model, report bootstrap intervals. | Analysis only, once labelled data exists. |
| Session timing | Save `sessionStartTime` and `sessionEndTime` in the session JSON so stroke frequency is reproducible. | Minutes of frontend and backend code. |
| Committed `.pyc` files | `git rm --cached` the five files under `__pycache__/` (now ignored). Deleting files the current maintainer did not create waits for the Owner's approval. | Minutes. |
| Paper section 4 | Rewrite from regenerated results once the engine is fixed and real labelled data exists, or retitle it "planned analyses". | Writing time. |
| References | Verify or remove the two misplaced citations and add the handwriting and drawing kinematics literature the method actually rests on. | A few hours of reading. |
