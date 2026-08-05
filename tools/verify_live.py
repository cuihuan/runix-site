#!/usr/bin/env python3
"""Verify the live site, tolerating the edge's post-deploy inconsistency.

A single probe right after a deploy is not evidence. Cloudflare's edge nodes
pick up a new build at slightly different times, so the same URL can answer 200
from one node and 404 from another for a minute or two — which reads exactly
like a broken page and has sent this project chasing three ghosts already.

So: probe every URL repeatedly, and only report a failure that is *consistent*.
Anything that flickers is reported as still-propagating, not as broken.

    python3 tools/verify_live.py                 # every indexable page
    python3 tools/verify_live.py /faq /access    # just these
    python3 tools/verify_live.py --contains /faq "Questions buyers"
"""
import glob
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SITE = "https://runixcloud.io"
ROUNDS = 3
GAP = 8  # seconds between rounds, enough for a lagging node to catch up


def probe(path, needle=None):
    url = f"{SITE}{path}"
    args = ["curl", "-sL", "--compressed", "--max-time", "20",
            "-H", "Cache-Control: no-cache", f"{url}?_={int(time.time()*1000)}"]
    if needle is None:
        args = ["curl", "-sL", "-o", "/dev/null", "-w", "%{http_code}",
                "--max-time", "20", f"{url}?_={int(time.time()*1000)}"]
        return subprocess.run(args, capture_output=True, text=True).stdout.strip()
    body = subprocess.run(args, capture_output=True, text=True).stdout
    return "hit" if needle in body else "miss"


def paths_from_disk():
    out = []
    for f in sorted(glob.glob("*.html") + glob.glob("docs/*.html") + glob.glob("blog/*.html")):
        if os.path.basename(f) == "404.html":
            continue
        slug = f[:-5]
        if slug.endswith("/index"):
            out.append("/" + slug[:-5])
        elif slug == "index":
            out.append("/")
        else:
            out.append("/" + slug)
    return out


args = sys.argv[1:]
needle = None
if args and args[0] == "--contains":
    _, path, needle = args[0], args[1], " ".join(args[2:])
    targets = [path]
else:
    targets = args or paths_from_disk()

results = {t: [] for t in targets}
for round_no in range(ROUNDS):
    if round_no:
        time.sleep(GAP)
    for t in targets:
        results[t].append(probe(t, needle))

expected = "hit" if needle else "200"
broken, flaky = [], []
for t, seen in results.items():
    if all(s == expected for s in seen):
        continue
    (broken if all(s != expected for s in seen) else flaky).append((t, seen))

print(f"probed {len(targets)} path(s) x {ROUNDS} rounds")
for t, seen in flaky:
    print(f"  … {t}: still propagating {seen}")
for t, seen in broken:
    print(f"  ✗ {t}: consistently wrong {seen}")
if broken:
    sys.exit(1)
print("all consistently correct" if not flaky else "no consistent failures")
