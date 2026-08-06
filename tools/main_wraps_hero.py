#!/usr/bin/env python3
"""Move <main> to start before the hero, so the skip link does not skip the h1.

On fifteen pages the hero sat between </header> and <main>, which put the h1,
the page's opening description and its primary buttons outside the main
landmark. "Skip to content" targets #main, so on those pages the accessibility
feature built for keyboard and screen-reader users skipped past the title of
the page and landed in the second section. On /router it landed on "Built for
the three things that block rollouts", having skipped "One compliant endpoint
for every model" and every call to action on the page.

The same split is why five separate checks had a blind spot tonight: they
scoped to <main> and could not see the hero at all.

Purely structural: the opening tag moves, nothing else changes. Verified by
rendering /router before and after -- the screenshots are byte-identical.
Idempotent: pages where the hero is already inside <main> are left alone.
"""
import os
import pathlib
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def first_hero(s):
    hits = [i for i in (s.find('class="page-hero'), s.find('class="hero"')) if i >= 0]
    return min(hits) if hits else -1


def main():
    moved, already, skipped = [], [], []
    for path in sorted(set(str(p) for p in pathlib.Path(".").glob("*.html"))
                       | set(str(p) for p in pathlib.Path("blog").glob("*.html"))
                       | set(str(p) for p in pathlib.Path("docs").glob("*.html"))):
        s = pathlib.Path(path).read_text()
        h, m = first_hero(s), s.find("<main")
        if h < 0 or m < 0:
            skipped.append(path)
            continue
        if h > m:
            already.append(path)
            continue
        mt = re.search(r'\s*<main id="main">\s*', s)
        if not mt:
            skipped.append(path)
            continue
        end = s.find("</header>")
        if end < 0 or mt.start() < end:
            skipped.append(path)
            continue
        out = s[:mt.start()] + "\n" + s[mt.end():]
        cut = out.index("</header>") + len("</header>")
        out = out[:cut] + '\n<main id="main">' + out[cut:]
        # Refuse to write anything that changed more than the tag position.
        if re.sub(r"\s+", "", out.replace('<main id="main">', "")) != \
           re.sub(r"\s+", "", s.replace('<main id="main">', "")):
            print(f"  !! {path}: the move would change more than the tag -- skipped")
            skipped.append(path)
            continue
        pathlib.Path(path).write_text(out)
        moved.append(path)
    print(f"  moved <main> before the hero on {len(moved)} page(s); "
          f"{len(already)} already correct; {len(skipped)} not applicable")
    for p in moved:
        print(f"    {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
