#!/usr/bin/env python3
"""Render /router-models: the models Runix Router routes to, each at its
vendor's public list price (decision of 2026-09-30: the catalogue shows
public prices, contract rates are quoted in writing).

Data: tools/models_catalog.json, one row per model with the vendor's name for
it, input / output / cached-input price in USD per million tokens, context
window, an optional tier note and the vendor page the price was read from,
plus a top-level as_of date. The page says where every number came from and
when; a model whose vendor no longer publishes a price is left out of the
data file rather than shown with a guess.

The head, header and footer come from the Router product page; the page
shell (page_shell.py) then adds this page's own bar, eyebrow and numbered
heads, so this runs before it. Idempotent. Run from the site root.
"""
import datetime
import html
import json
import pathlib
import re

SITE = "https://runixcloud.io"
DATA = pathlib.Path("tools/models_catalog.json")
OUT = pathlib.Path("router-models.html")
SHELL = pathlib.Path("router.html")

TITLE = "Router Models Catalogue: Public List Prices per Model"
DESC = ("Every model Runix Router routes to, at the vendor's public list price per million tokens, with "
        "context window and the vendor page each price was read from.")

FAQ = [
    ("Are these Runix prices or the vendors' prices?",
     "Both: Router's list price for each model is the vendor's public price, read from the vendor's own pricing page on the date shown. Contract rates can differ and are quoted in writing."),
    ("What does a model id on Router look like?",
     "The vendor's official id where the vendor publishes one, so an OpenAI-compatible client can send it unchanged. The table shows the id as Router accepts it beside the vendor's own name for the model."),
    ("Which models can my account use?",
     "The models on this list, subject to the allowed-models setting on your key, which is agreed at intake and can be changed on request."),
    ("What about cached input?",
     "Where a vendor publishes a cached-input price, Router bills cached tokens at that price; the column shows it, and a dash means the vendor does not publish one."),
    ("Why is a model I expected not on the list?",
     "A model stays on the catalogue only while its vendor publishes a list price for it. When a vendor retires a line, the model comes off until it is re-priced, and keys that named it are told before anything changes."),
]


def money(v):
    if v is None:
        return "&mdash;"
    s = f"{v:,.2f}".rstrip("0").rstrip(".")
    return f"${s}"


def tokens(v):
    """1000000 -> 1M, 1050000 -> 1.05M, 200000 -> 200K, 262144 -> 256K."""
    if v is None:
        return "&mdash;"
    if v >= 1_000_000:
        return f"{v / 1_000_000:g}M"
    if v % 1024 == 0:
        return f"{v // 1024}K"
    return f"{v / 1000:g}K"


def long_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.strftime('%B')} {d.day}, {d.year}"


def join(names):
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    rows = sorted(d["rows"], key=lambda r: (r["vendor"], r["id"]))
    vendors = sorted({r["vendor"] for r in rows})
    as_of = long_date(d["as_of"])
    src = SHELL.read_text(encoding="utf-8")

    trs = []
    for r in rows:
        note = html.escape(r.get("tier_note", ""), quote=False)
        name = html.escape(r["vendor_name"], quote=False)
        trs.append(
            f'          <tr><th scope="row"><code>{r["id"]}</code><span>{name}</span></th>'
            f'<td class="num">{tokens(r.get("context"))}</td>'
            f'<td class="num">{money(r["input"])}</td>'
            f'<td class="num">{money(r["output"])}</td>'
            f'<td class="num">{money(r.get("cache_read"))}</td>'
            f'<td class="src"><a href="{html.escape(r["source"], quote=True)}" rel="noopener">{html.escape(r["vendor"], quote=False)} pricing</a>{(" &middot; " + note) if note else ""}</td></tr>')
    table = "\n".join(trs)
    qas = "\n".join(f'      <div class="qa">\n        <h3>{html.escape(q, quote=False)}</h3>\n        <p>{html.escape(a, quote=False)}</p>\n      </div>' for q, a in FAQ)

    main_html = f'''<main id="main">
<div class="page-hero" id="overview">
  <div class="container">
    <h1><span class="line">Every model,</span>
<span class="line">at its public price</span></h1>
    <p>The models Runix Router routes to, each at the price its vendor publishes per million tokens. Router's list price is the vendor's public price; contract rates are quoted in writing. Prices as published on {as_of}.</p>
    <div class="actions">
      <a class="btn btn-primary" href="/about#contact">Request access</a>
      <a class="btn btn-ghost" href="/router">About Runix Router</a>
    </div>
  </div>
</div>

<section class="section">
  <div class="container">
    <div class="section-head center">
      <h2 id="catalogue">The catalogue</h2>
      <p>{len(rows)} models from {len(vendors)} vendors, at standard pay-as-you-go rates: not batch, not off-peak. Where a vendor prices by prompt length, the base tier is shown and the note says where it ends. Every row links to the page the price was read from.</p>
    </div>
    <div class="dsheet plain catalogue" tabindex="0" role="region" aria-label="Model catalogue with public list prices">
      <table aria-label="Model catalogue with public list prices">
        <thead><tr><th scope="col">Model id on Router</th><th scope="col" class="num">Context</th><th scope="col" class="num">Input / 1M</th><th scope="col" class="num">Output / 1M</th><th scope="col" class="num">Cached input / 1M</th><th scope="col">Source</th></tr></thead>
        <tbody>
{table}
        </tbody>
      </table>
    </div>
    <p class="src-note">USD per million tokens as published by {join(vendors)} on {as_of}. Vendors change prices without notice; the date is the day these were read, and the catalogue is rebuilt from its data file on every deploy. A model whose vendor has withdrawn its public list price is left off until it is re-priced.</p>
  </div>
</section>

<section class="section alt">
  <div class="container">
    <div class="section-head center">
      <h2 id="pricing">How a request is priced</h2>
      <p>Three rules, the same for every model on the list.</p>
    </div>
    <div class="grid cols-3">
      <div class="card">
        <h3>List price is the vendor's price</h3>
        <p>Router's list price for a model is the number on the vendor's own pricing page, input and output separately, per million tokens. There is no separate rate card to reconcile.</p>
      </div>
      <div class="card">
        <h3><code>auto</code> is priced at the ceiling</h3>
        <p>A request that lets Router choose the model is billed at the highest list price among the models it may choose from, so choosing <code>auto</code> never costs more than the most expensive explicit choice.</p>
      </div>
      <div class="card">
        <h3>Contract rates in writing</h3>
        <p>Volume and enterprise rates are quoted per workload and stated in writing before you commit; the catalogue shows list prices only.</p>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head center">
      <h2 id="questions">Common questions</h2>
    </div>
    <div class="qas">
{qas}
    </div>
  </div>
</section>

<section class="section section-end">
  <div class="container">
    <div class="cta-band">
      <h2>Put one endpoint in front of all of them</h2>
      <p>Tell us the models and the volume. A real person replies within one business day with a plan and, where volume warrants it, a rate in writing.</p>
      <a class="btn btn-grad" href="/about#contact">Request access</a>
    </div>
  </div>
</section>
</main>'''

    s = src
    s = re.sub(r"<title>.*?</title>", f"<title>{html.escape(TITLE, quote=False)}</title>", s, count=1)
    for attr, prop in (("name", "description"), ("property", "og:description"), ("name", "twitter:description")):
        s = re.sub(rf'<meta {attr}="{prop}" content="[^"]*">', f'<meta {attr}="{prop}" content="{html.escape(DESC)}">', s, count=1)
    for attr, prop in (("property", "og:title"), ("name", "twitter:title")):
        s = re.sub(rf'<meta {attr}="{prop}" content="[^"]*">', f'<meta {attr}="{prop}" content="{html.escape(TITLE)}">', s, count=1)
    s = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{SITE}/router-models">', s, count=1)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{SITE}/router-models">', s, count=1)
    # the page's own card; point_og.py versions it once make_og.py has drawn it
    card = f"{SITE}/assets/og/router-models.png"
    s = re.sub(r'(<meta (?:property="og:image(?::secure_url)?"|name="twitter:image") content=")[^"]*(")', lambda m: m.group(1) + card + m.group(2), s)

    ld = [
        {"@context": "https://schema.org", "@type": "ItemList", "name": "Runix Router model catalogue",
         "description": DESC, "numberOfItems": len(rows),
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": r["id"]} for i, r in enumerate(rows)]},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
            {"@type": "ListItem", "position": 2, "name": "Runix Router", "item": f"{SITE}/router"},
            {"@type": "ListItem", "position": 3, "name": "Models catalogue", "item": f"{SITE}/router-models"}]},
    ]
    blocks = list(re.finditer(r'<script type="application/ld\+json">.*?</script>\n?', s, re.S))
    new_ld = "\n".join('<script type="application/ld+json">\n' + json.dumps(b, ensure_ascii=False, indent=2) + "\n</script>" for b in ld) + "\n"
    s = s[:blocks[0].start()] + new_ld + s[blocks[-1].end():]
    a, b = s.index('<main id="main"'), s.index("</main>") + len("</main>")
    s = s[:a] + main_html + s[b:]
    s = re.sub(r"\n{3,}", "\n\n", s)

    old = OUT.read_text(encoding="utf-8") if OUT.exists() else None
    if old:
        # what point_og.py and page_shell.py added last time stays, so a rerun changes nothing
        m = re.search(r'content="(https://runixcloud\.io/assets/og/router-models\.png[^"]*)"', old)
        if m:
            s = s.replace(card, m.group(1))
        s_stripped = re.sub(r"[ \t]*<!--ps:bar-->.*?<!--/ps:bar-->\n?", "", old, flags=re.S)
        s_stripped = re.sub(r"[ \t]*<!--ps:eyebrow-->.*?<!--/ps:eyebrow-->\n?", "", s_stripped, flags=re.S)
        s_stripped = re.sub(r'[ \t]*<p class="sec-no">[^<]*</p>\n', "", s_stripped)
        s_stripped = s_stripped.replace('<main id="main" class="has-pbar">\n\n', '<main id="main">\n', 1)
        s_stripped = re.sub(r"\n{3,}", "\n\n", s_stripped)
        if s_stripped == s:
            print("models catalogue: unchanged")
            return
    OUT.write_text(s, encoding="utf-8")
    print(f"models catalogue: written ({len(rows)} rows, {len(vendors)} vendors)")


if __name__ == "__main__":
    main()
