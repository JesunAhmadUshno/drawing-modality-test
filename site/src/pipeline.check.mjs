// Known-answer parity check, run inside `npm run build`: the JS port must reproduce what the Python
// pipeline wrote into Records/*/*_report.json, and what analysis/engine_audit.py got from the engine.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { compactSession, dynamicFeatures, staticFeatures, efficiency, shapeQuality, overall, assess } from './pipeline.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const readJson = (p) => JSON.parse(fs.readFileSync(path.join(ROOT, p), 'utf8'));
const close = (a, b, tol, what) => assert.ok(Math.abs(a - b) <= tol * Math.max(1, Math.abs(b)), `${what}: port ${a} vs recorded ${b}`);

const FIELDS = ['speed.average', 'speed.maximum', 'speed.variance', 'acceleration.average', 'acceleration.maximum', 'acceleration.variance',
  'timing.total_drawing_time_ms', 'timing.total_pause_time_ms', 'timing.strokes', 'timing.points', 'pauses.count', 'pauses.average_duration_ms',
  'pauses.maximum_duration_ms', 'rhythm.avg_inter_stroke_interval_ms', 'movement.direction_changes', 'movement.average_curvature', 'movement.maximum_curvature'];
const get = (o, p) => p.split('.').reduce((v, k) => v[k], o);

let dyn = 0, scoring = 0, compDiff = [], symDiff = [];
for (const id of fs.readdirSync(path.join(ROOT, 'Records')).sort()) {
  const rp = `Records/${id}/${id}_report.json`, sp = `Records/${id}/JSON/${id}.json`;
  if (!fs.existsSync(path.join(ROOT, rp)) || !fs.existsSync(path.join(ROOT, sp))) continue;
  const rep = readJson(rp);
  const d = rep.features?.dynamic;
  if (!d?.speed) continue;
  // backend_api.py concatenates every task's strokes into one list before analysis; do the same.
  const strokes = compactSession(readJson(sp)).tasks.flatMap((t) => t.strokes);
  const port = dynamicFeatures(strokes);
  for (const f of FIELDS) close(get(port, f), get(d, f), 1e-9, `${id} ${f}`);
  const a = rep.analysis.assessment, sh = rep.features.static?.shape;
  assert.equal(efficiency(d.speed.variance, d.pauses.count), a.drawing_efficiency, `${id} efficiency`);
  assert.equal(efficiency(port.speed.variance, port.pauses.count), a.drawing_efficiency, `${id} efficiency from port features`);
  if (sh?.compactness != null) assert.equal(shapeQuality(sh.compactness, sh.symmetry_x, sh.symmetry_y), a.shape_quality, `${id} shape quality`);
  const o = overall(a.drawing_efficiency, a.shape_quality);
  assert.equal(o.score, a.overall_assessment.score, `${id} score`);
  assert.equal(o.grade, a.overall_assessment.grade, `${id} grade`);
  // Static geometry is an approximation of OpenCV's thick polyline; record how far off it is.
  const st = staticFeatures(strokes);
  if (sh?.compactness != null) compDiff.push(Math.abs(st.compactness - sh.compactness) / sh.compactness);
  if (sh?.symmetry_x != null) symDiff.push(Math.max(Math.abs(st.symmetry_x - sh.symmetry_x), Math.abs(st.symmetry_y - sh.symmetry_y)));
  dyn++; scoring++;
}
assert.ok(dyn >= 20, `expected the recorded scored reports, found ${dyn}`);
const worstComp = Math.max(...compDiff), worstSym = Math.max(...symDiff);
// The approximate rasteriser is labelled approximate on the page; it must still stay this close.
assert.ok(worstComp < 0.05, `compactness approximation drifted: worst relative error ${worstComp}`);
assert.ok(worstSym < 0.02, `symmetry approximation drifted: worst absolute error ${worstSym}`);

// Engine: compare against the Python engine's own output (python analysis/engine_audit.py).
const audit = readJson('analysis/engine_audit.json');
for (const row of audit.reports) {
  const id = row.report.replace('_report.json', '');
  const e = assess(readJson(`Records/${id}/${row.report}`));
  for (const k of ['stress', 'anxiety', 'burnout', 'cognitive_load', 'wellness']) assert.equal(e[k], row[k], `${row.report} ${k}`);
  for (const [k, v] of Object.entries(row.indicators)) close(e.indicators[k], v, 1e-5, `${row.report} indicator ${k}`);
}
console.log('pipeline parity ok', { dynamicReports: dyn, scoringReports: scoring, engineReports: audit.reports.length,
  worstCompactnessRelErr: +worstComp.toFixed(4), worstSymmetryAbsErr: +worstSym.toFixed(4) });
