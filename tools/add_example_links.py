#!/usr/bin/env python3
"""Link each product page that has something to show to its examples on example.runixcloud.io.

The examples site is behind an access key the team hands out, so the link says so instead of looking like a
public demo. Only products with real material there get a link: Router (capability walkthrough, console),
FS (quick-learn walkthrough), Comic (a finished test episode) and Data (an embodied-robotics data platform).
Code, Models and Pipeline have nothing there yet and get nothing.

The link sits on its own line under the hero buttons (a hero-note, so no stylesheet change and no asset bump),
so the two buttons keep their order and width.
Idempotent: the block carries markers and is replaced on every run. Run from the site root, after
product_template.py.
"""
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

BASE = "https://example.runixcloud.io"
PAGES = {
    "router.html": ("router", "See the gateway walkthrough and console"),
    "fs.html": ("fs", "See the Runix FS walkthrough"),
    "comic.html": ("comic", "Watch an episode made end to end"),
    "data.html": ("embedded", "See the embodied-robotics data platform"),
}
START, END = "<!-- example-link -->", "<!-- /example-link -->"


def block(slug, label):
    return (f'{START}<p class="hero-note"><a href="{BASE}/{slug}/" rel="noopener">{label} &rarr;</a>'
            f' On our examples site; the access key comes from the Runix team.</p>{END}')


for name, (slug, label) in PAGES.items():
    path = pathlib.Path(name)
    doc = path.read_text(encoding="utf-8")
    doc = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?\s*", "", doc, flags=re.S)
    hero = doc.index('<section class="split-hero" id="overview">')
    actions = doc.index('<div class="actions">', hero)
    end = doc.index("</div>", actions) + len("</div>")
    indent = re.search(r"\n([ \t]*)<div class=\"actions\">", doc[hero:actions + 30]).group(1)
    doc = doc[:end] + "\n" + indent + block(slug, label) + doc[end:]
    path.write_text(doc, encoding="utf-8")
    print(f"{name}: example link -> {BASE}/{slug}/")
