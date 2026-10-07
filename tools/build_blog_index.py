#!/usr/bin/env python3
"""Rebuild the blog index, the home page's writing block and the blog half of
the sitemap from whatever is published.

Posts live in blog/. Posts waiting for their turn live in scheduled/ and are
excluded from the deploy, so this script is the single place that decides what
the site says exists.

2026-10-07: the index groups posts by the layer of the stack they are about,
read from each post's own <meta property="article:tag"> (tools/tag_posts.py
tagged the posts written before the tag existed; tools/write_post.py writes it
for every post since). A flat list of fifty-odd posts was unbrowsable; the
layers are the site's one map, so the blog uses the same one. The home page's
writing section is drawn from the same groups, between its <!--writing-->
markers, so the home page never advertises three posts out of sixty.

    python3 tools/build_blog_index.py
"""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://runixcloud.io"

# (tag as written in the posts, section id, heading, the layer line, hub link)
GROUPS = [
    ("Agents", "agents", "Agents", "Layer 05 &middot; domain agents and the harnesses that run them", "/agents"),
    ("Gateway", "gateway", "Gateway", "Layer 04 &middot; one way in to every model", "/router"),
    ("Models", "models", "Models", "Layer 03 &middot; open-weight models, tuned and served", "/models"),
    ("Data", "data", "Data", "Layer 02 &middot; domain data, cleaned for training and evaluation", "/data"),
    ("Infrastructure", "infrastructure", "Infrastructure", "Layer 01 &middot; storage that keeps GPUs fed", "/fs"),
    ("Company", "company", "Company", "Announcements, and why the stack is drawn the way it is", "/about"),
]
TAG_FALLBACK = {"Creators": "Agents", "Announcement": "Company"}


def read_posts():
    posts = []
    for p in sorted((ROOT / "blog").glob("*.html")):
        if p.name == "index.html":
            continue
        s = p.read_text()
        meta = re.search(
            r'<div class="post-meta"><span class="cat">([^<]*)</span>'
            r"<span>([^<]*)</span><span>·</span><span>([^<]*)</span></div>", s)
        tag = re.search(r'<meta property="article:tag" content="([^"]*)">', s)
        cat = meta.group(1)
        posts.append({
            "slug": p.stem,
            "cat": cat,
            "tag": tag.group(1) if tag else TAG_FALLBACK.get(cat, "Gateway"),
            "date": meta.group(2),
            "read": meta.group(3),
            "headline": re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S).group(1).strip(),
            "desc": re.search(r'<meta name="description" content="([^"]*)">', s).group(1),
            "iso": re.search(r'"datePublished": "([^"]*)"', s).group(1),
        })
    posts.sort(key=lambda x: (x["iso"], x["headline"]), reverse=True)
    return posts


def card(p):
    # The "Read post" link goes exactly where the headline above it already
    # goes; aria-hidden plus tabindex=-1 keeps the affordance visible and drops
    # the duplicate from the tab order and the screen reader's link list.
    return (f"""      <div class="card">
        <div class="post-meta"><span class="cat">{p['cat']}</span><span>{p['date']}</span><span>·</span><span>{p['read']}</span></div>
        <h3><a href="/blog/{p['slug']}">{p['headline']}</a></h3>
        <p class="excerpt">{html.escape(p['desc'], quote=False)}</p>
        <a class="read-more" href="/blog/{p['slug']}" aria-hidden="true" tabindex="-1">Read post →</a>
      </div>""")


def grouped(posts):
    by = {g[0]: [] for g in GROUPS}
    for p in posts:
        by.setdefault(p["tag"], []).append(p)
    return by


def write_index(posts):
    by = grouped(posts)
    chips, sections, n = [], [], 1
    for i, (tag, sid, heading, line, hub) in enumerate(GROUPS):
        items = by.get(tag, [])
        if not items:
            continue
        chips.append(f'<li><a class="pd-chip" href="#{sid}">{heading} <i>{len(items)}</i></a></li>')
        n += 1
        alt = " alt" if i % 2 == 0 else ""
        sections.append(f"""<section class="section{alt}">
  <div class="container">
    <div class="section-head center">
      <p class="sec-no">{n:02d} &middot; {heading}</p>
      <h2 id="{sid}">{heading}</h2>
      <p>{line}. {len(items)} post{'s' if len(items) != 1 else ''}, newest first. <a href="{hub}">{heading} on the stack</a>.</p>
    </div>
    <div class="blog-list">
{chr(10).join(card(p) for p in items)}
    </div>
  </div>
</section>""")
    idx = ROOT / "blog/index.html"
    s = idx.read_text()
    s = re.sub(r"<!--count-->.*?<!--/count-->", f"<!--count-->{len(posts)} posts<!--/count-->", s, count=1, flags=re.S)
    s = re.sub(r"<!--chips-->.*?<!--/chips-->",
               '<!--chips--><ul class="topic-chips" aria-label="Posts by layer">' + "".join(chips) + "</ul><!--/chips-->",
               s, count=1, flags=re.S)
    s = re.sub(r"<!--posts-->.*?<!--/posts-->", "<!--posts-->\n" + "\n\n".join(sections) + "\n<!--/posts-->",
               s, count=1, flags=re.S)
    s = write_blog_schema(s, posts)
    idx.write_text(s)
    write_home(posts)


def write_home(posts):
    """The home page's writing section: one card per layer, three newest posts each."""
    home = ROOT / "index.html"
    if not home.exists():
        return
    s = home.read_text()
    if "<!--writing-->" not in s:
        return
    by = grouped(posts)
    cards = []
    for tag, sid, heading, line, hub in GROUPS:
        items = by.get(tag, [])
        if not items:
            continue
        lis = "".join(f'\n          <li><a href="/blog/{p["slug"]}">{p["headline"]}</a></li>' for p in items[:3])
        cards.append(f"""      <div class="card wcard">
        <p class="card-layer">{line.split(' &middot; ')[0] if ' &middot; ' in line else 'Company'}</p>
        <h3>{heading}</h3>
        <ul class="wlist">{lis}
        </ul>
        <a class="read-more" href="/blog/#{sid}">All {len(items)} {heading} post{'s' if len(items) != 1 else ''} &rarr;</a>
      </div>""")
    block = '<!--writing-->\n    <div class="wgrid">\n' + "\n".join(cards) + "\n    </div>\n    <!--/writing-->"
    s = re.sub(r"<!--writing-->.*?<!--/writing-->", block, s, count=1, flags=re.S)
    home.write_text(s)


def write_blog_schema(s, posts):
    """The Blog JSON-LD lists every published post, like the cards do."""
    import json
    m = re.search(r'(<script type="application/ld\+json">\n?)(\s*\{.*?"@type": "Blog".*?\})(\n?</script>)', s, re.S)
    if not m:
        return s
    data = json.loads(m.group(2))
    data["blogPost"] = [
        {"@type": "BlogPosting", "headline": html.unescape(re.sub(r"<[^>]+>", "", p["headline"])),
         "url": f"{BASE}/blog/{p['slug']}", "datePublished": p["iso"]}
        for p in posts
    ]
    return s[:m.start(2)] + json.dumps(data, ensure_ascii=False, indent=2) + s[m.end(2):]


def write_sitemap(posts):
    sm = ROOT / "sitemap.xml"
    t = sm.read_text()
    t = re.sub(r"\s*<url><loc>https://runixcloud\.io/blog/[^<]+</loc>.*?</url>", "", t)
    block = "".join(
        f'  <url><loc>{BASE}/blog/{p["slug"]}</loc><lastmod>{p["iso"]}</lastmod>'
        f"<priority>0.6</priority></url>\n" for p in posts)
    anchor = f'  <url><loc>{BASE}/terms</loc>'
    t = t.replace(anchor, block + anchor, 1)
    # The hub changes with every post, so its lastmod is the newest post's
    # date; it sat at 2026-07-23 while posts went out through September.
    if posts:
        t = re.sub(rf"(<url><loc>{BASE}/blog/</loc><lastmod>)[^<]*(</lastmod>)",
                   rf"\g<1>{posts[0]['iso']}\g<2>", t, count=1)
    sm.write_text(t)


if __name__ == "__main__":
    posts = read_posts()
    write_index(posts)
    write_sitemap(posts)
    waiting = sorted(p.stem for p in (ROOT / "scheduled").glob("*.html")) if (ROOT / "scheduled").exists() else []
    print(f"published: {len(posts)}")
    by = grouped(posts)
    for tag, *_ in GROUPS:
        print(f"  {tag:15s} {len(by.get(tag, []))}")
    if waiting:
        print(f"waiting in scheduled/: {len(waiting)}")
