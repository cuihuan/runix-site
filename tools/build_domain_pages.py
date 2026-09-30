#!/usr/bin/env python3
"""Render the six Runix Data domain pages from tools/domains.py.

Each page is <slug>.html at the site root (so every gate that globs *.html
covers it), built from one template: the Data page's head, header and footer,
with the domain's own title, description, structured data and body. The body
is the same shape on every page -- hero with a reference card, the data the
domain covers, the rules and the public practice each follows, the public
references, what a delivery carries, questions, and a closing band -- so the
six read as one set.

Idempotent: a page is rewritten only when its rendered text changes. Run from
the site root, then run flagship_nav.py (header and footer) and
stack_build.py (nothing to do for these pages, but it is the same routine).
"""
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from domains import DOMAINS  # noqa: E402
from stack_build import eyebrow  # noqa: E402

SITE = "https://runixcloud.io"
SHELL = pathlib.Path("data.html")

SHARED_FAQ = [
    ("Do you sell ready-made {name} datasets?",
     "Not off the shelf. Runix Data builds to a specification agreed in writing: from data you provide or "
     "have the rights to use, or from public sources whose licences permit your use. The rules on this page "
     "apply either way."),
    ("What happens to the data we send?",
     "It is processed only to do the work you asked for. It is not used to train models, ours or anyone "
     "else's, and it is not sold."),
]

DELIVERY = [
    ("Provenance and licence, per record", "Where each record came from, what was done to it, and the licence or permission it was used under."),
    ("A quality report", "Coverage, duplication and the checks each record passed, plus what was dropped and why."),
    ("Evaluation kept apart", "Evaluation data split from training data by source, so a score is not inflated by near-duplicates."),
]


def text(s):
    """Visible text of a fragment, for structured data."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def main_html(d):
    name, slug = d["name"], d["slug"]
    subject = f"Runix%20Data%3A%20{name.replace(' ', '%20')}"
    width = max(len(k) for k, _ in d["panel"]) + 2
    panel = "\n".join(f'<span class="a">{k.ljust(width)}</span>{v}' for k, v in d["panel"])
    kinds = "\n".join(
        f'      <div class="card">\n        <h3>{k}</h3>\n        <p>{t}</p>\n      </div>' for k, t in d["kinds"])
    rules = "\n".join(
        f'      <div class="fcell">\n        <span class="fno" aria-hidden="true">{i:02d}</span>\n'
        f'        <h3>{title}</h3>\n        <p>{t}</p>\n        <p class="basis"><b>Follows</b> {basis}</p>\n      </div>'
        for i, (title, t, basis) in enumerate(d["rules"], 1))
    refs = "\n".join(
        f'      <li><a href="{url}" rel="noopener">{n}</a><span>{what}</span></li>' for n, url, what in d["refs"])
    delivery = "\n".join(
        f'      <div class="card">\n        <h3>{t}</h3>\n        <p>{p}</p>\n      </div>' for t, p in DELIVERY)
    faqs = [(q, a) for q, a in d["faq"]] + [(q.format(name=name), a) for q, a in SHARED_FAQ]
    qas = "\n".join(
        f'      <div class="qa">\n        <h3>{q}</h3>\n        <p>{a}</p>\n      </div>' for q, a in faqs)
    return f'''<main id="main">
<section class="split-hero">
  <div class="container">
    <div>
      {eyebrow("data")}
      <h1><span class="line">{d["h1"][0]}</span>
<span class="line">{d["h1"][1]}</span></h1>
      <p class="sub">{d["sub"]}</p>
      <div class="actions">
        <!--email_off--><a class="btn btn-primary" href="mailto:sales@runixcloud.io?subject={subject}">Request early access</a><!--/email_off-->
        <a class="btn btn-ghost" href="/data#domains">All six domains</a>
      </div>
      <p class="hero-note">Part of <a href="/data">Runix Data</a>. This page sets out the rules we apply in this domain and the public standards they follow.</p>
    </div>
    <div>
      <div class="term">
        <div class="term-bar"><i></i><i></i><i></i><b>{name.lower()}: what each record is checked against</b></div>
<pre>{panel}</pre>
      </div>
      <p class="term-cap">A reference card. Each line names a public standard or convention; the rules below say how it is applied.</p>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head center">
      <h2>The data this covers</h2>
      <p>Cleaned and structured from what you provide or have the rights to use, or built to a specification agreed in writing.</p>
    </div>
    <div class="grid cols-2">
{kinds}
    </div>
  </div>
</section>

<section class="section alt">
  <div class="container">
    <div class="section-head center">
      <h2>The rules, and where they come from</h2>
      <p>Each rule follows a public standard or an established practice in the field, named with it, so you can check the reasoning rather than take ours on trust.</p>
    </div>
    <div class="fgrid">
{rules}
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head center">
      <h2>Public references</h2>
      <p>The standards and open sources these rules are built on. They are other organisations' work, linked so you can read them yourself.</p>
    </div>
    <ul class="refs">
{refs}
    </ul>
  </div>
</section>

<section class="section alt">
  <div class="container">
    <div class="section-head center">
      <h2>What every delivery carries</h2>
      <p>The same in every domain; the <a href="/data">Runix Data</a> page has the full list.</p>
    </div>
    <div class="grid cols-3">
{delivery}
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head center">
      <h2>Common questions</h2>
    </div>
    <div class="qas">
{qas}
    </div>
  </div>
</section>

<section class="section section-end">
  <div class="container">
    <div class="cta-band">
      <h2>{d["cta"]}</h2>
      <p>A slice of the real data and what the model has to do with it. We reply within one business day, and the scoped plan that follows includes the parts we think are not worth doing.</p>
      <!--email_off--><a class="btn btn-grad" href="mailto:sales@runixcloud.io?subject={subject}">Request early access</a><!--/email_off-->
    </div>
  </div>
</section>
</main>'''


def structured(d):
    url = f"{SITE}/{d['slug']}"
    faqs = [(q, a) for q, a in d["faq"]] + [(q.format(name=d["name"]), a) for q, a in SHARED_FAQ]
    blocks = [
        {"@context": "https://schema.org", "@type": "Service",
         "name": f"Runix Data: {d['name']}",
         "serviceType": f"{d['name']} data preparation for AI training and evaluation",
         "description": text(d["sub"]),
         "provider": {"@id": f"{SITE}/#org"}, "url": url},
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": text(q),
                         "acceptedAnswer": {"@type": "Answer", "text": text(a)}} for q, a in faqs]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList",
         "itemListElement": [
             {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
             {"@type": "ListItem", "position": 2, "name": "Runix Data", "item": f"{SITE}/data"},
             {"@type": "ListItem", "position": 3, "name": d["name"], "item": url}]},
    ]
    return "\n".join('<script type="application/ld+json">\n' + json.dumps(b, ensure_ascii=False, indent=2)
                     + "\n</script>" for b in blocks)


def page(shell, d):
    s = shell
    url = f"{SITE}/{d['slug']}"
    title, desc = html.escape(d["title"], quote=False), html.escape(d["description"])
    s = re.sub(r"<title>.*?</title>", f"<title>{title}</title>", s, count=1)
    for prop in ("og:title", "twitter:title"):
        attr = "property" if prop.startswith("og") else "name"
        s = re.sub(rf'<meta {attr}="{prop}" content="[^"]*">', f'<meta {attr}="{prop}" content="{title}">', s, count=1)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', s, count=1)
    for prop in ("og:description", "twitter:description"):
        attr = "property" if prop.startswith("og") else "name"
        s = re.sub(rf'<meta {attr}="{prop}" content="[^"]*">', f'<meta {attr}="{prop}" content="{desc}">', s, count=1)
    s = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', s, count=1)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', s, count=1)
    # The card is rendered by make_og.py and pointed at by point_og.py. A page
    # that already points at its own card keeps that version; a new page gets
    # a placeholder, which qa.py reports until the card exists.
    def card(m):
        if f"/assets/og/{d['slug']}.png" in m.group(2):
            return m.group(0)
        return f"{m.group(1)}{SITE}/assets/og/{d['slug']}.png?v=0{m.group(3)}"
    s = re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")([^"]*)(")', card, s)
    # Structured data: the shell's blocks are replaced wholesale.
    blocks = list(re.finditer(r'<script type="application/ld\+json">.*?</script>\n?', s, re.S))
    if blocks:
        s = s[:blocks[0].start()] + structured(d) + "\n" + s[blocks[-1].end():]
    a, b = s.index('<main id="main">'), s.index("</main>") + len("</main>")
    return s[:a] + main_html(d) + s[b:]


def main():
    shell = SHELL.read_text(encoding="utf-8")
    changed = 0
    for d in DOMAINS:
        p = pathlib.Path(f"{d['slug']}.html")
        old = p.read_text(encoding="utf-8") if p.exists() else None
        # An existing page is its own shell, so its header, footer and card
        # stay as the other builders left them and a rerun changes nothing.
        new = page(old or shell, d)
        if new != old:
            p.write_text(new, encoding="utf-8")
            changed += 1
    print(f"domain pages: {changed} of {len(DOMAINS)} changed")


if __name__ == "__main__":
    main()
