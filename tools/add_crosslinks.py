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
    "llm-gateway-guide": ["what-openai-compatible-actually-means"],
    "what-is-an-llm-gateway": ["llm-feature-pre-launch-checklist"],
    "ai-vendor-data-questions": ["where-your-prompts-actually-go"],
    "llm-observability": ["where-your-prompts-actually-go"],
    "llm-rate-limits": ["how-long-should-an-llm-request-wait"],
    "streaming-llm-failover": ["how-long-should-an-llm-request-wait"],
    "prompt-caching-explained": ["did-the-model-change-make-it-worse"],
    "openrouter-alternatives": ["llm-feature-pre-launch-checklist"],
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
for source, targets in FORWARD.items():
    path = pathlib.Path(f"blog/{source}.html")
    if not path.exists():
        print(f"  ! no such post: {source}")
        continue
    html = path.read_text()
    block = re.search(r'(<aside class="related">.*?<ul>)(.*?)(</ul>)', html, re.S)
    if not block:
        print(f"  ! {source} has no related block")
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
