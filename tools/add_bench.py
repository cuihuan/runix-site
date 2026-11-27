#!/usr/bin/env python3
"""Add Runix Bench, the open LLM gateway benchmark, as a product page (2026-11-27).

The benchmark has run in public since 2026-10 (github.com/cuihuan/llm-gateway-bench,
live at benchmark.runixcloud.io) and the site mentioned it in one sentence on
the home page. It is now a product in the Gateway layer: the tool that measures
the layer, ours included.

Everything stated here comes from that repository: the five dimensions and
their rules (docs/methodology.md), the probe cadence (.github/workflows/probe.yml,
every six hours), the 30-day window and the endpoint count (web/data.json as of
2026-11-27: eleven endpoints, three of them official direct baselines) and the
hosted Terminal-Bench runner (runner/README.md).

Writes bench.html in the shape the product builders expect (a split hero with
two columns, section heads, a Common questions section, a closing band); then
run stack_build.py, product_template.py and sync_schema.py, which add the
locator, the product bar, the panel, the specifications and the numbering.
Also adds the page to the sitemap. Idempotent: an existing bench.html is left
alone (edit it, or delete it to rebuild).
"""
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from make_page import _chrome  # noqa: E402

SITE = "https://runixcloud.io"
LIVE = "https://benchmark.runixcloud.io/"
REPO = "https://github.com/cuihuan/llm-gateway-bench"
TITLE = "Runix Bench — Open Benchmark for LLM Gateways and APIs"
DESC = ("Runix Bench measures any OpenAI-compatible LLM gateway from the outside: "
        "price against list, latency, 30-day uptime and whether the model is real.")

QAS = [
    ("What does Runix Bench measure?",
     "Five things about an LLM gateway or relay, in the order they matter to the team that depends on it: whether it can be trusted (the model behind the endpoint, data retention, a legal entity), its price against the official list price, its success rate over 30 days, its speed (time to first token and throughput), and whether repeated prompts hit a cache."),
    ("Is it free?",
     "Yes. The probe, the methodology and every raw result are open source under the MIT licence, and the self-test runs on your own machine with your own key. Managed probing and report hosting are described on the benchmark site."),
    ("Does my API key leave my machine?",
     "No. The self-test runs locally and calls the gateway you point it at directly. The key is read from an environment variable and is not written to the report."),
    ("Is Runix Router in the table?",
     "Not today. One gateway in the table is run by a related party; it is marked as such on its row and rated by the same rules as everyone else, never a tier higher for the relationship."),
    ("How often is the table updated?",
     "Every six hours, from a scheduled job that commits each run to the repository. Success rates are computed over a rolling 30-day window, with the 7-day figure beside it."),
    ("Why would a gateway company publish a gateway benchmark?",
     "Because a buyer should not have to trust any gateway's claims, including ours. The benchmark is built to be checked rather than believed: the prompts are in the script, the raw data is public and anyone can rerun it against the same endpoints."),
]


def section(cls, sid, h2, lede, body):
    sid_attr = f' id="{sid}"' if sid else ""
    lede_html = f"\n      <p>{lede}</p>" if lede else ""
    return f'''<section class="section{cls}"{sid_attr}>
  <div class="container">
    <div class="section-head center">
      <h2>{h2}</h2>{lede_html}
    </div>
{body}
  </div>
</section>'''


def fgrid(items):
    cells = "\n".join(f'''      <div class="fcell">
        <span class="fno" aria-hidden="true">{i:02d}</span>
        <h3>{t}</h3>
        <p>{p}</p>
      </div>''' for i, (t, p) in enumerate(items, 1))
    return f'    <div class="fgrid">\n{cells}\n    </div>'


def qas():
    items = "\n".join(f'''      <div class="qa">
        <h3>{q}</h3>
        <p>{a}</p>
      </div>''' for q, a in QAS)
    return f'    <div class="qas">\n{items}\n    </div>'


def page():
    head_common, header, footer = _chrome()
    url = f"{SITE}/bench"
    schema = [
        {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "Runix Bench",
         "applicationCategory": "DeveloperApplication", "operatingSystem": "Any",
         "description": "An open, black-box benchmark for LLM API gateways and relays: trust and integrity, price against list, 30-day stability, speed and cache behaviour, reproducible with your own key.",
         "url": url, "publisher": {"@id": f"{SITE}/#org"},
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
         "isBasedOn": {"@type": "SoftwareSourceCode", "name": "LLM Gateway Bench", "codeRepository": REPO,
                       "license": "https://opensource.org/licenses/MIT", "programmingLanguage": "JavaScript"}},
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in QAS]},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Runix Bench", "item": url}]},
    ]
    blocks = "".join('<script type="application/ld+json">\n' + json.dumps(b, ensure_ascii=False, indent=2)
                     + "\n</script>\n" for b in schema)
    hero = f'''<section class="split-hero">
  <div class="container">
    <div>
      <span class="badge">Runix Bench · Available</span>
      <h1><span class="line">The open benchmark</span>
<span class="line">for LLM gateways</span></h1>
      <p class="sub">Runix Bench measures any OpenAI-compatible gateway or relay from the outside, the way your application sees it: price against the official list price, time to first token and throughput, success rate over 30 days, and whether the model behind the endpoint is the one on the label. Every raw result is public.</p>
      <div class="actions">
        <a class="btn btn-primary" href="{LIVE}">See the live leaderboard</a>
        <a class="btn btn-ghost" href="{REPO}" rel="noopener">Run it on your gateway</a>
      </div>
      <p class="hero-note">Open source under the MIT licence. Measure, don't trust: the probe, the prompts and the data are in <a href="{REPO}" rel="noopener">the repository</a>, so a result can be checked rather than believed.</p>
    </div>
    <div>
    </div>
  </div>
</section>'''
    term = f'''<section class="section example-band" id="example">
  <div class="container">
    <div class="example-grid">
      <div class="term">
        <div class="term-bar"><i></i><i></i><i></i><b>test your own gateway</b></div>
<pre>$ git clone {REPO}
$ cd llm-gateway-bench && npm install
$ PROBE_KEY=<span class="g">$YOUR_KEY</span> npm run compare -- \\
    --model your-model-id \\
    --url https://your-gateway.example \\
    --name <span class="g">"My Gateway"</span> --price-in 0.2 --price-out 1.0
# a self-contained report: the gap to the best on price,
# speed, stability, behaviour and cache</pre>
      </div>
      <div class="example-note">
        <p class="example-title">compare a gateway with the best</p>
        <p>One command against the gateway you already use, with your own key. The report puts it beside the best measured endpoint on each dimension, and the key never leaves your machine.</p>
      </div>
    </div>
  </div>
</section>'''
    dims = section("", "capabilities", "Five questions, in the order they matter",
                   "A team picking a gateway asks whether it can trust it, then whether it is cheap, then whether it stays up. The benchmark answers in that order, and reads a low price next to trust: a gateway far under list price is a warning sign, not a bargain.",
                   fgrid([
                       ("Trust and integrity", "Is it the real model, and will the operator still be there? A fixed request set goes to the gateway and to the official API at once, following the K2 Vendor Verifier method, and the answers are compared. Data retention and the legal entity are annotated with links to the source."),
                       ("Price against list", "The gateway's price divided by the official list price, per model and as one index across models. Cache pricing and hidden multipliers are recorded beside it."),
                       ("Stability over 30 days", "Success rate from a probe every six hours, with rate limits, outages and timeouts counted apart. Errors the probe causes itself, such as an unauthorised key, are excluded and shown separately."),
                       ("Speed", "Time to first token at p50, and p95 only when a run has at least five samples. Throughput is counted after the first token, the convention llmperf and Artificial Analysis use. Fake streaming, a reply buffered and then dumped, is flagged."),
                       ("Cache", "Whether a repeated prompt is billed and served as a cache hit, measured rather than taken from the price page."),
                       ("Three ratings, no fourth", "Each claim is verified, claimed but unverified, or unverified. Nothing without an evidence link is ever marked verified, and a related party is never rated a tier higher for the relationship."),
                   ]))
    how = section(" alt", "how", "Where it sits, and how it measures",
                  "The benchmark stands where your application stands: outside the gateway, calling its public endpoint. It needs no access to anyone's infrastructure and no cooperation from the operator.",
                  fgrid([
                      ("A public probe", "The probe script and its prompts are in the repository. Each request carries a random id so a gateway cannot serve it from a cache, output is capped, and concurrency stays at four or under so a run never becomes a load test."),
                      ("Scheduled, then committed", "A scheduled job probes every tracked endpoint every six hours and commits the raw result. Leaderboard figures come from a rolling 30-day window; older runs stay in the data and do not move the table."),
                      ("Agent runs on Terminal-Bench", "Beyond single calls, the same Terminal-Bench tasks can run through two routers with Claude Code or Codex as the agent, verifier scores and costs side by side, with A/A and A/B statistics. These runs are hosted by our team on request."),
                      ("Unknown stays unknown", "A measurement that could not be taken is shown as missing, never as zero. Network latency from a scheduled runner is labelled as an estimate, and the probe region is printed on every figure."),
                  ]))
    why = section("", None, "Why a gateway company publishes a gateway benchmark",
                  "We sell a gateway, so a benchmark we run could be read as marketing. It is built so that it does not have to be trusted: the method is written down before the numbers, the raw data is public, and anyone can rerun it against the same endpoints with their own key. That is the same rule we hold our own products to.",
                  f'''    <div class="grid cols-3">
      <a class="card card-clickable" href="{LIVE}" rel="noopener" aria-label="Open the leaderboard">
        <p class="card-layer">Live</p>
        <h3>The leaderboard</h3>
        <p>Eleven endpoints as of 2026-11-27: eight gateways and three official direct connections as the baseline.</p>
        <span class="read-more">Open the leaderboard&nbsp;&rarr;</span>
      </a>
      <a class="card card-clickable" href="{REPO}/blob/main/docs/methodology.md" rel="noopener" aria-label="Read the methodology">
        <p class="card-layer">Method</p>
        <h3>The methodology</h3>
        <p>Every metric, how it is collected, what is excluded and why, with the sources each convention follows.</p>
        <span class="read-more">Read the methodology&nbsp;&rarr;</span>
      </a>
      <a class="card card-clickable" href="/blog/how-to-benchmark-an-llm-gateway" aria-label="Read the guide">
        <p class="card-layer">Guide</p>
        <h3>How to benchmark a gateway</h3>
        <p>The checks to run before a gateway carries production traffic, and the red flags each one catches.</p>
        <span class="read-more">Read the guide&nbsp;&rarr;</span>
      </a>
    </div>''')
    start = section(" alt", "early-access", "How to start",
                    "Runix Bench is self-serve. Nothing here needs an account with us.",
                    '''    <div class="prun">
      <div class="pstep">
        <h3><span class="pstep-n">01</span>Read the table</h3>
        <p>Open the live leaderboard and sort by the dimension you care about. Each figure links to the run it came from.</p>
      </div>
      <div class="pstep">
        <h3><span class="pstep-n">02</span>Test your own gateway</h3>
        <p>Clone the repository and run the self-test with your own key. It writes one report you can share.</p>
      </div>
      <div class="pstep">
        <h3><span class="pstep-n">03</span>Ask for an agent run</h3>
        <p>For a comparison of two routers on Terminal-Bench, <!--email_off--><a href="mailto:sales@runixcloud.io?subject=Runix%20Bench%20agent%20run">write to us</a><!--/email_off--> with the models and the routers to compare.</p>
      </div>
    </div>''')
    faq = section("", "faq", "Common questions", None, qas())
    close = f'''<section class="section section-end">
  <div class="container">
    <div class="cta-band">
      <h2>Measure the gateway you already use</h2>
      <p>One command, your own key, a report that shows where it stands against the best on price, speed, stability and integrity.</p>
      <a class="btn btn-grad" href="{REPO}" rel="noopener">Run the self-test</a>
    </div>
  </div>
</section>'''
    body = "\n\n".join([hero, term, dims, how, why, start, faq, close])
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
{head_common}
<title>{TITLE}</title>
<meta name="description" content="{DESC}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{DESC}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Runix Lab">
<meta property="og:image" content="{SITE}/assets/og-cover.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}/assets/og-cover.png">
<meta property="og:locale" content="en_US">
<meta name="twitter:title" content="{TITLE}">
<meta name="twitter:description" content="{DESC}">
{blocks}</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
{header}

<main id="main">
{body}
</main>

{footer}

</body>
</html>
"""


def main():
    p = pathlib.Path("bench.html")
    changed = []
    if not p.exists():
        p.write_text(page(), encoding="utf-8")
        changed.append("bench.html")
    sm = pathlib.Path("sitemap.xml")
    t = sm.read_text(encoding="utf-8")
    if "/bench</loc>" not in t:
        t = t.replace('  <url><loc>https://runixcloud.io/fs</loc>',
                      '  <url><loc>https://runixcloud.io/bench</loc><lastmod>2026-11-27</lastmod><priority>0.9</priority></url>\n'
                      '  <url><loc>https://runixcloud.io/fs</loc>', 1)
        sm.write_text(t, encoding="utf-8")
        changed.append("sitemap.xml")
    print("add bench: " + (", ".join(changed) if changed else "nothing to do"))


if __name__ == "__main__":
    main()
