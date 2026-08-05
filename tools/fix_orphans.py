#!/usr/bin/env python3
"""Link the pages nothing links to.

Measured first, over body links only — navigation and footer appear on every
page, so counting them makes every page look well-connected and hides the
problem. Of 44 pages: /blog/introducing-runix and /careers had zero inbound
body links, /faq and /glossary had one each.

Each link added below is one a reader would actually follow from where it sits.
Anywhere a link would only be there for the crawler, none is added — the point
is to stop wasting pages, not to raise a number.

Idempotent. Run from the site root.
"""
import os
import pathlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

EDITS = [
    # /about is the company page; the announcement post is the company story,
    # and the careers page is what a reader who liked the page looks for next.
    ("about.html",
     "<p>Runix AI Inc is a company incorporated in Wyoming, United States. It builds and\n"
     "        operates infrastructure for teams putting AI into production, and sells it directly —\n"
     "        there is no reseller between you and the people who run the service.</p>",
     "<p>Runix AI Inc is a company incorporated in Wyoming, United States. It builds and\n"
     "        operates infrastructure for teams putting AI into production, and sells it directly —\n"
     "        there is no reseller between you and the people who run the service. The longer\n"
     "        version of why it exists is in <a href=\"/blog/introducing-runix\">the announcement\n"
     "        post</a>.</p>"),

    ("about.html",
     "<li><strong>Long-term over short-term.</strong> We would rather keep a customer for years than win a quarter.</li>",
     "<li><strong>Long-term over short-term.</strong> We would rather keep a customer for years than win a quarter.</li>\n"
     "          <li><strong>Written down, not remembered.</strong> Decisions live in documents rather than in "
     "someone's head — which is also what <a href=\"/careers\">working here</a> is like.</li>"),

    # The docs hub is where a reader first hits a term they do not know, and
    # the first place they wonder whether a question is answered elsewhere.
    ("docs/index.html",
     '<div class="section-head center"><h2 id="product-guides">Product guides</h2></div>',
     '<div class="section-head center"><h2 id="product-guides">Product guides</h2>\n'
     '      <p>Unfamiliar terms are defined in the <a href="/glossary">glossary</a>; the questions '
     'buyers ask before reading any of this are answered on the <a href="/faq">FAQ</a>.</p></div>'),
]

changed = 0
for path, old, new in EDITS:
    if old == new:
        continue
    p = pathlib.Path(path)
    html = p.read_text()
    if new.split(">")[1][:30] in html and old not in html:
        continue  # already applied
    if old not in html:
        print(f"  ! {path}: anchor not found, skipped")
        continue
    p.write_text(html.replace(old, new, 1))
    changed += 1
    print(f"  {path}: linked")

# The blog index is reachable from the nav on every page but from no body copy,
# so no page ever passes a reader to it in context.
p = pathlib.Path("index.html")
html = p.read_text()
marker = 'href="/blog/"'
if html.count(marker) <= 1:  # nav only
    print("  ! index.html: no body link to /blog — add one where it reads naturally")

print(f"  {changed} edit(s) applied")
