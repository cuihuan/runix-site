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
# Drafts are not deployed and not in the sitemap, but a draft with a broken
# schema block or a dead internal link only announces itself at publish time,
# which is the worst moment to find out. They get the structural checks.
DRAFTS = sorted(glob.glob("scheduled/*.html"))

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


for page in PAGES + DRAFTS:
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
        desc = re.search(r'name="description" content="(.*?)"', html, re.S)
        if desc:
            # Search results truncate around 160 characters; past that the end of
            # the sentence — usually the reason to click — is never shown.
            text = re.sub(r"\s+", " ", desc.group(1)).strip()
            if len(text) > 160:
                fail(page, f"meta description is {len(text)} chars; truncates past ~160")

    # --- structured data ------------------------------------------------
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            json.loads(block)
        except Exception as exc:
            fail(page, f"invalid JSON-LD: {exc}")

    if base != "404.html" and not re.search(r'<script type="application/ld\+json">', html):
        fail(page, "no structured data")

    # An unbalanced script tag leaves JSON rendering as visible text.
    opens, closes = len(re.findall(r"<script\b", html)), html.count("</script>")
    if opens != closes:
        fail(page, f"unbalanced script tags ({opens} open, {closes} close)")
    head = html[: html.index("</head>")] if "</head>" in html else ""
    if re.search(r'"@context"', re.sub(r"<script\b.*?</script>", "", head, flags=re.S)):
        fail(page, "JSON-LD leaked outside a script block in the head")

    # --- content hygiene ------------------------------------------------
    if "PENDING" in html and page not in DRAFTS:
        fail(page, "publish.py date placeholder left in a live page")
    if re.search(r"lorem ipsum|TODO:|FIXME|XXX_PLACEHOLDER", html, re.I):
        fail(page, "placeholder text left in the page")
    # The range is escaped rather than written literally, so this file does not
    # contain the very characters it exists to reject — otherwise the tool trips
    # its own check the moment anyone points it at itself.
    if re.search(r"[\u4e00-\u9fff]", html):
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

# --- internal links use the URLs the host serves ---------------------------
# Every internal .html link costs a 308. A site-wide pass fixed 1110 of them,
# and then build_blog_index.py quietly reintroduced 42 on the next publish
# because it wrote "<slug>.html". Generators are exactly where this comes back.
for page in PAGES:
    for href in set(re.findall(r'href="([^"]+\.html[^"]*)"', open(page).read())):
        if href.startswith(("http://", "https://", "//")):
            continue
        fail(page, f"internal link keeps the .html extension (costs a 308): {href}")

# --- one status per product, everywhere ----------------------------------
# Statuses on this site are meant to be literal, so the same product must not
# be "in development" on one page and something else on another. Read from the
# structured labels (hero badges and card-meta) rather than from prose: a
# sentence-level scan cannot tell which card a "Status:" belongs to when cards
# carry no sentence punctuation, and it reports three inconsistencies that are
# not real.
PRODUCT_STATUS = {"router": "early access", "pipeline": "in development",
                  "code": "in development", "comic": "in development"}
seen_status = {}
for page in PAGES:
    doc = open(page).read()
    for badge in re.findall(r'<span class="badge">([^<]*)</span>', doc):
        for prod, expected in PRODUCT_STATUS.items():
            if f"Runix {prod.capitalize()} " in badge and "\u00b7" in badge:
                got = badge.split("\u00b7", 1)[1].strip().lower()
                if got != expected:
                    fail(page, f"badge says Runix {prod} is “{got}”, "
                               f"elsewhere it is “{expected}”")
    for meta in re.findall(r'<p class="card-meta">(.*?)</p>', doc, re.S):
        text = " ".join(re.sub(r"<[^>]+>", " ", meta).split())
        m = re.search(r"Status:\s*([^\u00b7|]+)", text)
        if m:
            seen_status.setdefault(page, []).append(m.group(1).strip().lower())
# Cards appear in product order on both index pages; compare the multisets.
expected_set = sorted(PRODUCT_STATUS.values())
for page, statuses in seen_status.items():
    if len(statuses) == len(expected_set) and sorted(statuses) != expected_set:
        fail(page, f"card statuses {sorted(statuses)} do not match the "
                   f"canonical set {expected_set}")

# --- two links with nothing between them ----------------------------------
# Automated link insertion produced "<a>FAQ</a> <a>Glossary</a>", which reads
# as "the FAQ Glossary". Inside a sentence, two anchors separated only by
# whitespace almost always means a missing conjunction or comma. Adjacent links
# in a list or a nav are normal, so only paragraphs are checked.
for page in PAGES:
    doc = open(page).read()
    body = doc[doc.find("<main"):doc.find("</main>")] if "<main" in doc else doc
    for para in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S):
        if re.search(r"</a>\s+<a\b", para, re.S):
            snippet = " ".join(re.sub(r"<[^>]+>", " ", para).split())[:80]
            fail(page, f"two links with only a space between them: “{snippet}”")

# --- every address the site asks people to write to must exist ------------
# The whole funnel is "email us". An address in a CTA that has no routing rule
# drops customer mail silently, which is the most expensive failure this site
# can have and the one nobody would notice. Verified 2026-08-06 against the
# zone's Cloudflare Email Routing rules: each of these has an enabled rule, and
# a catch-all exists behind them. Adding an address here without adding the
# rule is the mistake this guards against.
ROUTED = {"contact", "sales", "support", "billing", "hello", "cuihuan"}
for page in PAGES:
    for addr in set(re.findall(r"mailto:([a-z0-9._%-]+)@runixcloud\.io", open(page).read(), re.I)):
        if addr.lower() not in ROUTED:
            fail(page, f"mailto:{addr}@runixcloud.io has no known routing rule — "
                       f"mail to it would be dropped")

# --- structured data must match what the page says ------------------------
# FAQPage markup that answers a question differently from the visible copy is
# worse than none: it is what an assistant quotes, and nobody proofreads it.
# Every question and answer must appear verbatim in the rendered text.
import html as _html

for page in PAGES:
    doc = open(page).read()
    visible = " ".join(_html.unescape(re.sub(r"<(script|style)\b.*?</\1>", " ",
                                             doc, flags=re.S | re.I)).split())
    visible = " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", visible)).split())
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', doc, re.S):
        try:
            data = json.loads(block)
        except Exception:
            continue
        if data.get("@type") != "FAQPage":
            continue
        for entry in data.get("mainEntity", []):
            for label, value in (("question", entry.get("name", "")),
                                 ("answer", entry.get("acceptedAnswer", {}).get("text", ""))):
                needle = " ".join(_html.unescape(value).split())
                if needle and needle not in visible:
                    fail(page, f"FAQPage {label} is not in the visible copy: “{needle[:70]}”")

# --- claims the site is not allowed to make ------------------------------
# The standing rule is that Runix never publishes a customer count, an uptime
# percentage, a latency figure or a certification it does not hold. Copy is
# where that rule gets broken, usually by someone reaching for a number to make
# a sentence land. These patterns fail the build rather than warn, because a
# fabricated proof point is not a style problem — it is the one thing a buyer would
# be entitled to be angry about.
# Scoped to the sentence, and — except for "trusted by", which is inherently a
# first-person marketing line — only when the sentence is about us. The blog
# teaches buyers to tell "SOC 2 in progress" from "SOC 2 certified"; that is the
# best use of those words on this site and must not trip the gate.
SELF = re.compile(r"\b(runix|we|our|us)\b", re.I)
FORBIDDEN = [
    (r"\d+(\.\d+)?\s*%\s*(uptime|availability|sla)", "an uptime or availability percentage", True),
    (r"\btrusted by\b", "a 'trusted by' claim", False),
    (r"\b\d+\+?\s*(customers|companies|enterprises)\b", "a customer count", True),
    (r"\b(SOC\s*2|ISO\s*27001|PCI[- ]DSS)\b[^.]{0,40}\b(certified|compliant|attested)\b",
     "a certification the company does not hold", True),
    (r"\b\d+(\.\d+)?\s*(ms|milliseconds)\b", "a latency figure", True),
]
for page in PAGES:
    text = re.sub(r"<[^>]+>", " ", open(page).read())
    text = re.sub(r"\s+", " ", text)
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        for pattern, what, needs_self in FORBIDDEN:
            match = re.search(pattern, sentence, re.I)
            if not match:
                continue
            if needs_self and not SELF.search(sentence):
                continue          # discussing the concept, not claiming it
            fail(page, f"{what}: “{sentence.strip()[:110]}”")

# --- the nav is the same everywhere -------------------------------------
# It is the most-seen component on the site; an item missing on one page makes
# the whole bar shift when a visitor navigates.
navs = {}
for page in PAGES:
    html = open(page).read()
    start = html.find('<div class="nav-links">')
    if start < 0:
        fail(page, "no nav-links block")
        continue
    block = html[start:html.find("</div>", start)]
    navs[page] = tuple(re.findall(r">([^<>]+)</a>", block))
if navs:
    common = max(set(navs.values()), key=list(navs.values()).count)
    for page, items in navs.items():
        if items != common:
            fail(page, f"nav differs from the rest: {items} vs {common}")

# --- the entity graph resolves ------------------------------------------
defined_ids, referenced_ids = set(), set()
for page in PAGES:
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', open(page).read(), re.S):
        try:
            data = json.loads(block)
        except Exception:
            continue  # already reported above

        def walk(node, page=page):
            if isinstance(node, list):
                for item in node:
                    walk(item)
                return
            if not isinstance(node, dict):
                return
            if "@id" in node:
                (defined_ids if len(node) > 1 else referenced_ids).add(node["@id"])
            if node.get("@type") == "BreadcrumbList":
                for step in node.get("itemListElement", []):
                    if "#" in str(step.get("item", "")):
                        fail(page, f"breadcrumb step points at a fragment: {step.get('item')}")
            for value in node.values():
                walk(value)

        walk(data)
for dangling in sorted(referenced_ids - defined_ids):
    fail("structured data", f"@id referenced but never defined: {dangling}")

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
print(f"checked {len(PAGES)} pages and {len(DRAFTS)} draft(s)")
for note in notes:
    print(f"  note: {note}")
if failures:
    print(f"\n{len(failures)} problem(s):")
    for f in failures:
        print(f"  ✗ {f}")
    sys.exit(1)
print("all checks passed")
