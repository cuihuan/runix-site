#!/usr/bin/env python3
"""Write the gateway security-review post into scheduled/.

'secure llm gateway' is in the keyword pool with no body content behind it.
Buyer's-eye view: the questions a security review actually asks of any LLM
gateway (ours included), phrased so the reader can run the review themselves.
No certifications claimed, no vendors named.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "llm-gateway-security-review"
TITLE = "Security review questions for an LLM gateway — Runix"
H1 = "The security review an LLM gateway should survive"
DESC = ("Eight questions a security review should ask any LLM gateway — key custody, "
        "logging, retention, tenant isolation, egress — and what good answers look like.")

BODY = """<p>An LLM gateway holds a position of unusual trust: every prompt your company sends
passes through it, and the provider keys it holds can spend your money and read your traffic.
That is true whether the gateway is a product you bought or a service you wrote in a week.
This is the review we think any gateway should survive — phrased as questions, because the
point is that you can ask them of anyone, including us.</p>

<h2>1. Who holds the provider keys, and how?</h2>

<p>The whole premise of a gateway is key consolidation: your teams hold gateway keys, the
gateway holds the provider keys. The questions that follow are mechanical. Where do provider
keys live at rest — an encrypted store, or a config file? Who can read them — which staff,
which processes, which logs? Can a gateway key holder ever extract a provider key through
any API surface, error message or debug endpoint? The last one deserves an actual test, not
an assurance: trigger errors and read what comes back.</p>

<h2>2. What do gateway keys authorize, and how narrowly?</h2>

<p>Per-key scoping is the security payoff of the whole arrangement. A key should be
limitable to specific models and groups, carry its own quota so a leak has a bounded blast
radius, and be revocable in seconds without touching any other key. If disabling one team's
key requires rotating a shared credential, the gateway has recreated the problem it was
bought to solve.</p>

<h2>3. What is logged, and does the operator need it?</h2>

<p>There is a spectrum. Billing needs token counts, model ids, timestamps, key ids — pure
metadata. Debugging sometimes wants request bodies. Those are different retention classes
and a review should get a straight answer per class: are prompt and completion
<em>bodies</em> stored at all, for how long, and can body logging be disabled for your
tenant? "We keep metadata for accounting and do not persist message content" is a coherent
answer. "Logs are kept for quality purposes" is not an answer; it is a question that has not
been answered yet.</p>

<h2>4. How long does anything live, and can you make it shorter?</h2>

<p>Whatever is stored, the follow-ups are the same: what is the retention period, is it
enforced by machinery (a TTL, a partition drop) or by intention (someone means to delete it),
and what happens on your deletion request? Ask specifically about backups and about trace or
debug captures made during incident response — the ad-hoc copies are the ones that outlive
every policy.</p>

<h2>5. What separates you from the operator's other tenants?</h2>

<p>Multi-tenancy is fine; undisclosed multi-tenancy is not. Can another tenant's key ever
route to your dedicated upstream, read your logs, or exhaust the quota you paid for? If you
have negotiated a dedicated provider account or region for compliance reasons, what —
concretely, in configuration — prevents your traffic from ever using the shared pool, and
can the operator show you that configuration's effect rather than describe it?</p>

<h2>6. Where does traffic go, and where is it processed?</h2>

<p>A gateway adds a hop, and the hop has a geography. Which jurisdictions do the gateway
itself and its storage run in? Which upstream providers, and in which of <em>their</em>
regions, can a given model id resolve to? Model routing is exactly the place where a
data-residency promise dies silently — a failover target in another jurisdiction is a
compliance event nobody scheduled. If residency matters to you, the answer must cover the
failover path, not just the happy path.</p>

<h2>7. What happens on the operator's worst day?</h2>

<p>Assume the gateway operator is compromised. What does the attacker get — live traffic,
stored bodies, provider keys, all three? Now assume merely a bad deploy: does the gateway
fail closed (requests error) or open (requests bypass controls)? For billing controls
specifically, ask whether quota enforcement reads from a source that can lag, because a
quota check against stale state is an overdraft mechanism with extra steps.</p>

<h2>8. Can you verify any of this from the outside?</h2>

<p>The strongest answers are the ones you can test with a key and an afternoon: error
responses that leak nothing, per-request token accounting you can recompute, a revocation
that takes effect mid-session, a model list that matches the contract. A gateway that
invites that testing is making a structural claim — that its security posture survives
contact with a motivated customer — and that claim is worth more than any diagram.</p>

<p>We keep our own answers to these questions on the <a href="/security">security page</a>,
and the parts you can test from outside, we would rather you test. The review is the
product working as intended: the entire argument for putting a gateway in front of your LLM
traffic is that trust concentrated in one place can be inspected in one place.</p>
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
