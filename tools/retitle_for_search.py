#!/usr/bin/env python3
"""Give the search-facing titles the words people actually search for.

The posts written in August took a narrative voice in the <title> -- "Tracing
where your prompts go", "Telling whether a model change made things worse".
They read well and they are honest, but nobody types them into a search box,
and at 33-56 characters they left up to 27 characters of the ~60 Google renders
completely unused. The July posts did not have this problem ("What Is an LLM
Gateway? A Plain Definition"), so the site was carrying two conventions.

Only <title> changes. og:title and twitter:title keep the narrative wording,
because a shared link is read by a person who already clicked, not matched
against a query -- and because make_og.py builds the social card from the h1,
so the 53 cards do not get rebuilt by this.

Every replacement below keeps the claim the page already makes. Nothing is
promised in a title that the body does not deliver.

Idempotent: pages already carrying the new title are skipped.
"""
import os
import pathlib
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LIMIT = 62  # Google renders roughly 60 on desktop; a couple over is fine, far over is truncation.

TITLES = {
    # -- blog: narrative -> query-shaped, keyword first
    "blog/did-the-model-change-make-it-worse.html":
        "Detecting LLM Quality Regression After a Model Update | Runix",
    "blog/how-long-should-an-llm-request-wait.html":
        "LLM API Timeouts: How Long Should a Request Wait? | Runix",
    "blog/llm-retry-budget.html":
        "LLM Retry Strategy: Use a Budget, Not a Retry Count | Runix",
    "blog/llm-gateway-security-review.html":
        "LLM Gateway Security: 8 Questions for Your Review | Runix",
    "blog/migrating-to-an-llm-gateway-without-downtime.html":
        "Migrating to an LLM Gateway Without Downtime | Runix",
    "blog/model-deprecation-without-a-redeploy.html":
        "Handling LLM Model Deprecation Without a Redeploy | Runix",
    "blog/what-openai-compatible-actually-means.html":
        "What \"OpenAI-Compatible\" Actually Means for Your API | Runix",
    "blog/where-your-prompts-actually-go.html":
        "Where Your Prompts Go: Tracing LLM Data Flow | Runix",
    "blog/why-your-llm-bill-doesnt-match-the-price-list.html":
        "Why Your LLM Bill Doesn't Match the Token Price List | Runix",
    "blog/llm-feature-pre-launch-checklist.html":
        "LLM Production Checklist: 12 Decisions Before Launch | Runix",
    # -- site pages carrying no searchable term at all
    "faq.html":
        "LLM Gateway FAQ: Billing, Access, Models and Support | Runix",
    "glossary.html":
        "LLM Gateway Glossary: Key Terms Defined | Runix",
    "reliability.html":
        "LLM Failover: How Runix Handles Provider Outages | Runix",
    "docs/router.html":
        "Runix Router Docs — OpenAI-Compatible API Quickstart",
}

TITLE_TAG = re.compile(r"<title>(.*?)</title>", re.S)


def main():
    changed, over = 0, []
    for path, new in sorted(TITLES.items()):
        p = pathlib.Path(path)
        if not p.exists():
            print("  !! %s does not exist" % path)
            return 1
        if len(new) > LIMIT:
            over.append((path, len(new), new))
            continue
        doc = p.read_text()
        m = TITLE_TAG.search(doc)
        if not m:
            print("  !! %s has no <title>" % path)
            return 1
        if m.group(1).strip() == new:
            continue
        # Only the <title> element. og:title is a content= attribute and is not
        # matched by this pattern, which is what keeps the social wording.
        p.write_text(TITLE_TAG.sub(lambda _: "<title>%s</title>" % new, doc, count=1))
        changed += 1
    for path, n, new in over:
        print("  !! %s: title is %d chars, over the %d limit -- %s" % (path, n, LIMIT, new))
    if over:
        return 1
    print("  retitled %d page(s) for search; social titles untouched" % changed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
