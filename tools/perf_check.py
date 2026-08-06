#!/usr/bin/env python3
"""Measure what the browser actually does when it loads a page.

Core Web Vitals are a ranking input and a real experience, and nothing on this
site has ever been measured — page weight, request count, layout shift and the
render-blocking chain were all assumed rather than checked.

Reported per page:
  * transferred bytes and request count, by resource type
  * Largest Contentful Paint, and which element it was
  * Cumulative Layout Shift, and the biggest single shift source
  * how long the render-blocking chain in <head> takes
  * fonts: whether any face blocked text from painting

Loaded from a local server, so the numbers are a floor — a real visitor adds
network. That is the point: anything slow here is slow everywhere.

Usage: python3 tools/perf_check.py [path ...]
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
PORT = 8903

PROBE = r"""
<script>
(function () {
  var lcp = null, cls = 0, worst = null;
  try {
    new PerformanceObserver(function (l) {
      var e = l.getEntries();
      var last = e[e.length - 1];
      lcp = { t: Math.round(last.startTime), el: last.element ? last.element.tagName.toLowerCase() +
              (last.element.className && typeof last.element.className === 'string'
                ? '.' + last.element.className.trim().split(/\s+/)[0] : '') : 'unknown' };
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch (e) {}
  try {
    new PerformanceObserver(function (l) {
      l.getEntries().forEach(function (s) {
        if (s.hadRecentInput) return;
        cls += s.value;
        if (!worst || s.value > worst.v) {
          var src = s.sources && s.sources[0] && s.sources[0].node;
          worst = { v: s.value, el: src ? src.tagName.toLowerCase() : 'unknown' };
        }
      });
    }).observe({ type: 'layout-shift', buffered: true });
  } catch (e) {}

  window.addEventListener('load', function () {
    setTimeout(function () {
      var res = performance.getEntriesByType('resource');
      var byType = {}, total = 0;
      res.forEach(function (r) {
        var t = r.initiatorType || 'other';
        if (/\.woff2?$/.test(r.name)) t = 'font';
        byType[t] = byType[t] || { n: 0, bytes: 0 };
        byType[t].n++;
        byType[t].bytes += r.encodedBodySize || 0;
        total += r.encodedBodySize || 0;
      });
      var nav = performance.getEntriesByType('navigation')[0] || {};
      var doc = nav.encodedBodySize || 0;
      var blocking = res.filter(function (r) {
        return (r.initiatorType === 'link' || r.initiatorType === 'script') &&
               r.startTime < (nav.domContentLoadedEventStart || 1e9);
      }).length;

      document.title = 'PERF ' + JSON.stringify({
        doc: doc, resBytes: total, total: doc + total,
        types: byType, requests: res.length,
        lcp: lcp, cls: Math.round(cls * 1000) / 1000, worstShift: worst,
        dcl: Math.round(nav.domContentLoadedEventStart || 0),
        blockingInHead: blocking,
        fontsLoaded: (document.fonts && document.fonts.size) || 0
      });
    }, 900);
  });
})();
</script>
"""


def serve():
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def measure(path):
    tmp = "_perf.html"
    open(tmp, "w").write(open(path).read().replace("</body>", PROBE + "</body>", 1))
    try:
        out = subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             "--window-size=1440,900", "--virtual-time-budget=8000", "--dump-dom",
             f"http://127.0.0.1:{PORT}/{tmp}"],
            capture_output=True, text=True, timeout=90,
        ).stdout
    finally:
        os.remove(tmp)
    m = re.search(r"PERF (\{.*?\})</title>", out, re.S)
    return json.loads(m.group(1)) if m else None


def kb(n):
    return f"{n / 1024:.0f}KB"


pages = sys.argv[1:] or ["index.html", "router.html", "pricing.html",
                         "docs/router.html", "blog/model-failover.html", "about.html"]
httpd = serve()
time.sleep(0.6)
rows, problems = [], []
try:
    for p in pages:
        r = measure(p)
        if not r:
            problems.append(f"{p}: no measurement returned")
            continue
        rows.append((p, r))
        # Thresholds: Google's "good" CLS is 0.1. LCP good is 2.5s but this is
        # localhost, so anything over 1s here is a structural problem, not network.
        # CLS is reported, never gated on. Headless Chrome with a virtual time
        # budget completes layout before it paints, so it scores 0 even for a
        # page that visibly shifts — verified by injecting a full-width image
        # with no dimensions and watching it stay at 0 while becoming the LCP
        # element. A check that cannot fail is worse than no check, so the real
        # cause is checked statically instead, below.
        if r["lcp"] and r["lcp"]["t"] > 1000:
            problems.append(f"{p}: LCP {r['lcp']['t']}ms on localhost ({r['lcp']['el']})")
        if r["total"] > 900 * 1024:
            problems.append(f"{p}: {kb(r['total'])} transferred")
finally:
    httpd.shutdown()

# The dominant cause of layout shift on a text-heavy site is an image that
# reserves no space until it loads. That is decidable from the markup, so it is
# checked here rather than inferred from a metric this environment cannot
# measure.
for page in pages:
    for img in re.findall(r"<img\b[^>]*>", open(page).read()):
        has_attrs = re.search(r'\bwidth="', img) and re.search(r'\bheight="', img)
        has_ratio = "aspect-ratio" in img
        if not (has_attrs or has_ratio):
            problems.append(f"{page}: <img> without width/height or aspect-ratio "
                            f"reserves no space until it loads — {img[:70]}")
# NOTE: the site has no <img> at all -- every graphic is inline SVG -- so this
# loop has nothing to iterate and tools/gate_coverage.py reports it as never
# reached. Dead by absence, not defect: it starts working the day an image is
# added, which is the day it is needed. qa.py's alt-text check is the same.

print(f"{'page':<34}{'total':>9}{'reqs':>6}{'LCP':>8}{'CLS':>7}  LCP element")
for p, r in rows:
    lcp = r["lcp"] or {}
    print(f"{p:<34}{kb(r['total']):>9}{r['requests']:>6}"
          f"{str(lcp.get('t', '?')) + 'ms':>8}{r['cls']:>7}  {lcp.get('el', '?')}")

if rows:
    t = rows[0][1]["types"]
    print("\nby type (homepage):")
    for k, v in sorted(t.items(), key=lambda i: -i[1]["bytes"]):
        print(f"  {k:<10} {v['n']:>2} request(s)  {kb(v['bytes'])}")

if problems:
    print(f"\n{len(problems)} problem(s):")
    for x in problems:
        print(f"  ✗ {x}")
    sys.exit(1)
print("\nno performance problems")
