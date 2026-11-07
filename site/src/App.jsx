import { useMemo, useState, useEffect, useRef, useCallback, useId } from 'react';
import D from './generated/derived.json';
import { analyse, dynamicFeatures, staticFeatures, efficiency, shapeQuality, overall } from './pipeline.js';

const REPO = 'https://github.com/JesunAhmadUshno/drawing-modality-test';
const blob = (p) => `${REPO}/blob/main/${p}`;
const fmt = (n) => Math.round(n).toLocaleString('en-US');
const pct = (x, d = 0) => `${(x * 100).toFixed(d)}%`;
const fx = (x, d = 2) => (x == null ? 'n/a' : (+x).toFixed(d));
const C = D.counts, R = D.record, K = D.claims;
const one = (vals) => vals.map((v) => v.toFixed(1)).join(', ');
const [CW, CH] = D.canvas;
const scored = D.reports.filter((r) => r.score != null);

const SECTIONS = [['top', 'Overview', '◎'], ['draw', 'Draw', '✎'], ['replay', 'Replay', '▶'], ['tasks', 'Per task', '▥'], ['scoring', 'Scoring', 'ƒ'], ['engine', 'Engine', '⚙'], ['data', 'Data', '▦'], ['claims', 'Claims', '≠'], ['reproduce', 'Reproduce', '❯_']];

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) { els.forEach((e) => e.classList.add('in')); return; }
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.08 });
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, []);
}

function MenuBar() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => { const t = setInterval(() => setNow(new Date()), 30000); return () => clearInterval(t); }, []);
  return (
    <div className="menubar" role="banner">
      <span className="apple" aria-hidden="true">◆</span>
      <a className="app" href="#top">PulseKey Lab</a>
      <a className="m" href="../">Capture app</a>
      <a className="m" href={blob('docs/research-review.md')}>Research review</a>
      <a className="m" href={blob('RESEARCH_PAPER.md')}>Paper</a>
      <span className="spacer" />
      <span className="status"><i /> Parity-checked port</span>
      <a href={REPO}>GitHub ↗</a>
      <span className="clock">{now.toLocaleString('en-US', { weekday: 'short', hour: 'numeric', minute: '2-digit' })}</span>
    </div>
  );
}

function Dock() {
  const [active, setActive] = useState('top');
  useEffect(() => {
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && setActive(e.target.id)), { rootMargin: '-45% 0px -50% 0px' });
    SECTIONS.forEach(([id]) => { const el = document.getElementById(id); if (el) io.observe(el); });
    return () => io.disconnect();
  }, []);
  return (
    <nav className="dock" aria-label="Sections">
      {SECTIONS.map(([id, label, icon]) => (
        <a key={id} href={`#${id}`} className={active === id ? 'on' : ''} aria-current={active === id ? 'true' : undefined}>
          <span className="ico" aria-hidden="true">{icon}</span><span className="lbl">{label}</span>
        </a>
      ))}
    </nav>
  );
}

function Range({ label, value, min, max, step, onChange, show }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label} <span>{show}</span></label>
      <input id={id} type="range" min={min} max={max} step={step} value={value} onChange={(e) => onChange(+e.target.value)} />
    </div>
  );
}

function Select({ label, value, onChange, options }) {
  const id = useId();
  return (
    <div className="field"><label htmlFor={id}>{label}</label>
      <select id={id} value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>
    </div>
  );
}

const sessionLabel = (s) => `${s.id.replace('session-', '#')} · ${s.tasks.length} tasks · ${fmt(s.points)} pts${s.copies > 1 ? ` · ${s.copies} copies` : ''}`;

export default function App() {
  useReveal();
  return (
    <div className="wrap">
      <MenuBar />
      <div className="glow" aria-hidden="true" />
      <Hero />
      <DrawPad />
      <Replay />
      <PerTask />
      <Scoring />
      <Engine />
      <Data />
      <Claims />
      <Reproduce />
      <Dock />
      <footer>
        Every number on this page is computed at build time from <code>Records/</code>, <code>RESEARCH_PAPER.md</code> and <code>README.md</code>, or live in your browser by a port of the repo's Python code.
        The stress, anxiety, burnout and cognitive-load scores are unvalidated heuristics, not health measures or advice. Code: see <a href={blob('LICENSE')}>LICENSE</a>.
      </footer>
    </div>
  );
}

function Hero() {
  return (
    <header className="card hero window" id="top" data-title="pulsekey.app — audit">
      <div className="head">
        <p className="eyebrow">Research prototype · drawing as a psychomotor signal</p>
        <span className="pill warn">● Unvalidated</span>
      </div>
      <h1>PulseKey turns a drawing into {C.metricsPerReport} metrics, but its {C.reportFiles} reports come from {C.distinctPayloads} distinct drawings, and <em>stress scores {one(R.stressValues)} on every one</em>.</h1>
      <p className="sub">
        PulseKey records seven drawing and writing tasks in the browser and runs a Python feature pipeline over the strokes.
        This page ports that pipeline to JavaScript (checked against the recorded reports on every build), lets you draw into it, replays the recorded sessions, and sets the write-up's claims next to what the repo's own records show.
      </p>
      <div className="actions">
        <a className="btn primary" href="#draw">Draw into the pipeline</a>
        <a className="btn ghost" href="#claims">Claims vs record</a>
        <span className="hint">The original capture app still lives at the <a href="../">site root</a>.</span>
      </div>
      <div className="tiles">
        <div className="tile"><div className="num">{C.sessionFiles}</div><div className="cap">session JSON files in Records/, with {C.reportFiles} report files</div></div>
        <div className="tile"><div className="num">{C.distinctPayloads}</div><div className="cap">distinct stroke payloads ({C.duplicatedFiles} files are resubmissions, {C.emptyPayloads} is empty)</div></div>
        <div className="tile"><div className="num">{C.substantive}</div><div className="cap">substantive drawings (at least {D.substantiveThreshold} points)</div></div>
        <div className="tile"><div className="num">{pct(C.pressureModeShare)}</div><div className="cap">of {fmt(C.pressurePoints)} pressure readings equal {C.pressureMode}: mouse input, no pressure signal</div></div>
      </div>
    </header>
  );
}

// ---------- live drawing pad ----------
function DrawPad() {
  const canvasRef = useRef(null);
  const first = `${D.sessions[0].id}|${D.sessions[0].tasks[0].id}`;
  const [strokes, setStrokes] = useState(() => D.sessions[0].tasks[0].strokes);
  const cur = useRef(null);
  const [sample, setSample] = useState(first);
  const res = useMemo(() => (strokes.length ? analyse(strokes) : null), [strokes]);

  const paint = useCallback((list) => {
    const c = canvasRef.current; if (!c) return;
    const ctx = c.getContext('2d');
    ctx.clearRect(0, 0, CW, CH);
    ctx.strokeStyle = getComputedStyle(c).color; ctx.lineWidth = 3; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (const s of list) {
      ctx.beginPath();
      s.p.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y)));
      if (s.p.length === 1) ctx.lineTo(s.p[0][0] + 0.1, s.p[0][1]);
      ctx.stroke();
    }
  }, []);
  useEffect(() => { paint(strokes); }, [strokes, paint]);
  useEffect(() => {
    const m = window.matchMedia('(prefers-color-scheme: dark)');
    const f = () => paint(strokes); m.addEventListener('change', f); return () => m.removeEventListener('change', f);
  }, [strokes, paint]);

  // Same capture as frontend/drawingCapture.js: canvas coordinates rounded, Date.now() timestamps.
  const pt = (e) => { const r = canvasRef.current.getBoundingClientRect(); return [Math.round((e.clientX - r.left) * (CW / r.width)), Math.round((e.clientY - r.top) * (CH / r.height)), Date.now()]; };
  const down = (e) => {
    e.currentTarget.setPointerCapture(e.pointerId); const p = pt(e); cur.current = { s: p[2], e: p[2], p: [p] };
    if (sample) { setSample(''); setStrokes([]); paint([]); } // drawing replaces a loaded recording
  };
  const move = (e) => {
    if (!cur.current) return;
    const p = pt(e); cur.current.p.push(p); cur.current.e = p[2];
    const ctx = canvasRef.current.getContext('2d'); const q = cur.current.p;
    ctx.strokeStyle = getComputedStyle(canvasRef.current).color; ctx.lineWidth = 3; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(q[q.length - 2][0], q[q.length - 2][1]); ctx.lineTo(p[0], p[1]); ctx.stroke();
  };
  const up = () => { if (!cur.current) return; const s = cur.current; cur.current = null; setStrokes((l) => [...l, s]); };

  const loadSample = (v) => {
    setSample(v);
    if (!v) return;
    const [sid, tid] = v.split('|');
    const t = D.sessions.find((s) => s.id === sid).tasks.find((x) => String(x.id) === tid);
    setStrokes(t.strokes);
  };
  const options = [['', 'Load a recorded task (recorded)…'], ...D.sessions.flatMap((s) => s.tasks.map((t) => [`${s.id}|${t.id}`, `${s.id.replace('session-', '#')} · ${t.title}`]))];
  const e = res?.engine;
  return (
    <section id="draw" className="card window reveal" data-title="canvas.draw — live">
      <div className="head">
        <div>
          <p className="eyebrow">Live · runs in your browser</p>
          <h2>Draw anything. Stress stays at {one(R.stressValues)}.</h2>
          <p className="sub">
            Each stroke goes through the JavaScript port of <a href={blob('features/dynamic_features.py')}>dynamic_features.py</a>, the scoring in <a href={blob('integration_pipeline.py')}>integration_pipeline.py</a> and
            the engine in <a href={blob('features/mental_health_assessment.py')}>mental_health_assessment.py</a>. The engine looks for keys the pipeline never writes, so tremor, speed inconsistency, pause frequency, fluidity and pressure fall back to fixed defaults whatever you draw.
          </p>
        </div>
        <span className={`pill ${sample ? 'warn' : 'info'}`}>{sample ? '● Recorded task loaded' : `${strokes.length} strokes`}</span>
      </div>
      <div className="pad">
        <canvas ref={canvasRef} width={CW} height={CH} aria-label="Drawing pad: draw with a mouse, pen or finger" onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up} />
        {!strokes.length && <p className="pad-hint" aria-hidden="true">Draw here: a pentagon, a clock, your name</p>}
      </div>
      {sample && <p className="hint" style={{ textAlign: 'center' }}>Showing a recorded task, labelled recorded. Start drawing to replace it with your own strokes.</p>}
      <div className="actions" style={{ marginTop: 12 }}>
        <button className="btn ghost" onClick={() => setStrokes((l) => l.slice(0, -1))} disabled={!strokes.length}>Undo stroke</button>
        <button className="btn ghost" onClick={() => { setStrokes([]); setSample(''); }} disabled={!strokes.length}>Clear</button>
        <div className="field" style={{ minWidth: 0, flex: '1 1 260px' }}>
          <Select label="Or load a recorded task" value={sample} onChange={loadSample} options={options} />
        </div>
      </div>
      {res ? (
        <div className="grid2" style={{ marginTop: 8 }}>
          <div>
            <h3>Pipeline output</h3>
            <div className="tiles two">
              <div className="tile"><div className="num">{res.dynamic.pauses.count}</div><div className="cap">pauses (every gap between strokes)</div></div>
              <div className="tile"><div className="num">{fx(res.dynamic.speed.variance, 3)}</div><div className="cap">speed variance, px²/ms²</div></div>
              <div className="tile"><div className="num">{fx(res.eff)}</div><div className="cap">drawing efficiency</div></div>
              <div className="tile"><div className="num">{fx(res.quality)}</div><div className="cap">shape quality (approximate raster)</div></div>
              <div className="tile"><div className="num">{fx(res.score)} <small>{res.grade}</small></div><div className="cap">overall score and grade</div></div>
              <div className="tile"><div className="num">{res.dynamic.movement.direction_changes}</div><div className="cap">direction changes over 30°</div></div>
            </div>
            {res.dynamic.droppedStrokes > 0 && <p className="hint">{res.dynamic.droppedStrokes} stroke(s) had two points in the same millisecond, so the Python code drops them from speed entirely; the port does the same.</p>}
          </div>
          <div>
            <h3>Engine output <span className="pill warn" style={{ marginLeft: 6 }}>Heuristic, not advice</span></h3>
            <div className="bars" style={{ marginTop: 12 }}>
              {[['Stress', e.stress], ['Anxiety', e.anxiety], ['Burnout', e.burnout], ['Cognitive load', e.cognitive_load], ['Wellness', e.wellness]].map(([k, v]) => (
                <div className="bar-row" key={k}>
                  <div className="lab"><span>{k}</span><b>{v.toFixed(1)}</b></div>
                  <div className="track"><div className="fill" style={{ width: `${v}%`, background: k === 'Wellness' ? 'var(--good)' : 'var(--primary)' }} /></div>
                </div>
              ))}
            </div>
            <p className="hint" style={{ marginTop: 10 }}>Stress and anxiety are built only from inputs that are always missing, so they cannot change. Burnout and cognitive load move with efficiency, shape quality and session length.</p>
          </div>
        </div>
      ) : <p className="hint">Results appear after your first stroke.</p>}
    </section>
  );
}

// ---------- recorded replay ----------
function Replay() {
  const [sid, setSid] = useState(D.sessions[0].id);
  const session = D.sessions.find((s) => s.id === sid);
  const [tid, setTid] = useState(String(session.tasks[0].id));
  const task = session.tasks.find((t) => String(t.id) === tid) ?? session.tasks[0];
  const t0 = task.strokes[0].s, t1 = Math.max(...task.strokes.map((s) => s.e));
  const [cursor, setCursor] = useState(t1);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(2);
  useEffect(() => { setCursor(t1); setPlaying(false); }, [sid, tid]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!playing) return;
    let raf, last = performance.now();
    const step = (now) => {
      setCursor((c) => { const n = c + (now - last) * speed; if (n >= t1) { setPlaying(false); return t1; } return n; });
      last = now; raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [playing, speed, t1]);
  const pts = task.strokes.flatMap((s) => s.p);
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const pad = 20, bx = Math.min(...xs) - pad, by = Math.min(...ys) - pad, bw = Math.max(...xs) - Math.min(...xs) + 2 * pad, bh = Math.max(...ys) - Math.min(...ys) + 2 * pad;
  const drawn = task.strokes.filter((s) => s.s <= cursor).length;
  return (
    <section id="replay" className="card window reveal" data-title={`Records/${session.id}.json — replay`}>
      <div className="head">
        <div>
          <p className="eyebrow">Recorded replay</p>
          <h2>The {C.substantive} substantive drawings, stroke by stroke, on their real clock.</h2>
          <p className="sub">Playback uses the recorded per-point timestamps. Gaps between strokes are where the pipeline counts a "pause", including the gaps between tasks once the backend merges all seven into one list.</p>
        </div>
        <span className="pill warn">● RECORDED</span>
      </div>
      <div className="controls">
        <Select label="Session" value={sid} onChange={(v) => { setSid(v); setTid(String(D.sessions.find((s) => s.id === v).tasks[0].id)); }} options={D.sessions.map((s) => [s.id, sessionLabel(s)])} />
        <Select label="Task" value={tid} onChange={setTid} options={session.tasks.map((t) => [String(t.id), `${t.id}. ${t.title} (${t.strokes.length} strokes)`])} />
        <Range label="Time" value={cursor} min={t0} max={t1} step={10} onChange={(v) => { setPlaying(false); setCursor(v); }} show={`${((cursor - t0) / 1000).toFixed(1)} / ${((t1 - t0) / 1000).toFixed(1)} s`} />
        <div className="field"><span className="flabel">Playback</span>
          <div className="seg" role="group" aria-label="Playback speed">
            {[1, 2, 4].map((v) => <button key={v} aria-pressed={speed === v} onClick={() => setSpeed(v)}>{v}×</button>)}
          </div>
        </div>
      </div>
      <div className="actions" style={{ marginTop: 0, marginBottom: 12 }}>
        <button className="btn primary" onClick={() => { if (cursor >= t1) setCursor(t0); setPlaying((p) => !p); }}>{playing ? 'Pause' : 'Play recording'}</button>
        <span className="hint">{drawn} of {task.strokes.length} strokes drawn</span>
      </div>
      <svg className="chart replay" viewBox={`${bx} ${by} ${bw} ${bh}`} role="img" aria-label={`Recorded strokes for ${task.title}, replayed up to ${((cursor - t0) / 1000).toFixed(1)} seconds`}>
        {task.strokes.map((s, i) => {
          if (s.s > cursor) return null;
          const p = s.p.filter((q) => q[2] <= cursor);
          if (!p.length) return null;
          return <polyline key={i} fill="none" stroke={s.e <= cursor ? 'var(--text)' : 'var(--primary)'} strokeWidth={Math.max(2, bw / 300)} strokeLinecap="round" strokeLinejoin="round" points={p.map((q) => `${q[0]},${q[1]}`).join(' ')} />;
        })}
      </svg>
    </section>
  );
}

// ---------- per-task metrics ----------
const METRICS = [
  ['pauses', 'Pause count', (r) => r.dyn.pauses.count, 0],
  ['pauseTime', 'Pause time (s)', (r) => r.dyn.timing.total_pause_time_ms / 1000, 1],
  ['speed', 'Mean speed (px/ms)', (r) => r.dyn.speed.average, 3],
  ['dir', 'Direction changes', (r) => r.dyn.movement.direction_changes, 0],
  ['eff', 'Efficiency', (r) => r.eff, 1],
  ['compact', 'Compactness (approx.)', (r) => r.stat.compactness, 3],
];
function PerTask() {
  const [sid, setSid] = useState(D.sessions.find((s) => s.tasks.length === 7)?.id ?? D.sessions[0].id);
  const [metric, setMetric] = useState('pauses');
  const session = D.sessions.find((s) => s.id === sid);
  const rows = useMemo(() => {
    const one = (strokes) => { const dyn = dynamicFeatures(strokes); return { dyn, eff: efficiency(dyn.speed.variance, dyn.pauses.count), stat: staticFeatures(strokes) }; };
    return { tasks: session.tasks.map((t) => ({ title: t.title, ...one(t.strokes) })), merged: one(session.tasks.flatMap((t) => t.strokes)) };
  }, [session]);
  const [, label, get, dp] = METRICS.find((m) => m[0] === metric);
  const merged = get(rows.merged), vals = rows.tasks.map(get);
  const sum = vals.reduce((s, v) => s + v, 0);
  const scale = Math.max(merged, ...vals) || 1;
  return (
    <section id="tasks" className="card window reveal" data-title="tasks.csv — per-task vs merged">
      <div className="head">
        <div>
          <p className="eyebrow">Unit of analysis · computed live</p>
          <h2>The backend merges seven different drawings into one, then measures the blend.</h2>
          <p className="sub">
            <a href={blob('backend_api.py')}>backend_api.py</a> concatenates every task's strokes before analysis, so the gaps between tasks become pauses and the geometry spans unrelated drawings.
            Here the same port runs on each task separately. The dark marker shows the merged value the report stores.
          </p>
        </div>
        <div className="seg" role="group" aria-label="Metric">
          {METRICS.map(([k, l]) => <button key={k} aria-pressed={metric === k} onClick={() => setMetric(k)}>{l.replace(/ \(.*\)/, '')}</button>)}
        </div>
      </div>
      <div className="controls" style={{ gridTemplateColumns: 'minmax(0, 1fr)' }}>
        <Select label="Recorded session (recorded)" value={sid} onChange={setSid} options={D.sessions.map((s) => [s.id, sessionLabel(s)])} />
      </div>
      <div className="bars">
        {rows.tasks.map((t, i) => (
          <div className="bar-row" key={t.title}>
            <div className="lab"><span>{t.title}</span><b>{vals[i].toFixed(dp)}</b></div>
            <div className="track"><div className="fill" style={{ width: `${(vals[i] / scale) * 100}%`, background: 'var(--primary)' }} /><div className="ref" style={{ left: `${(merged / scale) * 100}%` }} /></div>
          </div>
        ))}
        <div className="bar-row">
          <div className="lab"><span><b>All tasks merged (what the report stores)</b></span><b>{merged.toFixed(dp)}</b></div>
          <div className="track"><div className="fill" style={{ width: `${(merged / scale) * 100}%`, background: 'var(--warn)' }} /></div>
        </div>
      </div>
      <p className="hint" style={{ marginTop: 12 }}>
        {metric === 'pauses' || metric === 'pauseTime'
          ? <>Sum of the per-task values: {sum.toFixed(dp)}. The merged value is larger because the {session.tasks.length - 1} gaps between tasks are counted too.</>
          : metric === 'eff'
            ? <>Efficiency is {fx(rows.merged.eff, 1)} merged. More than 20 pauses zeroes the pause term, which the merged list always passes.</>
            : metric === 'compact'
              ? <>Compactness divides ink by the bounding box, so merging drawings in different places changes it. Approximate raster, labelled as such.</>
              : <>Per-task values describe one drawing each; the merged value describes none of them.</>}
      </p>
    </section>
  );
}

// ---------- scoring explorer ----------
function Scoring() {
  const base = scored.find((r) => r.compactness != null) ?? scored[0];
  const [sv, setSv] = useState(+base.speedVar.toFixed(2));
  const [pauses, setPauses] = useState(base.pauses);
  const [comp, setComp] = useState(+base.compactness.toFixed(2));
  const [symX, setSymX] = useState(+base.symX.toFixed(2));
  const [symY, setSymY] = useState(+base.symY.toFixed(2));
  const eff = efficiency(sv, pauses), q = shapeQuality(comp, symX, symY), o = overall(eff, q);
  const W = 460, H = 240, p = { l: 36, r: 10, t: 12, b: 26 }, PMAX = 100;
  const x = (v) => p.l + (Math.min(v, PMAX) / PMAX) * (W - p.l - p.r);
  const y = (v) => p.t + (1 - v / 100) * (H - p.t - p.b);
  const line = Array.from({ length: 101 }, (_, i) => `${x(i)},${y(efficiency(sv, i))}`).join(' ');
  const effs = scored.map((r) => r.efficiency);
  return (
    <section id="scoring" className="card window reveal" data-title="integration_pipeline.py — scoring">
      <p className="eyebrow">Scoring formula · calculator</p>
      <h2>Two terms, one stuck at zero: why every substantive session grades F.</h2>
      <p className="sub">
        Efficiency is 0.6·(1 − speed variance / 1000) + 0.4·(1 − pauses / 20). Recorded speed variance is tiny (well under 1), so the first term is about 60, and any session with more than 20 strokes loses the second term entirely.
        Overall = 0.4·efficiency + 0.6·shape quality. Recorded scores run {R.scoreMin} to {R.scoreMax}; grades: {Object.entries(R.grades).map(([g, n]) => `${n} × ${g}`).join(', ')}.
        Sliders start at a recorded session's values.
      </p>
      <div className="grid2" style={{ marginTop: 16 }}>
        <div>
          <div className="controls" style={{ gridTemplateColumns: '1fr' }}>
            <Range label="Speed variance" value={sv} min={0} max={1000} step={0.01} onChange={setSv} show={sv.toFixed(2)} />
            <Range label="Pause count" value={pauses} min={0} max={100} step={1} onChange={setPauses} show={pauses} />
            <Range label="Compactness" value={comp} min={0} max={1} step={0.01} onChange={setComp} show={comp.toFixed(2)} />
            <Range label="Vertical-axis symmetry" value={symX} min={0} max={1} step={0.01} onChange={setSymX} show={symX.toFixed(2)} />
            <Range label="Horizontal-axis symmetry" value={symY} min={0} max={1} step={0.01} onChange={setSymY} show={symY.toFixed(2)} />
          </div>
          <div className="tiles two" style={{ marginTop: 0 }}>
            <div className="tile"><div className="num">{eff.toFixed(2)}</div><div className="cap">efficiency</div></div>
            <div className="tile"><div className="num">{q.toFixed(2)}</div><div className="cap">shape quality</div></div>
            <div className="tile"><div className="num">{o.score.toFixed(2)}</div><div className="cap">overall score</div></div>
            <div className="tile"><div className="num">{o.grade}</div><div className="cap">grade (A ≥ 90 … F &lt; 60)</div></div>
          </div>
        </div>
        <div>
          <h3>Efficiency by pause count, with the {scored.length} scored reports</h3>
          <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Efficiency against pause count, with recorded reports as dots">
            {[0, 20, 40, 60, 80, 100].map((t) => <g key={t}><line className="axis" x1={p.l} x2={W - p.r} y1={y(t)} y2={y(t)} /><text x={p.l - 6} y={y(t) + 4} textAnchor="end">{t}</text></g>)}
            <line className="axis" x1={x(20)} x2={x(20)} y1={p.t} y2={H - p.b} strokeDasharray="4 4" />
            <text x={x(20) + 4} y={p.t + 12}>20 pauses</text>
            <polyline fill="none" stroke="var(--primary)" strokeWidth="2.5" points={line} />
            {scored.map((r) => <circle key={r.file} cx={x(r.pauses)} cy={y(r.efficiency)} r="5" fill="var(--warn)" fillOpacity="0.55" stroke="var(--surface-strong)" />)}
            <circle cx={x(pauses)} cy={y(eff)} r="6" fill="var(--primary)" stroke="var(--surface-strong)" strokeWidth="2" />
            <text x={p.l} y={H - 6}>0 pauses</text><text x={W - p.r} y={H - 6} textAnchor="end">{PMAX}+ pauses</text>
          </svg>
          <p className="hint">Orange: recorded reports (efficiency {Math.min(...effs)} to {Math.max(...effs)}). Blue: the formula at your speed variance.</p>
        </div>
      </div>
    </section>
  );
}

// ---------- engine audit ----------
function Engine() {
  const [file, setFile] = useState(D.reports.find((r) => r.score != null)?.file ?? D.reports[0].file);
  const r = D.reports.find((x) => x.file === file);
  return (
    <section id="engine" className="card window reveal" data-title="mental_health_assessment.py — audit">
      <div className="head">
        <div>
          <p className="eyebrow">Engine audit · computed at build time</p>
          <h2>Five of the inputs are never there, so stress and anxiety are constants.</h2>
          <p className="sub">
            For each indicator: the report key <code>_extract_indicators</code> reads, how many of the {C.reportFiles} recorded reports contain it, and the default it silently uses otherwise.
            The build checks this port against <a href={blob('analysis/engine_audit.py')}>analysis/engine_audit.py</a>, which runs the Python engine on every report.
          </p>
        </div>
        <span className="pill bad">Stress {one(R.stressValues)} · Anxiety {one(R.anxietyValues)}</span>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ minWidth: 960 }}>
          <thead><tr><th>Indicator</th><th>Key read</th><th>Present</th><th>Fallback</th><th>Feeds</th></tr></thead>
          <tbody>
            {D.audit.map((a) => (
              <tr key={a.name}><td className="mono">{a.name}</td><td className="mono">{a.path}</td>
                <td className={a.present ? 'ok' : 'no'}>{a.present} / {C.reportFiles}</td><td>{a.fallback ?? 'computed'}</td><td>{a.used}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="grid2" style={{ marginTop: 18, alignItems: 'end' }}>
        <Select label="Recorded report" value={file} onChange={setFile} options={D.reports.map((x) => [x.file, `${x.session}${x.score == null ? ' (no features)' : ''}`])} />
        <div className="tiles five" style={{ marginTop: 0 }}>
          {[['Stress', r.engine.stress], ['Anxiety', r.engine.anxiety], ['Burnout', r.engine.burnout], ['Cognitive', r.engine.cognitive_load], ['Wellness', r.engine.wellness]].map(([k, v]) => (
            <div className="tile" key={k}><div className="num">{v.toFixed(1)}</div><div className="cap">{k}</div></div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------- data provenance ----------
function Data() {
  const g = D.groups;
  const W = 960, H = 220, p = { l: 36, r: 10, t: 14, b: 40 };
  const maxC = Math.max(...g.map((x) => x.files.length));
  const bw = (W - p.l - p.r) / g.length;
  const y = (v) => p.t + (1 - v / maxC) * (H - p.t - p.b);
  return (
    <section id="data" className="card window reveal" data-title="Records/ — provenance">
      <p className="eyebrow">Data provenance · computed at build time</p>
      <h2>{C.sessionFiles} files, {C.distinctPayloads} drawings: most of the record is resubmissions.</h2>
      <p className="sub">
        Files were grouped by an exact hash of their stroke coordinates and timestamps. Identical payloads saved several times, seconds apart, are one drawing, not several sessions.
        Across all files there are {fmt(C.totalPoints)} points, but only {fmt(C.distinctPoints)} distinct ones.
      </p>
      <svg className="chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Number of saved copies for each distinct stroke payload" style={{ marginTop: 12 }}>
        {Array.from({ length: maxC + 1 }, (_, i) => i).filter((i) => i % 2 === 0).map((t) => <g key={t}><line className="axis" x1={p.l} x2={W - p.r} y1={y(t)} y2={y(t)} /><text x={p.l - 6} y={y(t) + 4} textAnchor="end">{t}</text></g>)}
        {g.map((x, i) => (
          <g key={x.hash}>
            <rect x={p.l + i * bw + 6} width={bw - 12} y={y(x.files.length)} height={y(0) - y(x.files.length)} rx="6" fill={x.points >= D.substantiveThreshold ? 'var(--primary)' : 'var(--muted)'} opacity="0.8" />
            <text x={p.l + i * bw + bw / 2} y={y(x.files.length) - 6} textAnchor="middle" style={{ fill: 'var(--text)' }}>{x.files.length}×</text>
            <text x={p.l + i * bw + bw / 2} y={H - 22} textAnchor="middle">{fmt(x.points)}</text>
          </g>
        ))}
        <text x={p.l} y={H - 4}>points per payload, most-copied first (blue: at least {D.substantiveThreshold} points)</text>
      </svg>
      <div className="tiles" style={{ marginTop: 12 }}>
        <div className="tile"><div className="num">{Math.max(...g.map((x) => x.files.length))}</div><div className="cap">copies of the most-resubmitted drawing</div></div>
        <div className="tile"><div className="num">{D.pressureHist.length}</div><div className="cap">distinct pressure value{D.pressureHist.length === 1 ? '' : 's'} recorded ({D.pressureHist.map((h) => h.value).join(', ')})</div></div>
        <div className="tile"><div className="num">{C.completeReports}</div><div className="cap">reports marked complete, of {C.reportFiles}</div></div>
        <div className="tile"><div className="num">{C.reportFiles - C.scoredReports}</div><div className="cap">reports with no features (validation failed)</div></div>
      </div>
    </section>
  );
}

// ---------- claims vs record ----------
function Claims() {
  const src = (c) => <a href={`${blob(c.file)}#L${c.line}`}>{c.file}:{c.line}</a>;
  const rows = [
    [K.sessions, `${K.sessions.value} sessions`, `${C.sessionFiles} files, ${C.distinctPayloads} distinct payloads, ${C.substantive} substantive`, 'bad'],
    [K.complete, `${K.complete.value} complete`, `${C.completeReports} of ${C.reportFiles} reports complete; ${C.sessionFiles - C.reportFiles} files have no report`, 'bad'],
    [K.taskAverages[0], `Task scores ${K.taskAverages.map((t) => t.value).join(', ')}`, `Recorded scores ${R.scoreMin} to ${R.scoreMax}, all grade ${Object.keys(R.grades).join('')}`, 'bad'],
    [K.stress, `Stress mean ${K.stress.value}, SD ${K.stress.sd}`, `Stress ${one(R.stressValues)} in all ${C.reportFiles} reports (SD 0)`, 'bad'],
    [K.anxiety, `Anxiety mean ${K.anxiety.value}`, `Anxiety ${one(R.anxietyValues)} in all ${C.reportFiles} reports`, 'bad'],
    [K.rStressAnxiety, `r = ${K.rStressAnxiety.value}`, R.rStressAnxiety == null ? 'Undefined: both scores are constant' : `r = ${R.rStressAnxiety.toFixed(2)}`, 'bad'],
    [K.rEffBurnout, `r = ${K.rEffBurnout.value}`, `r = ${fx(R.rEffBurnout)} across the ${C.scoredReports} scored reports (duplicates included)`, 'bad'],
    [K.wellnessGood, `${K.wellnessGood.value} sessions "Good"`, Object.entries(R.wellness).map(([k, n]) => `${n} ${k}`).join(', '), 'bad'],
  ];
  const threats = [
    ['No ground truth', 'No PHQ-9, GAD-7, PSS or burnout inventory was collected and no stress was induced, so the four scores are weightings, not measurements.'],
    ['One participant, few drawings', `${C.substantive} substantive drawings, apparently from one person. Nothing here generalises.`],
    ['No pressure signal', `All recorded pressure is ${C.pressureMode} (mouse input), so pressure features carry no information.`],
    ['Approximate geometry', 'The browser rasteriser approximates OpenCV; the build holds it to 5% on compactness and 0.02 on symmetry. Dynamic features match to 1e-9.'],
    ['Session length unknown', 'The saved JSON drops session start and end, so stroke frequency cannot be reproduced and is left out.'],
    ['Engine bug, not fixed', 'Fixing the key mismatch would change scores for new sessions and stale the old reports. That is a product decision, recorded in docs/research-review.md.'],
  ];
  return (
    <section id="claims" className="card window reveal" data-title="RESEARCH_PAPER.md — diff vs Records/">
      <p className="eyebrow">Claims vs record</p>
      <h2>The paper's results section does not come from this code or these records.</h2>
      <p className="sub">Left: quoted from the documents, not reproduced. Right: computed from <code>Records/</code> at build time. The README now frames PulseKey as a research prototype; the paper's section 4 still reads as a validated result.</p>
      <div style={{ overflowX: 'auto', marginTop: 12 }}>
        <table style={{ minWidth: 680 }}>
          <thead><tr><th>Source</th><th>Claimed (quoted, not reproduced)</th><th>What the records show</th><th>Verdict</th></tr></thead>
          <tbody>
            {rows.map(([c, claim, rec, v]) => (
              <tr key={c.line}><td className="mono">{src(c)}</td><td>{claim}</td><td>{rec}</td><td><span className={`pill ${v}`}>Not supported</span></td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <h3 style={{ marginTop: 22 }}>Limitations and threats to validity</h3>
      <div className="grid2" style={{ marginTop: 10 }}>
        {threats.map(([t, d]) => <div className="tile" key={t}><h3>{t}</h3><p className="hint" style={{ margin: '6px 0 0', fontSize: 13 }}>{d}</p></div>)}
      </div>
    </section>
  );
}

function Reproduce() {
  const docs = [
    ['docs/research-review.md', 'Research review', 'Graded against a PhD rubric'],
    ['analysis/engine_audit.py', 'Engine audit', 'Python engine on every report'],
    ['site/src/pipeline.js', 'JS port', 'Dynamic features, scoring, engine'],
    ['site/src/pipeline.check.mjs', 'Parity check', 'Runs inside npm run build'],
    ['features/dynamic_features.py', 'Dynamic features', 'The Python original'],
    ['RESEARCH_PAPER.md', 'Paper', 'With a reproducibility note'],
  ];
  return (
    <section id="reproduce" className="card window reveal" data-title="Terminal — reproduce">
      <p className="eyebrow">Reproduce it</p>
      <h2>Three commands check the pipeline, the port and this page.</h2>
      <ol className="steps" style={{ marginTop: 16 }}>
        <li><span className="n">1</span><div><b>Python suite</b><div className="hint"><code>pip install -r requirements-test.txt && python tests/integration_tests.py && python -m pytest tests</code></div></div></li>
        <li><span className="n">2</span><div><b>Engine audit</b><div className="hint"><code>python analysis/engine_audit.py</code> rewrites <code>analysis/engine_audit.json</code></div></div></li>
        <li><span className="n">3</span><div><b>Dashboard with parity check</b><div className="hint"><code>cd site && npm ci && npm run build</code> fails if the port drifts from the recorded reports</div></div></li>
      </ol>
      <div className="docs" style={{ marginTop: 20 }}>
        {docs.map(([p, t, d]) => <a key={p} href={blob(p)}><b>{t}</b><small>{d}</small></a>)}
      </div>
    </section>
  );
}
