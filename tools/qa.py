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

# --- a stated count must match what is on the page ------------------------
# /pipeline said "Six stages" and showed six cards while /docs/pipeline,
# /docs/ and llms.txt all said "five" — two different decompositions of the
# same process, and a prospect reading both pages sees a contradiction about
# how the product works. Nothing was watching the number.
NUMBER_WORDS = {"three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
for page in PAGES:
    doc = open(page).read()
    for word, expected in NUMBER_WORDS.items():
        # Only when the count is in a heading — that is a page presenting the
        # list. The same phrase in prose is a reference to it, and counting the
        # headings that happen to follow gives a false positive (it did, on
        # /docs/, where the following headings are other products' cards).
        m = re.search(rf"<h[12][^>]*>[^<]*\b{word}\s+(?:pipeline\s+)?stages\b",
                      doc, re.I)
        if not m:
            continue
        section = doc[m.end():]
        end = section.find("</section>")
        window = section[:end if end > 0 else 4000]
        # Product pages list stages as cards, docs list them as bullets. Count
        # whichever the page used — counting only h3 missed the docs entirely.
        cards = len(re.findall(r"<h3[^>]*>", window))
        if not cards:
            first_list = re.search(r"<ul>(.*?)</ul>", window, re.S)
            cards = len(re.findall(r"<li\b", first_list.group(1))) if first_list else 0
        if cards and cards != expected:
            fail(page, f"heading says “{word} stages” but lists {cards}")

# --- versioned asset URLs -------------------------------------------------
# /assets/* is cached for a year as immutable. An asset referenced without a
# ?v= would therefore be pinned in browsers for a year with no way to replace
# it — the one failure mode that policy introduces.
for page in PAGES:
    doc = open(page).read()
    for ref in set(re.findall(r'(?:href|src)="([^"]*assets/[^"]+)"', doc)):
        if "?v=" not in ref:
            fail(page, f"asset referenced without a ?v= while /assets/* is "
                       f"immutable for a year: {ref}")

# --- every page's share card exists, is the size it claims, and is its own --
# og:image:width/height are hints social platforms lay out against before the
# image loads. If they stop matching the file, previews crop wrong -- and that
# only ever shows up when somebody shares a link, which is the worst time.
#
# This used to measure assets/og-cover.png for every page. Once each page got
# its own card that was the wrong file, and the check passed only because the
# cards happen to share the cover's dimensions -- coverage in appearance only.
# It now resolves each page's own declared og:image.
#
# The duplicate check is the defect that motivated the cards: fifty pages
# declaring one untitled image, so every shared link previewed identically.
import struct as _struct
_seen_og = {}
for page in PAGES:
    _doc = open(page).read()
    _m = re.search(r'property="og:image" content="([^"]+)"', _doc)
    if not _m:
        continue
    _ref = _m.group(1)
    _local = os.path.normpath(re.sub(r"\?.*$", "", _ref).replace("https://runixcloud.io/", ""))
    if not os.path.isfile(_local):
        fail(page, f"og:image points at {_ref}, which is not a file in this repo")
        continue
    _seen_og.setdefault(_local, []).append(page)
    _data = open(_local, "rb").read(24)
    if _data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(page, f"og:image {_local} is not a PNG")
        continue
    _w, _h = _struct.unpack(">II", _data[16:24])
    _dw = re.search(r'og:image:width" content="(\d+)"', _doc)
    _dh = re.search(r'og:image:height" content="(\d+)"', _doc)
    if _dw and int(_dw.group(1)) != _w:
        fail(page, f"og:image:width says {_dw.group(1)} but {_local} is {_w}")
    if _dh and int(_dh.group(1)) != _h:
        fail(page, f"og:image:height says {_dh.group(1)} but {_local} is {_h}")
    _tw = re.search(r'name="twitter:image" content="([^"]+)"', _doc)
    if _tw and _tw.group(1) != _ref:
        fail(page, "twitter:image and og:image disagree, so previews differ by platform")

for _local, _pages in sorted(_seen_og.items()):
    # index.html deliberately keeps the brand cover.
    if len(_pages) > 1:
        fail(_pages[1], f"{len(_pages)} pages share the share card {_local} "
                        f"({', '.join(_pages[:3])}...) -- every preview looks the same")

import html as _html2

# --- examples do not name a model that will be retired --------------------
# A dated vendor model id in an example is a countdown. blog/llm-gateway-guide
# shipped "model": "claude-sonnet-4" in a sample request; that id was retired
# on 2026-06-15, so the example named something that no longer exists -- which
# is precisely what our own deprecation post warns about. Placeholders in
# generic examples; real ids only where they are the subject.
MODEL_ID_SUBJECT_PAGES = {"blog/model-deprecation-without-a-redeploy.html"}
_MODEL_ID = re.compile(
    r"\b(?:claude-[a-z0-9]+-[0-9][\w.-]*|gpt-[0-9][\w.-]*|gemini-[0-9][\w.-]*)\b", re.I)
for page in PAGES:
    if page in MODEL_ID_SUBJECT_PAGES:
        continue
    for _blk in re.findall(r"<pre[^>]*>(?:<code[^>]*>)?(.*?)(?:</code>)?</pre>",
                           open(page).read(), re.S):
        _code = _html2.unescape(re.sub(r"<[^>]+>", "", _blk))
        _m = _MODEL_ID.search(_code)
        if _m:
            fail(page, f"a code example names the model id \u201c{_m.group(0)}\u201d, which "
                       f"will be retired on someone else's schedule -- use a placeholder")

# --- code examples must survive being copied ------------------------------
# Every code block now has a Copy button, so a snippet that only works after a
# human edits it is worse than no snippet. The homepage shipped a JSON body
# with a "#" comment inside it -- valid-looking, and a parse error the moment
# anyone pasted it.
import html as _html2
import json as _json2
for page in PAGES:
    for _blk in re.findall(r"<pre[^>]*>(?:<code[^>]*>)?(.*?)(?:</code>)?</pre>",
                           open(page).read(), re.S):
        _code = _html2.unescape(re.sub(r"<[^>]+>", "", _blk))
        for _body in re.findall(r"-d\s+'(\{.*?\})'", _code, re.S):
            try:
                _json2.loads(_body)
            except _json2.JSONDecodeError as _exc:
                fail(page, f"a curl example's JSON body does not parse as written, "
                           f"so copying it fails: {_exc}")

# --- Python examples must run, not just parse -----------------------------
# The router quickstart passed api_key=RUNIX_API_KEY, which is valid Python and
# a NameError the moment anyone copies it. Same shape as the JSON comment: the
# snippet looks right and fails on paste.
import ast as _ast
for page in PAGES:
    for _blk in re.findall(r"<pre[^>]*>(?:<code[^>]*>)?(.*?)(?:</code>)?</pre>",
                           open(page).read(), re.S):
        _code = _html2.unescape(re.sub(r"<[^>]+>", "", _blk)).strip()
        if not re.search(r"^\s*(from|import)\s", _code, re.M):
            continue
        try:
            _tree = _ast.parse(_code)
        except SyntaxError as _exc:
            fail(page, f"a Python example does not parse: {_exc}")
            continue
        _assigned = {n.id for n in _ast.walk(_tree)
                     if isinstance(n, _ast.Name) and isinstance(n.ctx, _ast.Store)}
        _imported = set()
        for _n in _ast.walk(_tree):
            if isinstance(_n, (_ast.Import, _ast.ImportFrom)):
                for _a in _n.names:
                    _imported.add(_a.asname or _a.name.split(".")[0])
        _used = {n.id for n in _ast.walk(_tree)
                 if isinstance(n, _ast.Name) and isinstance(n.ctx, _ast.Load)}
        _undefined = _used - _assigned - _imported - set(dir(__builtins__))
        if _undefined:
            fail(page, f"a Python example uses undefined name(s) "
                       f"{sorted(_undefined)} — copying it raises NameError")

# --- the mobile nav has a no-script fallback ------------------------------
# Under 920px the nav links are display:none and only .open reveals them, and
# .open is added by script. Without this block a visitor with scripting off has
# no navigation at all except the footer.
for page in PAGES:
    doc = open(page).read()
    if 'class="nav-toggle"' in doc and "<noscript>" not in doc:
        fail(page, "mobile nav depends on script with no <noscript> fallback")

# --- every SVG is either decorative or labelled ---------------------------
# The site uses inline SVG for every icon and has no <img> at all, so this is
# where alternative text lives or fails to. A decorative icon needs
# aria-hidden, or a screen reader announces "graphic" for each of 43 of them;
# an informative one needs role="img" and a label, or it announces nothing.
for page in PAGES:
    for tag in re.findall(r"<svg\b[^>]*>", open(page).read()):
        if "aria-hidden" in tag:
            continue
        if 'role="img"' in tag and ("aria-labelledby" in tag or "aria-label" in tag):
            continue
        fail(page, f"svg is neither aria-hidden nor role=img with a label: {tag[:70]}")

# --- same link text must mean the same destination ------------------------
# A screen-reader user can list the links on a page. Fourteen entries all
# reading "Read more on this", each going somewhere different, is a page they
# cannot navigate — the glossary shipped exactly that. The same text pointing
# at the same place is fine and common; it is the divergence that fails.
GENERIC = {"read more", "read more on this", "learn more", "click here",
           "here", "this page", "more", "read post"}
for page in PAGES:
    doc = open(page).read()
    body = doc[doc.find("<main"):doc.find("</main>")] if "<main" in doc else doc
    body = re.sub(r"<nav\b.*?</nav>", " ", body, flags=re.S | re.I)
    by_text = {}
    for tag, href, text in re.findall(r'(<a\b[^>]*href="([^"]+)"[^>]*>)(.*?)</a>', body, re.S):
        # A link removed from the accessibility tree is not in the link list a
        # screen-reader user reads, so it cannot collide with anything there.
        # It must also be unfocusable, which is checked separately below --
        # aria-hidden on a focusable element is its own violation.
        if 'aria-hidden="true"' in tag:
            continue
        label = " ".join(re.sub(r"<[^>]+>", " ", text).split()).lower()
        if not label:
            continue
        target = href.split("#")[0]
        # A mailto with a prefilled subject is the same destination — the same
        # inbox — so three "contact@..." links differing only in ?subject= are
        # not the failure this check is for.
        if target.startswith("mailto:"):
            target = target.split("?")[0]
        by_text.setdefault(label, set()).add(target)
    for label, targets in by_text.items():
        # There used to be an exemption here for "read post →". It was written
        # to quieten the blog index, where every card carried both a headline
        # link and a "Read post" link to the same post -- twenty-five identical
        # entries in the link list. The exemption hid the defect instead of
        # fixing it; the duplicates are now decorative and the exemption is gone.
        if len(targets) > 1:
            fail(page, f"link text “{label}” points at {len(targets)} different "
                       f"destinations: {sorted(targets)[:3]}")
        if label in GENERIC and len(by_text) > 1:
            notes.append(f"{page}: non-descriptive link text “{label}”")

# --- a ruled list does not rule off its last row ---------------------------
# A border-bottom on every row of a repeated element leaves a hairline under
# the final one, separating content from nothing. The site already drops it on
# .contact-card .row and .facts .frow; the pricing plans were the one list that
# did not, and it read as an unfinished card. This makes the convention a rule
# rather than something three selectors happen to agree on.
_css = open(os.path.join("assets", "style.css")).read()
_css_flat = re.sub(r"/\*.*?\*/", " ", _css, flags=re.S)
for _sel, _body in re.findall(r"([^{}]+)\{([^}]*)\}", _css_flat):
    _sel = " ".join(_sel.split())
    if "border-bottom" not in _body or ":last-child" in _sel or ":not(" in _sel:
        continue
    if re.search(r"border-bottom:\s*(none|0)", _body):
        continue
    # Only repeated children can have a "last" one worth exempting.
    if not re.search(r"\b(li|dt|dd|tr|\.row|\.frow|\.item)\s*$", _sel):
        continue
    if not re.search(re.escape(_sel) + r":last-child\s*\{[^}]*border-bottom:\s*(none|0)",
                     _css_flat):
        fail("assets/style.css",
             f"“{_sel}” rules every row including the last, leaving a hairline "
             f"under nothing -- add a :last-child reset")

# --- a hero CTA does not repeat a link already on the same screen ----------
# /router's hero offered four buttons, and the fourth pointed at exactly the
# URL the global "Sign in" in the header points at -- the same destination
# twice on one screen, four hundred pixels apart. Four equal-weight choices in
# a hero means no clear next step; one of them being a duplicate makes that
# worse for nothing. The check is deliberately narrow: same href as a header
# link, not merely similar intent. "See how billing works" also resolves to
# /pricing, but it answers a question a prospect actually has and reads
# nothing like the nav item, so it is not the same defect.
for page in PAGES:
    doc = open(page).read()
    _head = doc[:doc.find("</header>")] if "</header>" in doc else ""
    _nav_hrefs = set(re.findall(r'<a\b[^>]*href="([^"#]+)"', _head))
    # The hero is <section class="hero"> on the home page and
    # <div class="page-hero"> on every product page. The first version of this
    # check only matched the former, so it never ran on the page whose defect
    # motivated it -- the gate reported clean while the duplicate was still
    # there. Match the actual container, and take the button block inside it.
    _hero = re.search(r'<(section|div) class="[^"]*\b(?:page-)?hero\b[^"]*".*?</\1>', doc, re.S)
    if not _hero or not _nav_hrefs:
        continue
    # Match the whole anchor, not just its opening tag. The first version
    # tested the label against the opening tag, where the label is not -- so
    # the condition was always false and the gate could never fire.
    for _a in re.findall(r'<a\b[^>]*class="[^"]*\bbtn\b[^"]*"[^>]*>.*?</a>',
                         _hero.group(0), re.S):
        _h = re.search(r'href="([^"#]+)"', _a)
        if _h and _h.group(1) in _nav_hrefs and "sign in" in _a.lower():
            fail(page, f"a hero button points at {_h.group(1)}, which the header "
                       f"already links to on the same screen")

# --- the pipeline stage count is one number, not a per-page opinion --------
# /pipeline lists the stages; every other page states how many there are in
# prose. That number diverged twice: the product page said six while docs and
# llms.txt said five (with a stale #the-five-stages anchor), and after that was
# fixed /about was still saying five. Derive the number from the page that
# actually lists them and make every prose claim agree.
_WORD = {"four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
_pipe = open("pipeline.html").read() if os.path.isfile("pipeline.html") else ""
_m = re.search(r"<h2[^>]*>[^<]*stages[^<]*</h2>(.*?)(?=<h2|</section>)", _pipe, re.S | re.I)
if _m:
    _real = len(re.findall(r"<h3\b", _m.group(1)))
    if _real:
        for page in PAGES + ["llms.txt"]:
            if not os.path.isfile(page):
                continue
            _txt = open(page).read()
            for _w in re.findall(r"\b(" + "|".join(_WORD) + r")\s+(?:pipeline\s+)?stages\b", _txt, re.I):
                if _WORD[_w.lower()] != _real:
                    fail(page, f"says “{_w} stages” but /pipeline lists {_real}")

# --- counted claims are derived, not typed --------------------------------
# The pipeline stage count above is one instance of a class: a number stated in
# prose on several pages, with the thing being counted living on one page. Two
# of tonight's defects were this shape, and the second was residue from fixing
# the first. Each entry below sources its number from the page that actually
# lists the items.
_COUNTED = [
    # (source page, section heading pattern, item tag, prose pattern, label)
    # The item tag differs per page -- /pipeline uses <h3> per stage, the comic
    # guide uses <li>. Getting it wrong produces a section with zero items,
    # which is now an error rather than a skip, so a mis-pointed check announces
    # itself instead of passing.
    # The stages are listed in the docs guide, not on the product page. The
    # first version of this pointed at comic.html, which has no stages section,
    # so the gate silently did nothing -- it reported clean because it never
    # ran. A source page that does not match must be an error, not a skip;
    # see the assertion below.
    ("docs/comic.html", r"<h2[^>]*>[^<]*stages[^<]*</h2>", "li",
     r"\b(" + "|".join(_WORD) + r")\s+production\s+stages\b", "production stages"),
]
for _src, _sec, _tag, _prose, _label in _COUNTED:
    if not os.path.isfile(_src):
        continue
    _m = re.search(_sec + r"(.*?)(?=<h2|</section>)", open(_src).read(), re.S | re.I)
    if not _m:
        fail(_src, f"is the source of truth for {_label} but has no section "
                   f"matching it -- this check would silently do nothing")
        continue
    _real = len(re.findall(rf"<{_tag}\b", _m.group(1)))
    if not _real:
        fail(_src, f"has a {_label} section with no items -- this check would "
                   f"silently do nothing")
        continue
    for page in PAGES + ["llms.txt"]:
        if not os.path.isfile(page):
            continue
        for _w in re.findall(_prose, open(page).read(), re.I):
            if _WORD[_w.lower()] != _real:
                fail(page, f"says “{_w} {_label}” but {_src} lists {_real}")

# --- the products the site claims to have are the products it has ----------
# "four products" appears in prose; the products themselves are pages. If one
# ships or is dropped, the sentence is the thing that gets forgotten.
_PRODUCT_PAGES = [f for f in ("router.html", "pipeline.html", "code.html", "comic.html")
                  if os.path.isfile(f)]
for page in PAGES + ["llms.txt"]:
    if not os.path.isfile(page):
        continue
    for _w in re.findall(r"\b(" + "|".join(_WORD) + r")\s+products\b", open(page).read(), re.I):
        if _WORD[_w.lower()] != len(_PRODUCT_PAGES):
            fail(page, f"says “{_w} products” but the site has "
                       f"{len(_PRODUCT_PAGES)} product pages")

# --- naming one of our own pages in prose means linking it -----------------
# The FAQ answered "do you have SOC 2?" with "the Security page describes the
# controls that are actually in place" and did not link the Security page. An
# answer that points somewhere should take you there.
#
# Blog posts are excluded on purpose, not for convenience: the deprecation post
# says "the FAQ answers: No. Retirement dates aren't extendable", and that is
# Anthropic's FAQ. Auto-linking it would have sent readers to our own page and
# attributed someone else's policy to us.
_NAMED_PAGES = {
    "the Security page": "/security",
    "the reliability page": "/reliability",
    "the pricing page": "/pricing",
    "the access page": "/access",
}
for page in PAGES:
    if page.startswith("blog/"):
        continue
    doc = open(page).read()
    _self = "/" + (page[:-5].replace("/index", "") if page != "index.html" else "")
    _vis = re.sub(r"<script\b.*?</script>", " ", doc, flags=re.S)
    _vis = re.sub(r"<a\b.*?</a>", " ", _vis, flags=re.S)
    for _phrase, _target in _NAMED_PAGES.items():
        if _target.rstrip("/") == _self.rstrip("/"):
            continue
        # Case-insensitive on purpose: the FAQ writes "The Security page" at the
        # start of a sentence. The first version of this matched only the
        # lower-case article, so it could not fire on the very sentence that
        # motivated it.
        if re.search(re.escape(_phrase), re.sub(r"<[^>]+>", " ", _vis), re.I):
            fail(page, f"names “{_phrase}” in prose without linking it to {_target}")

# --- a hidden link must also be unfocusable --------------------------------
# aria-hidden="true" on something a keyboard can still reach is WCAG 4.1.2:
# focus lands on an element the screen reader refuses to announce, and the user
# is somewhere with no name. Whenever we hide a redundant link we must also
# take it out of the tab order.
for page in PAGES:
    doc = open(page).read()
    for tag in re.findall(r'<a\b[^>]*aria-hidden="true"[^>]*>', doc):
        if 'tabindex="-1"' not in tag:
            fail(page, "a link is aria-hidden but still focusable -- focus would "
                       "land somewhere a screen reader will not announce")

    # Hiding a link is only safe while something else in the same card still
    # reaches it. Making the docs cards match the blog nearly produced a card
    # whose only link to its guide was the decorative one -- the page would have
    # been visible, clickable with a mouse, and unreachable by keyboard.
    for card in re.split(r'<div class="card"', doc)[1:]:
        card = card.split("</section>")[0]
        _dec = [a or b for a, b in re.findall(
            r'<a[^>]*aria-hidden="true"[^>]*href="([^"]+)"'
            r'|<a[^>]*href="([^"]+)"[^>]*aria-hidden="true"', card)]
        _real = re.findall(r'<a\b(?![^>]*aria-hidden)[^>]*href="([^"]+)"', card)
        for _d in _dec:
            if _d not in _real:
                fail(page, f"a card hides its only link to {_d} -- that page "
                           f"becomes unreachable by keyboard")

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

# --- every list of posts agrees with every other --------------------------
# Five surfaces enumerate the posts: the files themselves, sitemap.xml,
# feed.xml, llms.txt and the blog index. publish.py rebuilds all of them, so
# they agree today -- but a hand edit to any one of them desyncs the set
# silently, and the symptom is a post that exists and is never discovered.
_posts = {os.path.basename(p)[:-5] for p in glob.glob("blog/*.html")
          if os.path.basename(p) != "index.html"}
_surfaces = {}
if os.path.isfile("sitemap.xml"):
    _surfaces["sitemap.xml"] = {m for m in re.findall(
        r"<loc>https://runixcloud\.io/blog/([a-z0-9-]+)</loc>", open("sitemap.xml").read())}
if os.path.isfile("feed.xml"):
    _surfaces["feed.xml"] = {m for m in re.findall(
        r"<link>https://runixcloud\.io/blog/([a-z0-9-]+)</link>", open("feed.xml").read())}
if os.path.isfile("llms.txt"):
    _surfaces["llms.txt"] = {m for m in re.findall(
        r"runixcloud\.io/blog/([a-z0-9-]+)\)", open("llms.txt").read())}
if os.path.isfile("blog/index.html"):
    _surfaces["blog index"] = {m for m in re.findall(
        r'href="/blog/([a-z0-9-]+)"', open("blog/index.html").read())}
for _name, _listed in _surfaces.items():
    for _missing in sorted(_posts - _listed):
        fail(_name, f"does not list the published post {_missing}")
    for _extra in sorted(_listed - _posts):
        fail(_name, f"lists {_extra}, which is not a published post")

# --- the feed is valid RSS ------------------------------------------------
# A malformed feed does not error anywhere — readers just silently stop
# updating, and nobody finds out. build_feed.py generates it from each post's
# schema, so a change there can break every entry at once.
if os.path.isfile("feed.xml"):
    import xml.etree.ElementTree as _ET
    from email.utils import parsedate_to_datetime as _parsedate
    try:
        _root = _ET.parse("feed.xml").getroot()
        _ch = _root.find("channel")
        if _ch is None:
            fail("feed.xml", "no <channel>")
        else:
            for _req in ("title", "link", "description"):
                if _ch.find(_req) is None or not (_ch.find(_req).text or "").strip():
                    fail("feed.xml", f"channel is missing <{_req}>")
            _items = _ch.findall("item")
            if not _items:
                fail("feed.xml", "no items")
            for _i, _it in enumerate(_items):
                for _req in ("title", "link", "description", "pubDate", "guid"):
                    if _it.find(_req) is None or not (_it.find(_req).text or "").strip():
                        fail("feed.xml", f"item {_i + 1} is missing <{_req}>")
                _pd = _it.find("pubDate")
                if _pd is not None and _pd.text:
                    try:
                        _parsedate(_pd.text)
                    except Exception:
                        fail("feed.xml", f"item {_i + 1} pubDate is not RFC 822: {_pd.text}")
            _posts = len([p for p in glob.glob("blog/*.html")
                          if os.path.basename(p) != "index.html"])
            if len(_items) != _posts:
                fail("feed.xml", f"has {len(_items)} items but {_posts} posts are published")
    except _ET.ParseError as _exc:
        fail("feed.xml", f"is not well-formed XML: {_exc}")

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
