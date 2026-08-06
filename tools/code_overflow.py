#!/usr/bin/env python3
"""Find code samples that are cut off at desktop width.

The homepage sample -- the most prominent element on the most important page --
had a comment line 35px wider than its container. overflow-x is auto so it can
be scrolled, but macOS overlay scrollbars are invisible until you scroll, so a
reader just sees a sentence that stops mid-word. Nothing indicated there was
more to see.

At 1440px there is room; a sample that does not fit is a line we wrote too
long, not a layout constraint. On a phone a curl command genuinely cannot fit
and horizontal scroll is the right answer, so this only measures desktop.
"""
import os
import pathlib
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
WIDTH = 1440
PROBE = "__code_overflow_probe.html"

SCRIPT = """<script>
window.addEventListener('load', () => {
  document.querySelectorAll('pre').forEach((p, i) => {
    if (p.scrollWidth > p.clientWidth + 1)
      p.setAttribute('data-cut', `${i}:${p.scrollWidth - p.clientWidth}`);
  });
});
</script></body>"""


def main():
    if not os.path.exists(CHROME):
        print("  Chrome not found -- cannot measure code overflow")
        return 0
    pages = sorted(set(str(p) for p in [_p for _p in pathlib.Path(".").glob("*.html") if not _p.name.startswith("_")])
                   | set(str(p) for p in [_p for _p in pathlib.Path("blog").glob("*.html") if not _p.name.startswith("_")])
                   | set(str(p) for p in [_p for _p in pathlib.Path("docs").glob("*.html") if not _p.name.startswith("_")]))
    bad, checked = [], 0
    probe = pathlib.Path(PROBE)
    for page in pages:
        doc = pathlib.Path(page).read_text()
        if "<pre" not in doc:
            continue
        checked += 1
        # The probe lives in the site root so relative asset paths resolve.
        probe.write_text(doc.replace("</body>", SCRIPT))
        try:
            r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                                f"--window-size={WIDTH},1400", "--virtual-time-budget=5000",
                                "--dump-dom", f"file://{os.getcwd()}/{PROBE}"],
                               capture_output=True, text=True, timeout=90)
        finally:
            probe.unlink(missing_ok=True)
        for m in re.findall(r'data-cut="(\d+):(\d+)"', r.stdout):
            bad.append((page, int(m[0]), int(m[1])))
    for page, idx, px in bad:
        print(f"  ✗ {page}: code sample #{idx + 1} is cut off by {px}px at {WIDTH}px wide")
    print(f"  measured {checked} page(s) with code samples at {WIDTH}px"
          f" -- {len(bad)} cut off")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
