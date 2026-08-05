#!/usr/bin/env python3
"""Add /faq, /access and /reliability.

Every claim on these three pages already appears somewhere on the site —
llms.txt's buyer-facts section, the pricing tiers, the router page's failover
description, the docs. Nothing here is new information about the product, and
in particular there are no uptime figures, no latency figures and no customers,
because none of those exist to quote yet.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_page import SITE, crumbs, render  # noqa: E402


def faq_schema(pairs, url):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "url": url,
        "publisher": {"@id": f"{SITE}/#org"},
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in pairs
        ],
    }


# --------------------------------------------------------------------- FAQ
FAQ = [
    ("Which Runix products can I use today?",
     "Runix Router is in early access and running traffic. Runix Pipeline is being built "
     "with design partners. Runix Code and Runix Comic are in development with waitlists "
     "open — they are not generally available."),
    ("How do I get access to the Router?",
     "Keys are issued on request rather than through self-serve signup. Tell us what you "
     "are building, the volume you expect and your timeline, and you get a reply within "
     "one business day."),
    ("How does billing work?",
     "Usage-based in USD, metered per token or per request depending on the model, with "
     "itemised statements. You can draw down a prepaid balance or be invoiced. There is no "
     "published rate card — quotes are per workload, and the rate table is stated in "
     "writing before you commit."),
    ("Is there a free way to evaluate it?",
     "Yes. Evaluation credits are issued on request, with full router functionality and no "
     "card required to start."),
    ("What happens to our prompt and response data?",
     "It is processed to serve your request. It is not used to train models and it is not "
     "sold. Operational metadata — usage counts, latency, error codes — is kept to run "
     "billing, reliability and support."),
    ("Do you have SOC 2 or ISO 27001?",
     "No. Runix does not claim SOC 2, ISO 27001 or PCI status, and will not display badges "
     "it has not earned. The Security page describes the controls that are actually in "
     "place."),
    ("Can we sign an MSA and a DPA?",
     "Yes, both on request and reviewed per engagement. Where an order form and the "
     "standard Terms disagree, the order form takes precedence."),
    ("Is there a service level agreement?",
     "Not during early access. The Router is built to route around provider failure, and "
     "the reliability page describes exactly how — but that is a description of the "
     "mechanism, not a published SLA."),
    ("Who am I contracting with?",
     "Runix AI Inc, a company incorporated in Wyoming, United States."),
    ("How quickly do you reply?",
     "Within one business day, at contact@runixcloud.io."),
]

faq_url = f"{SITE}/faq"
faq_body = "\n".join(
    f"<h2>{q}</h2>\n<p>{a}</p>" for q, a in FAQ
) + (
    '\n<h2>Something not covered here?</h2>\n'
    '<p>Ask directly — <!--email_off--><a href="mailto:contact@runixcloud.io">'
    'contact@runixcloud.io</a><!--/email_off-->. If it is a question a buyer would '
    'reasonably have, it belongs on this page, and we will add it.</p>'
)
render(
    slug="faq",
    title="Frequently asked questions — Runix",
    description="Straight answers on access, billing, data handling, contracting and "
                "certifications for Runix Router and the rest of the product line.",
    badge="FAQ",
    h1="Questions buyers actually ask",
    lede="Access, billing, data handling, contracts. If an answer would need a number we "
         "cannot stand behind yet, it says so instead.",
    body=faq_body,
    schema=[faq_schema(FAQ, faq_url), crumbs("FAQ", faq_url)],
)

# ------------------------------------------------------------------ ACCESS
access_url = f"{SITE}/access"
ACCESS_FAQ = [
    ("Why is there no self-serve signup?",
     "Because keys carry real quotas and routing configuration, and during early access "
     "those are set per team rather than issued blindly."),
    ("What does it cost to evaluate?",
     "Nothing. Evaluation credits are issued on request and no card is required to start."),
    ("How long does it take?",
     "You get a reply within one business day."),
]
render(
    slug="access",
    title="How to get access to Runix Router — Runix",
    description="Runix Router is in early access: keys are issued after a short intake "
                "rather than through self-serve signup. Here is exactly what that involves.",
    badge="Early access",
    h1="How access works",
    lede="Keys are issued on request, not through self-serve signup. That is a deliberate "
         "choice, and this page describes precisely what happens between asking and "
         "sending your first request.",
    body="""<h2>1. Tell us what you are building</h2>
<p>Send your use case, the volume you expect, and your timeline to
<!--email_off--><a href="mailto:contact@runixcloud.io">contact@runixcloud.io</a><!--/email_off-->.
Rough numbers are fine; the point is to size the quota and pick sensible routing, not to
qualify you.</p>

<h2>2. We reply within one business day</h2>
<p>You get an access plan and a quote for the workload you described. Pricing is
usage-based in USD and the rate table is stated in writing — there is no published rate
card because quotes depend on the models and volume you actually use.</p>

<h2>3. Evaluate before you pay</h2>
<p>Evaluation credits are issued on request. Full router functionality, no card required
to start. This is the stage where you find out whether the failover behaviour and the cost
reporting match what you need.</p>

<h2>4. Your key arrives configured</h2>
<p>A key is not just a credential here. It carries its own quota and limits, the set of
models it is allowed to call, and routing preferences applied server-side — so the
controls are in place from the first call rather than bolted on later. Issue separate keys
per team or product and the usage reporting splits along those lines.</p>

<h2>5. Then you integrate</h2>
<p>Integration is a base-URL change: point your existing OpenAI-compatible client at
<code>https://api.router.runixcloud.io/v1</code> and swap the key. The
<a href="/docs/router">Router quickstart</a> covers model selection, streaming, failover
semantics and the error envelope.</p>

<h2>Common questions</h2>
""" + "\n".join(f"<h3>{q}</h3>\n<p>{a}</p>" for q, a in ACCESS_FAQ) + """
<p>Everything else is on the <a href="/faq">FAQ</a>, and what happens when a provider
degrades is on the <a href="/reliability">reliability page</a>.</p>""",
    schema=[faq_schema(ACCESS_FAQ, access_url), crumbs("Access", access_url)],
)

# ------------------------------------------------------------- RELIABILITY
rel_url = f"{SITE}/reliability"
render(
    slug="reliability",
    title="How Runix Router handles provider failure — Runix",
    description="Circuit breaking, retry budgets and mid-stream re-issue: how the router "
                "routes around a failing model provider, and why there is no published SLA "
                "during early access.",
    badge="Reliability",
    h1="What happens when a provider fails",
    lede="A gateway earns its place on the bad days. This is the mechanism, described "
         "plainly — not a status page, and not a service level agreement.",
    body="""<h2>No published SLA during early access</h2>
<p>Start with what this page is not. Runix Router is in early access, and there is no
published SLA, no uptime percentage and no historical availability chart — because
publishing one would mean standing behind a number we have not operated long enough to
promise. What follows is how the system behaves, which is a different and more useful
claim.</p>

<h2>Failure is expected, so it is designed for</h2>
<p>Model providers degrade. They rate-limit, they time out, they return errors in bursts,
and they have bad hours that have nothing to do with your code. A router that simply
forwards requests passes every one of those through to your users.</p>
<ul>
<li><strong>Errors, rate limits and timeouts trip a circuit breaker.</strong> The request is
re-issued to a healthy alternative under a retry budget, so a provider's bad hour does not
become your outage — and the budget exists so that retrying never becomes its own outage.</li>
<li><strong>Mid-stream failures are re-issued too.</strong> A failure part-way through a
streamed response is the awkward case most integrations get wrong; the mechanics and the
edge cases are in <a href="/blog/streaming-llm-failover">how streaming failover works</a>.</li>
<li><strong>A degrading provider leaves the rotation</strong> before it drags your latency,
and comes back when health checks pass.</li>
</ul>

<h2>Why the key matters here</h2>
<p>Failover is only safe if the alternative is one you would have chosen. Routing
preferences are set per key server-side — cheapest acceptable, latency-first, provider
allowlists — so when the router moves a request, it moves it inside the boundary you
defined rather than to whatever happened to be up.</p>

<h2>What you can verify yourself</h2>
<p>Every response carries a request id, and errors use a structured envelope, so a failure
can be traced to a specific call rather than argued about. The
<a href="/docs/router">Router quickstart</a> documents the error shape and the failover
semantics in full.</p>

<h2>What is not here yet</h2>
<p>A continuously updated public status feed is not live. When it is, it will report
measured availability rather than an aspiration. Until then, the honest answer to "what is
your uptime" is that we will tell you what we have measured for your workload, and we will
not quote a number we cannot evidence. If reliability guarantees are a procurement
requirement for you, say so during <a href="/access">intake</a> and we will tell you
plainly whether early access fits.</p>""",
    schema=[
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": "How Runix Router handles provider failure",
            "description": "Circuit breaking, retry budgets and mid-stream re-issue.",
            "url": rel_url,
            "isPartOf": {"@id": f"{SITE}/#website"},
            "publisher": {"@id": f"{SITE}/#org"},
        },
        crumbs("Reliability", rel_url),
    ],
)

print("  wrote faq.html, access.html, reliability.html")
