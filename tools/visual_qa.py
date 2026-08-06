#!/usr/bin/env python3
"""Render every page in a real browser and report what breaks geometrically.

tools/qa.py reads the HTML; this one renders it. They catch different things —
a page can have perfect markup and still push a code block off the right edge
on a phone, or ship a 44px-wide tap target, or hide a heading under the sticky
header. None of that is visible in the source.

Checks, at three widths:
  * horizontal overflow of the document, and which element causes it
  * any element whose box extends past the viewport
  * text rendered below 12px
  * primary controls (buttons, nav links) under the 24x24 minimum from
    WCAG 2.2 Target Size (Minimum), 2.5.8
  * headings that would land under the sticky header when linked to
  * WCAG AA contrast, resolved from what actually rendered rather than from
    the stylesheet (this is the check that catches a theme flip leaving
    light-on-light text behind)

Usage: python3 tools/visual_qa.py [path ...]      (default: every page)
Exits non-zero if anything fails.
"""
import glob
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 8901
WIDTHS = [(375, "phone"), (768, "tablet"), (1440, "desktop")]

PROBE = r"""
<script>window.addEventListener('load',function(){setTimeout(function(){
  var out = {overflow:null, wide:[], tiny:[], small_targets:[], covered:[], vw:0,
  // How many elements each selector-based detector actually looked at. A
  // detector that examines nothing can never report anything, and reads as
  // coverage -- see tools/gate_coverage.py for the same idea in qa.py.
  seen: {controls:0, contentlinks:0, anchors:0}};
  out.vw = document.documentElement.clientWidth;
  var vw = document.documentElement.clientWidth;

  if (document.documentElement.scrollWidth > vw + 1) {
    out.overflow = document.documentElement.scrollWidth - vw;
  }

  function label(e){
    var s = e.tagName.toLowerCase();
    if (e.id) s += '#' + e.id;
    else if (e.className && typeof e.className === 'string')
      s += '.' + e.className.trim().split(/\s+/).slice(0,2).join('.');
    return s;
  }

  var all = document.querySelectorAll('body *');
  for (var i = 0; i < all.length; i++) {
    var e = all[i], r = e.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    var cs = getComputedStyle(e);
    if (cs.visibility === 'hidden' || cs.display === 'none') continue;

    // Boxes that stick out past the right edge. Ignore anything the author
    // deliberately made scrollable — that is the correct fix, not a bug.
    if (r.right > vw + 1 && cs.overflowX !== 'auto' && cs.overflowX !== 'scroll') {
      var p = e.parentElement, scrollable = false;
      while (p && p !== document.body) {
        var pcs = getComputedStyle(p);
        if (pcs.overflowX === 'auto' || pcs.overflowX === 'scroll') { scrollable = true; break; }
        p = p.parentElement;
      }
      if (!scrollable && out.wide.length < 6)
        out.wide.push(label(e) + ' right=' + Math.round(r.right));
    }

    // Text too small to read. Only leaf nodes with actual text.
    if (e.children.length === 0 && e.textContent.trim().length > 3) {
      var fs = parseFloat(cs.fontSize);
      if (fs < 12 && out.tiny.length < 6)
        out.tiny.push(label(e) + ' ' + fs + 'px');
    }
  }

  // WCAG 2.2 2.5.8 minimum target size, applied to real controls rather than
  // inline prose links (which the spec exempts).
  var controls = document.querySelectorAll('.btn, .nav-links a, button, .copy-btn');
      out.seen.controls += controls.length;
  for (var j = 0; j < controls.length; j++) {
    var c = controls[j], cr = c.getBoundingClientRect();
    if (cr.width === 0 || cr.height === 0) continue;
    if ((cr.width < 24 || cr.height < 24) && out.small_targets.length < 6)
      out.small_targets.push(label(c) + ' ' + Math.round(cr.width) + 'x' + Math.round(cr.height));
  }

  // Contrast, measured on what actually rendered. A light-on-light or
  // dark-on-dark regression survives every source-level check there is; the
  // only way to catch it is to resolve the real colours in the browser.
  function rgba(s){
    var m = s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    var p = m[1].split(',').map(parseFloat);
    return {c: [p[0], p[1], p[2]], a: p.length > 3 ? p[3] : 1};
  }
  function rgb(s){
    var v = rgba(s);
    return (v && v.a > 0) ? v.c : null;
  }
  function over(top, alpha, bottom){    // src-over compositing
    return [0,1,2].map(function(i){ return top[i]*alpha + bottom[i]*(1-alpha); });
  }
  function lum(c){
    var a = c.map(function(v){ v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); });
    return 0.2126*a[0] + 0.7152*a[1] + 0.0722*a[2];
  }
  function bgOf(e){
    // Collect every painted layer up to the first opaque one, then composite
    // them. Treating a 10%-alpha tint as if it were solid is how a perfectly
    // legible badge gets reported at 1.96:1 — the layers have to be blended,
    // not just the topmost one read.
    var layers = [], grad = false, base = [255,255,255];
    while (e && e !== document.documentElement) {
      var cs = getComputedStyle(e);
      if (cs.backgroundImage && cs.backgroundImage !== 'none') grad = true;
      var v = rgba(cs.backgroundColor);
      if (v && v.a > 0) {
        if (v.a >= 0.999) { base = v.c; break; }
        layers.push(v);
      }
      e = e.parentElement;
    }
    for (var n = layers.length - 1; n >= 0; n--) base = over(layers[n].c, layers[n].a, base);
    return {c: base, grad: grad};
  }
  out.contrast = [];
  var texts = document.querySelectorAll('body *');
  for (var m2 = 0; m2 < texts.length; m2++) {
    var el = texts[m2];
    if (el.children.length !== 0) continue;
    var txt = el.textContent.trim();
    if (txt.length < 3) continue;
    var r2 = el.getBoundingClientRect();
    if (r2.width === 0 || r2.height === 0) continue;
    var s2 = getComputedStyle(el);
    if (s2.visibility === 'hidden' || parseFloat(s2.opacity) < 0.5) continue;
    if (s2.webkitTextFillColor === 'rgba(0, 0, 0, 0)') continue;  // gradient text
    var fgv = rgba(s2.color);
    if (!fgv || fgv.a === 0) continue;
    var bg = bgOf(el);
    if (bg.grad) continue;   // can't resolve a gradient to one number honestly
    // Semi-transparent text blends with what is behind it, same as background.
    var fg = fgv.a < 1 ? over(fgv.c, fgv.a, bg.c) : fgv.c;
    var l1 = lum(fg), l2 = lum(bg.c);
    var ratio = (Math.max(l1,l2) + 0.05) / (Math.min(l1,l2) + 0.05);
    var size = parseFloat(s2.fontSize), bold = parseInt(s2.fontWeight, 10) >= 700;
    var need = (size >= 24 || (bold && size >= 18.66)) ? 3.0 : 4.5;
    if (ratio < need && out.contrast.length < 8) {
      out.contrast.push(label(el) + ' ' + ratio.toFixed(2) + ':1 (needs ' + need + ') "' +
                        txt.slice(0, 24) + '"');
    }
  }

  // WCAG 1.4.1: if colour is the only thing marking a link, the link must
  // contrast with the surrounding text by at least 3:1. Links inside .feature
  // lists were rendering LIGHTER than the body text — technically a different
  // colour, in practice a de-emphasis. Underlined links are exempt.
  out.dimlinks = [];
  var content = document.querySelectorAll('main a[href^="/"], main a[href^="http"], .page-hero a[href^="/"], .hero a[href^="/"]');
      out.seen.contentlinks += content.length;
  for (var q = 0; q < content.length; q++) {
    var a = content[q];
    if (a.closest('nav') || a.closest('footer') || a.classList.contains('btn')) continue;
    var ar = a.getBoundingClientRect();
    if (ar.width === 0 || ar.height === 0) continue;
    var as = getComputedStyle(a);
    if (as.textDecorationLine.indexOf('underline') >= 0) continue;   // has a non-colour cue
    var parent = a.parentElement;
    if (!parent) continue;
    var ps = getComputedStyle(parent);
    var lc = rgba(as.color), pc = rgba(ps.color);
    if (!lc || !pc) continue;
    var la = lum(lc.c), pa = lum(pc.c);
    var ratio2 = (Math.max(la, pa) + 0.05) / (Math.min(la, pa) + 0.05);
    // Same colour as the surrounding text is fine only if the whole block is a
    // link (a card, a nav row); a link inside a sentence needs to stand out.
    if (parent.textContent.trim() === a.textContent.trim()) continue;
    // A link wrapping a heading is a card or block link — the whole surface is
    // the affordance, so it does not need to stand out from a sentence.
    if (a.querySelector('h1,h2,h3,h4')) continue;
    if (ratio2 < 3 && out.dimlinks.length < 5)
      out.dimlinks.push(label(a) + ' vs its text ' + ratio2.toFixed(2) + ':1 "' +
                        a.textContent.trim().slice(0, 24) + '"');
  }

  // Anything linkable must clear the sticky header once scrolled to.
  var hdr = document.querySelector('.site-header');
  if (hdr) {
    var hh = hdr.getBoundingClientRect().height;
    var targets = document.querySelectorAll('h1[id], h2[id], h3[id]');
        out.seen.anchors += targets.length;
    for (var k = 0; k < targets.length; k++) {
      var sm = parseFloat(getComputedStyle(targets[k]).scrollMarginTop) || 0;
      if (sm < hh && out.covered.length < 4)
        out.covered.push(label(targets[k]) + ' scroll-margin=' + sm + ' header=' + Math.round(hh));
    }
  }

  document.title = 'VQA ' + JSON.stringify(out);
}, 250);});</script>
"""


def serve():
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def probe(path, width):
    """Render `path` at exactly `width` and return what the probe found.

    Chrome headless clamps its viewport to a 500px minimum, so --window-size=375
    silently renders at 500 and every phone-width check is a lie. The target is
    therefore loaded inside an iframe of the requested width: media queries and
    getBoundingClientRect inside an iframe key off the iframe's own viewport, so
    375 really is 375. The frame is same-origin, so the parent can read the
    result the probe leaves in the inner document's title.
    """
    inner, outer = "_vqa.html", "_vqa_frame.html"
    open(inner, "w").write(open(path).read().replace("</body>", PROBE + "</body>", 1))
    open(outer, "w").write(
        f'<!DOCTYPE html><html><body style="margin:0">'
        f'<iframe id="f" src="/{inner}" style="width:{width}px;height:900px;border:0"></iframe>'
        f'<script>window.addEventListener("load",function(){{'
        f'  var n=0,t=setInterval(function(){{'
        f'    var d=document.getElementById("f").contentDocument;'
        f'    if(d&&d.title.indexOf("VQA ")===0){{document.title=d.title;clearInterval(t);}}'
        f'    if(++n>60)clearInterval(t);'
        f'  }},100);}});</script></body></html>')
    try:
        out = subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             f"--window-size={max(width + 60, 620)},1000",
             "--virtual-time-budget=6000", "--dump-dom",
             f"http://127.0.0.1:{PORT}/{outer}"],
            capture_output=True, text=True, timeout=90,
        ).stdout
    finally:
        for f in (inner, outer):
            if os.path.exists(f):
                os.remove(f)
    match = re.search(r"VQA (\{.*?\})</title>", out, re.S)
    return json.loads(match.group(1)) if match else None


pages = sys.argv[1:] or sorted(
    [_p for _p in glob.glob("*.html") if not os.path.basename(_p).startswith("_")] + [_p for _p in glob.glob("docs/*.html") if not os.path.basename(_p).startswith("_")] + [_p for _p in glob.glob("blog/*.html") if not os.path.basename(_p).startswith("_")]
)
httpd = serve()
time.sleep(0.6)

problems = []
examined = {}
try:
    for page in pages:
        for width, name in WIDTHS:
            r = probe(page, width)
            if r is None:
                problems.append(f"{page} @{name}: probe did not report")
                continue
            if r.get("vw") != width:
                problems.append(f"{page} @{name}: asked for {width}px, rendered at {r.get('vw')}px")
            if r["overflow"]:
                problems.append(f"{page} @{name}: page scrolls {r['overflow']}px sideways")
            for w in r["wide"]:
                problems.append(f"{page} @{name}: past right edge — {w}")
            for t in r["tiny"]:
                problems.append(f"{page} @{name}: text under 12px — {t}")
            for s in r["small_targets"]:
                problems.append(f"{page} @{name}: target under 24x24 — {s}")
            for d in r.get("dimlinks", []):
                problems.append(f"{page} @{name}: link not distinguishable — {d}")
            for c in r.get("contrast", []):
                problems.append(f"{page} @{name}: contrast — {c}")
            for c in r["covered"]:
                problems.append(f"{page} @{name}: anchor lands under header — {c}")
            for _k, _v in (r.get("seen") or {}).items():
                examined[_k] = examined.get(_k, 0) + _v
finally:
    httpd.shutdown()

print(f"rendered {len(pages)} page(s) x {len(WIDTHS)} widths")

# A detector whose selector matches nothing cannot report anything, and a run
# with zero findings then reads as coverage it does not have. qa.py has the same
# failure mode; tools/gate_coverage.py finds it there by tracing. Here the
# detectors live in the browser, so the probe counts what each one looked at.
_dead = [k for k, v in sorted(examined.items()) if v == 0]
if _dead:
    print("  ! detector(s) examined nothing, so they cannot report: "
          + ", ".join(_dead))
    problems.append("a detector examined no elements: " + ", ".join(_dead))
else:
    print("  detectors examined: "
          + ", ".join(f"{k}={v}" for k, v in sorted(examined.items())))
if problems:
    seen, unique = set(), []
    for p in problems:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    print(f"\n{len(unique)} problem(s):")
    for p in unique:
        print(f"  ✗ {p}")
    sys.exit(1)
print("no geometric problems")
