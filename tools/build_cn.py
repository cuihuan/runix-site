#!/usr/bin/env python3
"""Render the Chinese edition (runixcloud.com) from the English pages.

The two sites are one site. Nothing is written twice: build_cn.py reads each
page listed in i18n.CN_PAGES, splits it into translation units, replaces each
with its entry in the catalog i18n/zh-CN.json, and writes the result with the
Chinese edition's language, canonical URL, alternates and links. The layout,
the stylesheet and every builder stay shared, so a design or product change
reaches both editions in the same deploy.

A translation unit is the inner HTML of an element that holds text and no
block-level element (a heading, a paragraph, a list item, a link, a button),
or the value of a text attribute (title, alt, aria-label, placeholder, the
description and social meta). Inline markup stays inside the unit, so a
translator can reorder a sentence around its links. Code, pre, script, style
and anything marked translate="no" are never units.

A page ships only when every unit on it has a translation: an English edit
that is not yet translated stops the build and names the strings, instead of
drifting into a half-English page. CN_STALE_OK="<reason>" lets the build fall
back to English for the missing units, for an urgent English-only fix.

    python3 tools/build_cn.py --extract         # i18n/zh-CN.todo.json: what is missing, by page
    python3 tools/build_cn.py --out DIR         # render the edition into DIR (no site files touched)
    python3 tools/build_cn.py --check           # exit 1 if anything is missing
    python3 tools/build_cn.py --alternates      # hreflang on the English pages (only once ZH_LIVE)

Per-page notes that exist only in Chinese live in the catalog under "@" keys
("@notice:router.html"): one paragraph inserted after the hero's deck. A key
"page.html::English" overrides the shared translation on that page only.
"""
import html as _html
import json
import os
import pathlib
import re
import shutil
import sys
from html.parser import HTMLParser

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from i18n import CN_PAGES, CN_PATHS, EN, ZH, ZH_LANG, ZH_LIVE, path_of  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "i18n" / "zh-CN.json"
TODO = ROOT / "i18n" / "zh-CN.todo.json"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SKIP = {"script", "style", "pre", "code", "svg", "noscript", "template", "textarea", "kbd", "samp"}
BLOCK = {"html", "head", "body", "div", "section", "main", "header", "footer", "nav", "article", "aside",
         "ul", "ol", "li", "dl", "dt", "dd", "table", "thead", "tbody", "tfoot", "tr", "td", "th", "caption",
         "p", "h1", "h2", "h3", "h4", "h5", "h6", "figure", "figcaption", "blockquote", "form", "fieldset",
         "details", "summary", "pre", "hr", "title", "button", "label", "select", "option", "legend"}
TEXT_ATTRS = {"title", "alt", "aria-label", "placeholder"}
META_TEXT = {"description", "og:title", "og:description", "twitter:title", "twitter:description", "og:image:alt"}
# Strings that are the same in both editions: names, hosts, addresses, ids.
IDENTITY = re.compile(
    r"^(Runix( Lab| AI Inc| Router| Bench| FS| Models| Data| Pipeline| Code| Comic)?|AI Unix|Curvine|"
    r"[\w.-]+\.(io|com|ai|dev|org|net)(/\S*)?|[\w.+-]+@[\w.-]+|https?://\S+|[\w./-]*\d[\w./-]*|"
    r"OpenAI|Anthropic|Google|AWS|Azure|GitHub|Hugging Face|Kubernetes|Amazon S3|MinIO|PyTorch|Spark|Flink|"
    r"LangChain|LlamaIndex|Vercel AI SDK|OpenAI SDK|FUSE|POSIX|Terminal-Bench|Harbor|MIT|Apache 2\.0|R)$")


def norm(s):
    return " ".join(s.split())


def has_letters(s):
    return re.search(r"[A-Za-z]", re.sub(r"<[^>]+>|&[a-z]+;|&#\d+;", " ", s)) is not None


class Tree(HTMLParser):
    """Elements with absolute source offsets; positions come from getpos()."""

    def __init__(self, src):
        super().__init__(convert_charrefs=False)
        self.src = src
        self.lines = [0]
        for m in re.finditer("\n", src):
            self.lines.append(m.end())
        self.root = {"tag": "#root", "attrs": {}, "kids": [], "texts": [], "parent": None, "s": 0, "se": 0}
        self.cur = self.root
        self.feed(src)
        self.close()

    def off(self):
        ln, col = self.getpos()
        return self.lines[ln - 1] + col

    def handle_starttag(self, tag, attrs):
        s = self.off()
        se = s + len(self.get_starttag_text())
        el = {"tag": tag, "attrs": dict(attrs), "kids": [], "texts": [], "parent": self.cur, "s": s, "se": se}
        self.cur["kids"].append(el)
        if tag in VOID:
            el["es"] = el["e"] = se
        else:
            self.cur = el

    def handle_startendtag(self, tag, attrs):
        s = self.off()
        se = s + len(self.get_starttag_text())
        self.cur["kids"].append({"tag": tag, "attrs": dict(attrs), "kids": [], "texts": [], "parent": self.cur,
                                 "s": s, "se": se, "es": se, "e": se})

    def handle_endtag(self, tag):
        es = self.off()
        e = self.src.index(">", es) + 1
        node = self.cur
        while node is not self.root and node["tag"] != tag:
            node = node["parent"]
        if node is self.root:
            return
        # close everything opened inside it that never closed (p, li)
        n = self.cur
        while n is not node:
            n.setdefault("es", es)
            n.setdefault("e", es)
            n = n["parent"]
        node["es"], node["e"] = es, e
        self.cur = node["parent"]

    def handle_data(self, data):
        if data.strip():
            self.cur["texts"].append(data)

    def handle_entityref(self, name):
        self.cur["texts"].append("&" + name + ";")

    def handle_charref(self, name):
        self.cur["texts"].append("&#" + name + ";")


def skipped(el):
    a = el["attrs"]
    return el["tag"] in SKIP or a.get("translate") == "no" or "notranslate" in (a.get("class") or "").split() \
        or a.get("type") == "application/ld+json"


def has_block(el):
    for k in el["kids"]:
        if k["tag"] in BLOCK:
            return True
        if not skipped(k) and has_block(k):
            return True
    return False


def has_text(el):
    if any(has_letters(t) for t in el["texts"]):
        return True
    return any(not skipped(k) and has_text(k) for k in el["kids"])


def units(src):
    """Yield (start, end, msgid) for every translatable span of `src`."""
    tree = Tree(src)
    out = []

    def attrs_of(el):
        a = el["attrs"]
        for name in TEXT_ATTRS:
            if a.get(name) and has_letters(a[name]):
                out.append(("attr", el, name))
        if el["tag"] == "meta" and (a.get("name") in META_TEXT or a.get("property") in META_TEXT) and a.get("content"):
            out.append(("attr", el, "content"))
        if el["tag"] == "input" and a.get("type") in ("submit", "button") and a.get("value"):
            out.append(("attr", el, "value"))

    def walk(el):
        for k in el["kids"]:
            attrs_of(k)
            if skipped(k) or "es" not in k:
                continue
            direct = any(has_letters(t) for t in k["texts"])
            # A unit has text of its own. An element that only groups labelled
            # children (a card link with a title and a line, a row of buttons)
            # is descended into, so each child is translated once and reused
            # wherever it appears.
            if k["tag"] not in VOID and k["tag"] not in ("html", "head", "body") and has_text(k) \
                    and not has_block(k) and direct:
                out.append(("inner", k, None))
                # attributes inside the unit (a title on a link) are still units
                def inner_attrs(n):
                    for kk in n["kids"]:
                        attrs_of(kk)
                        inner_attrs(kk)
                inner_attrs(k)
            else:
                # loose text beside block children: each run is its own unit
                if k["tag"] not in VOID:
                    walk(k)
                    lone = [t for t in k["texts"] if has_letters(t)]
                    for t in lone:
                        pos = src.find(t, k["se"], k["es"])
                        if pos >= 0:
                            out.append(("text", (pos, pos + len(t)), None))
    walk(tree.root)
    spans = []
    for kind, el, name in out:
        if kind == "inner":
            s, e = el["se"], el["es"]
            spans.append((s, e, norm(src[s:e]), "inner"))
        elif kind == "text":
            s, e = el
            raw = src[s:e]
            lead = len(raw) - len(raw.lstrip())
            trail = len(raw) - len(raw.rstrip())
            spans.append((s + lead, e - trail, norm(raw), "inner"))
        else:
            tag = src[el["s"]:el["se"]]
            m = re.search(r'\s' + re.escape(name) + r'="([^"]*)"', tag)
            if not m:
                continue
            s = el["s"] + m.start(1)
            spans.append((s, el["s"] + m.end(1), norm(_html.unescape(m.group(1))), "attr"))
    spans = sorted(set(spans))
    # drop spans nested in another span (a link's title inside a translated paragraph stays a unit only once)
    keep, last_end = [], -1
    for sp in spans:
        if sp[3] == "inner" and sp[0] < last_end:
            continue
        keep.append(sp)
        if sp[3] == "inner":
            last_end = max(last_end, sp[1])
    return [sp for sp in keep if has_letters(sp[2]) and not IDENTITY.match(re.sub(r"<[^>]+>", "", sp[2]).strip())]


def jsonld_strings(src):
    """Text values of the page's structured data that a reader sees in search results."""
    out = []
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', src, re.S):
        try:
            data = json.loads(m.group(1))
        except ValueError:
            continue

        def walk(v, key=None):
            if isinstance(v, dict):
                for k, x in v.items():
                    walk(x, k)
            elif isinstance(v, list):
                for x in v:
                    walk(x, key)
            elif isinstance(v, str) and key in ("name", "description", "text", "headline", "alternativeHeadline", "alternateName") \
                    and has_letters(v) and not IDENTITY.match(v.strip()):
                out.append(norm(v))
        walk(data)
    return out


def load_catalog():
    if CATALOG.exists():
        return json.loads(CATALOG.read_text(encoding="utf-8"))
    return {}


def rewrite_href(href, src_page):
    """Internal links stay on the Chinese edition when the target has one, else go to English."""
    if href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return href
    if href.startswith(EN):
        rest = href[len(EN):] or "/"
        path = rest.split("#")[0].split("?")[0]
        return (ZH + rest) if path in CN_PATHS else href
    if href.startswith("/") and not href.startswith("//"):
        if href.startswith(("/assets/", "/favicon", "/feed.xml", "/llms.txt")):
            return href
        path = href.split("#")[0].split("?")[0]
        return href if path in CN_PATHS else EN + href
    return href


def localise(page, src, cat, missing, allow_stale):
    spans = units(src)
    out, pos = [], 0
    for s, e, msgid, kind in spans:
        # "page::string" overrides the shared entry on one page (a headline
        # split into lines reads in a different order in Chinese)
        zh = cat.get(f"{page}::{msgid}", cat.get(msgid))
        if zh is None:
            missing.setdefault(page, []).append(msgid)
            zh = msgid if allow_stale else None
        out.append(src[pos:s])
        if zh is None:
            out.append(src[s:e])
        elif kind == "attr":
            out.append(_html.escape(_html.unescape(zh), quote=True))
        else:
            out.append(zh)
        pos = e
    out.append(src[pos:])
    doc = "".join(out)
    # structured data
    def ld(m):
        try:
            data = json.loads(m.group(1))
        except ValueError:
            return m.group(0)

        def walk(v, key=None):
            if isinstance(v, dict):
                return {k: walk(x, k) for k, x in v.items()}
            if isinstance(v, list):
                return [walk(x, key) for x in v]
            if isinstance(v, str):
                if key in ("url", "item") and v.startswith(EN):
                    return rewrite_href(v, page)
                if key in ("name", "description", "text", "headline", "alternativeHeadline") and has_letters(v):
                    t = cat.get(norm(v))
                    if t is None and not IDENTITY.match(v.strip()):
                        missing.setdefault(page, []).append(norm(v))
                    return _html.unescape(re.sub(r"<[^>]+>", "", t)) if t else v
                if key == "inLanguage":
                    return ZH_LANG
            return v
        data = walk(data)
        return '<script type="application/ld+json">\n' + json.dumps(data, ensure_ascii=False, indent=2) + "\n</script>"
    doc = re.sub(r'<script type="application/ld\+json">(.*?)</script>', ld, doc, flags=re.S)
    # a note only the Chinese edition carries (the Router notice on where it is offered)
    note = cat.get(f"@notice:{page}")
    if note:
        doc = re.sub(r'(<p class="sub">.*?</p>)', lambda m: m.group(1) + f'\n      <p class="cn-notice">{note}</p>', doc, count=1, flags=re.S)
    # language, canonical, alternates, locale
    path = path_of(page)
    doc = doc.replace('<html lang="en">', f'<html lang="{ZH_LANG}">', 1)
    doc = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{ZH}{path}">', doc, count=1)
    doc = re.sub(r'\s*<link rel="alternate" hreflang="[^"]*" href="[^"]*">', "", doc)
    if page != "404.html":
        alts = (f'<link rel="alternate" hreflang="en" href="{EN}{path}">\n'
                f'<link rel="alternate" hreflang="{ZH_LANG}" href="{ZH}{path}">\n'
                f'<link rel="alternate" hreflang="x-default" href="{EN}{path}">')
        doc = re.sub(r'(<link rel="canonical" href="[^"]*">)', r"\1\n" + alts.replace("\\", "\\\\"), doc, count=1)
    doc = doc.replace('<meta property="og:locale" content="en_US">', '<meta property="og:locale" content="zh_CN">')
    doc = re.sub(r'(<meta property="og:url" content=")' + re.escape(EN), r"\1" + ZH, doc)
    # links
    doc = re.sub(r'(<a\b[^>]*\shref=")([^"]*)(")', lambda m: m.group(1) + rewrite_href(m.group(2), page) + m.group(3), doc)
    doc = re.sub(r'(<form\b[^>]*\saction=")([^"]*)(")', lambda m: m.group(1) + rewrite_href(m.group(2), page) + m.group(3), doc)
    # the language link points back at English
    lang = f'<a class="nav-lang" href="{EN}{path if page != "404.html" else "/"}" hreflang="en" lang="en">English</a>'
    if 'class="nav-lang"' in doc:
        doc = re.sub(r'<a class="nav-lang"[^>]*>[^<]*</a>', lang, doc)
    else:
        doc = re.sub(r'(\s*)(<a class="nav-cta")', r"\1" + lang.replace("\\", "\\\\") + r"\1\2", doc, count=1)
    return doc


def todo():
    cat = load_catalog()
    need = {}
    seen = set()
    for page in CN_PAGES:
        src = (ROOT / page).read_text(encoding="utf-8")
        ids = [u[2] for u in units(src)] + jsonld_strings(src)
        miss = []
        for i in ids:
            if i not in cat and i not in seen:
                miss.append(i)
                seen.add(i)
        if miss:
            need[page] = miss
    TODO.write_text(json.dumps(need, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n = sum(len(v) for v in need.values())
    print(f"build_cn: {n} string(s) to translate across {len(need)} page(s) -> {TODO.relative_to(ROOT)}")
    return n


SITE_FILES = ["_headers", "favicon.ico", "assets"]


def render(out):
    cat = load_catalog()
    allow = bool(os.environ.get("CN_STALE_OK"))
    missing = {}
    out = pathlib.Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for page in CN_PAGES:
        src = (ROOT / page).read_text(encoding="utf-8")
        doc = localise(page, src, cat, missing, allow)
        dst = out / page
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(doc, encoding="utf-8")
    for f in SITE_FILES:
        s = ROOT / f
        if s.is_dir():
            shutil.copytree(s, out / f, dirs_exist_ok=True)
        elif s.exists():
            shutil.copy2(s, out / f)
    # every other path is the English page
    redirects = ["# Generated by tools/build_cn.py: paths without a Chinese edition go to English."]
    for p in sorted(ROOT.glob("*.html")):
        if p.name.startswith("_") or p.name in CN_PAGES:
            continue
        redirects.append(f"/{p.stem} {EN}/{p.stem} 302")
    for d in ("blog", "docs", "payments", "scheduled"):
        redirects.append(f"/{d}/* {EN}/{d}/:splat 302")
    redirects.append(f"/pricing {EN}/plans 302")
    (out / "_redirects").write_text("\n".join(redirects) + "\n", encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {ZH}/sitemap.xml\n", encoding="utf-8")
    urls = "\n".join(f"  <url><loc>{ZH}{path_of(p)}</loc>"
                     f'<xhtml:link rel="alternate" hreflang="en" href="{EN}{path_of(p)}"/>'
                     f'<xhtml:link rel="alternate" hreflang="{ZH_LANG}" href="{ZH}{path_of(p)}"/></url>'
                     for p in CN_PAGES if p != "404.html")
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + urls + "\n</urlset>\n", encoding="utf-8")
    n = sum(len(set(v)) for v in missing.values())
    if n:
        for page, ids in missing.items():
            for i in sorted(set(ids))[:8]:
                print(f"  untranslated  {page}: {i[:90]}")
        if not allow:
            print(f"build_cn: {n} untranslated string(s); run --extract, translate i18n/zh-CN.todo.json "
                  f"into i18n/zh-CN.json, or set CN_STALE_OK=\"<reason>\" to ship English for them")
            return 1
        print(f"build_cn: {n} string(s) shipped in English (CN_STALE_OK={os.environ['CN_STALE_OK']!r})")
    print(f"build_cn: {len(CN_PAGES)} page(s) rendered into {out}")
    return 0


def alternates():
    """hreflang on the English pages that have a Chinese edition, only while
    runixcloud.com actually serves it (i18n.ZH_LIVE); removed otherwise."""
    changed = 0
    for page in CN_PAGES:
        if page == "404.html":
            continue
        p = ROOT / page
        t = p.read_text(encoding="utf-8")
        o = t
        t = re.sub(r'\n<link rel="alternate" hreflang="[^"]*" href="[^"]*">', "", t)
        if ZH_LIVE:
            path = path_of(page)
            alts = (f'\n<link rel="alternate" hreflang="en" href="{EN}{path}">'
                    f'\n<link rel="alternate" hreflang="{ZH_LANG}" href="{ZH}{path}">'
                    f'\n<link rel="alternate" hreflang="x-default" href="{EN}{path}">')
            t = re.sub(r'(<link rel="canonical" href="[^"]*">)', lambda m: m.group(1) + alts, t, count=1)
        if t != o:
            p.write_text(t, encoding="utf-8")
            changed += 1
    print(f"build_cn alternates: {changed} page(s) changed (ZH_LIVE={ZH_LIVE})")
    return 0


def main():
    a = sys.argv[1:]
    if "--alternates" in a:
        return alternates()
    if "--extract" in a:
        todo()
        return 0
    if "--check" in a:
        return 1 if todo() else 0
    if "--out" in a:
        return render(a[a.index("--out") + 1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
