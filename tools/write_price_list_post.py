#!/usr/bin/env python3
"""Write the billing-reconciliation post into scheduled/.

Nobody writes about the mechanics of why a token bill diverges from the
vendor's price list — cache multipliers, injected prompts, tokenizer churn,
tiered and off-peak rates. We spent a day reconciling a gateway's rate tables
against five vendors' pricing pages and this is the write-up. Fact-dense on
purpose; every number is from a public price list or our own ledger.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "why-your-llm-bill-doesnt-match-the-price-list"
TITLE = "Why your LLM bill doesn't match the price list — Runix"
H1 = "Why your LLM bill doesn't match the price list"
DESC = ("Cache multipliers, injected prompts, tokenizer changes, tiered rates: the mechanics "
        "behind a surprising token bill, and how to reconcile one request by hand.")

BODY = """<p>The per-token price is the one number everybody checks before picking a model, and
it is almost never the number that explains the bill. We recently reconciled a gateway's
rate tables against five vendors' published price lists, line by line, and then verified the
result by billing a single live request and recomputing it by hand. The differences we found
along the way fall into five mechanics, none of which appear in the headline price.</p>

<h2>1. Cached tokens have their own prices — two of them</h2>

<p>Every major provider now prices cached prompt tokens separately, and the multipliers are
not standardized. Reading a cached prefix typically costs about a tenth of the input rate —
OpenAI lists cached input at 10% of the normal price, Anthropic at 0.1&times;, and some
vendors go far lower still. Writing the cache is where they diverge: Anthropic charges a
25% premium on cache writes (more for a longer-lived cache), MiniMax similarly lists a write
price a quarter above input, while OpenAI charges nothing at all to create the cache.</p>

<p>That asymmetry means the same traffic pattern — a long, stable system prompt reused across
requests — produces structurally different bills per provider. It also means a billing layer
that applies one provider's multipliers to another's models is wrong in a way nobody notices:
the request succeeds, the ledger has numbers in it, and the numbers are quietly 25% off on
every cache write, or ten times too high on every cache read a missing entry falls back to
full price for.</p>

<p><strong>Check it:</strong> your usage object reports cached tokens separately
(<code>cache_read_input_tokens</code>, <code>cached_tokens</code>, or a vendor equivalent).
If your cost model multiplies total input tokens by one rate, it disagrees with the invoice
on exactly the workloads caching was supposed to make cheap.</p>

<h2>2. The prompt you sent is not the prompt you paid for</h2>

<p>Tools and agents inject context. System prompts, tool schemas, harness instructions,
memory files — all of it is input tokens at full price. The starkest example from our own
ledger: a two-word request ("Say OK") sent through a coding-assistant proxy arrived at the
model as <strong>4,099 prompt tokens</strong>, because the upstream injects its agent
scaffolding into every conversation. The reply was one token. More than 99.9% of that
request's cost was context the caller never wrote.</p>

<p>This is not misbehaviour — the scaffolding is what makes the tool work — but it changes
which price matters. For agentic traffic, the input rate and the cache-read rate dominate
everything else, because the injected prefix is large, repeated, and (if the provider and
client cooperate) cacheable. A model with a cheap output price and no cache discount can
cost more in an agent loop than a nominally pricier model with 0.1&times; cache reads.</p>

<h2>3. Tokenizers change between model generations</h2>

<p>Prices are quoted per million tokens, but the tokenizer decides how many tokens your text
is — and vendors revise tokenizers between model families. A recent Sonnet-generation change,
for example, tokenizes the same text to roughly 30% more tokens than its predecessor, which
shifts every token-denominated number: measured context usage, <code>max_tokens</code>
budgets, and the effective price of identical traffic, all without a price-list change.</p>

<p><strong>Check it:</strong> never reuse token counts measured on one model to budget
another. Count against the model you will bill on; the count endpoints are free.</p>

<h2>4. Tiered, off-peak and regional prices</h2>

<p>Some price lists are not one number per model. Alibaba's Qwen coder models bill the whole
request at a higher rate once the input crosses a context threshold (with three tiers, the
top one at more than double the base). DeepSeek publishes standard rates and a 50%-off
window covering most of the day. Several vendors publish different prices for their mainland
and international platforms for the same model id. A flat per-model rate — which is what most
billing layers, ours included, can express — is therefore an approximation of some vendors'
lists by construction. The honest options are to pin the rate to the tier most of your
traffic lands in and say so, or to bill at the ceiling. Silence is the only wrong choice.</p>

<h2>5. Models leave the price list</h2>

<p>The strangest case we hit: a model that was still serving traffic but no longer on its
vendor's price page at all — the line had been discontinued and replaced two weeks earlier,
and the old id lived on only in intermediaries' catalogues. There is no "official price" for
such a model; whatever anyone charges for it is a policy, not an alignment. If your provider
serves ids the upstream vendor has retired, ask what actually answers those requests, because
the answer decides what the fair rate would be.</p>

<h2>Reconcile one request by hand</h2>

<p>All five mechanics reduce to one habit: take a single real request and recompute its cost
from the raw numbers. The formula is the same everywhere:</p>

<pre><code>cost = plain_input &times; input_rate
     + cache_reads &times; cache_read_rate
     + cache_writes &times; cache_write_rate
     + output &times; output_rate</code></pre>

<p>Pull each token count from the response's usage object, each rate from the vendor's
pricing page (not from memory — they change), and compare against what your ledger recorded.
When we ran this against our own gateway after the audit, the recomputed figure matched the
ledger to the rounding of a single quota unit. When it does not match, one of the five
mechanics above is the reason, and now you know which number to go look at.</p>

<p>This is also, incidentally, the test to run against any gateway or reseller before
trusting its billing — <a href="/router">ours included</a>. A provider that shows you
per-request token breakdowns and survives a hand recomputation has earned the invoice. One
that only shows monthly totals is asking you to take the five mechanics on faith.</p>

<p class="note-line">Multipliers and list prices referenced above were read from the vendors'
own pricing pages on 20 August 2026. They change without notice — treat the mechanics as
durable and the numbers as a snapshot.</p>
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
