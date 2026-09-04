#!/usr/bin/env node
/**
 * WCAG AA contrast audit over the rendered pages.
 *
 * Reading hex values out of the stylesheet is not enough: colour inherits,
 * backgrounds stack, gradients live in background-image, and both the text and
 * the gradient's own stops can be translucent. Each of those produced a wrong
 * answer while this was written, and two of them produced a wrong answer in
 * two *different* tools on 2026-09-04:
 *
 *   - `transparent` computes to `rgba(0, 0, 0, 0)`. Read as a colour it is
 *     black, so the blog hero's near-black h1 scored 1.11:1 against its own
 *     background. It is not black; it is "whatever is behind this".
 *   - A stop like `rgba(91, 140, 255, 0.14)` is not #5B8CFF. Composited over
 *     the white beneath it, it is #E8EFFF, and the paragraph that scored
 *     2.57:1 against the raw stop measures 7.05:1 against the real surface.
 *
 * So: resolve the opaque backdrop first, composite every translucent gradient
 * stop onto it, composite the text's own alpha onto each candidate surface,
 * and score against the worst one.
 *
 * Serve the site first:  python3 -m http.server 8877 --bind 127.0.0.1 &
 * Exits non-zero when anything fails AA.
 *
 *   node tools/check_contrast.cjs [base-url]
 *   PW=/abs/path/to/node_modules/playwright-core node tools/check_contrast.cjs
 */
const { chromium } = (() => {
  const candidates = [
    process.env.PW,
    'playwright-core',
    'playwright',
    require('path').join(__dirname, '..', 'node_modules', 'playwright-core'),
  ].filter(Boolean);
  for (const c of candidates) {
    try { return require(c); } catch { /* try the next candidate */ }
  }
  console.error('playwright-core not found. `npm i playwright-core`, or set PW= to an install.');
  process.exit(2);
})();

const fs = require('fs');
const path = require('path');

const BASE = process.argv[2] || 'http://127.0.0.1:8877';
const ROOT = path.join(__dirname, '..');
const PAGES = [
  ...fs.readdirSync(ROOT).filter((f) => f.endsWith('.html')),
  ...fs.readdirSync(path.join(ROOT, 'blog')).filter((f) => f.endsWith('.html')).map((f) => 'blog/' + f),
  ...fs.readdirSync(path.join(ROOT, 'docs')).filter((f) => f.endsWith('.html')).map((f) => 'docs/' + f),
].filter((f) => !path.basename(f).startsWith('_')).sort().map((f) => '/' + f);

(async () => {
  const browser = await chromium.launch();
  const page = await (await browser.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const agg = new Map();

  for (const p of PAGES) {
    await page.goto(BASE + p, { waitUntil: 'networkidle' });
    const rows = await page.evaluate(() => {
      const lin = (v) => { v /= 255; return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
      const lum = (c) => 0.2126 * lin(c[0]) + 0.7152 * lin(c[1]) + 0.0722 * lin(c[2]);
      const over = (fg, a, bg) => fg.map((v, i) => v * a + bg[i] * (1 - a));
      const rgba = (s) => {
        const m = String(s).match(/rgba?\(([^)]+)\)/);
        if (!m) return null;
        const n = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
        return { c: n.slice(0, 3), a: n.length > 3 ? n[3] : 1 };
      };
      const hexToRgb = (h) => {
        const s = h.slice(1);
        const f = s.length < 6 ? s.split('').map((x) => x + x).join('') : s;
        return [0, 2, 4].map((i) => parseInt(f.substr(i, 2), 16));
      };
      // background-image is a comma-separated LIST of layers, and a comma also
      // separates a gradient's own arguments and an rgb()'s channels. Split at
      // depth zero only, or the layers of a gradient-border card come back
      // shredded into fragments.
      const splitLayers = (s) => {
        const out = [];
        let depth = 0, cur = '';
        for (const ch of s) {
          if (ch === '(') depth++;
          else if (ch === ')') depth--;
          else if (ch === ',' && depth === 0) { out.push(cur.trim()); cur = ''; continue; }
          cur += ch;
        }
        if (cur.trim()) out.push(cur.trim());
        return out;
      };
      // Colour stops of one layer, alpha preserved. Positions and keywords
      // like `to right` are skipped; only actual colours come back.
      const stopsOf = (layer) =>
        (layer.match(/rgba?\([^)]+\)|#[0-9a-fA-F]{3,8}\b/g) || [])
          .map((c) => (c.startsWith('#') ? { c: hexToRgb(c), a: 1 } : rgba(c)))
          .filter(Boolean);

      // Every surface the text can land on. Walks outward collecting paints
      // until one of them is opaque, then composites what was crossed back
      // down onto it.
      //
      // Layer order matters and is the thing that is easy to get wrong: within
      // one element, background-image layers paint over background-color, and
      // the FIRST layer in the list paints on top. The gradient-border trick
      // — `linear-gradient(#fff,#fff), linear-gradient(100deg, indigo, cyan)`
      // with background-clip padding-box/border-box — relies on exactly that:
      // the white layer covers the content box and the brand gradient only
      // shows through the border. Reading both layers' stops as candidate
      // surfaces scored the card's body text at 1.1:1 against a gradient the
      // text never touches. An opaque layer ends the search.
      const surfaces = (el) => {
        const stack = [];   // nearest-first; each entry is one layer's stops
        // Composite the crossed layers back-to-front onto each base candidate.
        const settle = (bases) => {
          let cands = bases;
          for (let i = stack.length - 1; i >= 0; i--) {
            cands = cands.flatMap((b) => stack[i].map((s) => (s.a >= 0.999 ? s.c : over(s.c, s.a, b))));
            if (cands.length > 24) cands = cands.slice(0, 24);   // bound the fan-out
          }
          return cands;
        };
        let n = el;
        while (n && n !== document.documentElement) {
          const cs = getComputedStyle(n);
          const img = cs.backgroundImage;
          if (img && img !== 'none') {
            for (const layer of splitLayers(img)) {
              const st = stopsOf(layer);
              if (!st.length) continue;                       // url(), none, gradient we cannot read
              if (st.every((s) => s.a >= 0.999)) return settle(st.map((s) => s.c));
              stack.push(st);
            }
          }
          const bg = rgba(cs.backgroundColor);
          if (bg && bg.a >= 0.999) return settle([bg.c]);
          if (bg && bg.a > 0) stack.push([bg]);
          n = n.parentElement;
        }
        return settle([[255, 255, 255]]);
      };

      const out = [];
      for (const el of document.querySelectorAll('p, span, li, a, h1, h2, h3, h4, td, th, b, em, strong, small, div, button, label')) {
        const hasOwnText = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
        if (!hasOwnText) continue;
        // aria-hidden text is removed from the accessibility tree, so it is
        // decoration by declaration and WCAG 1.4.3 does not apply to it. The
        // watermark layer numerals on the home page are the case here.
        if (el.closest('[aria-hidden="true"]')) continue;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.1) continue;
        const fg = rgba(cs.color);
        if (!fg) continue;
        // color: transparent means the glyphs are painted by something else
        // (-webkit-text-fill-color, a clipped background) or not at all. Scoring
        // it composites the text into its own background and always returns
        // 1:1, which is noise, not a finding.
        if (fg.a < 0.05) continue;
        const size = parseFloat(cs.fontSize);
        const weight = parseInt(cs.fontWeight) || 400;
        const need = (size >= 24 || (size >= 18.66 && weight >= 700)) ? 3 : 4.5;
        let worst = Infinity;
        for (const bg of surfaces(el)) {
          const text = fg.a >= 0.999 ? fg.c : over(fg.c, fg.a, bg);
          const [hi, lo] = [lum(text), lum(bg)].sort((a, b) => b - a);
          worst = Math.min(worst, (hi + 0.05) / (lo + 0.05));
        }
        if (worst < need) {
          out.push({
            sel: el.tagName.toLowerCase() + '.' + ((el.className || '').toString().split(' ')[0] || '-'),
            ratio: +worst.toFixed(2), need, size, color: cs.color,
            sample: el.textContent.trim().slice(0, 26),
          });
        }
      }
      return out;
    });

    for (const r of rows) {
      const k = `${r.sel} | ${r.color} | ${r.size}px`;
      if (!agg.has(k)) agg.set(k, { ...r, n: 0, pages: new Set() });
      agg.get(k).n++;
      agg.get(k).pages.add(p);
    }
  }
  await browser.close();

  const rows = [...agg.entries()].sort((a, b) => a[1].ratio - b[1].ratio);
  console.log(`pages checked: ${PAGES.length}`);
  console.log(`failing text style combinations: ${rows.length}`);
  for (const [k, v] of rows.slice(0, 16)) {
    const where = [...v.pages].slice(0, 4).join(' ') + (v.pages.size > 4 ? ` +${v.pages.size - 4}` : '');
    console.log(`  ${v.ratio} (need ${v.need})  ${k.padEnd(48)} x${v.n}  <<${v.sample}>>\n        ${where}`);
  }
  if (rows.length) process.exit(1);
  console.log('all text meets WCAG AA');
})();
