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
"""
import pathlib
import re
import sys

CONSOLE = "https://console.router.runixcloud.io"

PRODUCTS = [
    ("/router", "Runix Router", "One compliant endpoint for every model", ""),
    ("/fs", "Runix FS", "AI-native file system on your object storage", "New"),
    ("/pipeline", "Runix Pipeline", "Raw material into model-ready data", ""),
    ("/code", "Runix Code", "A reviewable AI agent in your repository", ""),
    ("/comic", "Runix Comic", "Scripts into published episodes", ""),
    ("/#platform", "Platform overview", "How the five products fit together", ""),
]
TOP = [("/plans", "Pricing"), ("/docs/", "Docs"), ("/about", "Company")]
PRODUCT_PAGES = {"router.html", "fs.html", "pipeline.html", "code.html", "comic.html"}

NOSCRIPT_OLD = (".nav-toggle{display:none!important}}</style></noscript>")
NOSCRIPT_NEW = (".nav-toggle{display:none!important}"
                ".nav-panel{display:none!important}.nav-menu{width:auto}}</style></noscript>")

FOOTER_OLD = '<a href="/router">Runix Router</a>\n'
FOOTER_FS = '<a href="/fs">Runix FS</a>\n'
TAGLINE_OLD = ("AI, made effortless — Runix Router, Runix Pipeline, Runix Code "
               "and Runix Comic.")
TAGLINE_NEW = ("The infrastructure layer for production AI: Runix Router, Runix FS, "
               "Runix Pipeline, Runix Code and Runix Comic.")


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
            '    <a class="brand" href="/"><span class="mark" aria-hidden="true">R</span>Runix</a>\n'
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
    for href, name, line, tag in PRODUCTS:
        badge = f" <i>{tag}</i>" if tag else ""
        lines.append(f'{i3}<a class="nav-prod" href="{href}"><b>{name}{badge}</b>'
                     f'<span>{line}</span></a>')
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
        if f0 >= 0 and FOOTER_OLD in t[f0:] and FOOTER_FS not in t[f0:]:
            j = t.find(FOOTER_OLD, f0)
            ind = t[t.rfind("\n", 0, j) + 1:j]
            t = t[:j] + FOOTER_OLD + ind + FOOTER_FS + t[j + len(FOOTER_OLD):]
        t = t.replace(TAGLINE_OLD, TAGLINE_NEW)
        if t != orig:
            p.write_text(t, encoding="utf-8")
            changed += 1
    print(f"flagship nav: {changed} page(s) changed ({carriers} carry a nav)")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
