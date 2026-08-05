#!/usr/bin/env python3
"""Bump the ?v= query on versioned assets so a change takes effect immediately.

These filenames carry no content hash and this account's deploy token cannot
purge Cloudflare's cache, so without a query bump a CSS edit can sit behind a
stale copy for hours. Run this after touching anything in assets/, before
deploying:

    python3 tools/bump_assets.py            # bump every tracked asset
    python3 tools/bump_assets.py style.css  # bump just one

Prints the new version so it can be quoted in a commit message.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

TRACKED = ["style.css", "site-config.js", "favicon.svg", "logo.svg", "og-cover.png"]
wanted = sys.argv[1:] or TRACKED
unknown = [w for w in wanted if w not in TRACKED]
if unknown:
    sys.exit(f"not a tracked asset: {', '.join(unknown)} (known: {', '.join(TRACKED)})")

pages = glob.glob("*.html") + glob.glob("docs/*.html") + glob.glob("blog/*.html")
current = {}
for asset in wanted:
    seen = set()
    for page in pages:
        for m in re.finditer(re.escape(asset) + r"(?:\?v=(\d+))?", open(page).read()):
            seen.add(int(m.group(1)) if m.group(1) else 0)
    current[asset] = max(seen) if seen else 0

changed_pages = set()
for asset in wanted:
    new = current[asset] + 1
    # Match the asset with or without an existing ?v=, but never inside a
    # longer filename (favicon.svg must not match my-favicon.svg).
    pattern = re.compile(r"(?<![\w.-])" + re.escape(asset) + r"(\?v=\d+)?")
    for page in pages:
        src = open(page).read()
        out = pattern.sub(f"{asset}?v={new}", src)
        if out != src:
            open(page, "w").write(out)
            changed_pages.add(page)
    print(f"  {asset}: v{current[asset]} -> v{new}")

print(f"updated {len(changed_pages)} page(s)")
