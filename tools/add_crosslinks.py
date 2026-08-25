#!/usr/bin/env python3
"""Link older posts forward to newer ones they should have pointed at.

A post's related-reading block is written when it is published and never
revisited, so the seven posts written tonight had one to three inbound links
each while the posts they directly answer had none pointing forward. This adds
the missing direction — only where the connection is real, and only up to five
items per block so the list stays scannable.

Idempotent. Run from the site root.
"""
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# from  ->  [(target slug, why it belongs there)]
FORWARD = {
    "build-vs-buy-llm-gateway": ["llm-feature-pre-launch-checklist",
                                 "migrating-to-an-llm-gateway-without-downtime"],
    "llm-gateway-guide": ["what-openai-compatible-actually-means",
                          "llm-gateway-security-review"],
    "what-is-an-llm-gateway": ["llm-feature-pre-launch-checklist",
                               "migrating-to-an-llm-gateway-without-downtime"],
    "ai-vendor-data-questions": ["where-your-prompts-actually-go",
                                 "llm-gateway-security-review"],
    "llm-observability": ["where-your-prompts-actually-go"],
    # per-key-llm-quotas (2026-08-25) answers the tenancy question this post and
    # the key-management one raise and leave open: rate limits are the provider
    # throttling you, key scope is one consumer's blast radius, and neither
    # covers several consumers sharing one pool.
    "llm-rate-limits": ["how-long-should-an-llm-request-wait",
                        "llm-retry-budget", "per-key-llm-quotas"],
    "streaming-llm-failover": ["how-long-should-an-llm-request-wait"],
    "prompt-caching-explained": ["did-the-model-change-make-it-worse",
                                 "why-your-llm-bill-doesnt-match-the-price-list"],
    "openrouter-alternatives": ["llm-feature-pre-launch-checklist"],

    # 2026-08-25: the three posts published on 08-20 were sitting on two inbound
    # links each while the posts that raise exactly their question pointed
    # nowhere. Each pairing below is the question-then-answer direction:
    # failover and rate limits both end at "so how many times do I retry",
    # key custody and prompt paths both end at "what will a security review
    # ask", and both cost posts end at "so why is the invoice a different
    # number". Same rule as the rest of the map -- only where the connection
    # is one a reader would follow.
    "model-failover": ["llm-retry-budget"],
    "how-long-should-an-llm-request-wait": ["llm-retry-budget"],
    "llm-api-key-management": ["llm-gateway-security-review", "per-key-llm-quotas"],
    "where-your-prompts-actually-go": ["llm-gateway-security-review"],
    "llm-cost-control": ["why-your-llm-bill-doesnt-match-the-price-list"],
    "llm-cost-attribution": ["why-your-llm-bill-doesnt-match-the-price-list",
                             "per-key-llm-quotas"],
}

# Six, not five. Every block is N posts plus one product page, so five meant
# four posts — and the posts that most needed a forward link were the ones
# already at the cap. Six keeps the list scannable and lets the relevant link
# land; anything past that stops being a recommendation and becomes an index.
MAX_ITEMS = 6


def headline(slug):
    html = pathlib.Path(f"blog/{slug}.html").read_text()
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", m.group(1)).split())


added = 0
missing = 0
for source, targets in FORWARD.items():
    path = pathlib.Path(f"blog/{source}.html")
    if not path.exists():
        print(f"  ! no such post: {source}")
        continue
    html = path.read_text()
    # [^>]* because the aside later gained aria-labelledby for the heading
    # association. The original pattern demanded the tag end right after the
    # class, so from that commit on this script matched nothing on every post,
    # printed a tidy "no related block" for each, and still exited 0 — which is
    # why nobody noticed for weeks. See the run check at the bottom.
    block = re.search(r'(<aside class="related"[^>]*>.*?<ul>)(.*?)(</ul>)', html, re.S)
    if not block:
        print(f"  ! {source} has no related block")
        missing += 1
        continue
    items = block.group(2)
    existing = len(re.findall(r"<li>", items))
    for slug in targets:
        if f'/blog/{slug}"' in items:
            continue
        if existing >= MAX_ITEMS:
            print(f"  - {source}: already at {MAX_ITEMS} items, skipping {slug}")
            continue
        items = f'\n    <li><a href="/blog/{slug}">{headline(slug)}</a></li>' + items
        existing += 1
        added += 1
        print(f"  {source} -> {slug}")
    html = html[:block.start(2)] + items + html[block.end(2):]
    path.write_text(html)

print(f"  added {added} forward link(s)")

# A map of 15 sources that matches none of them is not "nothing to do", it is a
# broken selector — the exact failure this script shipped with for weeks. Fail
# loudly instead of reporting a clean run.
if missing == len(FORWARD):
    print(f"  !! none of the {len(FORWARD)} sources matched — the related-block "
          f"selector no longer fits the markup")
    raise SystemExit(1)
