#!/usr/bin/env python3
"""Keep sitemap lastmod honest: bump it when the content changed, never otherwise.

Two failure modes, and this avoids both.

Stale: non-blog entries were hand-maintained, so /about still advertised
2026-07-24 after being substantially rewritten. Search engines use lastmod to
decide what to re-crawl; a page that changed and does not say so waits.

Falsely fresh: every asset-version bump touches all 46 files, and every commit
touches most of them. Bumping lastmod on that basis tells search engines the
whole site changed when nothing did — and Google's guidance is explicit that a
site whose lastmod cannot be trusted has its lastmod ignored, which loses the
signal for the pages that genuinely need it.

So the comparison is on the page's *content*: chrome, head, scripts and the
visually-hidden skip link removed, tags stripped, whitespace normalised, then
hashed. That normalisation was arrived at by checking: comparing raw <main>
reported all 45 pages changed, because <main> did not exist in the baseline at
all; comparing visible text reported the legal pages changed, because the only
difference was the words "Skip to content".

State lives in tools/lastmod.json (not deployed). First run adopts whatever is
there without bumping anything.

Usage:
    python3 tools/update_lastmod.py            # report only
    python3 tools/update_lastmod.py --write    # update sitemap.xml
"""
import datetime
import glob
import hashlib
import html as htmllib
import json
import os
import re
import sys
import zoneinfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

TZ = zoneinfo.ZoneInfo("Asia/Shanghai")
MANIFEST = os.path.join("tools", "lastmod.json")
SITE = "https://runixcloud.io"


def content_hash(path):
    text = open(path).read()
    for pattern in (r"<head\b.*?</head>", r"<header\b.*?</header>",
                    r"<footer\b.*?</footer>", r"<script\b.*?</script>",
                    r'<a class="skip-link".*?</a>'):
        text = re.sub(pattern, " ", text, flags=re.S | re.I)
    text = htmllib.unescape(re.sub(r"<[^>]+>", " ", text))
    text = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def slug(path):
    s = path[:-5]
    if s.endswith("/index"):
        s = s[:-6]
    return "/" if s == "index" else "/" + s


# Blog posts are excluded on purpose: their lastmod is the publication date,
# written by publish.py, and that is the right answer for an article. Adding a
# related-reading block to eighteen old posts is a real edit but not a
# significant modification, and bumping all of them would read as a site-wide
# refresh that did not happen.
pages = [p for p in sorted(glob.glob("*.html") + glob.glob("docs/*.html"))
         if os.path.basename(p) != "404.html"]
current = {p: content_hash(p) for p in pages}

previous = {}
if os.path.exists(MANIFEST):
    previous = json.load(open(MANIFEST))

first_run = not previous
today = datetime.datetime.now(TZ).date().isoformat()

changed = [p for p in pages if previous.get(p) != current[p]]
if first_run:
    print(f"  first run: adopting {len(pages)} hashes without changing any lastmod")
    changed = []
else:
    print(f"  {len(changed)} page(s) changed content since the last run")
    for p in changed:
        print(f"    {p}")

write = "--write" in sys.argv
if changed and write:
    sitemap = open("sitemap.xml").read()
    updated = 0
    for p in changed:
        loc = SITE + slug(p)
        loc_pattern = re.escape(loc if loc.endswith("/") else loc)
        pattern = rf"(<loc>{loc_pattern}/?</loc><lastmod>)[^<]*(</lastmod>)"
        sitemap, n = re.subn(pattern, rf"\g<1>{today}\g<2>", sitemap)
        updated += n
        if not n:
            print(f"    ! no sitemap entry matched for {loc}")
    open("sitemap.xml", "w").write(sitemap)
    print(f"  sitemap: {updated} lastmod value(s) set to {today}")
elif changed:
    print("  (report only — pass --write to update sitemap.xml)")

if write or first_run:
    json.dump(current, open(MANIFEST, "w"), indent=1, sort_keys=True)
    print(f"  manifest written: {len(current)} page(s)")
