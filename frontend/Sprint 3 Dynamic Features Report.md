# Sprint 3 Dynamic Features Report

**To:** Siamak  
**From:** Jesun  
**Date:** February 27, 2026  
**Scope:** Sprint 3 Dynamic Feature Extraction (Behavioral + Temporal)  
**Status:** Complete, validated, integration-ready

---

## 1) Executive Summary

Sprint 3 dynamic feature engineering is complete and production-ready. The implementation delivers a robust extraction pipeline for **24 dynamic metrics** from drawing-session JSON, with temporal validation, stroke-level signal processing, and export-ready outputs.

This module is designed to pair cleanly with:
- existing capture stack in `docs/` (`drawingCapture.js`, `taskManager.js`)
- Aramide's static feature module (18 geometric metrics)

Combined, the system supports a full **42-feature profile** (static + dynamic) for downstream assessment, scoring, and modeling.

---

## 2) Deliverables Completed

### Core Code
- `backend/sprint-3-dynamic-features/dynamic_feature_extraction.py` (~645 LOC)

### Core Components
- `DrawingSessionValidator` (temporal and structural integrity)
- `StrokeAnalyzer` (distance, velocity, acceleration, curvature primitives)
- `DynamicFeatureExtractor` (session-level orchestration and aggregation)

### Documentation + Usage
- `backend/sprint-3-dynamic-features/DYNAMIC_FEATURES_DOCUMENTATION.md`
- `backend/sprint-3-dynamic-features/usage_examples.py`
- Notebook-based validation executed successfully

---

## 3) System Architecture

### 3.1 Logical Architecture

```
Session JSON
  ↓
Validation Layer
  (schema + timestamp monotonicity + stroke integrity)
  ↓
Signal Layer
  (distance, time deltas, velocity, acceleration, curvature)
  ↓
Feature Layer
  (24 dynamic features grouped by behavioral domain)
  ↓
Export Layer
  (dict/DataFrame for merge with static features)
```

### 3.2 Module Responsibility Split

1. **DrawingSessionValidator**
  - Ensures required fields exist (`sessionId`, `taskStartTime`, `strokes`, `deviceInfo`)
  - Validates temporal order and timestamp monotonicity
  - Computes validation stats for diagnostics

2. **StrokeAnalyzer**
  - Computes geometric and temporal primitives per stroke
  - Isolates math-heavy computations for reuse and testability

3. **DynamicFeatureExtractor**
  - Orchestrates per-stroke analysis
  - Aggregates to session-level features
  - Returns consistent output object for integration pipeline

---

## 4) Data Pipeline (End-to-End)

### 4.1 Runtime Pipeline

```
Canvas Input (x, y, pressure, tilt, timestamp...)
→ docs/drawingCapture.js JSON export
→ Dynamic validator
→ StrokeAnalyzer math pass
→ Dynamic feature aggregation (24)
→ Merge with static features (18)
→ Scoring / reporting / ML input
```

### 4.2 Input/Output Contract

**Input**: Session JSON with strokes and point timestamps.  
**Output**: Structured dynamic-feature payload with lists + scalar metrics.

This aligns with existing capture schema and enables immediate integration with batch analytics and clinical scoring layers.

### 4.3 Algorithms Used (Exact)

The dynamic extractor uses deterministic numerical algorithms (no model training in this module):

1. **Temporal Integrity Validation Algorithm**
  - Rule-based schema checks + monotonic timestamp checks.
  - Rejects or warns on invalid temporal sequences.

2. **Euclidean Segment Distance Algorithm**
  - Computes point-to-point displacement using L2 norm.
  - Foundation for trajectory and velocity.

3. **Finite-Difference Velocity Estimation**
  - First derivative of position with respect to time.
  - Per-segment speed profile extraction.

4. **Finite-Difference Acceleration Estimation**
  - First derivative of velocity with respect to time.
  - Captures smoothness/jerk transitions.

5. **Vector-Angle Curvature Approximation**
  - Computes turning angle between consecutive segment vectors.
  - Approximates curvature as angle over local arc-length proxy.

6. **Threshold-Based Direction Change Detection**
  - Counts turning events above fixed threshold (default 30°).
  - Produces directional complexity metric.

7. **Inter-Stroke Pause Detection**
  - Uses consecutive stroke end/start times.
  - Builds pause duration distribution.

8. **Statistical Aggregation Algorithms**
  - Mean, max, min, variance across profiles.
  - Converts segment-level signals to session-level features.

9. **Spatial Envelope Estimation**
  - Bounding-box area from global min/max X/Y over all points.
  - Provides session-level geometric context.

---

## 5) Mathematical Foundations and Calculations

Let stroke points be $p_i=(x_i,y_i,t_i)$ for $i=1...n$.

### 5.1 Distance Per Segment

$$
d_i = \sqrt{(x_i-x_{i-1})^2 + (y_i-y_{i-1})^2}
$$

### 5.2 Time Delta Per Segment

$$
\Delta t_i = t_i - t_{i-1}
$$

### 5.3 Velocity Per Segment

$$
v_i = \frac{d_i}{\Delta t_i}
$$

### 5.4 Session Speed Metrics

$$
avg\_speed=\frac{1}{m}\sum_{i=1}^{m} v_i,
\quad
max\_speed=\max(v_i),
\quad
min\_speed=\min(v_i)
$$

$$
speed\_variance=\frac{1}{m}\sum_{i=1}^{m}(v_i-\bar v)^2
$$

### 5.5 Acceleration Profile

Using consecutive velocities:

$$
a_i = \frac{v_i - v_{i-1}}{\Delta t_i}
$$

$$
avg\_acceleration=\frac{1}{k}\sum_{i=1}^{k}|a_i|,
\quad
max\_acceleration=\max(|a_i|)
$$

$$
acceleration\_variance=\frac{1}{k}\sum_{i=1}^{k}(a_i-\bar a)^2
$$

### 5.6 Pause Logic

If stroke $s_j$ ends at $e_j$ and next stroke $s_{j+1}$ starts at $b_{j+1}$:

$$
pause_j = b_{j+1} - e_j
$$

Then:

$$
number\_of\_pauses=|\{pause_j : pause_j > 0\}|
$$

$$
avg\_pause\_duration=\frac{1}{q}\sum_{j=1}^{q}pause_j,
\quad
max\_pause\_duration=\max(pause_j)
$$

### 5.7 Rhythm and Frequency

Inter-stroke interval:

$$
ISI_j = b_{j+1}-b_j
$$

Stroke frequency:

$$
stroke\_frequency=\frac{N_{strokes}}{T_{drawing}/1000}
$$

### 5.8 Direction Change and Curvature Logic

For segment vector $\vec u_i=(x_i-x_{i-1}, y_i-y_{i-1})$, turning angle between consecutive segments:

$$
	heta_i = \arccos\left(\frac{\vec u_i\cdot\vec u_{i-1}}{\|\vec u_i\|\|\vec u_{i-1}\|}\right)
$$

- High count of significant $\theta_i$ values implies higher directional complexity.
- Curvature metrics aggregate magnitude/distribution of these directional changes.

---

## 6) Feature Logic by Behavioral Domain

### Speed Domain (5)
- Captures movement pace and consistency.
- Useful for confidence/hesitation signatures.

### Acceleration Domain (3)
- Captures smoothness vs jerkiness.
- Sensitive to unstable motor transitions.

### Timing Domain (3)
- Separates active drawing time from inactive periods.

### Pause Domain (4)
- Quantifies planning/hesitation windows between strokes.

### Rhythm Domain (3)
- Captures cadence regularity and production rate.

### Direction + Curvature Domain (4)
- Measures path complexity and control strategy.

### Session Statistics (4)
- Structural context for normalization and downstream modeling.

---

## 7) Code Review (Technical Assessment)

### 7.1 Strengths

1. **Separation of concerns**
  - Validator, analyzer, and extractor are clearly decoupled.

2. **Mathematical correctness and safeguards**
  - Euclidean distance and finite-difference derivatives are correctly applied.
  - Defensive handling around zero time deltas avoids divide-by-zero instability.

3. **Typed data containers**
  - Dataclasses improve readability, maintainability, and serialization consistency.

4. **Integration readiness**
  - Output schema is merge-friendly with static features.

5. **Validation-first pipeline**
  - Upstream data integrity checks reduce silent downstream error propagation.

### 7.2 Risks / Edge Cases (Observed)

1. **Timestamp granularity dependence**
  - Very coarse timestamps can flatten velocity/acceleration profiles.

2. **Outlier sensitivity**
  - Extreme point jumps may inflate max-speed or acceleration metrics.

3. **Sparse-stroke sessions**
  - Sessions with too few points reduce statistical robustness.

### 7.3 Recommended Hardening (Sprint 4)

1. Add robust outlier filtering (e.g., percentile clipping / Hampel-like filter).
2. Add configurable smoothing for velocity profile before second derivative steps.
3. Add per-device normalization profile (sampling-rate calibration).
4. Add confidence score per extracted feature set (based on validation quality).

---

## 8) Computational Logic (Pseudo-Flow)

```text
for each session:
  validate required fields and temporal ordering
  for each stroke:
   compute segment distances
   compute segment time deltas
   derive velocity profile
   derive acceleration profile
   derive curvature / direction changes
  aggregate across strokes:
   speed metrics
   acceleration metrics
   timing metrics
   pause metrics
   rhythm metrics
   direction/curvature metrics
   session statistics
  return dynamic feature object
```

---

## 9) Integration with Static Features and Docs Pipeline

### 9.1 Complementarity
- Dynamic: "how drawing happened" (time-behavior signals)
- Static: "what drawing looks like" (geometric shape signals)

### 9.2 Combined Pipeline

```
Capture JSON
→ Static Extractor (18)
→ Dynamic Extractor (24)
→ Feature Union (42)
→ Task-level scoring
→ Assessment summary
```

### 9.3 Why This Matters for Pulsekey-like Modality
- Reference-copy tasks benefit from static + dynamic jointly.
- Loop/writing tasks particularly benefit from dynamic smoothness, cadence, and pause metrics.
- Clock/complex tasks benefit from timing + direction-complexity signatures.

---

## 10) Validation Summary

- Notebook validation suite completed (6/6 passed).
- Import/path issues resolved and rerun confirmed.
- Feature outputs verified against synthetic and realistic drawing sessions.
- No blocking defects identified for extraction phase.

---

## 11) Integration Gaps (Non-blocking for Sprint 3 Acceptance)

1. Frontend-export to backend extractor bridge
2. Clinical scoring layer over 42-feature union
3. Final assessment-summary UI/report renderer

These are Sprint 4 integration concerns and do not block acceptance of Sprint 3 dynamic feature extraction.

---

## 12) Request for Siamak

Please review and approve:
1. Sprint 3 dynamic feature extraction as complete
2. Transition to Sprint 4 integration workstream
3. Prioritization of:
  - bridge API,
  - scoring logic,
  - summary/reporting layer

---

## Final Status

**Sprint 3 Dynamic Features: COMPLETE, REVIEWED, AND READY FOR INTEGRATION**
