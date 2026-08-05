#!/usr/bin/env python3
"""Build /glossary.

The terms buyers hit when they start evaluating a gateway, defined so that the
definition is quotable on its own. Each entry says what the thing is, how you
would measure or verify it, and the mistake people actually make — the last
part being what turns a glossary from filler into something worth linking to.

No benchmark values, no vendor performance figures: where a number would be
the interesting part, the entry says how to measure it instead of asserting
one.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_page import SITE, crumbs, render  # noqa: E402

URL = f"{SITE}/glossary"

# term, anchor, definition, how you'd measure/verify it, the common mistake, related link (or None)
TERMS = [
    ("LLM gateway", "llm-gateway",
     "A service that sits between your application and one or more model providers, presenting a single API while handling routing, retries, key custody, quotas and usage accounting.",
     "Point a client at it and remove a provider key from your application — if the request still works and the spend still shows up attributed correctly, the gateway is doing its job.",
     "Treating it as a proxy. A proxy forwards; a gateway takes responsibility for what happens when the thing it forwards to misbehaves.",
     "/blog/what-is-an-llm-gateway"),
    ("LLM router", "llm-router",
     "The part that decides which model or provider serves a given request, by cost, health, capability or explicit policy.",
     "Send the same request twice under different routing policies and compare which upstream served it — the response metadata should tell you.",
     "Assuming routing means cheapest. Routing on health matters more the day a provider degrades.",
     "/blog/llm-router-vs-llm-gateway"),
    ("Failover", "failover",
     "Re-issuing a request to a healthy alternative when the first choice errors, rate-limits or times out.",
     "Block one provider at the network level and watch whether requests still complete, and how the latency distribution changes when they do.",
     "Counting a retry to the same failing provider as failover. If the alternative shares the failure domain, nothing failed over.",
     "/blog/model-failover"),
    ("Retry budget", "retry-budget",
     "A cap on how much of your traffic may be retries, so that a widespread failure cannot turn into self-inflicted load amplification.",
     "Express it as a percentage of window traffic and alert when the retry share approaches it.",
     "Setting per-request retry counts without a global budget — three retries each sounds modest until every request needs them at once.",
     "/blog/model-failover"),
    ("Circuit breaker", "circuit-breaker",
     "A switch that stops sending traffic to an upstream once its failure rate crosses a threshold, then probes cautiously before restoring it.",
     "Watch the breaker state transitions in your logs during a real incident; a breaker that never opens is not tuned, it is decorative.",
     "Keying the breaker on the provider alone. Providers fail per model far more often than they fail entirely.",
     "/blog/model-failover"),
    ("Streaming (SSE)", "streaming",
     "Delivering a response incrementally as it is generated, usually as server-sent events, so the reader sees output before the model has finished.",
     "Measure time to first token separately from total time — streaming changes the first and barely moves the second.",
     "Assuming failover still works mid-stream. Once bytes have been sent, recovering cleanly is a different and harder problem.",
     "/blog/streaming-llm-failover"),
    ("Time to first token (TTFT)", "ttft",
     "The delay between sending a request and receiving the first token of the response.",
     "Measure at the client, on a streaming request, over a distribution — a single sample tells you nothing.",
     "Reporting an average. Latency distributions are skewed, so quote p50, p95 and p99 or say nothing.",
     None),
    ("Prompt caching", "prompt-caching",
     "Reusing the provider-side computation for a repeated prefix of a prompt, so the shared part is not paid for twice.",
     "Compare billed input tokens against sent input tokens for a workload with a stable system prompt; the gap is the cache working.",
     "Assuming any repetition caches. Caching keys on an exact prefix, so a timestamp near the top of the prompt quietly defeats it.",
     "/blog/prompt-caching-explained"),
    ("Rate limit (429)", "rate-limit",
     "A provider's cap on requests or tokens per interval, signalled by an HTTP 429 response.",
     "Track the ratio of 429s to total requests per provider and per model, not just the absolute count.",
     "Retrying a 429 immediately. Without backoff you consume the next window's allowance before it opens.",
     "/blog/llm-rate-limits"),
    ("Cost attribution", "cost-attribution",
     "Assigning model spend to the team, customer or feature that caused it, rather than to one undifferentiated bill.",
     "Issue separate keys per boundary you care about and check that the statement splits along the same lines.",
     "Attributing after the fact from logs. If the boundary is not in the key, the attribution is a reconstruction and it will be argued with.",
     "/blog/llm-cost-attribution"),
    ("Virtual key", "virtual-key",
     "A credential issued by the gateway rather than the provider, carrying its own quota, model allowlist and rate limits.",
     "Revoke one and confirm the blast radius is exactly one consumer and no provider key had to be rotated.",
     "Sharing one key across teams because it is easier. The day you need to revoke it, you find out what it cost.",
     "/blog/llm-api-key-management"),
    ("Blast radius", "blast-radius",
     "How much breaks when one credential, provider or component fails.",
     "Ask what stops working if this key leaks and has to be revoked in the next five minutes.",
     "Measuring it only for outages. A leaked credential is the more common incident and the answer is usually worse.",
     "/blog/llm-api-key-management"),
    ("Deduplication", "deduplication",
     "Removing repeated records from a corpus before it is used for retrieval or fine-tuning — exact, near-duplicate and semantic.",
     "Report how much was removed at each tier; a pipeline that cannot tell you what it dropped cannot be audited.",
     "Stopping at exact matches. Near-duplicates are the ones that quietly skew a retrieval corpus.",
     "/blog/ai-data-pipelines"),
    ("PII masking", "pii-masking",
     "Detecting and redacting personal data before it reaches a model or a stored corpus.",
     "Verify the failure mode: on an ambiguous field the pipeline should mask rather than pass through.",
     "Treating recall as the only metric. A masker that fails open is a compliance incident waiting for a bad input.",
     "/blog/ai-vendor-data-questions"),
    ("Observability (for LLM traffic)", "observability",
     "Recording enough about each request — latency, tokens, model, outcome, request id — to answer questions after the fact, without hoarding content you should not keep.",
     "Pick a past incident and check whether the logs you keep would have explained it.",
     "Logging whole prompts and responses by default. That is a data-retention liability, and it is rarely the field you needed.",
     "/blog/llm-observability"),
]


def entry_html(term, anchor, definition, measure, mistake, link):
    related = (
        f'\n<p class="g-more"><a href="{link}">Read more on this</a></p>' if link else ""
    )
    return f"""<h2 id="{anchor}">{term}</h2>
<p>{definition}</p>
<p><strong>How you would check it.</strong> {measure}</p>
<p><strong>Where people go wrong.</strong> {mistake}</p>{related}"""


body = (
    "<p>Terms that come up while evaluating a gateway, defined plainly. Each one says "
    "what the thing is, how you would verify it yourself, and the mistake that is easy "
    "to make. Where the interesting part would be a number, this page tells you how to "
    "measure it rather than quoting one.</p>\n\n"
    + "\n\n".join(entry_html(*t) for t in TERMS)
    + '\n\n<h2 id="missing">Something missing?</h2>\n'
      '<p>If a term left you guessing, tell us and it belongs here — '
      '<!--email_off--><a href="mailto:contact@runixcloud.io">contact@runixcloud.io</a>'
      '<!--/email_off-->.</p>'
)

schema = [
    {
        "@context": "https://schema.org",
        "@type": "DefinedTermSet",
        "name": "Runix LLM infrastructure glossary",
        "url": URL,
        "publisher": {"@id": f"{SITE}/#org"},
        "hasDefinedTerm": [
            {
                "@type": "DefinedTerm",
                "name": term,
                "description": definition,
                "url": f"{URL}#{anchor}",
                "inDefinedTermSet": URL,
            }
            for term, anchor, definition, _, _, _ in TERMS
        ],
    },
    crumbs("Glossary", URL),
]

render(
    slug="glossary",
    title="LLM gateway glossary — Runix",
    description="Failover, retry budgets, prompt caching, cost attribution, virtual keys: "
                "the terms that come up when evaluating an LLM gateway, defined plainly and "
                "with the common mistakes called out.",
    badge="Glossary",
    h1="LLM infrastructure, term by term",
    lede="Definitions you can quote, a way to verify each one yourself, and the mistake "
         "that is easy to make.",
    body=body,
    schema=schema,
)
print(f"  wrote glossary.html with {len(TERMS)} terms")
