#!/usr/bin/env python3
"""Render the cross-cutting pages from tools/solutions.py (2026-10-07, v5).

The product stack is the site's map, but a buyer arrives with a job, not a
layer, and the Agents layer is asked about by profession ("for coding", "for
media") rather than by product. So, beside the seven product pages:

  * /solutions and six audience pages (/for-platform-teams, ...): the problems
    one kind of team has, the products that address them and the role each
    plays, how working together starts, and what is in writing;
  * /agents: the Agents layer by professional domain, the two agents that
    exist today with their literal statuses, the domains that are candidates
    because the Data layer already has rules for them, and the principles
    every agent in the layer must satisfy;
  * /roadmap: where each product is, drawn from tools/stack.py's statuses, and
    what general availability adds. No dates: the site publishes none.

One template each, the same shell as the product pages (bar, split hero,
numbered sections, closing band). Content comes from tools/solutions.py and
statuses from tools/stack.py; nothing here is typed twice. Idempotent: an
existing page is its own shell, so header, footer and card survive a rerun and
a second run changes nothing. Run from the site root after product_template.py
and before page_shell.py (these pages draw their own bar, so page_shell leaves
them alone). Also keeps sitemap.xml listing every page it renders.
"""
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from stack import LAYERS, PRODUCTS, LAYER_OF, AGENT_DOMAINS, DOMAINS  # noqa: E402
from solutions import SOLUTIONS, AGENTS_HUB, ROADMAP  # noqa: E402
import build_blog_index as _blog  # noqa: E402

SITE = "https://runixcloud.io"
SHELL = pathlib.Path("about.html")
SALES = "/about#contact"
E = lambda s: html.escape(s, quote=False)  # noqa: E731

# Naming one of these pages in prose means linking it (qa.py enforces it on
# every non-blog page), and the copy in solutions.py is plain text.
NAMED = [("the Security page", "/security"), ("the reliability page", "/reliability"),
         ("the pricing page", "/plans"), ("the access page", "/access")]


def L(s):
    """Escaped prose with the named pages linked."""
    out = E(s)
    for phrase, href in NAMED:
        out = re.sub(re.escape(phrase), lambda m: f'<a href="{href}">{m.group(0)}</a>', out, flags=re.I)
    return out


def text(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


def status_span(key, cls="live"):
    st = PRODUCTS[key][5]
    live = f' class="{cls}"' if st == "early access" else ""
    return f"<span{live}>{st.capitalize()}</span>"


def post_title(slug):
    p = pathlib.Path("blog") / f"{slug}.html"
    if not p.exists():
        return None
    m = re.search(r"<h1[^>]*>(.*?)</h1>", p.read_text(encoding="utf-8"), re.S)
    return text(m.group(1))


def bar(name, layer_html, status_html, links, cta_href, cta_label, name_href="#overview"):
    lis = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in links)
    cta = f'<a class="pbar-cta" href="{cta_href}">{cta_label}</a>'
    if cta_href.startswith("mailto:"):
        cta = f"<!--email_off-->{cta}<!--/email_off-->"
    return (f'<nav class="pbar" aria-label="{E(name)} on this page">\n'
            f'  <div class="container pbar-inner">\n'
            f'    <a class="pbar-name" href="{name_href}">{name}</a>\n'
            f'    {layer_html}\n    {status_html}\n'
            f'    <ul class="pbar-links">{lis}</ul>\n'
            f'    {cta}\n  </div>\n</nav>')


def head(n, label, h2, lede, hid):
    lede_html = f"\n      <p>{lede}</p>" if lede else ""
    return (f'    <div class="section-head center">\n      <p class="sec-no">{n:02d} &middot; {label}</p>\n'
            f'      <h2 id="{hid}">{h2}</h2>{lede_html}\n    </div>')


def qas(faq):
    return "\n".join(f'      <div class="qa">\n        <h3>{E(q)}</h3>\n        <p>{L(a)}</p>\n      </div>' for q, a in faq)


def close(h2, p, href, label):
    btn = f'<a class="btn btn-grad" href="{href}">{label}</a>'
    if href.startswith("mailto:"):
        btn = f"<!--email_off-->{btn}<!--/email_off-->"
    return (f'<section class="section section-end">\n  <div class="container">\n    <div class="cta-band">\n'
            f'      <h2>{E(h2)}</h2>\n      <p>{p}</p>\n      {btn}\n    </div>\n  </div>\n</section>')


# ---------------------------------------------------------------- solutions
def solution_main(d):
    name, slug = d["name"], d["slug"]
    subject = "Runix%3A%20" + name.replace(" ", "%20")
    mail = f"mailto:sales@runixcloud.io?subject={subject}"
    links = [("situation", "The situation"), ("stack", "The stack"), ("start", "How it starts"),
             ("writing", "In writing"), ("reading", "Reading"), ("faq", "Questions")]
    glance_rows = "\n".join(
        f'        <div><dt>{E(PRODUCTS[k][2])}</dt><dd>{E(PRODUCTS[k][3])} &middot; {PRODUCTS[k][5]}</dd></div>'
        for k, _role in d["stack"])
    situation = "\n".join(
        f'      <div class="card">\n        <h3>{E(t)}</h3>\n        <p>{L(x)}</p>\n      </div>' for t, x in d["situation"])
    rows = []
    for k, role in d["stack"]:
        num, lname = LAYER_OF[PRODUCTS[k][4]]
        rows.append(f'      <div class="srow">\n        <div class="sp"><a href="{PRODUCTS[k][1]}">{E(PRODUCTS[k][2])}</a>'
                    f'<span>Layer {num:02d} &middot; {lname}</span>{status_span(k)}</div>\n'
                    f'        <div class="sr">{L(role)}</div>\n      </div>')
    steps = "\n".join(
        f'      <div class="pstep">\n        <h3><span class="pstep-n">{i:02d}</span>{E(t)}</h3>\n        <p>{L(x)}</p>\n      </div>'
        for i, (t, x) in enumerate(d["path"], 1))
    writing = "\n".join(
        f'      <div class="card">\n        <h3>{E(t)}</h3>\n        <p>{L(x)}</p>\n      </div>' for t, x in d["writing"])
    reading = []
    for s in d["reading"]:
        t = post_title(s)
        if t:
            reading.append(f'      <li><a href="/blog/{s}">{E(t)}</a></li>')
    reading_html = "\n".join(reading)
    others = "".join(
        f'\n      <li><a class="pd-chip" href="/{o["slug"]}">{E(o["name"])}</a></li>' for o in SOLUTIONS if o["slug"] != slug)
    return f'''<main id="main" class="has-pbar">
{bar(E(name), '<a class="pbar-layer" href="/solutions">Solutions</a>', '<span class="pbar-status">By team</span>', links, mail, "Talk to sales")}
<section class="split-hero" id="overview">
  <div class="container">
    <div>
      <div class="prod-eyebrow"><span class="sl-row"><a class="stack-loc" href="/solutions">Solutions<span class="visually-hidden">: every team the stack is built for</span></a></span><span class="badge">For {E(name.lower())}</span></div>
      <h1><span class="line">{E(d["h1"][0])}</span>
<span class="line">{E(d["h1"][1])}</span></h1>
      <p class="sub">{E(d["sub"])}</p>
      <div class="actions">
        <!--email_off--><a class="btn btn-primary" href="{mail}">Talk to sales</a><!--/email_off-->
        <a class="btn btn-ghost" href="#stack">See the stack for this team</a>
      </div>
      <p class="hero-note">One of six <a href="/solutions">solution pages</a>. Statuses are literal: the products named below are in early access or in development, as marked.</p>
    </div>
    <div>
      <div class="glance">
        <p class="glance-title">The stack for {E(name.lower())}</p>
        <dl>
{glance_rows}
        </dl>
      </div>
    </div>
  </div>
</section>

<section class="section" id="situation">
  <div class="container">
{head(2, "Situation", "The situation", "Three things this team is usually dealing with when it calls.", "the-situation")}
    <div class="sgrid">
{situation}
    </div>
  </div>
</section>

<section class="section alt" id="stack">
  <div class="container">
{head(3, "Stack", "The products, and the role each plays", "Each one works on its own; together they are one path through the stack.", "the-products")}
    <div class="stackrole">
{chr(10).join(rows)}
    </div>
  </div>
</section>

<section class="section" id="start">
  <div class="container">
{head(4, "Start", "How it starts", "A person on the other end at every step; nothing here is self-serve.", "how-it-starts")}
    <div class="prun">
{steps}
    </div>
  </div>
</section>

<section class="section alt" id="writing">
  <div class="container">
{head(5, "In writing", "What is in writing", "The parts a review asks for, stated once and linked to the page that holds them.", "in-writing")}
    <div class="grid cols-3">
{writing}
    </div>
  </div>
</section>

<section class="section" id="reading">
  <div class="container">
{head(6, "Reading", "Reading for this team", "Engineering notes that cover the mechanics behind this page.", "reading-for-this-team")}
    <ul class="refs">
{reading_html}
    </ul>
    <p class="model-note">Other teams: <ul class="topic-chips">{others}
    </ul></p>
  </div>
</section>

<section class="section alt" id="faq">
  <div class="container">
{head(7, "Questions", "Common questions", "", "common-questions")}
    <div class="qas">
{qas(d["faq"])}
    </div>
  </div>
</section>

{close(d["cta"], "Tell us what you run today and what you are trying to change. We reply within one business day with a concrete plan, and we say which parts we would not do.", mail, "Talk to sales")}
</main>'''


def solution_schema(d):
    url = f"{SITE}/{d['slug']}"
    return [
        {"@context": "https://schema.org", "@type": "WebPage", "name": text(d["title"]),
         "description": text(d["description"]), "url": url, "isPartOf": {"@id": f"{SITE}/#website"},
         "about": {"@type": "Thing", "name": f"Runix for {d['name'].lower()}"}},
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": text(q),
                         "acceptedAnswer": {"@type": "Answer", "text": text(a)}} for q, a in d["faq"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList",
         "itemListElement": [
             {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
             {"@type": "ListItem", "position": 2, "name": "Solutions", "item": f"{SITE}/solutions"},
             {"@type": "ListItem", "position": 3, "name": d["name"], "item": url}]},
    ]


def solcard(d):
    prods = "".join(f'<li{" class=\"first\"" if i == 0 else ""}>{"Start: " if i == 0 else ""}{E(PRODUCTS[k][2])}</li>'
                    for i, (k, _) in enumerate(d["stack"]))
    return (f'      <a class="solcard" href="/{d["slug"]}" aria-label="Runix for {E(d["name"].lower())}">\n'
            f'        <p class="sk">For {E(d["name"].lower())}</p>\n        <h3>{E(d["h1"][0])} {E(d["h1"][1])}</h3>\n'
            f'        <p>{E(d["sub"])}</p>\n        <ul class="sol-products">{prods}</ul>\n'
            f'        <span class="read-more">Runix for {E(d["name"].lower())} &rarr;</span>\n      </a>')


HUB = {
    "title": "Solutions by Team: Platform, Model and Engineering | Runix",
    "description": "Six teams the Runix stack is built for, from platform and model teams to studios and labs: the problem each has, the products that fit, how work starts.",
    "h1": ("Runix, by what", "your team is trying to do"),
    "sub": "The stack is the map; this is the other way in. Six kinds of team, the problems each one usually calls about, the layers that address them, and how working together starts. Statuses stay literal on every page.",
    "faq": [
        ("Do I have to buy the whole stack?", "No. Every product works on its own and is bought on its own. A solution page names the products that usually fit one team; most teams start with one."),
        ("Which page should I read first?", "The one closest to your job. Platform teams own the integration with model providers; model teams train or tune; engineering organisations are adopting AI coding; studios make serialised visual stories; regulated industries answer reviewers; research labs move datasets and models for science."),
        ("What if none of these is my team?", "Write to us anyway. The pages are the six situations we see most, not a limit; a reply within one business day says which products apply and which do not."),
    ],
}


def hub_main():
    links = [("teams", "Teams"), ("how", "How to read"), ("faq", "Questions")]
    cards = "\n".join(solcard(d) for d in SOLUTIONS)
    return f'''<main id="main" class="has-pbar">
{bar("Solutions", '<a class="pbar-layer" href="/#platform">The stack</a>', '<span class="pbar-status">Six teams</span>', links, SALES, "Contact sales")}
<section class="split-hero" id="overview">
  <div class="container">
    <div>
      <div class="prod-eyebrow"><span class="sl-row"><a class="stack-loc" href="/#platform">Five layers, seven products<span class="visually-hidden">: see the whole stack</span></a></span><span class="badge">Solutions &middot; by team</span></div>
      <h1><span class="line">{E(HUB["h1"][0])}</span>
<span class="line">{E(HUB["h1"][1])}</span></h1>
      <p class="sub">{E(HUB["sub"])}</p>
      <div class="actions">
        <a class="btn btn-primary" href="#teams">Find your team</a>
        <a class="btn btn-ghost" href="/#products">Browse by product</a>
      </div>
      <p class="hero-note">Every product is also sold on its own; a solution page names the ones that usually fit one team.</p>
    </div>
    <div>
      <div class="glance">
        <p class="glance-title">Six teams, five layers</p>
        <dl>
{chr(10).join(f'        <div><dt>{E(d["name"])}</dt><dd>{", ".join(E(PRODUCTS[k][2]) for k, _ in d["stack"])}</dd></div>' for d in SOLUTIONS)}
        </dl>
      </div>
    </div>
  </div>
</section>

<section class="section" id="teams">
  <div class="container">
{head(2, "Teams", "Six teams, one stack", "Each page: the situation, the products and their roles, how it starts, what is in writing, reading, and questions.", "six-teams-one-stack")}
    <div class="sol-grid">
{cards}
    </div>
  </div>
</section>

<section class="section alt" id="how">
  <div class="container">
{head(3, "How to read", "How to read these pages", "", "how-to-read-these-pages")}
    <div class="grid cols-3">
      <div class="card">
        <h3>Statuses are literal</h3>
        <p>Router, FS, Models and Data are in early access; Pipeline, Code and Comic are in development. A solution page that names a product in development says so, and the page describes what is being built.</p>
      </div>
      <div class="card">
        <h3>Nothing is invented</h3>
        <p>No customer names, no uptime numbers, no certifications. What is in writing is linked to the page that holds it: <a href="/terms">the terms</a>, <a href="/privacy">the privacy policy</a>, <a href="/security">the Security page</a> and <a href="/plans">the pricing page</a>.</p>
      </div>
      <div class="card">
        <h3>One product is a fine start</h3>
        <p>The pages describe a path through the stack, not a bundle. Most teams begin with one layer and add the next when the first has earned it.</p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="faq">
  <div class="container">
{head(4, "Questions", "Common questions", "", "common-questions")}
    <div class="qas">
{qas(HUB["faq"])}
    </div>
  </div>
</section>

{close("Tell us which team you are", "Your stack today, the thing you are trying to change, and the volume. A reply within one business day names the products that apply and the ones that do not.", SALES, "Contact sales")}
</main>'''


def hub_schema():
    url = f"{SITE}/solutions"
    return [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": text(HUB["title"]),
         "description": text(HUB["description"]), "url": url, "isPartOf": {"@id": f"{SITE}/#website"},
         "hasPart": [{"@type": "WebPage", "name": f"Runix for {d['name'].lower()}", "url": f"{SITE}/{d['slug']}"} for d in SOLUTIONS]},
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": text(q),
                         "acceptedAnswer": {"@type": "Answer", "text": text(a)}} for q, a in HUB["faq"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList",
         "itemListElement": [
             {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
             {"@type": "ListItem", "position": 2, "name": "Solutions", "item": url}]},
    ]


# ------------------------------------------------------------------- agents
def agents_main():
    d = AGENTS_HUB
    links = [("what", "What an agent is"), ("domains", "By domain"), ("next", "What comes next"),
             ("principles", "Principles"), ("faq", "Questions")]
    num, lname = LAYER_OF["applications"]
    defs = "\n".join(
        f'      <div class="fcell">\n        <span class="fno" aria-hidden="true">{i:02d}</span>\n        <h3>{E(t)}</h3>\n        <p>{L(x)}</p>\n      </div>'
        for i, (t, x) in enumerate(d["definition"], 1))
    doms = []
    for dom in d["domains"]:
        k = dom["product"]
        p = PRODUCTS[k]
        mail = f'mailto:contact@runixcloud.io?subject=Runix%20{p[2].split()[-1]}%20waitlist'
        doms.append(f'''      <div class="adom" id="{dom["key"]}">
        <p class="k">For {E(dom["audience"].lower())}</p>
        <h3>{E(dom["name"])}</h3>
        <p class="aud">Served today by <a href="{p[1]}">{E(p[2])}</a> &middot; {E(p[3])}</p>
        <p>{L(dom["text"])}</p>
        <span class="st">Status: {p[5]}</span>
        <div class="actions">
          <a class="btn btn-primary" href="{p[1]}">Explore {E(p[2])}</a>
          <!--email_off--><a class="btn btn-ghost" href="{mail}">Join the waitlist</a><!--/email_off-->
        </div>
      </div>''')
    dom_pages = {label: slug for slug, label, _focus in DOMAINS}
    nxt = []
    for name, why in d["next"]:
        slug = dom_pages.get(name)
        link = f'\n        <a class="read-more" href="/{slug}">The {E(name)} data rules &rarr;</a>' if slug else ""
        nxt.append(f'      <div class="card">\n        <h3>{E(name)}</h3>\n        <p>{L(why)}</p>{link}\n      </div>')
    princ = "\n".join(
        f'      <div class="card">\n        <h3>{E(t)}</h3>\n        <p>{L(x)}</p>\n      </div>' for t, x in d["principles"])
    glance = "\n".join(
        f'        <div><dt>{E(dom["name"])}</dt><dd>{E(PRODUCTS[dom["product"]][2])} &middot; {PRODUCTS[dom["product"]][5]}</dd></div>'
        for dom in d["domains"])
    return f'''<main id="main" class="has-pbar">
{bar("Agents", f'<a class="pbar-layer" href="/#platform">{num:02d} &middot; {lname}</a>', '<span class="pbar-status">Two agents today</span>', links, SALES, "Contact sales")}
<section class="split-hero" id="overview">
  <div class="container">
    <div>
      <div class="prod-eyebrow"><span class="sl-row"><a class="stack-loc" href="/#platform"><span class="sl-mini" aria-hidden="true"><i class="on"></i><i></i><i></i><i></i><i></i></span>Layer {num:02d} &middot; {lname}<span class="visually-hidden">: see the whole stack</span></a></span><span class="badge">Agents &middot; by domain</span></div>
      <h1><span class="line">{E(d["h1"][0])}</span>
<span class="line">{E(d["h1"][1])}</span></h1>
      <p class="sub">{E(d["sub"])}</p>
      <div class="actions">
        <a class="btn btn-primary" href="#domains">The agents, by domain</a>
        <a class="btn btn-ghost" href="#next">What comes next</a>
      </div>
      <p class="hero-note">Two agents exist today, both in development with waitlists open. The rest of this page says where the next ones come from, without promising one.</p>
    </div>
    <div>
      <div class="glance">
        <p class="glance-title">The layer at a glance</p>
        <dl>
{glance}
        <div><dt>Runs as</dt><dd>An independent agent per domain, each with its own harness</dd></div>
        <div><dt>Gateway</dt><dd>Runix Router is optional in front of an agent's model calls</dd></div>
        <div><dt>Candidates</dt><dd>{", ".join(E(n) for n, _ in d["next"])}: domains the Data layer already has rules for</dd></div>
        </dl>
      </div>
    </div>
  </div>
</section>

<section class="section" id="what">
  <div class="container">
{head(2, "Definitions", "What an agent in this layer is", "Three definitions the rest of the page depends on.", "what-an-agent-in-this-layer-is")}
    <div class="fgrid">
{defs}
    </div>
  </div>
</section>

<section class="section alt" id="domains">
  <div class="container">
{head(3, "By domain", "The agents, by professional domain", "One agent per domain, each built around the tools, data rules, evaluation and review gate of that profession.", "the-agents-by-professional-domain")}
    <div class="agent-dom">
{chr(10).join(doms)}
    </div>
  </div>
</section>

<section class="section" id="next">
  <div class="container">
{head(4, "Next", "Where the next agents come from", "An agent needs its domain's rules before it needs a model. The Data layer already has rules for these four; none of them has an agent announced, and this page does not announce one.", "where-the-next-agents-come-from")}
    <div class="next-grid">
{chr(10).join(nxt)}
    </div>
  </div>
</section>

<section class="section alt" id="principles">
  <div class="container">
{head(5, "Principles", "What every agent here must satisfy", "", "what-every-agent-here-must-satisfy")}
    <div class="grid cols-2">
{princ}
    </div>
  </div>
</section>

<section class="section" id="faq">
  <div class="container">
{head(6, "Questions", "Common questions", "", "common-questions")}
    <div class="qas">
{qas(d["faq"])}
    </div>
  </div>
</section>

{close("Tell us which domain you work in", "The job you want an agent to take over, the material it would work on, and who reviews its output. We reply within one business day with where the nearest agent is and what it can do today.", SALES, "Contact sales")}
</main>'''


def agents_schema():
    d = AGENTS_HUB
    url = f"{SITE}/agents"
    return [
        {"@context": "https://schema.org", "@type": "CollectionPage", "name": text(d["title"]),
         "description": text(d["description"]), "url": url, "isPartOf": {"@id": f"{SITE}/#website"},
         "hasPart": [{"@type": "SoftwareApplication", "name": PRODUCTS[dom["product"]][2],
                      "url": f"{SITE}{PRODUCTS[dom['product']][1]}", "applicationCategory": dom["name"]} for dom in d["domains"]]},
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": text(q),
                         "acceptedAnswer": {"@type": "Answer", "text": text(a)}} for q, a in d["faq"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList",
         "itemListElement": [
             {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
             {"@type": "ListItem", "position": 2, "name": "Agents", "item": url}]},
    ]


# ------------------------------------------------------------------ roadmap
def roadmap_main():
    d = ROADMAP
    links = [("board", "The board"), ("shipped", "Shipped"), ("ga", "At general availability"), ("how", "How it is run"), ("faq", "Questions")]
    shipped = "\n".join(
        f'      <li><span class="when">{E(when)}</span><span class="what">{L(what)} <a href="{href}">{E(label)}</a></span></li>'
        for when, what, href, label in d["shipped"])
    rows = []
    for key, num, lname, _role in LAYERS:
        for pk in [k for k, v in PRODUCTS.items() if v[4] == key]:
            p = PRODUCTS[pk]
            today, next_ = d["products"][pk]
            rows.append(f'''    <div class="rm-row">
      <div class="rm-head"><a href="{p[1]}">{E(p[2])}</a><span>Layer {num:02d} &middot; {lname}</span>{status_span(pk)}</div>
      <div class="rm-cells">
        <div class="rm-cell"><span class="rk">Status</span>{E(p[5].capitalize())}: {L(d["status_line"][p[5]])}</div>
        <div class="rm-cell"><span class="rk">Today</span>{L(today)}</div>
        <div class="rm-cell"><span class="rk">Next</span>{L(next_)}</div>
      </div>
    </div>''')
    ga = "\n".join(
        f'      <div class="card">\n        <h3>{E(t)}</h3>\n        <p>{L(x)}</p>\n      </div>' for t, x in d["ga"])
    princ = "\n".join(
        f'      <div class="card">\n        <h3>{E(t)}</h3>\n        <p>{L(x)}</p>\n      </div>' for t, x in d["principles"])
    counts = {}
    for v in PRODUCTS.values():
        counts[v[5]] = counts.get(v[5], 0) + 1
    glance = "\n".join(f'        <div><dt>{E(st.capitalize())}</dt><dd>{", ".join(E(v[2]) for v in PRODUCTS.values() if v[5] == st)}</dd></div>'
                       for st in ("early access", "in development"))
    return f'''<main id="main" class="has-pbar">
{bar("Roadmap", '<a class="pbar-layer" href="/about">Company</a>', '<span class="pbar-status">No dates published</span>', links, SALES, "Contact sales")}
<section class="split-hero" id="overview">
  <div class="container">
    <div>
      <div class="prod-eyebrow"><span class="sl-row"><a class="stack-loc" href="/#platform">Five layers, seven products<span class="visually-hidden">: see the whole stack</span></a></span><span class="badge">Roadmap &middot; statuses are literal</span></div>
      <h1><span class="line">{E(d["h1"][0])}</span>
<span class="line">{E(d["h1"][1])}</span></h1>
      <p class="sub">{E(d["sub"])}</p>
      <div class="actions">
        <a class="btn btn-primary" href="#board">The board</a>
        <a class="btn btn-ghost" href="/about">About the company</a>
      </div>
      <p class="hero-note">Drawn from the same product definitions as the home page and the header, so this page cannot say one thing and the stack another.</p>
    </div>
    <div>
      <div class="glance">
        <p class="glance-title">Seven products today</p>
        <dl>
{glance}
        <div><dt>Dates</dt><dd>None published. Cohorts and design partners set the order.</dd></div>
        </dl>
      </div>
    </div>
  </div>
</section>

<section class="section" id="board">
  <div class="container">
{head(2, "Board", "The board", "One row per product: its status, what a team can do with it today, and the next thing that changes.", "the-board")}
    <div class="rmap">
      <div class="rm-legend"><span>Product</span><span>Status</span><span>Today</span><span>Next</span></div>
{chr(10).join(rows)}
    </div>
  </div>
</section>

<section class="section alt" id="shipped">
  <div class="container">
{head(3, "Shipped", "What has shipped, with the date", "The dates the site already publishes, in order. A state is published when it is reached.", "what-has-shipped")}
    <ol class="shipped">
{shipped}
    </ol>
  </div>
</section>

<section class="section" id="ga">
  <div class="container">
{head(4, "At GA", "What general availability adds", E(d["ga_lede"]), "what-general-availability-adds")}
    <div class="grid cols-3">
{ga}
    </div>
  </div>
</section>

<section class="section alt" id="how">
  <div class="container">
{head(5, "How it is run", "How the roadmap is run", "", "how-the-roadmap-is-run")}
    <div class="grid cols-3">
{princ}
    </div>
    <div class="feature" style="margin-top: 48px;">
      <div>
        <h3>Early access</h3>
        <p>{L(d["now"])}</p>
      </div>
      <div>
        <h3>In development</h3>
        <p>{L(d["building"])}</p>
      </div>
    </div>
  </div>
</section>

<section class="section" id="faq">
  <div class="container">
{head(6, "Questions", "Common questions", "", "common-questions")}
    <div class="qas">
{qas(d["faq"])}
    </div>
  </div>
</section>

{close("Ask about the product you are waiting for", "Tell us which product and what you would do with it. We reply within one business day with where it is and what you could use today.", SALES, "Contact sales")}
</main>'''


def roadmap_schema():
    d = ROADMAP
    url = f"{SITE}/roadmap"
    return [
        {"@context": "https://schema.org", "@type": "WebPage", "name": text(d["title"]),
         "description": text(d["description"]), "url": url, "isPartOf": {"@id": f"{SITE}/#website"},
         "about": {"@id": f"{SITE}/#org"}},
        {"@context": "https://schema.org", "@type": "FAQPage",
         "mainEntity": [{"@type": "Question", "name": text(q),
                         "acceptedAnswer": {"@type": "Answer", "text": text(a)}} for q, a in d["faq"]]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList",
         "itemListElement": [
             {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
             {"@type": "ListItem", "position": 2, "name": "Company", "item": f"{SITE}/about"},
             {"@type": "ListItem", "position": 3, "name": "Roadmap", "item": url}]},
    ]


# ------------------------------------------------------------------ render
def page(shell, slug, title, description, main_html, blocks):
    s = shell
    url = f"{SITE}/{slug}"
    assert '"' not in description, f"{slug}: a description must not contain a double quote"
    t, dsc = html.escape(title, quote=False), html.escape(description, quote=False)
    s = re.sub(r"<title>.*?</title>", f"<title>{t}</title>", s, count=1)
    for prop in ("og:title", "twitter:title"):
        attr = "property" if prop.startswith("og") else "name"
        s = re.sub(rf'<meta {attr}="{prop}" content="[^"]*">', f'<meta {attr}="{prop}" content="{t}">', s, count=1)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{dsc}">', s, count=1)
    for prop in ("og:description", "twitter:description"):
        attr = "property" if prop.startswith("og") else "name"
        s = re.sub(rf'<meta {attr}="{prop}" content="[^"]*">', f'<meta {attr}="{prop}" content="{dsc}">', s, count=1)
    s = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', s, count=1)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', s, count=1)

    def card(m):
        if f"/assets/og/{slug}.png" in m.group(2):
            return m.group(0)
        return f"{m.group(1)}{SITE}/assets/og/{slug}.png?v=0{m.group(3)}"
    s = re.sub(r'(<meta (?:property="og:image"|name="twitter:image") content=")([^"]*)(")', card, s)
    # Only the page's own blocks are replaced; the shared Organization graph
    # (tools/add_org_graph.py) sits after them and stays.
    found = [m for m in re.finditer(r'<script type="application/ld\+json">.*?</script>\n?', s, re.S)
             if '"@graph"' not in m.group(0)]
    ld = "\n".join('<script type="application/ld+json">\n' + json.dumps(b, ensure_ascii=False, indent=2) + "\n</script>" for b in blocks)
    if found:
        s = s[:found[0].start()] + ld + "\n" + s[found[-1].end():]
    a, b = s.index('<main id="main"'), s.index("</main>") + len("</main>")
    return s[:a] + main_html + s[b:]


def ensure_sitemap(slugs):
    sm = pathlib.Path("sitemap.xml")
    t = sm.read_text(encoding="utf-8")
    import datetime, zoneinfo
    today = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Shanghai")).date().isoformat()
    added = 0
    for slug in slugs:
        if f"<loc>{SITE}/{slug}</loc>" in t:
            continue
        entry = f'  <url><loc>{SITE}/{slug}</loc><lastmod>{today}</lastmod><priority>0.7</priority></url>\n'
        anchor = f"  <url><loc>{SITE}/docs/</loc>"
        t = t.replace(anchor, entry + anchor, 1) if anchor in t else t.replace("</urlset>", entry + "</urlset>", 1)
        added += 1
    if added:
        sm.write_text(t, encoding="utf-8")
    return added


def write_home():
    """The home page's "Who it is for" grid and roadmap summary, between markers."""
    home = pathlib.Path("index.html")
    if not home.exists():
        return 0
    s = home.read_text(encoding="utf-8")
    orig = s
    if "<!--teams-->" in s:
        cards = "\n".join(solcard(d) for d in SOLUTIONS)
        s = re.sub(r"<!--teams-->.*?<!--/teams-->",
                   '<!--teams-->\n    <div class="sol-grid">\n' + cards + '\n    </div>\n    <!--/teams-->',
                   s, count=1, flags=re.S)
    if "<!--roadmap-->" in s:
        ea = [v for v in PRODUCTS.values() if v[5] == "early access"]
        dev = [v for v in PRODUCTS.values() if v[5] == "in development"]
        li = lambda items: "".join(f'\n          <li><a href="{v[1]}">{E(v[2])}</a><span>{E(v[3])}</span></li>' for v in items)  # noqa: E731
        ga = "".join(f'\n          <li><b>{E(t)}</b></li>' for t, _ in ROADMAP["ga"])
        block = f'''<!--roadmap-->
    <div class="grid cols-3 rm-sum">
      <div class="card">
        <p class="card-layer"><b>Now</b> &middot; early access</p>
        <h3>{len(ea)} products a team can use today</h3>
        <ul class="wlist">{li(ea)}
        </ul>
      </div>
      <div class="card">
        <p class="card-layer">Building &middot; in development</p>
        <h3>{len(dev)} products with waitlists and design partners</h3>
        <ul class="wlist">{li(dev)}
        </ul>
      </div>
      <div class="card">
        <p class="card-layer">Next &middot; at general availability</p>
        <h3>What general availability adds</h3>
        <ul class="wlist">{ga}
        </ul>
        <a class="read-more" href="/roadmap">The roadmap, without dates &rarr;</a>
      </div>
    </div>
    <!--/roadmap-->'''
        s = re.sub(r"<!--roadmap-->.*?<!--/roadmap-->", block, s, count=1, flags=re.S)
    if s != orig:
        home.write_text(s, encoding="utf-8")
        return 1
    return 0


def main():
    shell = SHELL.read_text(encoding="utf-8")
    jobs = [("solutions", HUB["title"], HUB["description"], hub_main(), hub_schema()),
            ("agents", AGENTS_HUB["title"], AGENTS_HUB["description"], agents_main(), agents_schema()),
            ("roadmap", ROADMAP["title"], ROADMAP["description"], roadmap_main(), roadmap_schema())]
    for d in SOLUTIONS:
        jobs.append((d["slug"], d["title"], d["description"], solution_main(d), solution_schema(d)))
    changed = 0
    for slug, title, desc, main_html, blocks in jobs:
        p = pathlib.Path(f"{slug}.html")
        old = p.read_text(encoding="utf-8") if p.exists() else None
        new = page(old or shell, slug, title, desc, main_html, blocks)
        if new != old:
            p.write_text(new, encoding="utf-8")
            changed += 1
    changed += write_home()
    added = ensure_sitemap([j[0] for j in jobs])
    print(f"solutions, agents, roadmap: {changed} page(s) changed; sitemap +{added}")


if __name__ == "__main__":
    main()
