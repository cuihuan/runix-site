#!/usr/bin/env python3
"""Give the docs pages the navigation a reference page is expected to have.

Three things were missing, all of them things a reader hits within the first
minute:

1. No headings had ids, so nothing in the docs could be linked to. A support
   reply cannot say "see section 4" with a URL.
2. The router guide has eight sections and no table of contents, so finding
   "failover semantics" meant scrolling and hoping.
3. Every docs page was a dead end: no link back to the docs index, no link to
   the sibling guides, nothing at the bottom but the article's last paragraph.

The table of contents renders as a plain box above the article on narrow
screens and moves into the left margin as a sticky rail from 1200px up, where
that margin is otherwise empty.

Idempotent. Run from the site root.
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# title shown in the sibling nav, in the order the docs index lists them
DOCS = [
    ("router", "Router"),
    ("pipeline", "Pipeline"),
    ("code", "Code"),
    ("comic", "Comic"),
]
TITLES = dict(DOCS)


def slug(text):
    """'4. Failover semantics' -> 'failover-semantics'."""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^\s*\d+[.)]\s*", "", text)  # drop the section number
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def add_ids(html):
    """Give every h2 without one a stable id derived from its text."""
    seen = set()

    def repl(match):
        attrs, text = match.group(1), match.group(2)
        if "id=" in attrs:
            return match.group(0)
        anchor = slug(text)
        n = 2
        while anchor in seen:
            anchor, n = f"{slug(text)}-{n}", n + 1
        seen.add(anchor)
        return f'<h2{attrs} id="{anchor}">{text}</h2>'

    return re.sub(r"<h2([^>]*)>(.*?)</h2>", repl, html, flags=re.S)


def toc_for(html):
    items = re.findall(r'<h2[^>]*id="([^"]+)"[^>]*>(.*?)</h2>', html, re.S)
    if len(items) < 4:  # a two-item contents list is noise, not navigation
        return ""
    links = "".join(
        f'\n    <li><a href="#{anchor}">{re.sub(r"<[^>]+>", "", text).strip()}</a></li>'
        for anchor, text in items
    )
    return (
        '<nav class="doc-toc" aria-labelledby="toc-heading">\n'
        '  <p id="toc-heading" class="toc-title">On this page</p>\n'
        f"  <ul>{links}\n  </ul>\n"
        "</nav>\n"
    )


def sibling_nav(current):
    others = "".join(
        f'\n    <li><a href="/docs/{s}">{TITLES[s]} documentation</a></li>'
        for s, _ in DOCS
        if s != current
    )
    return (
        '\n<nav class="doc-next" aria-labelledby="more-docs">\n'
        '  <p id="more-docs" class="toc-title">More documentation</p>\n'
        f"  <ul>{others}\n"
        '    <li><a href="/docs/">All documentation</a></li>\n'
        "  </ul>\n"
        "</nav>\n"
    )


changed = []
for path in sorted(glob.glob("docs/*.html")):
    name = os.path.basename(path)[:-5]
    html = open(path).read()
    before = html

    html = add_ids(html)

    if 'class="doc-toc"' not in html and name in TITLES:
        toc = toc_for(html)
        if toc:
            # The rail sits beside the article, so both go inside one wrapper.
            html = html.replace(
                '<article class="article">',
                f'<div class="doc-wrap">\n{toc}\n<article class="article">',
                1,
            )
            html = html.replace("</article>", "</article>\n</div>", 1)

    if 'class="doc-next"' not in html and name in TITLES:
        html = html.replace("</article>", sibling_nav(name) + "</article>", 1)

    if html != before:
        open(path, "w").write(html)
        changed.append(name)

print(f"  docs nav: updated {len(changed)} page(s): {', '.join(changed) or 'none'}")

# The h2 ids are only useful if a jump actually lands on the heading. The header
# is sticky at 68px, so without scroll-margin every anchor on the site scrolls
# its target under the header.
#
# This block used to append scroll-margin-top and the whole .doc-toc/.doc-next
# rule set to style.css on first run. That path has been dead since the first
# run succeeded -- the guard is permanently true -- and the copy it carried had
# drifted badly: it still spelled sizes as 12px/14px/13px after style.css moved
# to the type-scale tokens, and it was the second home of the var(--muted)
# reference that was never defined anywhere. A dead second copy of live CSS is
# worse than no copy, so it is gone: assets/style.css is the source of truth for
# these rules. What remains is the check, because silently rendering the docs
# pages without their contents rail is a worse failure than stopping.
css = open("assets/style.css").read()
missing = [sel for sel in ("scroll-margin-top", ".doc-toc", ".doc-next") if sel not in css]
if missing:
    raise SystemExit(
        "assets/style.css no longer defines: " + ", ".join(missing) + "\n"
        "These rules are maintained in style.css, not generated here. Restore them."
    )
print("  style.css: docs rail present")
