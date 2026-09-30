#!/usr/bin/env python3
"""Rebuild the header nav, the footer product column and the no-script nav
fallback on every page, for the 2026-09-29 flagship pass.

What changes and why:

  * "Platform" and "Products" were two anchors into the home page. With a
    fifth product (Runix FS) the header now carries a Products menu that
    names all five with one line each, and "Platform overview" moves inside
    it. "Products" itself stays a real link to /#products, so a touch or
    no-script visitor still lands on the full product list.
  * The footer's Product column gains Runix FS, and the footer tagline names
    all five products.
  * The <noscript> fallback hides the menu panel: without script the phone
    nav is a wrapped row of top-level links, and five product rows with
    descriptions would push the page down by a screen.

The nav is rebuilt structurally (balanced <div> matching) rather than by
string replacement, because each page marks its own item active and the
block now contains a nested <div>. Idempotent: a second run changes nothing.
Run from the site root.

2026-09-30, second pass: the products are now drawn as a five-layer stack
(tools/stack.py is the one definition). The Products menu groups them by
layer, top to bottom as the home page draws them; the footer's Product column
is rebuilt from the same list; and the lockup reads "Runix Lab" in the header
and the footer. The company is still Runix AI Inc and the products keep their
"Runix X" names -- only the mark changes.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from stack import LAYERS, PRODUCTS as STACK, products_in, product_pages  # noqa: E402

CONSOLE = "https://console.router.runixcloud.io"

TOP = [("/plans", "Pricing"), ("/docs/", "Docs"), ("/about", "Company")]
PRODUCT_PAGES = set(product_pages())
# The Runix Data domain pages sit under a product, so the menu marks Products.
from domains import DOMAINS as _DOMAINS  # noqa: E402
PRODUCT_PAGES |= {f"{d['slug']}.html" for d in _DOMAINS}

NOSCRIPT_OLD = (".nav-toggle{display:none!important}}</style></noscript>")
NOSCRIPT_NEW = (".nav-toggle{display:none!important}"
                ".nav-panel{display:none!important}.nav-menu{width:auto}}</style></noscript>")

LOCKUP_OLD = '<span class="mark" aria-hidden="true">R</span>Runix</a>'
LOCKUP_NEW = ('<span class="mark" aria-hidden="true">R</span>Runix '
              '<span class="brand-lab">Lab</span></a>')

TAGLINE_NEW = ("Rebuild AI Unix: an efficient, stable, enterprise-grade AI "
               "operating system, in five layers from storage to applications.")


def footer_products(indent, active_href):
    """The footer's Product column, in the order the stack is drawn."""
    links = []
    for layer, *_ in LAYERS:
        for key in products_in(layer):
            _, href, name, *_rest = STACK[key]
            links.append((href, name))
            if key == "code":
                links.append(("/code-plans", "Code plans"))
    links.append(("/plans", "Pricing"))
    out = []
    for href, name in links:
        cls = ' class="active"' if href == active_href else ""
        out.append(f'{indent}<a href="{href}"{cls}>{name}</a>')
    return "\n".join(out)


def active_for(path):
    p = str(path)
    if p.startswith("docs/"):
        return "/docs/"
    if p == "about.html":
        return "/about"
    if p in ("plans.html", "pricing.html", "code-plans.html"):
        return "/plans"
    if p in PRODUCT_PAGES:
        return "products"
    return None


TOGGLE_SVG = ('<svg width="24" height="24" viewBox="0 0 24 24" fill="none" '
              'stroke="currentColor" stroke-width="2" stroke-linecap="round" '
              'aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg>')


def build_header_nav(path):
    """The whole <nav>: brand, menu button and links, in one canonical form.

    Rebuilt as a unit because the pages had drifted apart underneath the link
    list the nav check compares: 43 of 57 left the logo's fallback letter
    exposed to screen readers (no aria-hidden on .mark) and 8 had a menu button
    with no accessible name. Neither shows on screen, so neither was caught.
    """
    return ('  <nav class="nav" aria-label="Primary">\n'
            '    <a class="brand" href="/"><span class="mark" aria-hidden="true">R</span>Runix <span class="brand-lab">Lab</span></a>\n'
            f'    <button class="nav-toggle" aria-label="Toggle menu" aria-expanded="false">{TOGGLE_SVG}</button>\n'
            + build_nav(path, "    ") + "\n  </nav>")


def build_nav(path, indent):
    active = active_for(path)
    i1, i2, i3 = indent + "  ", indent + "    ", indent + "      "
    top_cls = "nav-menu-top active" if active == "products" else "nav-menu-top"
    lines = [f'{indent}<div class="nav-links">',
             f'{i1}<div class="nav-menu">',
             f'{i2}<a class="{top_cls}" href="/#products">Products</a>',
             f'{i2}<div class="nav-panel">']
    i4 = i3 + "  "
    for layer, num, lname, _role in LAYERS:
        lines.append(f'{i3}<div class="nav-layer">')
        lines.append(f'{i4}<p class="nav-layer-name"><span>{num:02d}</span>{lname}</p>')
        for key in products_in(layer):
            _, href, name, line, _l, _st, tag = STACK[key]
            badge = f" <i>{tag}</i>" if tag else ""
            lines.append(f'{i4}<a class="nav-prod" href="{href}"><b>{name}{badge}</b>'
                         f'<span>{line}</span></a>')
        lines.append(f'{i3}</div>')
    lines.append(f'{i3}<a class="nav-prod nav-stack-link" href="/#platform"><b>The whole stack '
                 f'<span aria-hidden="true">&rarr;</span></b><span>How the five layers fit together</span></a>')
    lines += [f'{i2}</div>', f'{i1}</div>']
    for href, label in TOP:
        cls = ' class="active"' if href == active else ""
        lines.append(f'{i1}<a href="{href}"{cls}>{label}</a>')
    lines.append(f'{i1}<a class="nav-signin" href="{CONSOLE}" target="_blank" '
                 f'rel="noopener">Sign in</a>')
    lines.append(f'{i1}<a class="nav-cta" href="/about#contact">Request access</a>')
    lines.append(f'{indent}</div>')
    return "\n".join(lines)


def div_span(text, start):
    """End offset of the <div> opened at `start`, counting nested divs."""
    depth = 0
    for m in re.finditer(r"<div\b|</div>", text[start:]):
        depth += 1 if m.group(0) != "</div>" else -1
        if depth == 0:
            return start + m.end()
    return None


def main():
    pages = sorted(p for p in pathlib.Path(".").rglob("*.html")
                   if not p.name.startswith("_") and "node_modules" not in p.parts)
    changed, carriers, problems = 0, 0, []
    for p in pages:
        rel = p.as_posix()
        t = p.read_text(encoding="utf-8")
        orig = t
        i = t.find('<nav class="nav" aria-label="Primary">')
        if i >= 0:
            carriers += 1
            end = t.find("</nav>", i)
            if end < 0 or '<div class="nav-links">' not in t[i:end]:
                problems.append(f"{rel}: header nav not in the expected shape")
                continue
            line_start = t.rfind("\n", 0, i) + 1
            t = t[:line_start] + build_header_nav(rel) + t[end + len("</nav>"):]
            if NOSCRIPT_OLD in t and NOSCRIPT_NEW not in t:
                t = t.replace(NOSCRIPT_OLD, NOSCRIPT_NEW, 1)
        # Only inside the footer: the same link can appear in body copy, and
        # the first match in the file is not necessarily the footer's.
        f0 = t.rfind("<footer")
        if f0 >= 0:
            foot = t[f0:]
            foot = foot.replace(LOCKUP_OLD, LOCKUP_NEW, 1)
            m = re.search(r'(<p class="footer-heading">Product</p>\n)((?:[ \t]*<a [^\n]*</a>\n)+)', foot)
            if m:
                ind = re.match(r"[ \t]*", m.group(2)).group(0)
                act = re.search(r'<a href="([^"]+)" class="active">', m.group(2))
                col = footer_products(ind, act.group(1) if act else None) + "\n"
                foot = foot[:m.start(2)] + col + foot[m.end(2):]
            else:
                problems.append(f"{rel}: footer has no Product column in the expected shape")
            t = t[:f0] + foot
            # The footer's description, replaced whole rather than matched
            # against known old wordings: four product pages carried a colon
            # variant of the 2026-08 tagline that no string here matched, so
            # they kept naming four products after the fifth shipped.
            t = t[:f0] + re.sub(r'(<p class="desc">)[^<]*(</p>)',
                                lambda m: m.group(1) + TAGLINE_NEW + m.group(2),
                                t[f0:], count=1)
        if t != orig:
            p.write_text(t, encoding="utf-8")
            changed += 1
    print(f"flagship nav: {changed} page(s) changed ({carriers} carry a nav)")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
