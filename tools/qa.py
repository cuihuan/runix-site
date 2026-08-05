#!/usr/bin/env python3
"""Pre-deploy checks for the Runix marketing site.

Run from the site root: python3 tools/qa.py
Exits non-zero if anything fails, so it can gate a deploy.

Covers the mistakes that have actually bitten this site before: a link edit
that lands in the footer instead of the nav, a JSON-LD block that stops
parsing, a page that quietly loses its canonical, an anchor that points at an
id nobody kept. Absolute hrefs are resolved against the site root the way the
host serves them, including extensionless clean URLs.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PAGES = sorted(glob.glob("*.html") + glob.glob("docs/*.html") + glob.glob("blog/*.html"))
# 404 is deliberately noindex and outside the nav/sitemap conventions.
INDEXABLE = [p for p in PAGES if os.path.basename(p) != "404.html"]

failures = []
notes = []


def fail(page, msg):
    failures.append(f"{page}: {msg}")


def resolve(src_file, href):
    """Map an href to a file on disk, or None if it is external/unresolvable."""
    if href.startswith(("http://", "https://", "mailto:", "tel:", "#", "data:")):
        return None
    path = href.split("#", 1)[0].split("?", 1)[0]
    if not path:
        return src_file
    base = "" if path.startswith("/") else os.path.dirname(src_file)
    target = os.path.normpath(os.path.join(base, path.lstrip("/")))
    for candidate in (target, target + ".html", os.path.join(target, "index.html")):
        if os.path.isfile(candidate):
            return candidate
    return target  # report as missing


ids_cache = {}


def ids_of(path):
    if path not in ids_cache:
        try:
            ids_cache[path] = set(re.findall(r'\bid="([^"]+)"', open(path).read()))
        except OSError:
            ids_cache[path] = set()
    return ids_cache[path]


for page in PAGES:
    html = open(page).read()
    base = os.path.basename(page)

    # --- structure -----------------------------------------------------
    if html.count("<h1") != 1:
        fail(page, f"expected exactly one h1, found {html.count('<h1')}")
    if "<main id=\"main\"" not in html:
        fail(page, "missing <main id=\"main\"> landmark")
    if 'class="skip-link"' not in html:
        fail(page, "missing skip link")
    if 'aria-label="Primary"' not in html:
        fail(page, "nav missing aria-label")
    if ">☰<" in html:
        fail(page, "hamburger uses a glyph instead of the SVG icon")

    # --- head ----------------------------------------------------------
    if "<title>" not in html:
        fail(page, "missing <title>")
    else:
        title = re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip()
        if len(title) > 70:
            notes.append(f"{page}: title is {len(title)} chars (over ~70 may truncate in results)")
    if base != "404.html":
        for tag, pattern in (
            ("meta description", r'name="description"'),
            ("canonical", r'rel="canonical"'),
            ("og:title", r'property="og:title"'),
            ("og:image", r'property="og:image"'),
        ):
            if not re.search(pattern, html):
                fail(page, f"missing {tag}")

    # --- structured data ------------------------------------------------
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(block)
        except Exception as exc:
            fail(page, f"invalid JSON-LD: {exc}")

    # --- content hygiene ------------------------------------------------
    if re.search(r"lorem ipsum|TODO:|FIXME|XXX_PLACEHOLDER", html, re.I):
        fail(page, "placeholder text left in the page")
    if re.search(r"[一-鿿]", html):
        fail(page, "CJK characters in an English-only site")
    for comment in re.findall(r"<!--(.*?)-->", html, re.S):
        if re.search(r"\.md\b|internal|margin|supply cost", comment, re.I):
            fail(page, "internal note left in an HTML comment")

    # --- links and anchors ----------------------------------------------
    for href in re.findall(r'href="([^"]+)"', html):
        target = resolve(page, href)
        if target is None:
            continue
        if not os.path.isfile(target):
            fail(page, f"link target missing: {href}")
            continue
        frag = href.split("#", 1)[1] if "#" in href else ""
        if frag and frag not in ids_of(target):
            fail(page, f"anchor not found: {href}")

    # --- images ----------------------------------------------------------
    for img in re.findall(r"<img\b[^>]*>", html):
        if 'alt=' not in img:
            fail(page, "img without alt")

# --- sitemap ------------------------------------------------------------
if os.path.isfile("sitemap.xml"):
    sm = open("sitemap.xml").read()
    listed = {
        u.rstrip("/").removeprefix("https://runixcloud.io").lstrip("/")
        for u in re.findall(r"<loc>([^<]+)</loc>", sm)
    }
    on_disk = set()
    for p in INDEXABLE:
        slug = p[:-5]
        if slug.endswith("/index"):
            slug = slug[:-6]
        on_disk.add("" if slug == "index" else slug)
    for missing in sorted(on_disk - listed):
        fail("sitemap.xml", f"page not listed: /{missing}")
    for extra in sorted(listed - on_disk):
        fail("sitemap.xml", f"lists a page that does not exist: /{extra}")
    if "404" in " ".join(listed):
        fail("sitemap.xml", "404 page should not be listed")
else:
    fail("sitemap.xml", "missing")

# --- report -------------------------------------------------------------
print(f"checked {len(PAGES)} pages")
for note in notes:
    print(f"  note: {note}")
if failures:
    print(f"\n{len(failures)} problem(s):")
    for f in failures:
        print(f"  ✗ {f}")
    sys.exit(1)
print("all checks passed")
