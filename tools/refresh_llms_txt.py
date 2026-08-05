#!/usr/bin/env python3
"""Regenerate the writing section of /llms.txt from the posts themselves.

The section was hand-maintained and had drifted: four posts listed, nineteen
published. A hand-kept list of a growing thing is a list that will be wrong,
so the entries now come from each post's own Article schema — the same source
build_feed.py uses, which is why the feed never drifted and this did.

Newest first, headline and description taken verbatim from the page, so the
file cannot claim a post says something it does not.

Only the section between "## Selected writing" and the next "## " is touched;
everything a human wrote in the rest of the file is left alone.

Idempotent. Run from the site root, after publishing a post.
"""
import glob
import json
import os
import re
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"

posts = []
for path in sorted(glob.glob("blog/*.html")):
    if path.endswith("index.html"):
        continue
    html = open(path).read()
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        data = json.loads(block)
        if data.get("@type") != "Article":
            continue
        try:
            when = datetime.fromisoformat(data.get("datePublished", ""))
        except ValueError:
            break
        posts.append({
            "title": data.get("headline", "").strip(),
            "url": f"{SITE}/{path[:-5]}",
            "desc": " ".join(data.get("description", "").split()),
            "when": when,
        })
        break

posts.sort(key=lambda p: p["when"], reverse=True)

lines = ["## Writing", "",
         f"All {len(posts)} posts, newest first. Descriptions are the pages' own.", ""]
for p in posts:
    lines.append(f"- [{p['title']}]({p['url']}) — {p['desc']}")
lines.append("")

body = "\n".join(lines)

txt = open("llms.txt").read()
# Replace whichever heading is currently there, and keep everything after it.
match = re.search(r"^## (Selected writing|Writing)\b.*?(?=^## )", txt, re.S | re.M)
if not match:
    raise SystemExit("could not find the writing section in llms.txt")
open("llms.txt", "w").write(txt[: match.start()] + body + txt[match.end():])
print(f"  llms.txt: writing section rebuilt from {len(posts)} post(s)")
