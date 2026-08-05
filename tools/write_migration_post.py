#!/usr/bin/env python3
"""Write the gateway-migration post into scheduled/.

Bottom-of-funnel: for the reader who has decided to put a gateway in front of
their traffic and has to do it without a maintenance window. Everything in it
is standard production practice — shadow traffic, percentage cutover, a
rollback that is one config change — plus the specific things about LLM traffic
that make the usual playbook insufficient: streaming, non-determinism, and
usage accounting that must not double-count during the overlap.

No Runix performance figure appears in it, and no competitor is named.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "migrating-to-an-llm-gateway-without-downtime"
TITLE = "Moving production LLM traffic to a gateway — Runix"
H1 = "Migrating to a gateway without a maintenance window"
DESC = ("Shadow, then a percentage, then a cutover you can reverse in one config change — "
        "and the three things about LLM traffic the usual playbook does not cover.")

BODY = """<p>Putting a gateway in front of live model traffic is a routing change on the hot
path of a product that is already earning money. The usual migration playbook applies —
shadow, ramp, keep the rollback one config change away — but LLM traffic breaks three of its
assumptions, and those are where migrations go wrong.</p>

<p>This is the sequence that works, and what to watch at each step.</p>

<h2>Before you start: make the endpoint a variable</h2>

<p>If the base URL is a string literal in your services, everything below requires a deploy,
which means your rollback also requires a deploy — and a rollback you cannot perform in
seconds is not a rollback. Move the base URL and the key into configuration you can change
without shipping code, and confirm you can change it and see the effect. That check is the
whole migration in miniature; if it does not work, nothing after this matters.</p>

<p>The same indirection is what lets you change model ids later without a redeploy, which is
a separate problem with the same solution — covered in
<a href="/blog/model-deprecation-without-a-redeploy">a post of its own</a>.</p>

<h2>Step 1: shadow, and compare what you can</h2>

<p>Send a copy of real requests through the gateway while the original path continues to
serve users. Discard the shadow response. You are not testing correctness yet — you are
testing that the request shape survives the trip.</p>

<p>What to compare on the shadow path:</p>

<ul>
<li><strong>Status codes.</strong> Any status the gateway returns that the provider did not is
    something to explain before you ramp.</li>
<li><strong>Response shape.</strong> Field presence, not field values. Is <code>usage</code>
    there? Is <code>finish_reason</code>? Do tool calls come back structured?</li>
<li><strong>Token counts.</strong> Compare the gateway's reported input tokens against the
    provider's for the same prompt. A systematic difference means the request is being
    modified somewhere.</li>
</ul>

<p><strong>What not to compare:</strong> the text of the completions. Two calls to the same
model with the same prompt do not produce the same output, so a diff of response bodies
produces noise that looks like a problem and is not. Compare distributions later, on real
traffic, with volume — not two responses side by side.</p>

<h2>Step 2: a percentage, chosen by blast radius</h2>

<p>Route a small share of production traffic through the gateway for real. Pick the share by
what you can afford to have degraded, not by a round number — and pick the <em>route</em>
deliberately. The best first candidate is high-volume and low-stakes: a summarisation
endpoint, a classification step, something with a fallback that is not "the feature is
broken". The worst first candidate is the one your demo uses.</p>

<p>Hold at each step long enough to see a full traffic cycle. LLM failure modes are often
time-of-day shaped, because provider capacity is; a two-hour soak at 10% during your quiet
period tells you very little about 10% at peak.</p>

<h2>Step 3: the three things that are different about LLM traffic</h2>

<p><strong>Streaming is a second integration.</strong> A gateway that handles non-streamed
requests perfectly can still break streaming: the framing, the terminator, tool-call deltas
arriving as fragments, or an error mid-stream that reaches your client as a truncated
response rather than an error. If any of your traffic streams, test it as a separate
migration with its own ramp. Read
<a href="/blog/streaming-llm-failover">what happens to a stream when a provider fails</a>
before you do.</p>

<p><strong>Usage accounting can double-count during the overlap.</strong> While both paths are
live you have two systems recording spend, and if you sum them your dashboard shows a cost
spike that did not happen. Decide before you ramp which system is authoritative for the
overlap window, and label the other one clearly. Finance discovering this on a monthly total
is an unpleasant conversation you can avoid entirely.</p>

<p><strong>Non-determinism hides regressions.</strong> Output varies run to run, so a quality
regression does not announce itself the way a broken field does. Have at least one automated
signal that does not depend on reading outputs: the parse rate on structured routes, the
share of <code>finish_reason: length</code>, refusal-shaped response rate. These move before
anyone files a ticket.</p>

<h2>Step 4: cut over, and keep the way back open</h2>

<p>At 100%, the old path should still be one config change away for at least a full billing
cycle. Two reasons: the failure you have not seen yet is the one that only appears at full
volume, and a rollback you have deleted is not a rollback.</p>

<p>Before you call it done, actually exercise the reversal. Flip back, confirm traffic serves,
flip forward. A rollback path nobody has run is a hypothesis.</p>

<h2>What to keep watching for a month</h2>

<ol>
<li><strong>Error rate by provider</strong>, not just overall — the aggregate hides one
    upstream degrading while the others compensate.</li>
<li><strong>Retry share.</strong> If the gateway is retrying more than you expect, something
    upstream is unhealthy and you are paying for it twice.</li>
<li><strong>Spend rate against its own recent norm</strong>, not against a fixed budget. A
    budget alarm tells you after the money is gone; a rate alarm tells you while it is
    happening.</li>
<li><strong>Time to first token</strong> as a distribution, per model. This is the number that
    tells you what the extra hop actually costs you — measure it yourself rather than
    accepting anyone's published figure, including ours.</li>
</ol>

<h2>The short version</h2>

<p>Make the endpoint a variable. Shadow to check shape, not text. Ramp on a route you can
afford to have degraded, through a full traffic cycle. Treat streaming as its own migration.
Decide who owns usage accounting during the overlap. Keep the rollback live and prove it
works. Then watch per-provider error rate, retry share, spend rate and TTFT for a month.</p>

<p>None of this is specific to any one gateway, which is the point — it is the same sequence
whether you are adopting <a href="/router">Runix Router</a>, something you host yourself, or
moving between two. If a vendor cannot describe how you would reverse the migration, that is
the answer to a different and more important question.</p>
"""

template = pathlib.Path("blog/what-openai-compatible-actually-means.html").read_text()
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
