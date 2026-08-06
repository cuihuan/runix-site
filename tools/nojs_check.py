#!/usr/bin/env python3
"""Verify the no-script navigation fallback actually reveals the nav.

Below 920px the nav links are display:none and only a script adds .open, so a
visitor with scripts off would see a hamburger that does nothing. A
<noscript><style> block on every page overrides that. It was added tonight
without being verified, because Chrome's --disable-javascript flag does nothing
in this build.

What this can and cannot establish, stated plainly:

  - CAN: that the fallback stylesheet, when applied, makes every nav link
    reachable at phone width. That is the part written by hand and the part
    that can be wrong. It is checked by lifting the CSS out of the <noscript>
    block, injecting it as an ordinary <style>, and measuring.
  - CANNOT: that <noscript> activates. That is browser behaviour, not ours, and
    blocking scripts with CSP does not trigger it -- CSP stops execution while
    the scripting-enabled flag stays on, so <noscript> remains inert. An earlier
    version of this file used CSP and would have reported a fallback failure
    that says nothing about the fallback.

So: presence of the block is checked as source, and its effect is checked by
rendering.
"""
import functools
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 8913
# Temp files written by the check tools use a leading underscore; every tool
# that globs pages skips them. A killed run leaves them behind twice tonight.
PAGES = ["index.html", "router.html", "pricing.html", "blog/index.html", "docs/index.html"]


def main():
    if not os.path.exists(CHROME):
        print("  Chrome not found")
        return 0
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *a, **k: None
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    bad = []
    try:
        for page in PAGES:
            src = open(page).read()
            m = re.search(r"<noscript>\s*(<style>.*?</style>)\s*</noscript>", src, re.S)
            if not m:
                bad.append(f"{page}: no <noscript> nav fallback at all")
                continue
            # Apply the fallback as an ordinary stylesheet, which is exactly
            # what the browser does once scripting is off.
            inner, frame = "_nojs.html", "_nojs_frame.html"
            open(inner, "w").write(src.replace("</head>", m.group(1) + "</head>", 1))
            open(frame, "w").write(
                f'<!DOCTYPE html><body style="margin:0">'
                f'<iframe id="f" src="/{inner}" style="width:375px;height:900px;border:0"></iframe>'
                f'<script>window.addEventListener("load",function(){{setTimeout(function(){{'
                f'  var d=document.getElementById("f").contentDocument;'
                f'  var vis=0, tog=0;'
                f'  d.querySelectorAll(".nav-links a[href]").forEach(function(a){{'
                f'    var r=a.getBoundingClientRect(); if(r.width>0&&r.height>0) vis++; }});'
                f'  var t=d.querySelector(".nav-toggle");'
                f'  if(t){{var tr=t.getBoundingClientRect(); tog=(tr.width>0&&tr.height>0)?1:0;}}'
                f'  var w=d.documentElement.scrollWidth - d.documentElement.clientWidth;'
                f'  document.title="NOJS "+JSON.stringify({{vis:vis,tog:tog,over:w}});'
                f'}},400);}});</script>')
            try:
                out = subprocess.run(
                    [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                     "--window-size=620,1000", "--virtual-time-budget=6000", "--dump-dom",
                     f"http://127.0.0.1:{PORT}/{frame}"],
                    capture_output=True, text=True, timeout=90).stdout
            finally:
                for f in (inner, frame):
                    os.path.exists(f) and os.remove(f)
            mm = re.search(r"<title>NOJS (\{[^<]*\})</title>", out)
            if not mm:
                bad.append(f"{page}: probe did not report")
                continue
            r = json.loads(mm.group(1))
            if r["vis"] < 5:
                bad.append(f"{page}: fallback applied and only {r['vis']} nav "
                           f"link(s) visible at 375px")
            if r["tog"]:
                bad.append(f"{page}: the hamburger is still shown with the "
                           f"fallback applied -- it does nothing without script")
            if r["over"] > 1:
                bad.append(f"{page}: fallback makes the page scroll "
                           f"{r['over']}px sideways at 375px")
    finally:
        httpd.shutdown()

    for b in bad:
        print(f"  ✗ {b}")
    print(f"  checked the no-script nav fallback on {len(PAGES)} page(s) "
          f"-- {len(bad)} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
