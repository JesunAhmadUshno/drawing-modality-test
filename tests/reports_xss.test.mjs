// reports.html must render values from Records/ as text, never as markup.
// Runs the page's inline script against a minimal stub DOM. Run: node --test tests/reports_xss.test.mjs
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const html = readFileSync(new URL('../frontend/reports.html', import.meta.url), 'utf8');
const script = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const PAYLOAD = '<img src=x onerror=alert(1)>';

function loadPage(details) {
  const written = [];
  const el = () => {
    const e = { style: {}, classList: { add() {}, remove() {} }, value: '', addEventListener() {}, appendChild() {} };
    Object.defineProperty(e, 'innerHTML', { set(v) { written.push(v); }, get() { return ''; } });
    return e;
  };
  const els = {};
  const ctx = {
    document: {
      getElementById: id => (els[id] ??= el()),
      createElement: el,
      addEventListener() {},
      body: el(),
    },
    fetch: async () => ({ ok: true, json: async () => details }),
    alert: msg => { throw new Error(msg); },
    Chart: class { destroy() {} },
    console,
  };
  vm.createContext(ctx);
  vm.runInContext(script, ctx);
  return { ctx, written };
}

test('session card escapes the session id', () => {
  const { ctx, written } = loadPage({});
  ctx.renderSessions([{ session_id: PAYLOAD, timestamp: 0, grade: PAYLOAD }]);
  const out = written.join('');
  assert.ok(!out.includes(PAYLOAD), out);
  assert.ok(out.includes('&lt;img src=x onerror=alert(1)&gt;'));
});

test('report details escape metadata values, metric paths and image names', async () => {
  const { ctx, written } = loadPage({
    report: { features: { dynamic: { [PAYLOAD]: PAYLOAD } } },
    session_json: { type: PAYLOAD },
    images: [{ name: PAYLOAD, url: '/x"onerror="alert(1)' }],
  });
  await ctx.viewReport('x1');
  const out = written.join('');
  assert.ok(!out.includes(PAYLOAD), out);
  assert.ok(!out.includes('"onerror="'), out);
});
