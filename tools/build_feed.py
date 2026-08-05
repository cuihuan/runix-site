#!/usr/bin/env python3
"""Generate /feed.xml from what the blog posts already declare.

Titles, descriptions and dates come from each post's own Article schema rather
than being restated here, so the feed cannot drift from the pages. Run after
adding or editing a post.
"""
import glob
import json
import os
import re
from email.utils import format_datetime
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SITE = "https://runixcloud.io"

items = []
for path in glob.glob("blog/*.html"):
    if path.endswith("index.html"):
        continue
    html = open(path).read()
    article = None
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        data = json.loads(block)
        if data.get("@type") == "Article":
            article = data
            break
    if not article:
        continue
    published = article.get("datePublished", "")
    try:
        when = datetime.fromisoformat(published).replace(tzinfo=timezone.utc)
    except ValueError:
        continue
    items.append({
        "title": article.get("headline", ""),
        "url": f"{SITE}/{path[:-5]}",
        "description": article.get("description", ""),
        "when": when,
    })

items.sort(key=lambda i: i["when"], reverse=True)
newest = items[0]["when"] if items else datetime.now(timezone.utc)

entries = "\n".join(
    f"""    <item>
      <title>{escape(i['title'])}</title>
      <link>{i['url']}</link>
      <guid isPermaLink="true">{i['url']}</guid>
      <description>{escape(i['description'])}</description>
      <pubDate>{format_datetime(i['when'])}</pubDate>
    </item>"""
    for i in items
)

open("feed.xml", "w").write(f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Runix Blog</title>
    <link>{SITE}/blog/</link>
    <atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Engineering notes on LLM gateways, reliability, cost control and data pipelines, from the team building Runix.</description>
    <language>en-us</language>
    <lastBuildDate>{format_datetime(newest)}</lastBuildDate>
{entries}
  </channel>
</rss>
""")

# Make the feed discoverable from the blog pages.
linked = 0
for path in glob.glob("blog/*.html"):
    html = open(path).read()
    if 'type="application/rss+xml"' in html:
        continue
    tag = f'<link rel="alternate" type="application/rss+xml" title="Runix Blog" href="{SITE}/feed.xml">'
    open(path, "w").write(html.replace("</head>", tag + "\n</head>", 1))
    linked += 1

print(f"  feed.xml: {len(items)} items, discoverable from {linked} page(s)")
