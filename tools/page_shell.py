#!/usr/bin/env python3
"""The page shell for every page that is not a product page (v4, 2026-09-30).

The product pages carry a product bar, an eyebrow and numbered section heads
(tools/product_template.py). This gives the same three things to the rest of
the site, so a visitor moving from /router to /security or a blog post stays
inside one shell:

  * a page bar under the header: the page's name, its section of the site
    (Pricing, Company, Legal, Blog, Docs, Payments), a status where the page
    has one (a legal document's version and date, a post's category and
    date), links to the page's own sections, and the action;
  * an eyebrow above the title naming the section of the site;
  * numbered section heads on pages built from sections.

Section links need ids; an <h2> without one gets a slug of its text. Pages
with their own contents list (the FAQ and the glossary) carry no section
links in the bar. Idempotent: generated markup carries markers and is
re-rendered on every run. Run from the site root after the other builders.
"""
import glob
import html as _html
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from stack import PRODUCTS  # noqa: E402
from domains import DOMAINS  # noqa: E402

SALES = ("/about#contact", "Contact sales")
SUPPORT = ("mailto:support@runixcloud.io?subject=Runix%20support", "Contact support")

# page -> (name in the bar, group label, group href, (cta href, cta label))
PAGES = {
    "plans.html": ("Pricing", "Pricing", "/plans", ("mailto:sales@runixcloud.io?subject=Runix%20pricing", "Talk to sales")),
    "code-plans.html": ("Code plans", "Pricing", "/plans", SALES),
    "about.html": ("About", "Company", "/about", ("#contact", "Contact us")),
    "security.html": ("Security", "Company", "/about", SALES),
    "reliability.html": ("Reliability", "Company", "/about", SALES),
    "access.html": ("Access", "Company", "/about", SALES),
    "faq.html": ("FAQ", "Company", "/about", SALES),
    "glossary.html": ("Glossary", "Company", "/about", SALES),
    "careers.html": ("Careers", "Company", "/about", ("mailto:contact@runixcloud.io?subject=Runix%20-%20introduction", "Write to us")),
    "terms.html": ("Terms of Service", "Legal", "/terms", SUPPORT),
    "privacy.html": ("Privacy Policy", "Legal", "/terms", SUPPORT),
    "refund.html": ("Refund Policy", "Legal", "/terms", SUPPORT),
    "delivery.html": ("Shipping &amp; Delivery", "Legal", "/terms", SUPPORT),
    "cancellation.html": ("Cancellation Policy", "Legal", "/terms", SUPPORT),
    "acceptable-use.html": ("Acceptable Use", "Legal", "/terms", SUPPORT),
    "docs/index.html": ("Docs", "Docs", "/docs/", SALES),
    "blog/index.html": ("Blog", "Blog", "/blog/", SALES),
    "pay.html": ("Payments", "Payments", "/pay", SUPPORT),
    "thanks.html": ("Payment received", "Payments", "/pay", SUPPORT),
}
# Pages with their own contents list carry no section links in the bar.
OWN_TOC = {"faq.html", "glossary.html"}
MAX_LINKS = 7

# Labels for numbered section heads, by the heading's text. A heading not
# listed gets its first two words.
LABELS = {
    "How each product is priced": "Products", "Why there is no checkout": "Why", "Common questions": "Questions",
    "One credit, every model": "Credits", "Team plans": "Plans", "How usage stays predictable": "Usage",
    "What Runix is": "Company", "How we work": "How we work", "What we publish openly": "In the open",
    "What we do not claim": "Not claimed", "How we work": "How we work", "Open roles": "Roles",
    "None of these quite you?": "Other roles", "All posts": "Posts", "Product guides": "Guides",
    "Background reading": "Reading", "Reliability requirements to check against": "Checklist",
    "Request an account": "Request",
}


def slug(text):
    t = _html.unescape(re.sub(r"<[^>]+>", " ", text))
    t = re.sub(r"^\s*\d+\.\s*", "", t)
    t = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
    return t[:60].rstrip("-") or "section"


def strip(doc):
    doc = re.sub(r"[ \t]*<!--ps:bar-->.*?<!--/ps:bar-->\n?", "", doc, flags=re.S)
    doc = re.sub(r"[ \t]*<!--ps:eyebrow-->.*?<!--/ps:eyebrow-->\n?", "", doc, flags=re.S)
    doc = re.sub(r'[ \t]*<p class="sec-no">[^<]*</p>\n', "", doc)
    return doc


def main_bounds(doc):
    a = doc.index('<main id="main"')
    a = doc.index(">", a) + 1
    return a, doc.index("</main>")


def give_ids(doc):
    """Every <h2> in <main> gets an id (a slug of its text), unique on the page."""
    a, b = main_bounds(doc)
    body = doc[a:b]
    ids = set(re.findall(r'\bid="([^"]+)"', doc))
    out, pos = [], 0
    for m in re.finditer(r"<h2\b([^>]*)>(.*?)</h2>", body, re.S):
        if re.search(r'\bid="', m.group(1)):
            continue
        s = base = slug(m.group(2))
        n = 2
        while s in ids:
            s = f"{base}-{n}"
            n += 1
        ids.add(s)
        out.append(body[pos:m.start()])
        out.append(f'<h2 id="{s}"{m.group(1)}>{m.group(2)}</h2>')
        pos = m.end()
    out.append(body[pos:])
    return doc[:a] + "".join(out) + doc[b:]


def sections(doc):
    """(id, text) of every <h2> in <main>, skipping the closing band and asides."""
    a, b = main_bounds(doc)
    body = doc[a:b]
    body = re.sub(r'<div class="cta-band">.*?</div>\s*</div>\s*</section>', " ", body, flags=re.S)
    body = re.sub(r"<aside\b.*?</aside>", " ", body, flags=re.S)
    body = re.sub(r"<nav\b.*?</nav>", " ", body, flags=re.S)
    out = []
    for m in re.finditer(r'<h2\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h2>', body, re.S):
        text = " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", m.group(2))).split())
        text = re.sub(r"^\d+\.\s*", "", text)
        if "visually-hidden" in m.group(0):
            continue
        out.append((m.group(1), text))
    return out


def legal_status(doc):
    m = re.search(r"Last updated: ([^&<]+?)&nbsp;.*?Version ([0-9.]+)", doc)
    return f"Version {m.group(2)} &middot; {m.group(1).strip()}" if m else None


def post_meta(doc):
    m = re.search(r'<div class="post-meta"><span class="cat">([^<]*)</span><span>([^<]*)</span>', doc)
    return (m.group(1), m.group(2)) if m else None


def bar(page, doc, name, group, ghref, cta, status=None, layer_is_link=True):
    # The landmark's name: the bar's own name, which never carries a quote
    # (a post title can, and a quote inside aria-label breaks the attribute).
    title = "This post" if not layer_is_link else f"{_html.unescape(name)} on this page"
    links = "" if page in OWN_TOC else "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in sections(doc)[:MAX_LINKS])
    layer = (f'<a class="pbar-layer" href="{ghref}">{group}</a>' if layer_is_link
             else f'<span class="pbar-layer">{group}</span>')
    st = f'\n    <span class="pbar-status">{status}</span>' if status else ""
    href, label = cta
    c = f'<a class="pbar-cta" href="{href}">{label}</a>'
    if href.startswith("mailto:"):
        c = f"<!--email_off-->{c}<!--/email_off-->"
    return (f'<!--ps:bar-->\n<nav class="pbar pbar-page" aria-label="{_html.escape(title, quote=True)}">\n'
            f'  <div class="container pbar-inner">\n'
            f'    <a class="pbar-name" href="#overview">{name}</a>\n'
            f'    {layer}{st}\n'
            f'    <ul class="pbar-links">{links}</ul>\n'
            f'    {c}\n'
            f'  </div>\n</nav>\n<!--/ps:bar-->')


def number_sections(doc):
    a, b = main_bounds(doc)
    body = doc[a:b]
    n, out, pos = 1, [], 0
    for m in re.finditer(r'<section class="([^"]*)"[^>]*>', body):
        end = body.find("</section>", m.end())
        sec = body[m.start():end]
        head = re.search(r'<div class="section-head[^"]*"[^>]*>\n?', sec)
        if not head or "cta-band" in sec:
            continue
        n += 1
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", sec, re.S)
        text = " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", h2.group(1))).split()) if h2 else ""
        label = LABELS.get(text) or " ".join(text.split()[:2])
        label = _html.escape(label, quote=False)
        sec = sec[:head.end()] + f'      <p class="sec-no">{n:02d} &middot; {label}</p>\n' + sec[head.end():]
        out.append(body[pos:m.start()])
        out.append(sec)
        pos = end
    out.append(body[pos:])
    return doc[:a] + "".join(out) + doc[b:]


def shell(page, doc):
    doc = strip(doc)
    doc = give_ids(doc)
    is_post = page.startswith("blog/") and page != "blog/index.html"
    if is_post:
        cat, date = post_meta(doc) or ("Post", "")
        b = bar(page, doc, "Blog", cat, "/blog/", SALES, status=date, layer_is_link=False)
        b = b.replace('href="#overview">Blog</a>', 'href="/blog/">Blog</a>')
    else:
        name, group, ghref, cta = PAGES[page]
        status = legal_status(doc) if group == "Legal" else None
        b = bar(page, doc, name, group, ghref, cta, status=status)
    # the hero is the overview the bar's name links to
    doc = re.sub(r'<div class="page-hero( center)?">', '<div class="page-hero" id="overview">', doc, count=1)
    doc = re.sub(r'<section class="plan-hero([^"]*)">', r'<section class="plan-hero\1" id="overview">', doc, count=1)
    # the bar, first inside main
    a, _ = main_bounds(doc)
    doc = doc[:a] + "\n" + b + doc[a:]
    doc = doc.replace('<main id="main">', '<main id="main" class="has-pbar">', 1)
    # the eyebrow, first in the hero's container (posts already carry their meta)
    if not is_post:
        h = doc.find('<div class="page-hero" id="overview">')
        if h >= 0:
            c = doc.index('<div class="container">', h) + len('<div class="container">')
            doc = doc[:c] + f'\n    <!--ps:eyebrow--><p class="page-eyebrow">{PAGES[page][1]}</p><!--/ps:eyebrow-->' + doc[c:]
    doc = number_sections(doc)
    return re.sub(r"\n{3,}", "\n\n", doc)


def main():
    product_pages = {v[0] for v in PRODUCTS.values()} | {f"{d['slug']}.html" for d in DOMAINS}
    targets = [p for p in PAGES] + sorted(p for p in glob.glob("blog/*.html") if not p.endswith("index.html"))
    changed = 0
    for page in targets:
        if page in product_pages:
            continue
        p = pathlib.Path(page)
        doc = p.read_text(encoding="utf-8")
        new = shell(page, doc)
        if new != doc:
            p.write_text(new, encoding="utf-8")
            changed += 1
    print(f"page shell: {changed} of {len(targets)} page(s) changed")


if __name__ == "__main__":
    main()
