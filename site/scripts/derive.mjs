// Build-time data step: reads the repo's own records and writes src/generated/derived.json.
// Ships stroke geometry and timing only (x, y, ms). deviceInfo, user agents, PNGs and pressure arrays stay out.
// Run: node scripts/derive.mjs (part of `npm run build`).
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { compactSession, assess, INDICATOR_SOURCES, getPath, CANVAS } from '../src/pipeline.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(here, '../..');
const rel = (p) => path.relative(ROOT, p).split(path.sep).join('/');
const readJson = (p) => JSON.parse(fs.readFileSync(p, 'utf8'));
const SUBSTANTIVE = 500; // points; a drawing below this is a smoke-test or one-shape submission

// Records/<id>/JSON/<id>.json and its sibling Records/<id>/<id>_report.json
const recDirs = fs.readdirSync(path.join(ROOT, 'Records')).filter((d) => fs.existsSync(path.join(ROOT, 'Records', d, 'JSON'))).sort();
const files = recDirs.map((d) => ({ id: d, json: path.join(ROOT, 'Records', d, 'JSON', `${d}.json`), report: path.join(ROOT, 'Records', d, `${d}_report.json`) })).filter((f) => fs.existsSync(f.json));

let totalPoints = 0, pressurePoints = 0;
const pressureHist = new Map();
const groups = new Map();
for (const f of files) {
  const raw = readJson(f.json);
  const { tasks, raw: strokes } = compactSession(raw);
  const pts = strokes.flatMap((s) => s.points);
  totalPoints += pts.length;
  for (const q of pts) if ('pressure' in q) { pressurePoints++; pressureHist.set(q.pressure, (pressureHist.get(q.pressure) ?? 0) + 1); }
  const hash = crypto.createHash('sha1').update(JSON.stringify(strokes.map((s) => s.points.map((q) => [q.x, q.y, q.timestamp])))).digest('hex').slice(0, 10);
  const g = groups.get(hash) ?? { hash, files: [], points: pts.length, strokes: strokes.length, tasks: tasks.filter((t) => t.strokes.length).length, data: tasks };
  g.files.push(f.id);
  groups.set(hash, g);
  f.hash = hash;
}
const groupList = [...groups.values()].sort((a, b) => b.files.length - a.files.length || b.points - a.points);

const reports = files.filter((f) => fs.existsSync(f.report)).map((f) => {
  const r = readJson(f.report);
  const a = r.analysis?.assessment ?? {};
  const o = a.overall_assessment;
  const eng = assess(r);
  return {
    file: rel(f.report), session: f.id, hash: f.hash, complete: !!r.summary?.is_complete,
    dynamic: r.features?.dynamic ?? null, shape: r.features?.static?.shape ?? null,
    efficiency: a.drawing_efficiency ?? null, quality: a.shape_quality ?? null, score: o?.score ?? null, grade: o?.grade ?? null,
    engine: { stress: eng.stress, anxiety: eng.anxiety, burnout: eng.burnout, cognitive_load: eng.cognitive_load, wellness: eng.wellness },
    present: INDICATOR_SOURCES.map(([, p]) => getPath(r, p) !== undefined),
  };
});

const audit = INDICATOR_SOURCES.map(([name, p, fallback, used], i) => ({ name, path: p, fallback, used, present: reports.filter((r) => r.present[i]).length }));
const scored = reports.filter((r) => r.score != null);
const pearson = (x, y) => {
  const mx = x.reduce((s, v) => s + v, 0) / x.length, my = y.reduce((s, v) => s + v, 0) / y.length;
  let sxy = 0, sxx = 0, syy = 0;
  x.forEach((v, i) => { sxy += (v - mx) * (y[i] - my); sxx += (v - mx) ** 2; syy += (y[i] - my) ** 2; });
  return sxx && syy ? sxy / Math.sqrt(sxx * syy) : null; // null: one side is constant, r is undefined
};

// Claims are quoted from the documents verbatim; numbers inside them are parsed, never retyped.
const paper = fs.readFileSync(path.join(ROOT, 'RESEARCH_PAPER.md'), 'utf8').split('\n');
const readme = fs.readFileSync(path.join(ROOT, 'README.md'), 'utf8').split('\n');
const find = (lines, needle, file) => {
  const i = lines.findIndex((l) => l.includes(needle));
  if (i < 0) throw new Error(`claim not found in ${file}: ${needle}`);
  return { file, line: i + 1, text: lines[i].replace(/\*\*/g, '').replace(/^[\s|*-]+|[\s|]+$/g, '').replace(/\s*\|\s*/g, ' | ').trim() };
};
const nums = (t) => (t.match(/-?\d+(\.\d+)?/g) ?? []).map(Number);
const claims = {
  sessions: find(paper, 'real-world drawing sessions', 'RESEARCH_PAPER.md'),
  readmeSessions: find(readme, 'sessions** analyzed', 'README.md'),
  taskAverages: paper.map((l, i) => [l, i]).filter(([l]) => l.includes('Average observed:')).map(([l, i]) => ({ file: 'RESEARCH_PAPER.md', line: i + 1, text: l.trim().replace(/^- /, ''), value: nums(l)[0] })),
  complete: find(paper, 'Sessions with complete metrics:', 'RESEARCH_PAPER.md'),
  stress: find(paper, '| **Stress** |', 'RESEARCH_PAPER.md'),
  anxiety: find(paper, '| **Anxiety** |', 'RESEARCH_PAPER.md'),
  rStressAnxiety: find(paper, 'Stress ↔ Anxiety:', 'RESEARCH_PAPER.md'),
  rEffBurnout: find(paper, 'Efficiency ↔ Burnout:', 'RESEARCH_PAPER.md'),
  wellnessGood: find(paper, 'Good (60-80):', 'RESEARCH_PAPER.md'),
};
for (const k of ['stress', 'anxiety', 'rStressAnxiety', 'rEffBurnout', 'sessions', 'readmeSessions', 'complete', 'wellnessGood']) claims[k].value = nums(claims[k].text)[0];
claims.stress.sd = nums(claims.stress.text)[1];
// the r line reads "Stress ↔ Anxiety: r = 0.62": take the number after "r ="
for (const k of ['rStressAnxiety', 'rEffBurnout']) claims[k].value = Number(claims[k].text.match(/r = (-?[\d.]+)/)[1]);

const wellnessLevel = (w) => (w >= 80 ? 'Excellent' : w >= 60 ? 'Good' : w >= 40 ? 'Fair' : w >= 20 ? 'Poor' : 'Critical');
const tally = (arr) => arr.reduce((m, k) => ((m[k] = (m[k] ?? 0) + 1), m), {});

const sessions = groupList.filter((g) => g.points >= SUBSTANTIVE).map((g) => {
  const rep = reports.find((r) => r.hash === g.hash && r.dynamic?.speed);
  return { id: g.files[0], hash: g.hash, copies: g.files.length, points: g.points, tasks: g.data.filter((t) => t.strokes.length), report: rep ? { efficiency: rep.efficiency, quality: rep.quality, score: rep.score, grade: rep.grade, pauses: rep.dynamic.pauses.count, speedVar: rep.dynamic.speed.variance } : null };
});

const out = {
  generatedFrom: ['Records/*/JSON/*.json', 'Records/*/*_report.json', 'RESEARCH_PAPER.md', 'README.md'],
  canvas: CANVAS,
  substantiveThreshold: SUBSTANTIVE,
  counts: {
    sessionFiles: files.length, reportFiles: reports.length, distinctPayloads: groups.size,
    emptyPayloads: groupList.filter((g) => g.points === 0).length, substantive: sessions.length,
    duplicatedFiles: files.length - groups.size, totalPoints, distinctPoints: groupList.reduce((s, g) => s + g.points, 0),
    pressurePoints, pressureModeShare: pressurePoints ? Math.max(...pressureHist.values()) / pressurePoints : 0,
    pressureMode: [...pressureHist.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? null,
    scoredReports: scored.length, completeReports: reports.filter((r) => r.complete).length,
  },
  pressureHist: [...pressureHist.entries()].map(([value, count]) => ({ value, count })),
  groups: groupList.map(({ data, ...g }) => g),
  reports: reports.map(({ dynamic, shape, present, ...r }) => ({ ...r, pauses: dynamic?.pauses?.count ?? null, speedVar: dynamic?.speed?.variance ?? null, compactness: shape?.compactness ?? null, symX: shape?.symmetry_x ?? null, symY: shape?.symmetry_y ?? null })),
  audit,
  record: {
    stressValues: [...new Set(reports.map((r) => r.engine.stress))], anxietyValues: [...new Set(reports.map((r) => r.engine.anxiety))],
    scoreMin: Math.min(...scored.map((r) => r.score)), scoreMax: Math.max(...scored.map((r) => r.score)),
    grades: tally(scored.map((r) => r.grade)), wellness: tally(reports.map((r) => wellnessLevel(r.engine.wellness))),
    rStressAnxiety: pearson(reports.map((r) => r.engine.stress), reports.map((r) => r.engine.anxiety)),
    rEffBurnout: pearson(scored.map((r) => r.efficiency), scored.map((r) => r.engine.burnout)),
  },
  claims,
  sessions,
};
fs.mkdirSync(path.join(here, '../src/generated'), { recursive: true });
fs.writeFileSync(path.join(here, '../src/generated/derived.json'), JSON.stringify(out));
console.log('derived ok', { ...out.counts, sizeKB: Math.round(JSON.stringify(out).length / 1024) });
