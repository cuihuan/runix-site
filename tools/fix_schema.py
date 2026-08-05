#!/usr/bin/env python3
"""Consolidate structured data into one entity graph.

Three problems this fixes, all found by auditing the live markup:

1. The site declared the company 51 separate times — every article's publisher
   and author, every product page's provider — as its own inline Organization
   object. To a parser those are 51 unrelated entities. One canonical
   Organization with an @id, referenced everywhere else, is one entity.

2. Ten pages carried no structured data at all, including /blog/ and every
   legal page.

3. Product breadcrumbs pointed their middle level at /#products, a fragment on
   another page rather than a real breadcrumb step.

Parses and re-serialises the JSON rather than pattern-matching it, so a block
that would come out malformed fails loudly here instead of silently on the
site. Idempotent. Run from the site root.
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
ORG_ID = f"{SITE}/#org"
ORG_REF = {"@id": ORG_ID}
BLOCK_RE = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)

changes = []


def canonical_of(html, path):
    m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    if m:
        return m.group(1)
    slug = path[:-5]
    if slug.endswith("/index"):
        return f"{SITE}/{slug[:-6]}"
    return SITE + "/" if slug == "index" else f"{SITE}/{slug}"


def title_of(html):
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return m.group(1).strip().replace("&amp;", "&") if m else ""


def description_of(html):
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    return m.group(1) if m else ""


def collapse_org(node, path):
    """Replace every inline copy of the company with a reference to the one."""
    if isinstance(node, list):
        return [collapse_org(n, path) for n in node]
    if not isinstance(node, dict):
        return node
    if (
        node.get("@type") == "Organization"
        and node.get("name") in ("Runix AI Inc", "Runix")
        and "@id" not in node
        and path != "index.html"          # the canonical definition lives on the homepage
    ):
        changes.append("org-ref")
        return dict(ORG_REF)
    return {k: collapse_org(v, path) for k, v in node.items()}


def fix_breadcrumb(node):
    """Drop the fragment-only middle step and renumber what is left."""
    if node.get("@type") != "BreadcrumbList":
        return node
    items = [
        it for it in node.get("itemListElement", [])
        if "#" not in str(it.get("item", ""))
    ]
    if len(items) != len(node.get("itemListElement", [])):
        changes.append("breadcrumb")
    for i, it in enumerate(items, start=1):
        it["position"] = i
    node["itemListElement"] = items
    return node


# --- pass 1: rewrite the blocks that already exist ------------------------
for path in sorted(glob.glob("*.html") + glob.glob("docs/*.html") + glob.glob("blog/*.html")):
    html = open(path).read()
    if not BLOCK_RE.search(html):
        continue

    def rewrite(match):
        data = json.loads(match.group(2))
        if data.get("@type") == "Organization" and "@id" not in data:
            data = {"@context": data.pop("@context"), "@type": "Organization", "@id": ORG_ID, **data}
            changes.append("org-id")
        data = collapse_org(data, path)
        if isinstance(data, dict):
            data = fix_breadcrumb(data)
        return match.group(1) + "\n" + json.dumps(data, ensure_ascii=False, indent=2) + "\n" + match.group(3)

    new = BLOCK_RE.sub(rewrite, html)
    if new != html:
        open(path, "w").write(new)

# --- pass 2: give the bare pages a graph ----------------------------------
BARE = {
    "about.html": "AboutPage",
    "security.html": "WebPage",
    "careers.html": "WebPage",
    "terms.html": "WebPage",
    "privacy.html": "WebPage",
    "refund.html": "WebPage",
    "cancellation.html": "WebPage",
    "acceptable-use.html": "WebPage",
}

def crumbs(name, url):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": url},
        ],
    }


def inject(path, blocks):
    html = open(path).read()
    payload = "".join(
        '<script type="application/ld+json">\n'
        + json.dumps(b, ensure_ascii=False, indent=2)
        + "\n</script>\n"
        for b in blocks
    )
    open(path, "w").write(html.replace("</head>", payload + "</head>", 1))
    changes.append("page-schema")


for path, kind in BARE.items():
    html = open(path).read()
    if BLOCK_RE.search(html):
        continue
    url = canonical_of(html, path)
    short = title_of(html).split("—")[0].strip()
    inject(path, [
        {
            "@context": "https://schema.org",
            "@type": kind,
            "name": short,
            "description": description_of(html),
            "url": url,
            "isPartOf": {"@id": f"{SITE}/#website"},
            "publisher": ORG_REF,
        },
        crumbs(short, url),
    ])

# --- pass 3: the blog index lists what it links to -------------------------
blog_index = "blog/index.html"
if not BLOCK_RE.search(open(blog_index).read()):
    posts = []
    for post in sorted(glob.glob("blog/*.html")):
        if post == blog_index:
            continue
        src = open(post).read()
        for block in BLOCK_RE.findall(src):
            data = json.loads(block[1])
            if data.get("@type") == "Article":
                posts.append({
                    "url": canonical_of(src, post),
                    "name": data.get("headline", title_of(src)),
                    "date": data.get("datePublished", ""),
                })
                break
    posts.sort(key=lambda p: p["date"], reverse=True)
    html = open(blog_index).read()
    url = canonical_of(html, blog_index)
    inject(blog_index, [
        {
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": "Runix Blog",
            "description": description_of(html),
            "url": url,
            "publisher": ORG_REF,
            "blogPost": [
                {"@type": "BlogPosting", "headline": p["name"], "url": p["url"], "datePublished": p["date"]}
                for p in posts
            ],
        },
        crumbs("Blog", url),
    ])
    print(f"  blog index lists {len(posts)} posts")

from collections import Counter
print("  " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(changes).items())))
