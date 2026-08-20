#!/usr/bin/env python3
"""Bring the Router docs in line with how billing actually works (2026-08-20).

The gateway now meters at the upstream vendors' published list rates with
input / output / cached tokens priced separately, and the rate table is
audited against the vendors' own pricing pages. The docs said only "billing
is usage-based in USD". This patch:

  - documents list-price metering and the per-response usage breakdown,
  - documents the model-id convention (official vendor ids pass through),
  - links the three sections to the three posts that explain the mechanics,
  - stamps the update date.

Idempotent: replaces toward a target state; a second run changes nothing.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PATH = "docs/router.html"
s = open(PATH).read()
orig = s

# 1. Update stamp.
s = s.replace("<span>Updated August 2, 2026</span>", "<span>Updated August 20, 2026</span>")

# 2. Model-id convention, appended to the model-selection section.
MODEL_IDS_P = (
    '<p>Model ids are the vendors’ own. Anthropic models answer to their official '
    'hyphenated ids (<code>claude-opus-5</code>, <code>claude-sonnet-4-6</code>), and other '
    'vendors’ models keep their catalogue names — there is no Runix-specific alias '
    'table to maintain, so an id copied from a vendor’s announcement works as-is. The '
    'authoritative list for your key is always <code>GET /v1/models</code>.</p>'
)
anchor2 = '<li><strong>Discover what a key can call</strong>'
if MODEL_IDS_P not in s:
    # place right after the model-selection </ul>
    idx = s.index(anchor2)
    ul_end = s.index("</ul>", idx) + len("</ul>")
    s = s[:ul_end] + "\n" + MODEL_IDS_P + s[ul_end:]

# 3. Rewrite section 5 with list-price metering and the usage breakdown.
OLD5_START = '<h2 id="limits-usage-and-cost">5. Limits, usage and cost</h2>'
NEW5 = OLD5_START + """
<ul>
<li><strong>List-price metering</strong> — requests are metered per token at the upstream
    vendors’ published rates, with input, output, cached-read and cache-write tokens priced
    separately — the same structure the vendors themselves publish. We audit the rate table
    against the vendors’ own pricing pages; the mechanics of why token bills diverge from
    price lists — and how to check one by hand — are in
    <a href="/blog/why-your-llm-bill-doesnt-match-the-price-list">Why your LLM bill doesn’t
    match the price list</a>.</li>
<li><strong>Usage on every response</strong> — the <code>usage</code> object carries the full
    token breakdown, cached tokens included, so any single request can be reconciled against
    the rate card without asking us. Billing is usage-based in USD with itemised statements;
    see <a href="/pricing">Pricing</a> for how quotes work.</li>
<li><strong>Per-key quotas</strong> — each key carries limits and quotas set during onboarding, revocable and adjustable without a redeploy.</li>
<li><strong>Attribution</strong> — issue separate keys per team or product to get cost attribution along the lines your finance team actually asks about; the reasoning is covered in <a href="/blog/llm-cost-attribution">LLM cost attribution</a>.</li>
</ul>"""
i5 = s.index(OLD5_START)
i6 = s.index('<h2 id="errors-and-request-ids">')
s = s[:i5] + NEW5 + "\n\n" + s[i6:]

# 4. Failover section: add the retry-budget post next to the failover post.
OLD4 = ('<p>For the background on retry budgets and failure taxonomy, read '
        '<a href="/blog/model-failover">Model failover for production LLM traffic</a>.</p>')
NEW4 = ('<p>For the background on failure taxonomy, read '
        '<a href="/blog/model-failover">Model failover for production LLM traffic</a>; why '
        'retries should be a spend budget rather than a count — and which errors deserve '
        'one at all — is covered in <a href="/blog/llm-retry-budget">Retry budgets for '
        'LLM APIs</a>.</p>')
if NEW4 not in s:
    s = s.replace(OLD4, NEW4)

# 5. Data handling: point evaluators at the security-review checklist.
SEC_P = ('<p>If you are evaluating us — or any gateway — '
         '<a href="/blog/llm-gateway-security-review">the security review an LLM gateway '
         'should survive</a> is the list of questions we think you should ask, including '
         'of Runix.</p>')
anchor7 = 'the security posture in <a href="/security">Security</a>.</p>'
if SEC_P not in s:
    s = s.replace(anchor7, anchor7 + "\n" + SEC_P)

# 6. Docs index: the Router card should name list-price billing.
IDX = "docs/index.html"
t = open(IDX).read()
t2 = t.replace(
    "streaming, failover semantics, limits and data handling.",
    "streaming, failover semantics, list-price billing, limits and data handling.",
)

if s != orig:
    open(PATH, "w").write(s)
    print(f"  patched {PATH}")
else:
    print(f"  {PATH} already at target state")
if t2 != t:
    open(IDX, "w").write(t2)
    print(f"  patched {IDX}")
else:
    print(f"  {IDX} already at target state")
