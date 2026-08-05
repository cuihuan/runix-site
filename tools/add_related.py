#!/usr/bin/env python3
"""Give every article a curated 'Related reading' block.

Measured before writing this: the average post carried 4 body links and five
carried none at all to a product page. Posts that sit in their own dead end are
a waste of the traffic they earn, and a reader who just finished the failover
article has an obvious next question.

The map below is hand-picked, not generated — three genuinely adjacent posts
and one product page that actually answers the question the post raises. Anchor
text is the real headline, because "read more" tells a reader nothing.

Idempotent. Run from the site root.
"""
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PRODUCT = {
    "/router": "Runix Router: one OpenAI-compatible endpoint across providers",
    "/reliability": "What happens when a provider fails",
    "/pricing": "How Runix pricing works",
    "/pipeline": "Runix Pipeline: managed data preparation",
    "/comic": "Runix Comic: script to screen",
}

RELATED = {
    # gateway fundamentals — the pillar and everything that should point at it
    "what-is-an-llm-gateway": (["llm-router-vs-llm-gateway", "llm-gateway-guide", "build-vs-buy-llm-gateway"], "/router"),
    "llm-gateway-guide": (["what-is-an-llm-gateway", "build-vs-buy-llm-gateway", "openrouter-alternatives"], "/router"),
    "llm-router-vs-llm-gateway": (["what-is-an-llm-gateway", "llm-gateway-guide", "model-failover"], "/router"),
    "build-vs-buy-llm-gateway": (["what-is-an-llm-gateway", "llm-gateway-guide", "llm-observability"], "/pricing"),
    "openrouter-alternatives": (["llm-gateway-guide", "build-vs-buy-llm-gateway", "llm-cost-control"], "/router"),
    # reliability
    "model-failover": (["streaming-llm-failover", "llm-rate-limits", "what-is-an-llm-gateway"], "/reliability"),
    "streaming-llm-failover": (["model-failover", "llm-rate-limits", "llm-gateway-guide"], "/reliability"),
    "llm-rate-limits": (["model-failover", "llm-cost-control", "llm-observability"], "/reliability"),
    # cost
    "llm-cost-control": (["prompt-caching-explained", "llm-cost-attribution", "llm-rate-limits"], "/pricing"),
    "llm-cost-attribution": (["llm-cost-control", "llm-observability", "llm-api-key-management"], "/pricing"),
    "prompt-caching-explained": (["llm-cost-control", "llm-cost-attribution", "llm-gateway-guide"], "/pricing"),
    # operating a model change
    "did-the-model-change-make-it-worse": (["model-deprecation-without-a-redeploy", "llm-observability", "migrating-to-an-llm-gateway-without-downtime"], "/router"),
    # adoption
    "migrating-to-an-llm-gateway-without-downtime": (["what-openai-compatible-actually-means", "streaming-llm-failover", "build-vs-buy-llm-gateway"], "/router"),
    # compatibility
    "what-openai-compatible-actually-means": (["llm-gateway-guide", "model-deprecation-without-a-redeploy", "streaming-llm-failover"], "/router"),
    # model lifecycle
    "model-deprecation-without-a-redeploy": (["llm-gateway-guide", "what-is-an-llm-gateway", "build-vs-buy-llm-gateway"], "/router"),
    # operations
    "llm-observability": (["llm-cost-attribution", "llm-api-key-management", "model-failover"], "/router"),
    "llm-api-key-management": (["llm-observability", "llm-cost-attribution", "ai-vendor-data-questions"], "/router"),
    # data
    "ai-data-pipelines": (["ai-vendor-data-questions", "llm-observability", "what-is-an-llm-gateway"], "/pipeline"),
    "ai-vendor-data-questions": (["ai-data-pipelines", "llm-api-key-management", "llm-observability"], "/pipeline"),
    # creators
    "how-to-make-a-comic-drama-with-ai": (["comic-drama-vs-webtoon-vs-motion-comic", "ai-data-pipelines"], "/comic"),
    "comic-drama-vs-webtoon-vs-motion-comic": (["how-to-make-a-comic-drama-with-ai", "what-is-an-llm-gateway"], "/comic"),
    # company
    "introducing-runix": (["what-is-an-llm-gateway", "llm-gateway-guide", "model-failover"], "/router"),
}

MARKER = 'class="related"'


def headline(slug):
    html = open(f"blog/{slug}.html").read()
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(1)).split())


titles = {slug: headline(slug) for slug in RELATED}
missing = [s for s in RELATED if not os.path.isfile(f"blog/{s}.html")]
assert not missing, f"unknown slug(s): {missing}"

added = 0
for slug, (siblings, product) in RELATED.items():
    path = f"blog/{slug}.html"
    html = open(path).read()
    if MARKER in html:
        continue
    items = "".join(
        f'\n  <li><a href="/blog/{s}">{titles[s]}</a></li>' for s in siblings
    )
    block = (
        f'\n<aside class="related">\n'
        f"  <h2>Related reading</h2>\n"
        f"  <ul>{items}\n"
        f'    <li><a href="{product}">{PRODUCT[product]}</a></li>\n'
        f"  </ul>\n"
        f"</aside>\n"
    )
    html = html.replace("</article>", block + "</article>", 1)
    open(path, "w").write(html)
    added += 1

print(f"  added a related-reading block to {added} post(s)")
