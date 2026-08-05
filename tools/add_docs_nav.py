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
# is sticky at 68px, so without scroll-margin every anchor on the site — 264 of
# them, including every glossary term — scrolls its target under the header.
css = open("assets/style.css").read()
if "scroll-margin-top" not in css:
    css += """
/* Sticky header is 68px; without this every in-page anchor lands with its
   heading hidden underneath it. */
:where(h1, h2, h3, h4, [id]) { scroll-margin-top: 88px; }

/* Documentation: contents rail + sibling nav */
.doc-wrap { max-width: 820px; margin: 0 auto; }
.doc-wrap .article { margin: 0; }
.doc-toc {
  padding: 40px 24px 0;
}
.toc-title {
  font-size: 12px; font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--muted); margin: 0 0 12px;
}
.doc-toc ul { list-style: none; margin: 0; padding: 0; }
.doc-toc li { margin: 0 0 8px; }
.doc-toc a {
  color: var(--muted); text-decoration: none; font-size: 14px; line-height: 1.45;
  display: block; border-left: 2px solid var(--line); padding: 2px 0 2px 12px;
}
.doc-toc a:hover { color: var(--ink); border-left-color: var(--indigo); }
.doc-next {
  border-top: 1px solid var(--line); margin-top: 56px; padding-top: 32px;
}
.doc-next .toc-title {
  font-size: 13px; font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--muted); margin: 0 0 16px;
}
.doc-next ul {
  list-style: none; margin: 0; padding: 0;
  display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}
.doc-next a { color: var(--indigo); text-decoration: none; font-weight: 500; }
.doc-next a:hover { text-decoration: underline; }

@media (min-width: 1200px) {
  .doc-wrap {
    /* Same container token as the header and hero, so the contents rail lines
       up with the logo and the h1 instead of sitting 20px to their left.
       212 + 40 + 820 exactly fills the 1072px content box. */
    max-width: var(--maxw);
    display: grid; grid-template-columns: 212px minmax(0, 820px); gap: 40px;
    padding: 0 24px;
  }
  .doc-toc {
    position: sticky; top: 92px; align-self: start;
    padding: 56px 0 0; max-height: calc(100vh - 120px); overflow-y: auto;
  }
}
"""
    open("assets/style.css", "w").write(css)
    print("  style.css: added scroll-margin-top and the docs rail")
else:
    print("  style.css: already carries the docs rail")
