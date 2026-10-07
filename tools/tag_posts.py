#!/usr/bin/env python3
"""Give every published post a layer tag, once.

The blog index groups posts by the layer of the stack they are about
(2026-10-07), read from each post's own <meta property="article:tag">. Posts
written since carry the tag from write_post.py; the thirty-one written before
are tagged here from a map, after which the map is history and the page is the
record. Idempotent: a post that already carries a tag is left alone.
"""
import os
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.chdir(ROOT)

LAYER = {
    "gateway": ["what-is-an-llm-gateway", "llm-gateway-guide", "llm-router-vs-llm-gateway",
                "build-vs-buy-llm-gateway", "openrouter-alternatives", "model-failover",
                "streaming-llm-failover", "llm-rate-limits", "llm-cost-control", "llm-cost-attribution",
                "prompt-caching-explained", "per-key-llm-quotas", "where-your-prompts-actually-go",
                "llm-feature-pre-launch-checklist", "how-long-should-an-llm-request-wait",
                "did-the-model-change-make-it-worse", "migrating-to-an-llm-gateway-without-downtime",
                "what-openai-compatible-actually-means", "model-deprecation-without-a-redeploy",
                "llm-observability", "llm-api-key-management", "why-your-llm-bill-doesnt-match-the-price-list",
                "llm-retry-budget", "llm-gateway-security-review"],
    "data": ["ai-data-pipelines", "ai-vendor-data-questions"],
    "agents": ["how-to-make-a-comic-drama-with-ai", "comic-drama-vs-webtoon-vs-motion-comic"],
    "infrastructure": ["introducing-runix-fs"],
    "company": ["introducing-runix", "rebuild-ai-unix"],
}
LABEL = {"infrastructure": "Infrastructure", "data": "Data", "models": "Models",
         "gateway": "Gateway", "agents": "Agents", "company": "Company"}

changed = 0
for layer, slugs in LAYER.items():
    for slug in slugs:
        p = ROOT / "blog" / f"{slug}.html"
        if not p.exists():
            print(f"  missing: {slug}")
            continue
        s = p.read_text(encoding="utf-8")
        if 'property="article:tag"' in s:
            continue
        tag = f'<meta property="article:tag" content="{LABEL[layer]}">\n'
        if '<meta property="article:section"' in s:
            s = s.replace('<meta property="article:section"', tag + '<meta property="article:section"', 1)
        else:
            s = s.replace("</head>", tag + "</head>", 1)
        p.write_text(s, encoding="utf-8")
        changed += 1
print(f"  tagged {changed} post(s)")
