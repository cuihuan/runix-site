#!/usr/bin/env python3
"""Write the retry-budget post into scheduled/.

'llm retry budget' is a long-tail query with no good answer page. The post
connects three things teams configure separately — per-request retries,
failover, and cost control — and argues they are one budget. Operational, no
vendor bashing, no invented numbers.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "llm-retry-budget"
TITLE = "Retry budgets for LLM APIs — Runix"
H1 = "Your LLM traffic needs a retry budget, not a retry count"
DESC = ("Retries multiply cost and load exactly when a provider is struggling. What a retry "
        "budget is, which errors deserve one, and how failover changes the arithmetic.")

BODY = """<p>Every HTTP client library has a retry knob, and for most APIs the default —
three attempts with exponential backoff — is fine, because most API calls are cheap and
idempotent. LLM calls are neither. A retried request re-sends the full prompt at full input
price, re-generates output you may already have paid for once, and lands on a provider at
the exact moment it is least able to serve it. The right mental model is not "how many times
should I retry" but "how much am I willing to spend on requests that have already failed
once" — a budget, not a count.</p>

<h2>Why retry counts go wrong for model traffic</h2>

<p>Three properties of LLM requests break the standard advice:</p>

<ul>
<li><strong>Requests are expensive and slow.</strong> A retried call is not a few
    milliseconds and a fraction of a cent; it can be thirty seconds and a meaningful
    fraction of the original cost. Retrying a large-context request three times quadruples
    its worst-case bill.</li>
<li><strong>Failures cluster.</strong> Rate limits and overload errors do not arrive
    uniformly; they arrive in bursts, provider-wide. When every client retries three times
    into the same burst, offered load triples at the worst moment. That is retry
    amplification, and it is how a provider's bad five minutes becomes your bad hour.</li>
<li><strong>Streams fail halfway.</strong> A streamed response that dies after 800 tokens
    already cost you those 800 output tokens on most providers. Retrying from scratch pays
    for them again. A retry policy that ignores partial output undercounts its own cost by
    the exact amount that hurts.</li>
</ul>

<h2>Sort errors before you spend on them</h2>

<p>A budget is only spent on failures that a retry can actually fix. That sorting is the
most valuable part of the whole exercise:</p>

<ul>
<li><strong>Retry, with backoff:</strong> 429 with a <code>retry-after</code> hint (honour
    the hint, not your own schedule), 500/502/503, connection resets, and timeouts where
    nothing was received. These are transient by definition.</li>
<li><strong>Do not retry:</strong> 400 (the request is malformed — it will be malformed
    again), 401/403 (credentials will not heal), 404 on a model id (it is gone; see
    deprecations), and content-policy refusals (deterministic on the same input — a retry is
    a second bill for the same no).</li>
<li><strong>Retry somewhere else:</strong> persistent 429s and overload responses on one
    provider while your error budget drains are not a retry problem, they are a routing
    problem. The correct "retry" is the same request against a different provider or model —
    failover — and it should draw from the same budget, because from the caller's point of
    view it is the same spend on the same failed intent.</li>
</ul>

<h2>What a budget looks like in practice</h2>

<p>Two limits, one global and one local:</p>

<ul>
<li><strong>Per-request:</strong> at most one or two extra attempts, ever, and a ceiling on
    total wall-clock time. The user has stopped waiting; there is no request so important
    that the fourth attempt rescues it.</li>
<li><strong>Global:</strong> retries as a percentage of traffic — if more than a few percent
    of requests system-wide are retries, stop retrying and start failing fast or failing
    over. This is the circuit-breaker view: the budget protects you from your own policy
    during an incident, which is precisely when the per-request view looks locally
    reasonable and is globally ruinous.</li>
</ul>

<p>The global limit is the one almost nobody implements, because it needs a place where all
LLM traffic is visible at once. Per-service retry configuration cannot see that the fleet
collectively tripled its offered load; a shared choke point can. That is the operational
argument for routing model traffic through one layer — whether that is a
<a href="/router">gateway</a> or something you built — and giving that layer, not each
client, the retry policy.</p>

<h2>The accounting question</h2>

<p>However you implement it, make retries visible in cost attribution. A request that
succeeded on attempt three should carry the cost of all three attempts, including the partial
output of any stream that died — otherwise your per-feature cost numbers silently exclude
exactly the traffic that is most expensive per successful answer. When an incident review
asks "what did that outage cost us", the difference between billed tokens and
tokens-per-successful-request is the answer, and you can only compute it if the ledger kept
attempts distinct from successes.</p>

<p>None of this is exotic to build, but all of it has to live in one place to work: the
timeout chain, the error sorting, the failover targets and the budget are one policy seen
from four angles. Splitting them across client libraries is how each piece ends up locally
correct and the system ends up retrying a content refusal four times during a rate-limit
storm — at full price.</p>
"""

template = pathlib.Path("blog/did-the-model-change-make-it-worse.html").read_text()
url = f"{SITE}/blog/{SLUG}"

page = template
page = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", page, count=1)
for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
    page = re.sub(rf'({re.escape(attr)} content=")[^"]*(")', lambda m: m.group(1) + DESC + m.group(2), page, count=1)
for attr in ('property="og:title"', 'name="twitter:title"'):
    page = re.sub(rf'({re.escape(attr)} content=")[^"]*(")', lambda m: m.group(1) + TITLE + m.group(2), page, count=1)
page = re.sub(r'(<link rel="canonical" href=")[^"]*(">)', rf"\g<1>{url}\g<2>", page, count=1)
page = re.sub(r'(<meta property="og:url" content=")[^"]*(">)', rf"\g<1>{url}\g<2>", page, count=1)


def _fix(block):
    d = json.loads(block)
    if d.get("@type") == "Article":
        d["headline"], d["description"], d["url"] = H1, DESC, url
        if isinstance(d.get("mainEntityOfPage"), dict):
            d["mainEntityOfPage"]["@id"] = url
    elif d.get("@type") == "BreadcrumbList":
        leaf = max(d["itemListElement"], key=lambda i: i["position"])
        leaf["name"], leaf["item"] = H1, url
    return json.dumps(d, ensure_ascii=False, indent=2)


page = re.sub(r'(<script type="application/ld\+json">\n)(.*?)(\n</script>)',
              lambda m: m.group(1) + _fix(m.group(2)) + m.group(3), page, flags=re.S)

words = len(re.sub(r"<[^>]+>", " ", BODY).split())
minutes = max(1, round(words / 200))
page = re.sub(r'(<div class="post-meta"><span class="cat">)[^<]*(</span><span>)[^<]*(</span><span>·</span><span>)[^<]*(</span></div>)',
              rf"\g<1>Engineering\g<2>PENDING\g<3>{minutes} min read\g<4>", page, count=1)
page = re.sub(r'(<h1 style="margin-top: 14px;">).*?(</h1>)', rf"\g<1>{H1}\g<2>", page, count=1, flags=re.S)

start = page.index('<article class="article">') + len('<article class="article">')
end = page.index("</article>")
page = page[:start] + "\n" + BODY.strip() + "\n" + page[end:]
page = re.sub(r'<aside class="related">.*?</aside>\s*', "", page, flags=re.S)

out = pathlib.Path("scheduled") / f"{SLUG}.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print(f"  wrote {out} — {words} words, {minutes} min read")
