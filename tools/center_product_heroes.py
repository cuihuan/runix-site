#!/usr/bin/env python3
"""Make each page's hero agree with the alignment of its own body.

The design system had a contradiction that showed up the moment the pages were
rendered rather than read: the product and pricing pages centre every section
heading below the fold, but open with a left-aligned hero. At 1280px that
leaves the right half of the first screen empty and then snaps the eye back to
the middle for the first real heading.

The rule applied here is that the hero follows the body:

  centred body (product and pricing pages, every section-head is .center)
      -> centred hero
  left-aligned body (about, careers, and every .article page: legal, docs,
      blog, FAQ, glossary)
      -> hero stays left, which is correct for a page you read top to bottom

Also trims the run-up to the first section. On /pricing the first plan card
started 591px down a 900px viewport, two thirds of the fold spent before the
thing the page exists to show.

Idempotent. Run from the site root.
"""
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# Pages whose every section-head is centred. index.html is excluded: it uses
# the split .hero with the code panel, which is a different component.
CENTRED = ["router.html", "pricing.html", "pipeline.html", "code.html",
           "comic.html", "code-plans.html"]

CSS = """
/* A page's hero follows the alignment of its own body: centred on the product
   and pricing pages, left on anything you read as an article. */
.page-hero.center { text-align: center; }
.page-hero.center p { margin-inline: auto; max-width: 680px; }
.page-hero.center .actions { justify-content: center; }

/* The hero already separates itself with a rule and a colour change; the first
   section does not need a full section's worth of padding on top of that. */
main > .section:first-child { padding-top: 64px; }
/* The hero glow was positioned for left-aligned text; centred heroes need it
   centred too, or the page lights up on one side of its own headline. */
.page-hero.center {
  background: radial-gradient(760px 320px at 50% 0%, rgba(91, 140, 255, 0.14), transparent 65%);
}
/* Stops the lede stranding a single word on its own last line. */
.page-hero p { text-wrap: pretty; }
"""

changed = []
for name in CENTRED:
    page = pathlib.Path(name)
    html = page.read_text()
    if 'class="page-hero center"' in html:
        continue
    assert '<div class="page-hero">' in html, name
    page.write_text(html.replace('<div class="page-hero">',
                                 '<div class="page-hero center">', 1))
    changed.append(name)

print(f"  centred the hero on {len(changed)} page(s): {', '.join(changed) or 'none'}")

# Anything not in the list must keep a left hero — assert it, so a page added
# later cannot silently inherit the wrong one.
for path in pathlib.Path(".").glob("*.html"):
    if path.name not in CENTRED and 'class="page-hero center"' in path.read_text():
        raise SystemExit(f"  {path.name} is centred but is not in the list")

css = pathlib.Path("assets/style.css")
s = css.read_text()
if ".page-hero.center" in s:
    print("  style.css already carries the centred variant")
else:
    css.write_text(s + CSS)
    print("  style.css: centred hero variant added")
