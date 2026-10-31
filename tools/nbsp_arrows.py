#!/usr/bin/env python3
"""Keep a link's trailing arrow on the same line as its last word (2026-10-31).

"Runix for engineering organisations →" wrapped on a phone with the arrow alone
on a line. The space before a trailing → / &rarr; becomes a no-break space, in
the pages and in the generators that write such links, so a rebuild keeps it.
Idempotent. Run from the site root.
"""
import glob
import pathlib
import re

ARROW = re.compile(r"(?<=\S) (&rarr;|→)(?=\s*</)")
GENERATORS = ["tools/build_blog_index.py", "tools/build_solutions.py", "tools/product_template.py"]


def main():
    changed = 0
    pages = glob.glob("*.html") + glob.glob("docs/*.html") + glob.glob("blog/*.html")
    for f in pages:
        if pathlib.Path(f).name.startswith("_"):
            continue
        p = pathlib.Path(f); t = p.read_text(encoding="utf-8")
        t2 = ARROW.sub(r"&nbsp;\1", t)
        if t2 != t:
            p.write_text(t2, encoding="utf-8"); changed += 1
    for f in GENERATORS:
        p = pathlib.Path(f); t = p.read_text(encoding="utf-8")
        t2 = "\n".join(ARROW.sub(r"&nbsp;\1", line) if "read-more" in line else line for line in t.split("\n"))
        if t2 != t:
            p.write_text(t2, encoding="utf-8"); changed += 1
    print(f"nbsp arrows: {changed} file(s) changed")


if __name__ == "__main__":
    main()
