// Component consistency audit (DESIGN.md): renders every page in Chrome and
// compares the computed style of each component across the whole site, which
// is what a source lint cannot see. Written 2026-11-27, when it found the
// section labels drawn at 18px on 184 elements because a more specific rule
// outranked the label's own. Report-only; run after a layout change:
//
//   python3 -m http.server -d . 8790 &   (or any server with clean URLs)
//   node tools/design_audit.mjs http://127.0.0.1:8790 pages.txt 1440
//
// pages.txt is one path per line (/, /fs, /docs/). Prints, per component,
// every distinct computed style and the pages that carry it; exit 1 when a
// label class or the section h2 has more than one.
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { setTimeout as sleep } from 'node:timers/promises';
const [base, pagesFile, w = '1440'] = process.argv.slice(2);
const pages = readFileSync(pagesFile, 'utf8').split('\n').filter(Boolean);
import { globSync } from 'node:fs';
const CHROME = (globSync(process.env.HOME + '/.cache/puppeteer/chrome-headless-shell/*/chrome-headless-shell-*/chrome-headless-shell')[0])
  || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9800 + Math.floor(Math.random() * 100);
const proc = spawn(CHROME, [`--remote-debugging-port=${port}`, '--hide-scrollbars', `--user-data-dir=/tmp/design-audit-${port}`, '--headless', 'about:blank'], { stdio: 'ignore' });
const PROBE = `(() => {
  const cs = (el) => getComputedStyle(el);
  const pick = (sel, f) => [...document.querySelectorAll(sel)].filter(e => e.offsetParent !== null).map(f);
  const font = e => { const s = cs(e); return s.fontSize + '/' + s.fontWeight + '/' + s.letterSpacing; };
  const hero = document.querySelector('.hero-flagship') ? 'centred-home' : document.querySelector('.split-hero') ? 'split' : document.querySelector('.page-hero.center') ? 'page-centred' : document.querySelector('.page-hero') ? 'page-left' : document.querySelector('.plan-hero') ? 'plan-hero' : document.querySelector('article h1') ? 'article' : 'other';
  return {
    hero,
    h1: pick('h1', font),
    h2: pick('main h2:not(.visually-hidden)', font),
    h3: pick('main h3', e => cs(e).fontSize),
    label: pick('.sec-no, .page-eyebrow, .k, .lpath-label, .card-layer, .lb-no, .fno, .pstep-n, .glance-title, .kicker-tag', e => e.className.split(' ')[0] + ':' + cs(e).color + ':' + cs(e).fontSize + ':' + cs(e).textTransform),
    btn: pick('main .btn', e => e.className.replace(/\\s+/g,'.') + ':' + Math.round(e.getBoundingClientRect().height) + ':' + cs(e).borderRadius + ':' + cs(e).fontSize),
    card: pick('main .card, main .pcard, main .fcell, main .lpath, main .qa', e => e.className.split(' ')[0] + ':' + cs(e).paddingTop + ':' + cs(e).borderTopLeftRadius + ':' + cs(e).boxShadow.slice(0, 18)),
    sectionPad: pick('main > section.section', e => cs(e).paddingTop),
    sizes: [...new Set([...document.querySelectorAll('main *')].filter(e => e.offsetParent !== null && e.childNodes.length && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())).map(e => cs(e).fontSize))],
  };
})()`;
let ws;
try {
  let target;
  for (let i = 0; i < 50; i++) { try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); if (target) break; } catch {} await sleep(100); }
  ws = new WebSocket(target.webSocketDebuggerUrl); await new Promise(r => ws.onopen = r);
  let id = 0; const pending = new Map();
  ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); } };
  const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', { width: +w, height: 900, deviceScaleFactor: 1, mobile: +w < 600 });
  const out = {};
  for (const p of pages) {
    await send('Page.navigate', { url: base + p });
    await sleep(900);
    const r = await send('Runtime.evaluate', { expression: PROBE, returnByValue: true });
    out[p] = r.result?.result?.value;
  }
  let fail = 0;
  for (const key of ['h1', 'h2', 'label', 'btn', 'card']) {
    const seen = new Map();
    for (const [p, v] of Object.entries(out)) for (const x of (v || {})[key] || []) {
      if (!seen.has(x)) seen.set(x, new Set()); seen.get(x).add(p);
    }
    console.log(key);
    for (const [x, ps] of [...seen].sort((a, b) => b[1].size - a[1].size))
      console.log(`  ${String(ps.size).padStart(4)} page(s)  ${x}   e.g. ${[...ps].slice(0, 3).join(' ')}`);
    if (key === 'label') {
      const byClass = new Map();
      for (const x of seen.keys()) { const c = x.split(':')[0]; if (c === 'k') continue; byClass.set(c, (byClass.get(c) || 0) + 1); }
      for (const [c, n] of byClass) if (n > 1) { console.log(`  ✗ label .${c} is drawn ${n} different ways`); fail = 1; }
    }
    if (key === 'h2') {
      const big = [...seen.keys()].filter(x => parseFloat(x) >= 30);
      if (big.length > 1) { console.log(`  ✗ section h2 is drawn ${big.length} different ways`); fail = 1; }
    }
  }
  console.log(`${Object.keys(out).length} page(s) audited`);
  process.exitCode = fail;
} finally { try { ws?.close(); } catch {} proc.kill('SIGKILL'); }
