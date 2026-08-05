#!/usr/bin/env python3
"""Give every article table its own scroll container.

A three-column comparison table cannot be made to fit 375px without either
shrinking the type past legibility or dropping a column. The honest answer is
to let the table keep its width and scroll inside a region of its own, so the
page body never scrolls sideways.

The wrapper is focusable and labelled, because a scrollable region that only a
mouse can reach is not reachable.

Idempotent. Run from the site root.
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CSS = """
/* Wide tables scroll inside their own region rather than pushing the page
   sideways. tabindex makes the region keyboard-scrollable. */
.article .table-scroll {
  overflow-x: auto; margin: 18px 0;
  border: 1px solid var(--line); border-radius: var(--radius);
}
.article .table-scroll table { margin: 0; min-width: 560px; border: none; }
.article .table-scroll:focus-visible { outline: 2px solid var(--indigo); outline-offset: 2px; }
"""

MARK = ('<div class="table-scroll" tabindex="0" role="region" '
        'aria-label="Table, scrolls horizontally">')

wrapped, skipped = 0, 0
for path in sorted(glob.glob("blog/*.html") + glob.glob("docs/*.html") + glob.glob("*.html")):
    html = open(path).read()
    if "<table" not in html:
        continue
    if "table-scroll" in html:
        skipped += 1
        continue
    count = len(re.findall(r"<table\b.*?</table>", html, flags=re.S))
    html = re.sub(r"<table\b.*?</table>", lambda m: MARK + "\n" + m.group(0) + "\n</div>",
                  html, flags=re.S)
    open(path, "w").write(html)
    wrapped += count
    print(f"    {path}: {count} table(s)")

print(f"  wrapped {wrapped} table(s); {skipped} page(s) already done")

css_path = "assets/style.css"
s = open(css_path).read()
if ".table-scroll" in s:
    print("  style.css already carries the table styles")
else:
    open(css_path, "w").write(s + CSS)
    print("  style.css: table scroll styles appended")
