#!/usr/bin/env python3
"""Render blog posts from JSON specs into scheduled/, one shape for every post.

Until 2026-10-07 each post had its own write_<name>_post.py that cloned a
published page and swapped the copy in. Twenty-seven posts were written in one
sitting for the v5 content expansion, so the cloning moved here and the copy
moved into data: a spec per post (title, description, category, layer, the
product it sends readers to, related posts, body HTML and a short FAQ), and one
renderer that draws every post the same way and refuses specs that break the
site's rules before they get anywhere near a gate.

    python3 tools/write_post.py spec.json [spec.json ...]
    python3 tools/write_post.py --dir /path/to/specs

Dates are stamped by tools/publish.py when the post goes live, never here, so
the site cannot claim a post existed before it did. Every rendered page is a
draft in scheduled/ until publish.py moves it.
"""
import glob
import html as _html
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)
SITE = "https://runixcloud.io"
TEMPLATE = ROOT / "blog" / "what-is-an-llm-gateway.html"

LAYER_LABEL = {"infrastructure": "Infrastructure", "data": "Data", "models": "Models",
               "gateway": "Gateway", "agents": "Agents", "company": "Company"}
CATEGORIES = {"Engineering", "Concepts", "Buyer's guide", "Compliance", "Security", "Creators", "Announcement"}

# Where a post sends its reader at the end. Anchor text names the destination.
PRODUCT = {
    "/router": "Runix Router: one OpenAI-compatible endpoint across providers",
    "/router-models": "The Router models catalogue, at vendors' public list prices",
    "/reliability": "What happens when a provider fails",
    "/plans": "How Runix pricing works",
    "/pipeline": "Runix Pipeline: the tooling that makes data model-ready",
    "/data": "Runix Data: domain data for training and evaluation",
    "/code-data": "Code data, verified by running the tests",
    "/models": "Runix Models: fine-tune and serve open-weight models",
    "/fs": "Runix FS: an AI-native file system on your object storage",
    "/code": "Runix Code: an independent coding agent, reviewable in your repository",
    "/comic": "Runix Comic: an independent agent for comic dramas",
    "/agents": "The Agents layer, by professional domain",
    "/security": "How Runix handles data, in plain language",
    "/about": "What Runix is, and how we work",
    "/solutions": "Runix by what your team is trying to do",
}

# The same rules qa.py enforces on published pages, applied to the body before
# a draft exists, so a spec that breaks one is reported by name.
SELF = re.compile(r"\b(runix|we|our|us)\b", re.I)
FORBIDDEN = [
    (r"\d+(\.\d+)?\s*%\s*(uptime|availability|sla)", "an uptime or availability percentage", True),
    (r"\btrusted by\b", "a 'trusted by' claim", False),
    (r"\b\d+\+?\s*(customers|companies|enterprises)\b", "a customer count", True),
    (r"\b(SOC\s*2|ISO\s*27001|PCI[- ]DSS)\b[^.]{0,40}\b(certified|compliant|attested)\b", "a certification claim", True),
    (r"\b\d+(\.\d+)?\s*(ms|milliseconds)\b", "a latency figure", True),
]
BANNED_WORDS = re.compile(r"\bkiro\b", re.I)


def text_of(fragment):
    return " ".join(_html.unescape(re.sub(r"<[^>]+>", " ", fragment)).split())


def check(spec, known_slugs):
    """Return a list of problems; an empty list means the spec may be rendered."""
    p = []
    for k in ("slug", "title", "h1", "description", "category", "layer", "product", "related", "body"):
        if k not in spec:
            p.append(f"missing key {k}")
    if p:
        return p
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", spec["slug"]):
        p.append("slug must be lower-case words joined by hyphens")
    if len(spec["title"]) > 70:
        p.append(f"title is {len(spec['title'])} chars (max 70)")
    if not (110 <= len(spec["description"]) <= 160):
        p.append(f"description is {len(spec['description'])} chars (110-160)")
    if '"' in spec["description"]:
        p.append("description contains a double quote")
    if spec["category"] not in CATEGORIES:
        p.append(f"unknown category {spec['category']!r}")
    if spec["layer"] not in LAYER_LABEL:
        p.append(f"unknown layer {spec['layer']!r}")
    if spec["product"] not in PRODUCT:
        p.append(f"unknown product page {spec['product']!r}")
    body = spec["body"]
    words = len(text_of(body).split())
    if not (600 <= words <= 1500):
        p.append(f"body is {words} words (600-1500)")
    if "<h1" in body:
        p.append("body contains an h1")
    h2 = len(re.findall(r"<h2\b", body))
    if not (3 <= h2 <= 8):
        p.append(f"body has {h2} h2 sections (3-8)")
    if re.search(r"<(div|span|img|script|style|iframe)\b", body):
        p.append("body uses an element the template does not allow (div/span/img/script/style/iframe)")
    if re.search(r'style="', body):
        p.append("body carries inline styles")
    if BANNED_WORDS.search(text_of(body) + spec["title"] + spec["description"]):
        p.append("names something the site never mentions")
    internal = re.findall(r'<a href="(/[^"]*)"', body)
    external = re.findall(r'<a href="(https?://[^"]*)"([^>]*)>', body)
    if len(internal) < 3:
        p.append(f"only {len(internal)} internal link(s); at least 3")
    if len(external) > 4:
        p.append(f"{len(external)} external links; at most 4")
    for url, attrs in external:
        if 'rel="noopener"' not in attrs:
            p.append(f"external link without rel=noopener: {url}")
        if "runixcloud.io" in url:
            p.append(f"site link written as an absolute URL: {url}")
    for href in internal:
        path = href.split("#")[0].split("?")[0]
        if path.startswith("/blog/"):
            if path[6:] not in known_slugs:
                p.append(f"links to a post that does not exist: {href}")
        elif path and path != "/":
            f = path.lstrip("/")
            if f.endswith("/"):
                f += "index"
            if not os.path.isfile(f + ".html") and f not in ("solutions", "agents", "roadmap") \
                    and not f.startswith("for-"):
                p.append(f"links to a page that does not exist: {href}")
    for s in spec["related"]:
        if s not in known_slugs:
            p.append(f"related post does not exist: {s}")
    if len(spec["related"]) != 3:
        p.append("related must name exactly 3 posts")
    plain = text_of(body)
    for sentence in re.split(r"(?<=[.!?])\s+", plain):
        for pattern, what, needs_self in FORBIDDEN:
            m = re.search(pattern, sentence, re.I)
            if m and (not needs_self or SELF.search(sentence)):
                p.append(f"{what}: {sentence.strip()[:90]!r}")
    if "\u2014" in plain or "\u2014" in spec["title"] or "\u2014" in spec["h1"]:
        p.append("uses an em dash")
    for q, a in spec.get("faq", []):
        if "<" in a:
            p.append("FAQ answers must be plain text")
    return p


def fix_tables(body):
    """Header cells say which way they head, and every table has a name.

    qa.py fails a table whose <th> cells carry no scope or whose <table> has no
    aria-label; the name is the nearest preceding heading's text, which is the
    sentence that already introduces the table on screen."""
    out, pos = [], 0
    for m in re.finditer(r"<table\b([^>]*)>(.*?)</table>", body, re.S):
        attrs, inner = m.group(1), m.group(2)
        heads = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", body[:m.start()], re.S)
        name = text_of(heads[-1]) if heads else "Comparison"
        if "aria-label" not in attrs:
            attrs = attrs + f' aria-label="{_html.escape(name, quote=True)}"'
        inner = re.sub(r"<th\b(?![^>]*scope=)([^>]*)>", r'<th scope="col"\1>', inner)
        out.append(body[pos:m.start()])
        # The same scroll container tools/wrap_tables.py gives every article
        # table, so a rendered post is what that builder would produce.
        before = body[max(0, m.start() - 120):m.start()]
        wrap = 'class="table-scroll"' not in before
        if wrap:
            out.append('<div class="table-scroll" tabindex="0" role="region" aria-label="Table, scrolls horizontally">\n')
        out.append(f"<table{attrs}>{inner}</table>")
        if wrap:
            out.append("\n</div>")
        pos = m.end()
    out.append(body[pos:])
    return "".join(out)


def headline_of(slug, batch):
    if slug in batch:
        return batch[slug]["h1"]
    for d in ("blog", "scheduled"):
        f = ROOT / d / f"{slug}.html"
        if f.exists():
            m = re.search(r"<h1[^>]*>(.*?)</h1>", f.read_text(), re.S)
            return text_of(m.group(1))
    return slug


def render(spec, batch):
    slug, url = spec["slug"], f"{SITE}/blog/{spec['slug']}"
    page = TEMPLATE.read_text(encoding="utf-8")
    title = _html.escape(spec["title"], quote=False)
    desc = _html.escape(spec["description"], quote=False)  # no double quotes allowed in a description (checked above)
    h1 = _html.escape(spec["h1"], quote=False)
    page = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", page, count=1)
    for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
        page = re.sub(rf'({re.escape(attr)} content=")[^"]*(")', lambda m: m.group(1) + desc + m.group(2), page, count=1)
    for attr in ('property="og:title"', 'name="twitter:title"'):
        page = re.sub(rf'({re.escape(attr)} content=")[^"]*(")', lambda m: m.group(1) + title + m.group(2), page, count=1)
    page = re.sub(r'(<link rel="canonical" href=")[^"]*(">)', rf"\g<1>{url}\g<2>", page, count=1)
    page = re.sub(r'(<meta property="og:url" content=")[^"]*(">)', rf"\g<1>{url}\g<2>", page, count=1)
    # The card is rendered by make_og.py and pointed at by point_og.py; a new
    # page gets a placeholder that qa.py reports until the card exists.
    card = f"{SITE}/assets/og/blog-{slug}.png?v=0"
    page = re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")[^"]*(")',
                  lambda m: m.group(1) + card + m.group(2), page)
    page = re.sub(r'(<meta property="article:section" content=")[^"]*(")',
                  lambda m: m.group(1) + _html.escape(spec["category"], quote=True) + m.group(2), page, count=1)
    for attr in ("article:published_time", "article:modified_time"):
        page = re.sub(rf'(<meta property="{attr}" content=")[^"]*(")', r"\g<1>PENDING\g<2>", page, count=1)
    layer_label = LAYER_LABEL[spec["layer"]]
    if 'property="article:tag"' in page:
        page = re.sub(r'(<meta property="article:tag" content=")[^"]*(")', rf"\g<1>{layer_label}\g<2>", page, count=1)
    else:
        page = page.replace('<meta property="article:section"',
                            f'<meta property="article:tag" content="{layer_label}">\n<meta property="article:section"', 1)

    # Structured data: Article and BreadcrumbList re-pointed; FAQPage added
    # from the spec's own questions, which are also rendered visibly below.
    def fix(block):
        d = json.loads(block)
        if d.get("@type") == "Article":
            d["headline"], d["description"] = spec["h1"], spec["description"]
            d["mainEntityOfPage"] = {"@type": "WebPage", "@id": url}
            d["image"] = card
            d["datePublished"] = d["dateModified"] = "PENDING"
        elif d.get("@type") == "BreadcrumbList":
            leaf = max(d["itemListElement"], key=lambda i: i["position"])
            leaf["name"], leaf["item"] = spec["h1"], url
        return json.dumps(d, ensure_ascii=False, indent=2)
    page = re.sub(r'(<script type="application/ld\+json">\n)(.*?)(\n</script>)',
                  lambda m: m.group(1) + fix(m.group(2)) + m.group(3), page, flags=re.S)
    page = re.sub(r'<script type="application/ld\+json">\n\{\n  "@context": "https://schema.org",\n  "@type": "FAQPage".*?</script>\n', "", page, flags=re.S)
    faq = spec.get("faq") or []
    if faq:
        block = {"@context": "https://schema.org", "@type": "FAQPage",
                 "mainEntity": [{"@type": "Question", "name": q,
                                 "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
        page = page.replace('<meta property="og:locale"',
                            '<script type="application/ld+json">\n' + json.dumps(block, ensure_ascii=False, indent=2)
                            + '\n</script>\n<meta property="og:locale"', 1)

    words = len(text_of(spec["body"]).split())
    minutes = max(1, round(words / 200))
    page = re.sub(r'(<div class="post-meta"><span class="cat">)[^<]*(</span><span>)[^<]*(</span><span>·</span><span>)[^<]*(</span></div>)',
                  lambda m: m.group(1) + _html.escape(spec["category"], quote=False) + m.group(2) + "PENDING"
                  + m.group(3) + f"{minutes} min read" + m.group(4), page, count=1)
    page = re.sub(r'(<h1 style="margin-top: 14px;">).*?(</h1>)', lambda m: m.group(1) + h1 + m.group(2), page, count=1, flags=re.S)

    body = fix_tables(spec["body"].strip())
    if faq:
        body += '\n\n<h2 id="questions">Questions this raises</h2>\n' + "\n".join(
            f"<h3>{_html.escape(q, quote=False)}</h3>\n<p>{_html.escape(a, quote=False)}</p>" for q, a in faq)
    product = spec["product"]
    name = PRODUCT[product].split(":")[0]
    callout = spec.get("callout") or (
        f'Related to this post: <a href="{product}">{name}</a>. '
        '<a href="/about#contact">Tell us what you are building</a> and we reply within one business day.')
    body += ('\n\n<div class="callout" style="margin-top:40px;">\n'
             '  <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5v.01"/></svg>\n'
             f'  <span>{callout}</span>\n'
             '</div>')
    related = "".join(f'\n    <li><a href="/blog/{s}">{_html.escape(headline_of(s, batch), quote=False)}</a></li>' for s in spec["related"])
    body += ('\n\n<aside class="related" aria-labelledby="related-reading">\n'
             '  <h2 id="related-reading">Related reading</h2>\n'
             f'  <ul>{related}\n    <li><a href="{product}">{PRODUCT[product]}</a></li>\n  </ul>\n</aside>')
    start = page.index('<article class="article">') + len('<article class="article">')
    end = page.index("</article>")
    page = page[:start] + "\n\n" + body + "\n" + page[end:]
    # The page bar is re-drawn by page_shell.py from the new headings.
    page = re.sub(r"[ \t]*<!--ps:bar-->.*?<!--/ps:bar-->\n?", "", page, flags=re.S)
    return page, words, minutes


def main(argv):
    paths = []
    if argv and argv[0] == "--dir":
        paths = sorted(glob.glob(os.path.join(argv[1], "*.json")))
    else:
        paths = argv
    if not paths:
        sys.exit(__doc__)
    specs = {}
    for path in paths:
        spec = json.load(open(path, encoding="utf-8"))
        specs[spec["slug"]] = spec
    known = {p.stem for p in (ROOT / "blog").glob("*.html") if p.stem != "index"}
    known |= {p.stem for p in (ROOT / "scheduled").glob("*.html")} | set(specs)
    bad = 0
    (ROOT / "scheduled").mkdir(exist_ok=True)
    for slug, spec in specs.items():
        problems = check(spec, known)
        if problems:
            bad += 1
            print(f"  REJECTED {slug}:")
            for pr in problems:
                print(f"      - {pr}")
            continue
        page, words, minutes = render(spec, specs)
        out = ROOT / "scheduled" / f"{slug}.html"
        out.write_text(page, encoding="utf-8")
        print(f"  wrote scheduled/{slug}.html  ({words} words, {minutes} min, {spec['layer']}/{spec['category']})")
    print(f"{len(specs) - bad} rendered, {bad} rejected")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1:])
