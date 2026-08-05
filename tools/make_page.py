#!/usr/bin/env python3
"""Build a new content page from the site's existing chrome.

Copying an existing page by hand is how nav links drift apart — this takes the
head, header and footer from a real page so a new one cannot fall out of sync,
and only fills in what is actually different: the metadata, the hero and the
body.

Used as a library by the scripts that add pages:

    from make_page import render
    render(slug="faq", title="…", description="…", badge="…", h1="…",
           lede="…", body="<h2>…</h2><p>…</p>", schema=[...])
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "terms.html")
SITE = "https://runixcloud.io"


def _chrome():
    """Pull the reusable pieces out of a page that already renders correctly."""
    html = open(TEMPLATE).read()
    head_open = html.index("<head>") + len("<head>")
    head = html[head_open:html.index("</head>")]
    # Drop whole script blocks first — filtering line by line would leave the
    # JSON body and its closing tag behind, and an orphaned </script> in the
    # head ends up rendered as visible text at the top of the page.
    head = re.sub(r"<script type=\"application/ld\+json\">.*?</script>", "", head, flags=re.S)
    # Keep the analytics tag, fonts, stylesheet and icons; drop page-specific meta.
    keep = []
    for line in head.splitlines():
        if re.search(r'<title>|name="description"|rel="canonical"|property="og:|name="twitter:', line):
            continue
        keep.append(line)
    head_common = "\n".join(l for l in keep if l.strip())
    header = html[html.index("<header"):html.index("</header>") + len("</header>")]
    footer = html[html.index("<footer"):html.index("</footer>") + len("</footer>")]
    return head_common, header, footer


def render(slug, title, description, badge, h1, lede, body, schema=(), out=None,
           force=False):
    head_common, header, footer = _chrome()
    url = f"{SITE}/{slug}"
    blocks = "".join(
        '<script type="application/ld+json">\n'
        + json.dumps(b, ensure_ascii=False, indent=2)
        + "\n</script>\n"
        for b in schema
    )
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_common}
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Runix">
<meta property="og:locale" content="en_US">
<meta property="og:image" content="{SITE}/assets/og-cover.png?v={_cover_version()}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:title" content="{title}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}/assets/og-cover.png?v={_cover_version()}">
{blocks}</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{header}

<div class="page-hero">
  <div class="container">
    <span class="badge">{badge}</span>
    <h1>{h1}</h1>
    <p>{lede}</p>
  </div>
</div>

<main id="main">
<article class="article">
{body}
</article>
</main>

{footer}

</body>
</html>
"""
    path = os.path.join(ROOT, out or f"{slug}.html")
    # This module builds a page; it does not maintain one. Pages get edited by
    # later passes — SEO metadata appended, copy tightened, schema regenerated —
    # and re-running the builder would silently revert all of it. It did:
    # re-running add_glossary.py restored a description that had been shortened
    # to fit search results and an og:image version that was nine bumps stale.
    # So refuse to clobber, and say what to do instead.
    if os.path.exists(path) and not force:
        print(f"  {path} already exists — not overwriting. "
              f"Edit the page, or pass force=True if you really mean to rebuild it.")
        return path
    open(path, "w").write(page)
    return path


def _cover_version():
    """Current ?v= on the share image, read from a page rather than hardcoded.

    This was a literal 3 while the live pages were on 12. Any page built by this
    module would have shipped pointing at a stale version of the share image —
    invisible until someone shared the link. bump_assets.py owns the number, so
    ask the pages what it is.
    """
    for candidate in ("index.html", "faq.html"):
        path = os.path.join(ROOT, candidate)
        if os.path.exists(path):
            m = re.search(r"og-cover\.png\?v=(\d+)", open(path).read())
            if m:
                return m.group(1)
    return "1"


def crumbs(name, url):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": name, "item": url},
        ],
    }
