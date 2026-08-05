#!/usr/bin/env python3
"""Write the timeouts post into scheduled/.

Operational, under-written, and connects the failover and streaming pieces:
standard HTTP timeout advice is actively wrong for LLM traffic, and the
failure it produces looks like a provider problem when it is a configuration
one. No vendor named, no Runix figure.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "how-long-should-an-llm-request-wait"
TITLE = "Timeouts for LLM requests — Runix"
H1 = "How long should an LLM request be allowed to take?"
DESC = ("Standard HTTP timeout advice is wrong for model traffic. Which timeout to set, "
        "where each one belongs, and why stacked timeouts cause the outage.")

BODY = """<p>Every HTTP client ships with a default timeout, and every piece of advice about it
assumes a request that either answers in under a second or has failed. Model traffic breaks
that assumption: a legitimate response can take a minute, a failed one can hang for the same
minute, and the two are indistinguishable until one of them ends.</p>

<p>Getting this wrong produces the most confusing class of incident there is — the one where
your dashboard says the provider is fine, the provider's status page says the provider is
fine, and your users are staring at spinners.</p>

<h2>Four timeouts, not one</h2>

<p>"The timeout" is almost always four separate things, and conflating them is the root of
most of the trouble.</p>

<ul>
<li><strong>Connect timeout</strong> — how long to wait for a TCP and TLS handshake. This
    should be short, a couple of seconds at most. A slow handshake means a network or DNS
    problem, and waiting longer never fixes it.</li>
<li><strong>Time to first byte</strong> — how long to wait for the response to <em>start</em>.
    On a streaming request this is the one that matters, and it is the only one that
    distinguishes "the model is thinking" from "nothing is coming".</li>
<li><strong>Inter-token (or read) timeout</strong> — once a stream has started, how long a gap
    between chunks is acceptable before you give up. Almost nobody sets this, and it is what
    catches a stream that dies mid-flight without closing.</li>
<li><strong>Total request timeout</strong> — the ceiling on the whole thing. This is the one
    everybody sets and the one that should usually be the loosest.</li>
</ul>

<p>Most client libraries expose a single number and apply it as the total. That single number
is then set low enough to catch hangs, which means it also kills legitimate long generations,
which shows up as sporadic failures on exactly your most valuable requests — the long,
complex ones.</p>

<h2>Streaming changes which number matters</h2>

<p>On a non-streamed request you cannot distinguish slow from stuck, so the total timeout is
all you have and it has to accommodate your longest legitimate response.</p>

<p>On a streamed request you can. First byte tells you the request was accepted and generation
started; the inter-token gap tells you it is still alive. That means you can set a tight
first-byte timeout — a few seconds — and a tight inter-token gap, while allowing the total to
run long. A response that takes ninety seconds but produces tokens steadily is healthy. A
response that produces nothing for ten seconds is not, and you no longer have to wait ninety
seconds to find out.</p>

<p>This is the strongest practical argument for streaming even when the interface does not
show tokens as they arrive: you get a failure signal you cannot otherwise have.</p>

<h2>Stacked timeouts are where outages come from</h2>

<p>A request typically crosses several hops, each with its own timeout: browser, your API,
your gateway, the provider. The rule that keeps this sane is that <strong>timeouts must
decrease as you move outward from the user</strong> — the outermost timeout is the longest,
each inner one shorter.</p>

<p>When they are ordered the other way, the outer layer gives up while the inner one is still
working. The inner request completes, having consumed the tokens and the money, and delivers
its response to a caller that stopped listening. You pay for output nobody received, your
error rate reports failures the provider never saw, and retries pile a second request on top
of a first that is still running.</p>

<p>Two rules follow:</p>

<ol>
<li><strong>Write the numbers down as a chain</strong>, not as four independent settings. If
    the browser waits 60s, your API should wait less, and whatever it calls should wait less
    again. If you cannot state the chain, you do not have one.</li>
<li><strong>Budget the retries inside the ceiling.</strong> A 30-second timeout with two
    retries is a 90-second worst case at the layer above, which needs to know that. This is
    the same reasoning as a <a href="/blog/model-failover">retry budget</a>, applied to time
    rather than to volume.</li>
</ol>

<h2>What a timeout should do</h2>

<p>Not "retry immediately with identical parameters". A timeout means something is slow, and
the most common reason is load — so an immediate identical retry adds load to a system that is
already struggling. That is how a slow provider becomes a down one.</p>

<p>Better, in order of preference:</p>

<ul>
<li><strong>Retry elsewhere.</strong> If another provider serves the same model or an
    acceptable alternative, that is a different failure domain and worth trying first.</li>
<li><strong>Retry smaller.</strong> Shorter context, lower max tokens, a faster model. A
    degraded answer beats a spinner.</li>
<li><strong>Fail honestly and fast.</strong> "This is taking longer than usual — try again"
    returned in five seconds preserves more trust than a ninety-second hang that ends in a
    generic error.</li>
</ul>

<p>What is worth avoiding in all three cases is silently paying twice. If the first request is
still running upstream when you start the second, you will be billed for both. Cancelling the
original — actually closing the connection, not just abandoning the promise — is the part
people skip.</p>

<h2>Numbers to start from</h2>

<p>These are starting points to be replaced by your own measurements, not recommendations
dressed as facts. Measure your own <a href="/blog/llm-observability">time to first token
distribution</a> per model and set from that.</p>

<ul>
<li><strong>Connect:</strong> a couple of seconds. Longer never helps.</li>
<li><strong>First byte:</strong> a small multiple of your p99 TTFT for that model. If p99 is
    two seconds, waiting thirty is waiting for nothing.</li>
<li><strong>Inter-token gap:</strong> generous relative to normal token spacing but far below
    your total — a stream that pauses for many seconds mid-generation is rarely recovering.</li>
<li><strong>Total:</strong> above your longest legitimate generation, with headroom, and
    strictly below whatever the layer above you allows.</li>
</ul>

<p>The one rule with no measurement behind it: the numbers must decrease outward-to-inward,
and you should be able to write the chain on one line. Most timeout incidents are not a badly
chosen number — they are four numbers nobody ever wrote down together.</p>

<p>Where this lands operationally: the timeout chain, the retry budget and the failover policy
are the same decision viewed three ways, which is the argument for them living in one place
rather than in four services' configuration files. That is what a gateway is for, and
<a href="/router">Runix Router</a> is ours — but the chain is yours to define either way, and
nobody else can tell you what your longest legitimate response looks like.</p>
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
