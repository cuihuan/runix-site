#!/usr/bin/env python3
"""Define the Organization and WebSite nodes on every page, not only the home page.

Every post, product page and guide points its author, publisher, provider or
isPartOf at https://runixcloud.io/#org or #website by @id. Those nodes were
defined on the home page alone, and a structured-data parser reads one page at
a time, so on 75 of 80 pages the author and publisher were entities with no
name (found by the 2026-10-07 SEO audit). This writes one compact @graph with
both nodes into the head of every page that references them and does not
define them, and a preconnect hint for the analytics origin every page loads.

Idempotent: a page that already defines the node is left alone. Run from the
site root; covers drafts in scheduled/ too, since they become pages.
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SITE = "https://runixcloud.io"

GRAPH = {
    "@context": "https://schema.org",
    "@graph": [
        {"@type": "Organization", "@id": f"{SITE}/#org", "name": "Runix AI Inc",
         "alternateName": "Runix Lab", "url": f"{SITE}/", "logo": f"{SITE}/assets/logo.svg"},
        {"@type": "WebSite", "@id": f"{SITE}/#website", "name": "Runix Lab", "url": f"{SITE}/",
         "publisher": {"@id": f"{SITE}/#org"}},
    ],
}
PRECONNECT = '<link rel="preconnect" href="https://www.googletagmanager.com">'
MARK = '"@id": "https://runixcloud.io/#org"'


def defines_org(head):
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', head, re.S):
        try:
            d = json.loads(block)
        except Exception:
            continue
        nodes = d.get("@graph", [d]) if isinstance(d, dict) else []
        for n in nodes:
            if isinstance(n, dict) and n.get("@type") == "Organization" and n.get("@id") == f"{SITE}/#org":
                return True
    return False


pages = sorted(p for p in glob.glob("*.html") + glob.glob("docs/*.html") + glob.glob("blog/*.html") + glob.glob("scheduled/*.html")
               if not os.path.basename(p).startswith("_"))
changed = 0
for page in pages:
    s = open(page, encoding="utf-8").read()
    if "</head>" not in s:
        continue
    head = s[: s.index("</head>")]
    orig = s
    block = '<script type="application/ld+json">\n' + json.dumps(GRAPH, ensure_ascii=False, indent=2) + "\n</script>\n"
    # The graph goes directly after the page's own blocks, so every builder
    # that replaces "the JSON-LD blocks" as one span (first to last) sees a
    # contiguous run and never swallows the meta tags between. A graph that
    # sits anywhere else (the first version appended it before </head>, and
    # three builders then cut everything from their first block to it) is
    # moved. The builders themselves skip the graph block when they render.
    if '"@graph"' in head:
        s = s.replace(block, "", 1)
        head = s[: s.index("</head>")]
    if ("#org" in head or "#website" in head) and not defines_org(head):
        own = list(re.finditer(r'<script type="application/ld\+json">.*?</script>\n?', head, re.S))
        if own:
            at = own[-1].end()
            s = s[:at] + block + s[at:]
        else:
            s = s.replace("</head>", block + "</head>", 1)
    if PRECONNECT not in s[: s.index("</head>")]:
        s = re.sub(r'(<script async src="https://www\.googletagmanager\.com/gtag/js[^>]*></script>)',
                   PRECONNECT + r"\n\1", s, count=1)
    if s != orig:
        open(page, "w", encoding="utf-8").write(s)
        changed += 1
print(f"  org graph and preconnect: {changed} of {len(pages)} page(s) changed")
