#!/usr/bin/env python3
"""Point each page at its own social card.

Every page declared the same og:image, so a shared link showed the same
untitled cover whatever it pointed to. This rewrites og:image and
twitter:image per page and versions each by the card's own content hash, so a
retitled page gets a new URL and the year-long immutable cache never serves a
card for a headline that changed.

Pages with no card of their own (the home page keeps the brand cover) are left
alone. Idempotent: running twice changes nothing.
"""
import hashlib
import os
import pathlib
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SITE = "https://runixcloud.io"

# 404 has no og tags by design -- nobody shares a not-found page.
SKIP = {"404.html"}

ATTRS = ('property="og:image"', 'name="twitter:image"', 'property="og:image:secure_url"')


def main():
    changed = 0
    missing = []
    for path in sorted(set(str(p) for p in pathlib.Path(".").glob("*.html"))
                       | set(str(p) for p in pathlib.Path("blog").glob("*.html"))
                       | set(str(p) for p in pathlib.Path("docs").glob("*.html"))):
        if path in SKIP:
            continue
        slug = path.replace("/", "-").replace(".html", "")
        card = pathlib.Path("assets/og") / f"{slug}.png"
        if not card.exists():
            continue
        ver = hashlib.sha256(card.read_bytes()).hexdigest()[:8]
        url = f"{SITE}/assets/og/{slug}.png?v={ver}"
        doc = before = pathlib.Path(path).read_text()
        for attr in ATTRS:
            doc = re.sub(rf'({re.escape(attr)} content=")[^"]*(")', lambda m: m.group(1) + url + m.group(2), doc)
        if 'property="og:image"' not in doc:
            missing.append(path)
            continue
        if doc != before:
            pathlib.Path(path).write_text(doc)
            changed += 1
    if missing:
        for m in missing:
            print(f"  !! {m} has no og:image tag to point")
        return 1
    print(f"  pointed {changed} page(s) at their own card")
    return 0


if __name__ == "__main__":
    sys.exit(main())
