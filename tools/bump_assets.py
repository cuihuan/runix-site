#!/usr/bin/env python3
"""Bump the ?v= query on versioned assets so a change takes effect immediately.

These filenames carry no content hash and this account's deploy token cannot
purge Cloudflare's cache, so without a query bump a CSS edit can sit behind a
stale copy for hours. Run this after touching anything in assets/, before
deploying:

    python3 tools/bump_assets.py             # bump every tracked asset
    python3 tools/bump_assets.py style.css   # bump just one
    python3 tools/bump_assets.py --if-changed  # bump only what actually changed

--if-changed hashes each asset against tools/assets.json and bumps only the
ones whose bytes moved. That is what deploy.sh runs, and it is what makes a
one-year cache on assets/ safe: an asset cannot be served stale, because a
changed asset always gets a new URL, and an unchanged one never needs one.

Prints the new version so it can be quoted in a commit message.
"""
import hashlib
import json
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

TRACKED = ["style.css", "site-config.js", "favicon.svg", "logo.svg", "og-cover.png",
           "fonts/inter-latin.woff2", "fonts/inter-latin-ext.woff2"]
MANIFEST = os.path.join("tools", "assets.json")

if_changed = "--if-changed" in sys.argv
args = [a for a in sys.argv[1:] if a != "--if-changed"]

if if_changed:
    previous = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
    digests = {a: hashlib.sha256(open(os.path.join("assets", a), "rb").read()).hexdigest()[:16]
               for a in TRACKED if os.path.exists(os.path.join("assets", a))}
    wanted = [a for a in TRACKED if digests.get(a) and previous.get(a) != digests[a]]
    first_run = not previous
    if first_run:
        json.dump(digests, open(MANIFEST, "w"), indent=1, sort_keys=True)
        print(f"  first run: recorded {len(digests)} asset hash(es), bumped nothing")
        sys.exit(0)
    if not wanted:
        print("  no asset changed")
        sys.exit(0)
else:
    wanted = args or TRACKED
unknown = [w for w in wanted if w not in TRACKED]
if unknown:
    sys.exit(f"not a tracked asset: {', '.join(unknown)} (known: {', '.join(TRACKED)})")

# Font URLs live in the stylesheet, not in the pages; everything else is
# referenced from the HTML. Both are rewritten the same way.
pages = (glob.glob("*.html") + glob.glob("docs/*.html") + glob.glob("blog/*.html")
         + ["assets/style.css"])
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

print(f"updated {len(changed_pages)} file(s)")

if if_changed:
    # Bumping one asset can change another. A font bump rewrites its URL inside
    # style.css, so the stylesheet's own bytes change — and if its ?v= does not
    # move in the same run, the edge keeps serving the previous stylesheet for a
    # year under the old immutable URL, and the new font is never fetched. So
    # re-hash and keep going until nothing more changes.
    for _round in range(5):
        after = {a: hashlib.sha256(open(os.path.join("assets", a), "rb").read()).hexdigest()[:16]
                 for a in TRACKED if os.path.exists(os.path.join("assets", a))}
        cascaded = [a for a in TRACKED if after.get(a) and digests.get(a) != after[a]]
        if not cascaded:
            break
        print(f"  cascade: {', '.join(cascaded)} changed as a result — bumping too")
        for asset in cascaded:
            seen = set()
            for page in pages:
                for m in re.finditer(re.escape(asset) + r"(?:\?v=(\d+))?", open(page).read()):
                    seen.add(int(m.group(1)) if m.group(1) else 0)
            new_v = (max(seen) if seen else 0) + 1
            pattern = re.compile(r"(?<![\w.-])" + re.escape(asset) + r"(\?v=\d+)?")
            for page in pages:
                src = open(page).read()
                out = pattern.sub(f"{asset}?v={new_v}", src)
                if out != src:
                    open(page, "w").write(out)
                    changed_pages.add(page)
            print(f"    {asset}: -> v{new_v}")
        digests = after
    else:
        sys.exit("  bump did not settle after 5 rounds — stopping rather than looping")

    final = {a: hashlib.sha256(open(os.path.join("assets", a), "rb").read()).hexdigest()[:16]
             for a in TRACKED if os.path.exists(os.path.join("assets", a))}
    json.dump(final, open(MANIFEST, "w"), indent=1, sort_keys=True)
    print(f"  manifest updated ({len(final)} asset(s))")
