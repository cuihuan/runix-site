#!/usr/bin/env python3
"""Rebuild the blog index and the blog half of the sitemap from whatever is published.

Posts live in blog/. Posts waiting for their turn live in scheduled/ and are
excluded from the deploy, so this script is the single place that decides what
the site says exists.

    python3 tools/build_blog_index.py
"""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://runixcloud.io"


def read_posts():
    posts = []
    for p in sorted((ROOT / "blog").glob("*.html")):
        if p.name == "index.html":
            continue
        s = p.read_text()
        meta = re.search(
            r'<div class="post-meta"><span class="cat">([^<]*)</span>'
            r"<span>([^<]*)</span><span>·</span><span>([^<]*)</span></div>", s)
        posts.append({
            "slug": p.stem,
            "cat": meta.group(1),
            "date": meta.group(2),
            "read": meta.group(3),
            "headline": re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S).group(1).strip(),
            "desc": re.search(r'<meta name="description" content="([^"]*)">', s).group(1),
            "iso": re.search(r'"datePublished": "([^"]*)"', s).group(1),
        })
    posts.sort(key=lambda x: (x["iso"], x["headline"]), reverse=True)
    return posts


# Links are the clean URLs the host actually serves. Writing "<slug>.html"
# costs a 308 on every card, and this generator runs on every publish — so it
# silently undid the site-wide clean-URL pass once already.
def write_index(posts):
    cards = [
        f"""      <div class="card">
        <div class="post-meta"><span class="cat">{p['cat']}</span><span>{p['date']}</span><span>·</span><span>{p['read']}</span></div>
        <h3><a href="/blog/{p['slug']}">{p['headline']}</a></h3>
        <p class="excerpt">{html.escape(p['desc'], quote=False)}</p>
        <a class="read-more" href="/blog/{p['slug']}">Read post →</a>
      </div>"""
        for p in posts
    ]
    idx = ROOT / "blog/index.html"
    s = idx.read_text()
    block = '<div class="blog-list">\n' + "\n".join(cards) + "\n    </div>"
    idx.write_text(re.sub(r'<div class="blog-list">.*?\n    </div>', block, s, count=1, flags=re.S))


def write_sitemap(posts):
    sm = ROOT / "sitemap.xml"
    t = sm.read_text()
    # drop every blog post entry, then re-add the published ones in order
    t = re.sub(r"\s*<url><loc>https://runixcloud\.io/blog/[^<]+</loc>.*?</url>", "", t)
    block = "".join(
        f'  <url><loc>{BASE}/blog/{p["slug"]}</loc><lastmod>{p["iso"]}</lastmod>'
        f"<priority>0.6</priority></url>\n" for p in posts)
    anchor = f'  <url><loc>{BASE}/terms</loc>'
    sm.write_text(t.replace(anchor, block + anchor, 1))


if __name__ == "__main__":
    posts = read_posts()
    write_index(posts)
    write_sitemap(posts)
    waiting = sorted(p.stem for p in (ROOT / "scheduled").glob("*.html")) if (ROOT / "scheduled").exists() else []
    print(f"published: {len(posts)}")
    for p in posts:
        print(f"  {p['iso']}  {p['slug']}")
    if waiting:
        print(f"waiting in scheduled/: {len(waiting)}")
        for w in waiting:
            print(f"  {w}")
