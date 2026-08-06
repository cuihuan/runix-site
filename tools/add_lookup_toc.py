#!/usr/bin/env python3
"""Give the lookup pages the same in-page index the docs already have.

Measured at 375px: the glossary is 16 entries and eleven screens tall with no
way to jump, and the FAQ is 11 questions and five screens. Both are pages
people arrive at looking for one thing. The docs pages already carry a
`.doc-toc`, so this reuses that component rather than inventing a second one --
same markup, same styling, same aria-labelledby pointing at its own heading.

The glossary index is alphabetical rather than numbered, because a glossary has
no order and numbering one would imply a sequence that is not there. The FAQ
keeps document order, because the questions are arranged deliberately.

Idempotent: a page that already has a .doc-toc is left alone.
"""
import html as _h
import os
import pathlib
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PAGES = {
    "glossary.html": ("Jump to a term", True),   # True = sort alphabetically
    "faq.html": ("The questions", False),
}


def main():
    done = []
    for path, (title, alpha) in PAGES.items():
        p = pathlib.Path(path)
        if not p.exists():
            continue
        s = p.read_text()
        if 'class="doc-toc"' in s:
            continue
        heads = re.findall(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', s, re.S)
        if len(heads) < 5:
            print(f"  {path}: only {len(heads)} sections with ids -- skipped")
            continue
        items = [(i, " ".join(_h.unescape(re.sub(r"<[^>]+>", "", t)).split()))
                 for i, t in heads]
        if alpha:
            # A glossary index lists terms. "Something missing?" is a contact
            # block that happens to be an h2; sorting it under S alongside real
            # entries reads as a term that is not one.
            items = [(i, t) for i, t in items if not t.rstrip().endswith("?")]
        if alpha:
            items.sort(key=lambda x: x[1].lower())
        lis = "\n".join(f'    <li><a href="#{i}">{_h.escape(t)}</a></li>' for i, t in items)
        toc = (f'<nav class="doc-toc" aria-labelledby="lookup-toc">\n'
               f'  <p id="lookup-toc" class="toc-title">{title}</p>\n'
               f'  <ul>\n{lis}\n  </ul>\n</nav>\n')
        # Straight after the opening <article>, which is where the docs put it.
        m = re.search(r'<article class="article">\s*', s)
        if not m:
            print(f"  {path}: no <article> to place it in -- skipped")
            continue
        p.write_text(s[:m.end()] + toc + s[m.end():])
        done.append(f"{path} ({len(items)} entries)")
    print(f"  added an in-page index to {len(done)} page(s)"
          + ("".join(f"\n    {d}" for d in done) if done else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
