#!/usr/bin/env python3
"""Advertise the feed from every page, not just the blog.

Feed readers, and the several assistant products that subscribe rather than
crawl, look for <link rel="alternate"> in the head of whatever page they were
handed. Only the 29 blog pages carried it, so anyone pointing a reader at the
home page or a product page was told the site has no feed.

Inserted right after the canonical link, which every page already has.
Idempotent: pages that already declare the feed are left alone.
"""
import os
import pathlib
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LINK = '<link rel="alternate" type="application/rss+xml" title="Runix Blog" href="https://runixcloud.io/feed.xml">'
CANONICAL = re.compile(r'(<link rel="canonical"[^>]*>)')


def pages():
    for pattern in ("*.html", "blog/*.html", "docs/*.html"):
        for p in sorted(pathlib.Path(".").glob(pattern)):
            if not p.name.startswith("_"):
                yield p


def main():
    added, skipped = 0, []
    for path in pages():
        doc = path.read_text()
        if "application/rss+xml" in doc:
            continue
        if not CANONICAL.search(doc):
            skipped.append(str(path))
            continue
        path.write_text(CANONICAL.sub(lambda m: m.group(1) + "\n" + LINK, doc, count=1))
        added += 1
    for s in skipped:
        print(f"  -- {s} has no canonical link to anchor to, left alone")
    print(f"  added the feed link to {added} page(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
