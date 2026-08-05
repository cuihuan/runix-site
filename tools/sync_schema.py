#!/usr/bin/env python3
"""Generate structured data from what the pages actually say.

Two gaps, found by listing every page's schema types side by side:

  * /pipeline shows a "Common questions" section with four answered questions
    and carries no FAQPage, while /router, /code and /comic all do. Rich
    results are the least of it — the schema is how an assistant knows the
    answer is on that page.
  * /pricing and /code-plans carry Service but no BreadcrumbList, which every
    other product page has.

The FAQ entries are read out of the rendered section rather than written here.
Hand-written schema drifts from the page the first time someone edits a
sentence, and a page whose markup answers a question differently from its
visible copy is worse than one with no markup at all.

Idempotent. Run from the site root.
"""
import html as htmllib
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"


def text_of(fragment):
    """Visible text of an HTML fragment, whitespace-normalised."""
    return " ".join(htmllib.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def faq_from_section(html, heading):
    """Read question/answer cards out of the section under `heading`."""
    start = html.find(f">{heading}</h2>")
    if start < 0:
        return []
    end = html.find("</section>", start)
    section = html[start:end]
    pairs = re.findall(r"<h3[^>]*>(.*?)</h3>\s*<p>(.*?)</p>", section, re.S)
    return [
        {
            "@type": "Question",
            "name": text_of(q),
            "acceptedAnswer": {"@type": "Answer", "text": text_of(a)},
        }
        for q, a in pairs
    ]


def crumbs(name, url):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": url},
        ],
    }


def inject(path, block):
    """Add a JSON-LD block before </head> if that @type is not already there."""
    p = pathlib.Path(path)
    doc = p.read_text()
    wanted = block["@type"]
    for existing in re.findall(r'<script type="application/ld\+json">(.*?)</script>', doc, re.S):
        try:
            if json.loads(existing).get("@type") == wanted:
                return False
        except Exception:
            pass
    tag = ('<script type="application/ld+json">\n'
           + json.dumps(block, ensure_ascii=False, indent=2)
           + "\n</script>\n")
    p.write_text(doc.replace("</head>", tag + "</head>", 1))
    return True


added = []

# Pages that show a question section. The heading text is the anchor; if a page
# renames its section this list must be updated, which is the point — silence
# would be worse.
FAQ_PAGES = [
    ("pipeline.html", "Common questions"),
    ("router.html", "Common questions"),
    ("code.html", "Common questions"),
    ("comic.html", "Common questions"),
    ("code-plans.html", "Common questions"),
    ("faq.html", None),        # whole page is the FAQ; handled by its own tool
    ("access.html", None),
]


def replace_faq(path, heading):
    """Rebuild the FAQPage block from the page's own visible question section."""
    p = pathlib.Path(path)
    doc = p.read_text()
    questions = faq_from_section(doc, heading)
    if not questions:
        return None
    block = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": questions}
    tag = ('<script type="application/ld+json">\n'
           + json.dumps(block, ensure_ascii=False, indent=2) + "\n</script>\n")

    existing = None
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>\n?', doc, re.S):
        try:
            if json.loads(m.group(1)).get("@type") == "FAQPage":
                existing = m
                break
        except Exception:
            pass
    if existing:
        if json.loads(existing.group(1)) == block:
            return 0
        doc = doc[:existing.start()] + tag + doc[existing.end():]
    else:
        doc = doc.replace("</head>", tag + "</head>", 1)
    p.write_text(doc)
    return len(questions)


for path, heading in FAQ_PAGES:
    if heading is None:
        continue
    n = replace_faq(path, heading)
    if n:
        added.append(f"{path} FAQPage rebuilt from the page ({n} questions)")
    elif n is None:
        print(f"  ! {path}: no '{heading}' section found")

# --- breadcrumbs the other product pages already have ----------------------
for path, name in (("pricing.html", "Pricing"), ("code-plans.html", "Coding plans")):
    if inject(path, crumbs(name, SITE + "/" + path[:-5])):
        added.append(f"{path} BreadcrumbList")

for a in added:
    print(f"  {a}")
if not added:
    print("  nothing to change")
print("  qa.py verifies every FAQPage string against the visible copy on every run")
