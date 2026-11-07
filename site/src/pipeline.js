// JavaScript port of the PulseKey analysis path, line for line where it matters:
//   features/dynamic_features.py      StrokeAnalyzer + DynamicFeatureExtractor aggregation
//   integration_pipeline.py           _calculate_efficiency, _calculate_shape_quality, _score_to_grade
//   features/static_features.py       rasterize + drawing_area + symmetry (APPROXIMATE: no OpenCV here)
//   features/mental_health_assessment.py  MentalHealthAssessmentEngine.assess
// A stroke is { s, e, p: [[x, y, t], ...] }: start and end in ms, points with a ms timestamp.
// pipeline.check.mjs runs this on the recorded sessions during `npm run build` and fails on drift.

export const CANVAS = [900, 650]; // backend_api.py: DrawingModalityPipeline(canvas_size=(900, 650))

const mean = (a) => a.reduce((s, v) => s + v, 0) / a.length;
const variance = (a) => { const m = mean(a); return a.reduce((s, v) => s + (v - m) ** 2, 0) / a.length; };
const max = (a) => a.reduce((m, v) => (v > m ? v : m), -Infinity);
const min = (a) => a.reduce((m, v) => (v < m ? v : m), Infinity);
// Python's round(x, n) on the values these formulas produce (ties are not exact in binary).
export const round = (x, n) => Number(x.toFixed(n));

function strokeKinematics(p) {
  const out = { speeds: [], accels: [], curvatures: [], dirChanges: 0 };
  if (p.length >= 2) {
    const d = [], dt = [];
    for (let i = 1; i < p.length; i++) {
      d.push(Math.sqrt((p[i][0] - p[i - 1][0]) ** 2 + (p[i][1] - p[i - 1][1]) ** 2));
      dt.push(p[i][2] - p[i - 1][2]);
    }
    // calculate_velocity: any zero time step drops the whole stroke from speed and acceleration.
    if (!dt.some((v) => v === 0)) {
      out.speeds = d.map((v, i) => v / dt[i]);
      if (out.speeds.length >= 2) for (let i = 0; i < out.speeds.length - 1; i++) out.accels.push((out.speeds[i + 1] - out.speeds[i]) / dt[i]);
    } else out.dropped = true;
  }
  if (p.length >= 3) {
    for (let i = 0; i < p.length - 2; i++) {
      const v1 = [p[i + 1][0] - p[i][0], p[i + 1][1] - p[i][1]], v2 = [p[i + 2][0] - p[i + 1][0], p[i + 2][1] - p[i + 1][1]];
      const n1 = Math.sqrt(v1[0] ** 2 + v1[1] ** 2), n2 = Math.sqrt(v2[0] ** 2 + v2[1] ** 2);
      if (n1 === 0 || n2 === 0) { out.curvatures.push(0); continue; }
      const angle = Math.acos(Math.min(1, Math.max(-1, (v1[0] * v2[0] + v1[1] * v2[1]) / (n1 * n2))));
      out.curvatures.push(angle / ((n1 + n2) / 2));
      if ((angle * 180) / Math.PI > 30) out.dirChanges++;
    }
  }
  return out;
}

// Returns the same nested shape integration_pipeline._extract_dynamic writes into the report
// (stroke_frequency is left out: it needs the session start and end, which the saved JSON lacks).
export function dynamicFeatures(strokes) {
  const speeds = [], accels = [], curv = [], pauses = [];
  let dirChanges = 0, drawing = 0, dropped = 0, points = 0;
  for (const st of strokes) {
    const k = strokeKinematics(st.p);
    speeds.push(...k.speeds); accels.push(...k.accels); curv.push(...k.curvatures);
    dirChanges += k.dirChanges; drawing += st.e - st.s; points += st.p.length;
    if (k.dropped) dropped++;
  }
  for (let i = 0; i < strokes.length - 1; i++) {
    const gap = strokes[i + 1].s - strokes[i].e;
    if (gap > 0) pauses.push(gap); // no duration threshold: every gap between strokes is a "pause"
  }
  const absA = accels.map(Math.abs);
  const pauseTotal = pauses.reduce((s, v) => s + v, 0);
  return {
    speed: { average: speeds.length ? mean(speeds) : 0, maximum: speeds.length ? max(speeds) : 0, variance: speeds.length ? variance(speeds) : 0 },
    acceleration: { average: accels.length ? mean(absA) : 0, maximum: accels.length ? max(absA) : 0, variance: accels.length ? variance(accels) : 0 },
    timing: { total_drawing_time_ms: drawing, total_pause_time_ms: pauseTotal, strokes: strokes.length, points },
    pauses: { count: pauses.length, average_duration_ms: pauses.length ? pauseTotal / pauses.length : 0, maximum_duration_ms: pauses.length ? max(pauses) : 0 },
    rhythm: { avg_inter_stroke_interval_ms: pauses.length ? pauseTotal / pauses.length : 0 },
    movement: { direction_changes: dirChanges, average_curvature: curv.length ? mean(curv) : 0, maximum_curvature: curv.length ? max(curv) : 0 },
    droppedStrokes: dropped,
  };
}

export function efficiency(speedVariance, pauseCount) {
  const es = Math.max(0, 1 - speedVariance / 1000);
  const ep = Math.max(0, 1 - pauseCount / 20);
  return round(Math.min(100, Math.max(0, (es * 0.6 + ep * 0.4) * 100)), 2);
}

export function shapeQuality(compactness, symX, symY) {
  return round(Math.min(100, Math.max(0, (compactness * 0.5 + Math.abs(symX) * 0.25 + Math.abs(symY) * 0.25) * 100)), 2);
}

export function grade(score) {
  return score >= 90 ? 'A' : score >= 80 ? 'B' : score >= 70 ? 'C' : score >= 60 ? 'D' : 'F';
}

export function overall(eff, quality) {
  const s = eff * 0.4 + quality * 0.6;
  return { score: round(s, 2), grade: grade(s) };
}

// APPROXIMATE port of StaticFeatureExtractor.rasterize: OpenCV draws each polyline at thickness 3.
// Here a pixel is ink when its centre lies within `radius` of a segment between int-truncated points.
// ponytail: radius 2.4 is a calibration knob, fitted so compactness lands within ~2% and symmetry
// within ~0.006 of the recorded OpenCV values (pipeline.check.mjs enforces 5% / 0.02); not pixel-exact.
export function rasterize(strokes, [W, H] = CANVAS, radius = 2.4) {
  const img = new Uint8Array(W * H);
  const r2 = radius * radius, pad = Math.ceil(radius);
  for (const st of strokes) {
    if (st.p.length < 2) continue;
    const q = st.p.map(([x, y]) => [Math.trunc(x), Math.trunc(y)]);
    for (let i = 1; i < q.length; i++) {
      const [ax, ay] = q[i - 1], [bx, by] = q[i];
      const dx = bx - ax, dy = by - ay, L = dx * dx + dy * dy;
      const x0 = Math.max(0, Math.min(ax, bx) - pad), x1 = Math.min(W - 1, Math.max(ax, bx) + pad);
      const y0 = Math.max(0, Math.min(ay, by) - pad), y1 = Math.min(H - 1, Math.max(ay, by) + pad);
      for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
        const t = L ? Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / L)) : 0;
        const ex = ax + t * dx - x, ey = ay + t * dy - y;
        if (ex * ex + ey * ey <= r2) img[y * W + x] = 1;
      }
    }
  }
  return img;
}

function corr(img, W, H, flipX) {
  let n = W * H, sa = 0, sb = 0, sab = 0, saa = 0, sbb = 0;
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const a = img[y * W + x], b = flipX ? img[y * W + (W - 1 - x)] : img[(H - 1 - y) * W + x];
    sa += a; sb += b; sab += a * b; saa += a * a; sbb += b * b;
  }
  const cov = sab / n - (sa / n) * (sb / n);
  const den = Math.sqrt((saa / n - (sa / n) ** 2) * (sbb / n - (sb / n) ** 2));
  return den ? cov / den : 0;
}

// compactness = ink pixels / bounding-box area, symmetry = correlation with the mirrored image.
export function staticFeatures(strokes, size = CANVAS) {
  const pts = strokes.flatMap((s) => s.p);
  if (!pts.length) return { compactness: 0, symmetry_x: 0, symmetry_y: 0, bbox: [0, 0, 0, 0] };
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const bbox = [min(xs), min(ys), max(xs), max(ys)];
  const area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]);
  const img = rasterize(strokes, size);
  let ink = 0; for (const v of img) ink += v;
  const [W, H] = size;
  return { compactness: area > 0 ? ink / area : 0, symmetry_x: corr(img, W, H, true), symmetry_y: corr(img, W, H, false), bbox };
}

// Where MentalHealthAssessmentEngine._extract_indicators looks for each input, and the value it
// silently falls back to when the key is missing.
export const INDICATOR_SOURCES = [
  ['tremor_index', 'features.dynamic.temporal.acceleration_profile', 0, 'stress 40%, anxiety 25%'],
  ['pause_ratio', 'features.dynamic.timing.total_pause_time_ms', null, 'not used in any score'],
  ['pause_frequency', 'features.dynamic.timing.pause_events', 0, 'stress 20%, anxiety 30%'],
  ['speed_inconsistency', 'features.dynamic.motion.avg_speed_per_stroke', 0, 'stress 30%, anxiety 20%, cognitive 25%'],
  ['efficiency_level', 'analysis.assessment.drawing_efficiency', 50, 'burnout 35%'],
  ['quality_level', 'analysis.assessment.shape_quality', 50, 'burnout 25%'],
  ['pressure_stability', 'raw_session_data.tasks', 0.5, 'stress 10%, anxiety 10%'],
  ['fluidity_index', 'features.dynamic.rhythm.rhythm_regularity', 0.5, 'anxiety 15%, cognitive 20%'],
  ['duration_concern', 'features.dynamic.timing.total_drawing_time_ms', null, 'burnout 15%, cognitive 10%'],
  ['completion_status', 'summary.is_complete', 0.5, 'burnout 20%, cognitive 20%'],
  ['error_count', 'summary.total_errors', 0, 'cognitive 25%'],
];

export const getPath = (o, path) => path.split('.').reduce((v, k) => (v != null && typeof v === 'object' ? v[k] : undefined), o);

const std = (a) => Math.sqrt(variance(a));

export function assess(report) {
  const dyn = report?.features?.dynamic ?? {};
  const timing = dyn.timing ?? {};
  const ind = {};
  const accel = dyn.temporal?.acceleration_profile;
  ind.tremor_index = Array.isArray(accel) && accel.length ? std(accel) / (mean(accel.map(Math.abs)) + 1e-5) : 0;
  const pause = timing.total_pause_time_ms ?? 0, draw = timing.total_drawing_time_ms ?? 1;
  ind.pause_ratio = pause / (pause + draw);
  ind.pause_frequency = Math.min((timing.pause_events ?? 0) / Math.max(timing.strokes ?? 1, 1), 1);
  const sps = dyn.motion?.avg_speed_per_stroke;
  ind.speed_inconsistency = Array.isArray(sps) && sps.length ? std(sps) / (mean(sps) + 1e-5) : 0;
  const a = report?.analysis?.assessment ?? {};
  ind.efficiency_level = a.drawing_efficiency ?? 50;
  ind.quality_level = a.shape_quality ?? 50;
  let pressure = 0.5;
  const tasks = report?.raw_session_data?.tasks;
  if (Array.isArray(tasks)) {
    const ps = tasks.flatMap((t) => (t.strokes ?? []).flatMap((s) => (s.points ?? []).filter((p) => 'pressure' in p).map((p) => p.pressure)));
    if (ps.length > 5) pressure = Math.max(0, Math.min(1 - std(ps) / (mean(ps) + 1e-5), 1));
  }
  ind.pressure_stability = pressure;
  ind.fluidity_index = dyn.rhythm?.rhythm_regularity ?? 0.5;
  const dur = (pause + draw) / 1000;
  ind.duration_concern = dur > 120 ? Math.min((dur - 120) / 120, 1) : dur < 30 ? Math.min((30 - dur) / 30, 1) : 0;
  const summary = report?.summary ?? {};
  ind.completion_status = summary.is_complete ? 1 : 0.5;
  ind.error_count = Math.min((summary.total_errors ?? 0) / 5, 1);

  const c100 = (v) => Math.min(v * 100, 100);
  const stress = Math.min(c100(ind.tremor_index) * 0.4 + c100(ind.speed_inconsistency) * 0.3 + ind.pause_frequency * 100 * 0.2 + (1 - ind.pressure_stability) * 100 * 0.1, 100);
  const anxiety = Math.min(c100(ind.tremor_index) * 0.25 + ind.pause_frequency * 100 * 0.3 + c100(ind.speed_inconsistency) * 0.2 + (1 - ind.fluidity_index) * 100 * 0.15 + (1 - ind.pressure_stability) * 100 * 0.1, 100);
  const burnout = Math.min((100 - ind.efficiency_level) * 0.35 + (100 - ind.quality_level) * 0.25 + (1 - ind.completion_status) * 100 * 0.2 + ind.duration_concern * 100 * 0.15, 100);
  const cognitive = Math.min(c100(ind.speed_inconsistency) * 0.25 + ind.error_count * 100 * 0.25 + (1 - ind.fluidity_index) * 100 * 0.2 + (1 - ind.completion_status) * 100 * 0.2 + ind.duration_concern * 100 * 0.1, 100);
  const wellness = 100 - (stress + anxiety + burnout + cognitive) / 4;
  return { stress: round(stress, 1), anxiety: round(anxiety, 1), burnout: round(burnout, 1), cognitive_load: round(cognitive, 1), wellness: round(wellness, 1), indicators: ind };
}

// A report-shaped object for a freshly drawn session, as backend_api.py would assemble it.
export function analyse(strokes) {
  const dynamic = dynamicFeatures(strokes);
  const stat = staticFeatures(strokes);
  const eff = efficiency(dynamic.speed.variance, dynamic.pauses.count);
  const quality = shapeQuality(stat.compactness, stat.symmetry_x, stat.symmetry_y);
  const report = { features: { dynamic, static: { shape: stat } }, analysis: { assessment: { drawing_efficiency: eff, shape_quality: quality } }, summary: { total_errors: 0, is_complete: true } };
  return { dynamic, stat, eff, quality, ...overall(eff, quality), engine: assess(report) };
}

// Session JSON (Records/ or test_data/) -> tasks of compact strokes, times relative to the first stroke.
const ms = (v) => (typeof v === 'number' ? v : Date.parse(v));
export function compactSession(raw) {
  const tasks = raw.tasks
    ? Object.values(raw.tasks).map((t) => ({ id: t.taskId, title: t.title, type: t.type, strokes: t.strokes ?? [] }))
    : [{ id: raw.taskId ?? 1, title: raw.taskTitle ?? 'task', type: 'single', strokes: raw.strokes ?? [] }];
  const all = tasks.flatMap((t) => t.strokes);
  const base = all.length ? Math.min(...all.map((s) => ms(s.startTime))) : 0;
  const conv = (s) => ({ s: ms(s.startTime) - base, e: ms(s.endTime) - base, p: s.points.map((q) => [q.x, q.y, q.timestamp - base]) });
  return { tasks: tasks.map((t) => ({ id: t.id, title: t.title, type: t.type, strokes: t.strokes.map(conv) })), raw: all };
}

