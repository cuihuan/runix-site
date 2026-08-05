#!/usr/bin/env python3
"""Normalise internal links and keep contact addresses crawlable.

Two jobs, both verified against the live site before this existed:

1. Every internal `.html` href costs a 301 hop, because the host serves clean
   URLs (`/router.html` -> `/router`). 1110 of those across the site is a lot
   of round trips for a visitor and a lot of hops for a crawler. Rewrite them
   to root-absolute clean URLs, which also removes every `../`.

2. Cloudflare's Scrape Shield rewrites `mailto:` anchors into a JS-decoded
   placeholder — `/about` served zero plaintext copies of the contact address.
   Anything that does not run JS, including most crawlers, sees no way to
   contact the company on the page the primary CTA points at. Wrapping each
   anchor in `<!--email_off-->` opts that element out at the edge.

Idempotent. Run from the site root: python3 tools/fix_links.py
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PAGES = glob.glob("*.html") + glob.glob("docs/*.html") + glob.glob("blog/*.html")

SKIP_PREFIX = ("http://", "https://", "mailto:", "tel:", "#", "data:", "//")


def clean_url(src_file, href):
    """Turn an internal .html href into the clean URL the host actually serves."""
    if href.startswith(SKIP_PREFIX):
        return None
    path, sep, frag = href.partition("#")
    if not path.endswith(".html"):
        return None
    base = "" if path.startswith("/") else os.path.dirname(src_file)
    target = os.path.normpath(os.path.join(base, path.lstrip("/")))
    if not os.path.isfile(target):
        return None  # leave anything we cannot resolve alone
    slug = target[: -len(".html")]
    if slug == "index":
        clean = "/"
    elif slug.endswith("/index"):
        clean = "/" + slug[: -len("index")]      # docs/index -> /docs/
    else:
        clean = "/" + slug
    return clean + sep + frag


def split_scripts(html):
    """Yield (is_script, chunk) so we never edit inside <script> blocks."""
    parts = re.split(r"(<script\b.*?</script>)", html, flags=re.S | re.I)
    for part in parts:
        yield bool(re.match(r"<script\b", part, re.I)), part


MAILTO_ANCHOR = re.compile(r'<a\b[^>]*href="mailto:[^"]*"[^>]*>.*?</a>', re.S | re.I)

links_fixed = pages_touched = mails_wrapped = 0

for page in PAGES:
    original = open(page).read()
    out = []
    for is_script, chunk in split_scripts(original):
        if is_script:
            out.append(chunk)
            continue

        def rewrite(match):
            global links_fixed
            href = match.group(1)
            clean = clean_url(page, href)
            if clean is None or clean == href:
                return match.group(0)
            links_fixed += 1
            return f'href="{clean}"'

        chunk = re.sub(r'href="([^"]+)"', rewrite, chunk)

        def wrap(match):
            global mails_wrapped
            anchor = match.group(0)
            mails_wrapped += 1
            return f"<!--email_off-->{anchor}<!--/email_off-->"

        # Only wrap anchors that are not already opted out.
        chunk = re.sub(
            r"(?<!<!--email_off-->)" + MAILTO_ANCHOR.pattern,
            wrap,
            chunk,
            flags=re.S | re.I,
        )
        out.append(chunk)

    result = "".join(out)
    if result != original:
        open(page, "w").write(result)
        pages_touched += 1

print(f"rewrote {links_fixed} internal link(s) to clean URLs")
print(f"opted {mails_wrapped} mailto anchor(s) out of edge obfuscation")
print(f"touched {pages_touched} page(s)")

leftover = 0
for page in PAGES:
    for href in re.findall(r'href="([^"]+\.html[^"]*)"', open(page).read()):
        if not href.startswith(SKIP_PREFIX):
            leftover += 1
if leftover:
    print(f"warning: {leftover} internal .html link(s) left unresolved", file=sys.stderr)
