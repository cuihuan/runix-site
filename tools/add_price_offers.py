#!/usr/bin/env python3
"""Put the published prices into the pricing page's structured data.

The page has said $0.01 per credit in prose since it launched, but its Service
node carried no offers, so the one number a buyer searches for was invisible to
anything reading the markup -- including the assistants people now ask "what
does Runix cost" instead of opening the page.

Only figures already visible on the page go in. The enterprise tier is quoted
in writing and has no published number, so it is described without a price
rather than given an invented one.

Idempotent: the offers block is rewritten from this file each run.
"""
import json
import os
import pathlib
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

PAGE = "plans.html"
SITE = "https://runixcloud.io"

OFFERS = [
    # The three tiers this file used to describe were removed from the page when
    # the plans went away: what is sold is prepaid balance, bought in whatever
    # amount you like. Structured data has to say the same thing the page says --
    # card acquirers read it, and so do the assistants people ask instead of
    # opening the page.
    {
        "@type": "Offer",
        "name": "Prepaid balance",
        "description": (
            "Prepaid credit drawn down by measured usage, with no plan and no monthly fee. "
            "Balance is spent at 0.8x published vendor list prices, so $50 covers about "
            "$62.50 of list-price usage. Top up from $10; credit does not expire."
        ),
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock",
        "url": f"{SITE}/plans",
        "eligibleQuantity": {
            "@type": "QuantitativeValue",
            "minValue": 10,
            "unitText": "USD",
        },
        "priceSpecification": {
            "@type": "UnitPriceSpecification",
            "price": "0.01",
            "priceCurrency": "USD",
            "unitText": "credit",
            "description": (
                "Every request meters in credits at $0.01 each, billed in USD. How many "
                "credits a request costs depends on the model and the size of the request."
            ),
        },
    },
    {
        # Kept without a price: evaluation credit is issued on request, not sold.
        "@type": "Offer",
        "name": "Evaluation credit",
        "description": "Free evaluation credit, issued on request. Same endpoint and models as a paid account, no card required.",
        "price": "0",
        "priceCurrency": "USD",
        "availability": "https://schema.org/LimitedAvailability",
        "url": f"{SITE}/about#contact",
    },
    {
        # No price: the rate is discounted by volume and quoted in writing, so
        # there is no published figure to put here.
        "@type": "Offer",
        "name": "Volume agreement",
        "description": "Discounted credit rate by volume, quoted in writing against your own models and traffic. Committed-use agreements, formal invoicing and DPAs on request.",
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock",
        "url": f"{SITE}/about#contact",
    },
]

LD_BLOCK = re.compile(r'(<script type="application/ld\+json">\s*)(\{.*?\})(\s*</script>)', re.S)


def main():
    doc = before = pathlib.Path(PAGE).read_text()

    def fix(m):
        try:
            node = json.loads(m.group(2))
        except json.JSONDecodeError:
            return m.group(0)
        if node.get("@type") != "Service":
            return m.group(0)
        node["offers"] = OFFERS
        return m.group(1) + json.dumps(node, indent=2, ensure_ascii=False) + m.group(3)

    doc = LD_BLOCK.sub(fix, doc, count=1)
    if '"offers"' not in doc:
        print("  !! no Service node on the plans page to attach offers to")
        return 1
    if doc != before:
        pathlib.Path(PAGE).write_text(doc)
        print(f"  wrote {len(OFFERS)} offer(s) into {PAGE}")
    else:
        print("  offers already current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
