#!/usr/bin/env python3
"""Render a per-page social card instead of shipping one image for all fifty.

Every page on the site declared the same og:image. Sharing any post into Slack
or X produced an identical card with no title on it, so the link carried none
of the thing that would make someone click it. This renders one card per page
from the page's own h1 and category, in the site's own type and colour.

Design is deliberately flat: no gradient mesh, no stock abstraction. A hairline
rule, the category in the accent, the headline at the largest size that fits,
and the wordmark. It has to survive being shown at 250px wide in a timeline,
which is the only size that matters.

Chrome renders it at 1200x630 and screenshots. Requires Chrome; skips with a
clear message if absent rather than silently shipping the shared cover.
"""

import html as _h
import json
import os
import pathlib
import re
import struct
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = pathlib.Path("assets/og")
W, H = 1200, 630

# Pages whose card is the brand cover, not a headline card.
# index keeps the brand cover; 404 is never deliberately shared and carries
# no og tags to point at a card.
COVER = {"index.html", "404.html"}

TPL = """<!doctype html><meta charset=utf-8>
<style>
@font-face {{ font-family: Inter; src: url({font}) format("woff2"); font-weight: 400 800; font-display: block; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:1200px; height:630px; }}
body {{
  font-family: Inter, -apple-system, "Segoe UI", Roboto, sans-serif;
  background:#0d1117; color:#fff;
  padding:72px 80px; display:flex; flex-direction:column; justify-content:space-between;
  -webkit-font-smoothing:antialiased;
}}
.top {{ display:flex; align-items:center; gap:14px; }}
.mark {{ width:30px; height:30px; }}
.name {{ font-size:25px; font-weight:650; letter-spacing:-0.015em; }}
.cat {{
  margin-left:auto; font-size:19px; font-weight:600; color:#3ec9e8;
  letter-spacing:0.055em; text-transform:uppercase;
}}
h1 {{
  font-size:{size}px; line-height:1.11; font-weight:680; letter-spacing:-0.028em;
  max-width:19ch; text-wrap:balance;
}}
.foot {{ display:flex; align-items:center; gap:18px; padding-top:26px;
         border-top:1px solid rgba(255,255,255,0.14); }}
.foot span {{ font-size:20px; color:#9aa3af; letter-spacing:-0.005em; }}
.dot {{ width:5px; height:5px; border-radius:50%; background:#3ec9e8; flex:none; }}
</style>
<div class=top>
  <svg class=mark viewBox="0 0 32 32" fill="none" aria-hidden="true">
    <rect x="1.4" y="1.4" width="29.2" height="29.2" rx="8.4"
          stroke="#3ec9e8" stroke-width="2.4"/>
    <path d="M10.6 22.4V9.6h6.2a4.1 4.1 0 0 1 0 8.2h-6.2M17 17.8l4.8 4.6"
          stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
  <div class=name>Runix</div>
  <div class=cat>{cat}</div>
</div>
<h1>{title}</h1>
<div class=foot><div class=dot></div><span>{foot}</span></div>
"""


def _text(p):
    return re.sub(r"\s+", " ", _h.unescape(re.sub(r"<[^>]+>", "", p))).strip()


def card_fields(path, doc):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", doc, re.S)
    title = _text(m.group(1)) if m else ""
    c = re.search(r'<span class="cat">([^<]*)</span>', doc)
    cat = _text(c.group(1)) if c else ""
    if not cat:
        cat = "Docs" if path.startswith("docs/") else "Runix"
    foot = "runixcloud.io"
    if path.startswith("blog/") and path != "blog/index.html":
        d = re.search(r'<span>((?:January|February|March|April|May|June|July|'
                      r'August|September|October|November|December) \d+, \d{4})</span>', doc)
        if d:
            foot = f"runixcloud.io · {d.group(1)}"
    return title, cat, foot


def size_for(title):
    n = len(title)
    return 78 if n <= 30 else 70 if n <= 48 else 62 if n <= 70 else 54


def render(jobs, font_uri):
    """One Chrome invocation per card; screenshot the 1200x630 viewport."""
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for path, out, title, cat, foot in jobs:
        doc = TPL.format(font=font_uri, size=size_for(title),
                         cat=_h.escape(cat), title=_h.escape(title), foot=_h.escape(foot))
        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
            f.write(doc)
            src = f.name
        try:
            subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                            f"--window-size={W},{H}", "--screenshot=" + str(out),
                            "--virtual-time-budget=2500", "file://" + src],
                           capture_output=True, timeout=60)
        finally:
            os.unlink(src)
        if not out.exists():
            print(f"  !! chrome produced nothing for {path}")
            continue
        d = out.read_bytes()
        w, h = struct.unpack(">II", d[16:24])
        if (w, h) != (W, H):
            print(f"  !! {out} is {w}x{h}, expected {W}x{H}")
            continue
        made.append((path, out, len(d)))
    return made


def check_fit(jobs, font_uri):
    """Measure every card in one Chrome run and report any that overflow.

    The size ladder keys off character count, but "Wm" and "il" are not the
    same width, so a count-based ladder can be wrong for a specific title.
    This stacks all the cards in one document, lets Chrome lay them out, and
    reads back the real gap between the headline and its neighbours.

    The first version of this measured every card at one font size, because
    the size lives in the shared <style> block and was only rendered once.
    Every card came back with an identical gap of 0 -- a gate that always
    fails is as useless as one that never does. Each card now carries its own
    size rule keyed by id.
    """
    css = TPL.format(font=font_uri, size=70, cat="", title="", foot="")
    css = css.split("<style>", 1)[1].split("</style>", 1)[0]
    css = css.replace("html,body { width:1200px; height:630px; }", "")
    css = css.replace("body {", ".card {")
    per = "\n".join(f"#c{i} h1{{font-size:{size_for(t)}px}}"
                     for i, (_p, _o, t, _c, _f) in enumerate(jobs))
    cards = []
    for i, (path, _out, title, cat, foot) in enumerate(jobs):
        inner = TPL.format(font=font_uri, size=size_for(title), cat=_h.escape(cat),
                           title=_h.escape(title), foot=_h.escape(foot))
        inner = inner.split("</style>", 1)[1]
        cards.append(f'<div class="card" id="c{i}" data-path="{_h.escape(path)}">{inner}</div>')

    doc = ("<!doctype html><meta charset=utf-8><style>" + css +
           "\n.card{width:1200px;height:630px;position:relative}\n" + per +
           "</style>" + "".join(cards) + """<script>
for (const c of document.querySelectorAll('.card')) {
  const h = c.querySelector('h1').getBoundingClientRect();
  const f = c.querySelector('.foot').getBoundingClientRect();
  const t = c.querySelector('.top').getBoundingClientRect();
  c.setAttribute('data-gap', Math.round(Math.min(f.top - h.bottom, h.top - t.bottom)));
  const el = c.querySelector('h1');
  // The box is capped at 19ch, so its width can never exceed the column --
  // measuring it was a gate that could not fail. Measure the overflow: a
  // single word longer than the column is the only way text escapes.
  c.setAttribute('data-wide', Math.max(0, el.scrollWidth - el.clientWidth));
  c.setAttribute('data-size', Math.round(parseFloat(getComputedStyle(c.querySelector('h1')).fontSize)));
}
</script>""")
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(doc)
        src = f.name
    try:
        r = subprocess.run([CHROME, "--headless", "--disable-gpu", "--dump-dom",
                            f"--window-size={W},{H}", "--virtual-time-budget=4000",
                            "file://" + src], capture_output=True, text=True, timeout=180)
    finally:
        os.unlink(src)

    rows = re.findall(r'data-path="([^"]+)" data-gap="(-?\d+)" data-wide="(\d+)" data-size="(\d+)"',
                      r.stdout)
    if os.environ.get("OG_DEBUG"):
        for path, gap, wide, size in rows:
            print(f"    gap {gap:>4}px  overflow {wide:>3}px  size {size}px  {path}")
    # A measurement where every card agrees exactly is a broken measurement,
    # not fifty identical cards.
    if len({r[1] for r in rows}) == 1 and len(rows) > 3:
        return len(rows), ["every card measured identically -- the measurement is not reading per-card layout"]
    bad = []
    for path, gap, wide, _size in rows:
        if int(gap) < 12:
            bad.append(f"{path}: {gap}px between the headline and its neighbours")
        if int(wide) > 0:
            bad.append(f"{path}: headline overflows its column by {wide}px (unbreakable word)")
    return len(rows), bad


def main():
    if not os.path.exists(CHROME):
        print("  Chrome not found -- cards not regenerated, pages keep their current og:image")
        return 0
    # The site loads Inter as a separate woff2, not a data URI -- the first
    # version of this script looked for a data URI, found none, and rendered
    # every card in Helvetica without saying so. Read the actual file, and
    # refuse to render rather than ship fifty cards in the wrong typeface.
    import base64
    fb = pathlib.Path("assets/fonts/inter-latin.woff2")
    if not fb.exists():
        print(f"  {fb} missing -- refusing to render cards in a fallback face")
        return 1
    font_uri = "data:font/woff2;base64," + base64.b64encode(fb.read_bytes()).decode()

    pages = sorted(set(str(p) for p in pathlib.Path(".").glob("*.html"))
                   | set(str(p) for p in pathlib.Path("blog").glob("*.html"))
                   | set(str(p) for p in pathlib.Path("docs").glob("*.html")))
    jobs = []
    for path in pages:
        if path in COVER:
            continue
        doc = pathlib.Path(path).read_text()
        title, cat, foot = card_fields(path, doc)
        if not title:
            continue
        slug = path.replace("/", "-").replace(".html", "")
        jobs.append((path, OUT / f"{slug}.png", title, cat, foot))

    seen, bad = check_fit(jobs, font_uri)
    if seen != len(jobs):
        print(f"  !! measured {seen} of {len(jobs)} cards -- not trusting this run")
        return 1
    if bad:
        for b in bad:
            print(f"  ✗ {b}")
        return 1
    print(f"  {seen} cards measured in Chrome, all fit")

    made = render(jobs, font_uri)
    total = sum(n for _, _, n in made)
    print(f"  rendered {len(made)} cards, {total // 1024}KB total, "
          f"largest {max((n for _,_,n in made), default=0) // 1024}KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
