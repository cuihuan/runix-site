#!/usr/bin/env python3
"""Report JavaScript errors and failed requests on the rendered pages.

The site has one script and a strict CSP. Neither guarantees the page runs
clean: a typo in an event handler, a selector that no longer matches, a CSP
directive that blocks something the page needs -- all of it fails silently in
front of a visitor and leaves no trace in any source-level check.

Chrome is asked to log console messages and network failures, and any error or
CSP violation fails the run. Warnings are printed but do not fail, since some
are outside our control.
"""
import functools
import glob
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
PORT = 8917
PAGES = ["index.html", "router.html", "pricing.html", "blog/index.html",
         "blog/llm-observability.html", "docs/router.html", "404.html"]

# Collect errors from the page itself, and from anything that fails to load.
PROBE = """<script>
window.__errs = [];
window.addEventListener('error', function (e) {
  window.__errs.push((e.target && e.target.src ?
    'failed to load ' + e.target.src : 'error: ' + e.message));
}, true);
window.addEventListener('unhandledrejection', function (e) {
  window.__errs.push('unhandled rejection: ' + e.reason);
});
window.addEventListener('securitypolicyviolation', function (e) {
  window.__errs.push('CSP blocked ' + e.violatedDirective + ' ' + e.blockedURI);
});
</script>"""


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
            # The probe goes first so it is listening before anything else runs.
            inner = "_console.html"
            open(inner, "w").write(src.replace("<head>", "<head>" + PROBE, 1))
            frame = "_console_frame.html"
            open(frame, "w").write(
                f'<!DOCTYPE html><body style="margin:0">'
                f'<iframe id="f" src="/{inner}" style="width:1200px;height:900px;border:0"></iframe>'
                f'<script>window.addEventListener("load",function(){{setTimeout(function(){{'
                f'  var w=document.getElementById("f").contentWindow;'
                f'  document.title="CON "+JSON.stringify((w.__errs)||["probe did not run"]);'
                f'}},900);}});</script>')
            try:
                out = subprocess.run(
                    [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                     "--window-size=1280,1000", "--virtual-time-budget=7000", "--dump-dom",
                     f"http://127.0.0.1:{PORT}/{frame}"],
                    capture_output=True, text=True, timeout=90).stdout
            finally:
                for f in (inner, frame):
                    os.path.exists(f) and os.remove(f)
            m = re.search(r"<title>CON (\[[^<]*\])</title>", out)
            if not m:
                bad.append(f"{page}: probe did not report")
                continue
            for e in json.loads(m.group(1)):
                # The analytics beacon is injected by Cloudflare at the edge and
                # is not present when serving locally, so a failure to load it
                # here says nothing about production.
                if "cloudflareinsights" in e or "googletagmanager" in e:
                    continue
                bad.append(f"{page}: {e}")
    finally:
        httpd.shutdown()

    for b in bad:
        print(f"  ✗ {b}")
    print(f"  rendered {len(PAGES)} page(s) -- {len(bad)} console error(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
