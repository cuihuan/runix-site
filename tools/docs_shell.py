#!/usr/bin/env python3
"""The docs shell (2026-09-30 redesign, v3; design canvas artboard 06).

  * Every guide gets a sidebar listing all guides grouped by layer, with the
    current one marked, and a breadcrumb above its title. The page's own
    "On this page" list stays and moves to the right column on wide screens.
  * The docs hub lists the guides by layer instead of by status.

Guides that live on a product page (Models and Data have their engagement
guide at /<product>#early-access) are listed the way the hub already lists
them. Idempotent: generated blocks carry markers. Run from the site root.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from stack import LAYERS, PRODUCTS, products_in  # noqa: E402

# product key -> (href of its guide, the guide's name)
GUIDES = {
    "code": ("/docs/code", "Rollout guide"),
    "comic": ("/docs/comic", "Workflow guide"),
    "router": ("/docs/router", "Quickstart and integration"),
    "models": ("/models#early-access", "How an engagement runs"),
    "data": ("/data#early-access", "How an engagement runs"),
    "pipeline": ("/docs/pipeline", "Engagement guide"),
    "fs": ("/docs/fs", "Quick start"),
}
COMPANY = [("/glossary", "Glossary"), ("/faq", "FAQ"), ("/access", "How access works")]


def sidebar(current):
    out = ['<!--ds:side-->', '<nav class="doc-side" aria-label="All guides">']
    for key, num, name, _role in LAYERS:
        out.append(f'  <p class="doc-side-h">{num:02d} &middot; {name}</p>')
        out.append('  <ul>')
        for pk in products_in(key):
            href, gname = GUIDES[pk]
            pname = PRODUCTS[pk][2]
            cur = ' aria-current="page"' if href == current else ""
            out.append(f'    <li><a href="{href}"{cur}><b>{pname}</b><span>{gname}</span></a></li>')
        out.append('  </ul>')
    out.append('  <p class="doc-side-h">Company</p>')
    out.append('  <ul>')
    for href, name in COMPANY:
        out.append(f'    <li><a href="{href}"><b>{name}</b></a></li>')
    out.append('  </ul>')
    out += ['</nav>', '<!--/ds:side-->']
    return "\n".join(out)


def crumb(key):
    _, num, lname = next((k, n, nm) for k, n, nm, _ in LAYERS if k == PRODUCTS[key][4])
    return (f'<!--ds:crumb--><p class="doc-crumb"><a href="/docs/">Docs</a> <span aria-hidden="true">/</span> '
            f'{num:02d} {lname} <span aria-hidden="true">/</span> {PRODUCTS[key][2]}</p><!--/ds:crumb-->')


def strip(doc):
    doc = re.sub(r"[ \t]*<!--ds:side-->.*?<!--/ds:side-->\n?", "", doc, flags=re.S)
    doc = re.sub(r"[ \t]*<!--ds:crumb-->.*?<!--/ds:crumb-->\n?", "", doc, flags=re.S)
    return doc


def guide_pages():
    changed = 0
    for key, (href, _g) in GUIDES.items():
        if not href.startswith("/docs/"):
            continue
        p = pathlib.Path(href[1:] + ".html")
        doc = p.read_text(encoding="utf-8")
        orig = doc
        doc = strip(doc)
        doc = doc.replace('<div class="doc-wrap has-side">', '<div class="doc-wrap">')
        # breadcrumb: first thing in the page hero's container
        hero = doc.index('<div class="page-hero">')
        cont = doc.index('<div class="container">', hero) + len('<div class="container">')
        doc = doc[:cont] + "\n    " + crumb(key) + doc[cont:]
        # sidebar: first child of the doc wrap
        w = doc.index('<div class="doc-wrap">')
        doc = doc[:w] + '<div class="doc-wrap has-side">\n' + sidebar(href) + doc[w + len('<div class="doc-wrap">'):]
        doc = re.sub(r"\n{3,}", "\n\n", doc)
        if doc != orig:
            p.write_text(doc, encoding="utf-8")
            changed += 1
    return changed


def hub():
    p = pathlib.Path("docs/index.html")
    doc = p.read_text(encoding="utf-8")
    orig = doc
    a = doc.index('<h2 id="product-guides">Product guides</h2>')
    a = doc.rfind('<div class="section-head', 0, a)
    b = doc.index('<p class="model-note">', a)
    region = doc[a:b]
    # the cards, keyed by the product their title links to
    cards = {}
    for m in re.finditer(r'<div class="card">\n(.*?)\n      </div>', region, re.S):
        card = m.group(0)
        h = re.search(r'<h3><a href="([^"]+)">', card)
        for key, (href, _g) in GUIDES.items():
            if h and h.group(1) == href:
                cards[key] = card
    head = re.search(r'<div class="section-head[^"]*">.*?</div>', region, re.S).group(0)
    rows = []
    for key, num, name, role in LAYERS:
        ks = [k for k in products_in(key) if k in cards]
        if not ks:
            continue
        rows.append(f'''    <div class="doc-hub-row">
      <div class="doc-hub-layer"><p class="doc-side-h">{num:02d} &middot; {name}</p><p>{role}</p></div>
      <div class="grid cols-2">
{chr(10).join(cards[k] for k in ks)}
      </div>
    </div>''')
    new = head + '\n    <div class="doc-hub">\n' + "\n".join(rows) + "\n    </div>\n    "
    doc = doc[:a] + new + doc[b:]
    doc = re.sub(r"\n{3,}", "\n\n", doc)
    if doc != orig:
        p.write_text(doc, encoding="utf-8")
        return 1
    return 0


def main():
    n = guide_pages() + hub()
    print(f"docs shell: {n} page(s) changed")


if __name__ == "__main__":
    main()
