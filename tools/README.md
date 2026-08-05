# site/tools

Everything here runs from the site root (`cd site && python3 tools/<name>.py`).
Nothing in this directory is deployed — `deploy.sh` excludes it.

Most of these are **one-shot builders**: they made a change once, they are
idempotent, and they exist so the change is reproducible and its reasoning is
written down next to it. A few are **checks you run repeatedly**. The
difference matters, so they are separated below.

---

## Run on every deploy (wired into `deploy.sh`)

| Tool | What it does | Fails the deploy? |
|---|---|---|
| `update_lastmod.py --write` | Bumps sitemap `lastmod` only for pages whose *content* hash changed. Never on an asset-version bump. | no |
| `qa.py` | Source-level checks: structure, meta, JSON-LD validity and FAQ/visible-copy agreement, link and anchor resolution, nav consistency, sitemap coverage, forbidden claims, mailto routing, product-status consistency, description length. | **yes** |
| `visual_qa.py` (6-page sample) | Renders in Chrome at 375/768/1440 — overflow, sub-12px text, target size, anchors under the sticky header, WCAG AA contrast, link distinguishability. | **yes** |
| `perf_check.py index.html` | Page weight, request count, LCP, and images without reserved space. | **yes** |
| `verify_live.py` | After upload: every path, three rounds, flicker reported as propagation rather than breakage. | **yes** |

## Run on a schedule

`daily_check.sh` bundles the periodic checks into one read-only run against
production — nothing it does changes anything, so it is safe unattended. It
verifies every path is serving, that `/security`'s TLS claim is still true,
that the pages pass their own checks, that the gateway still answers 401 to an
unauthenticated call, and that no certificate is inside 14 days of expiry.
Exit code is non-zero if anything failed.

    crontab -e
    17 9 * * *  /Users/cuihuan/Desktop/workspace/AI/runix/site/tools/daily_check.sh >> /tmp/runix-daily.log 2>&1

Certificates were 77-87 days out when this was written; the check is there
because a lapsed certificate takes everything down and gives a month of
warning nobody is watching for.

## Run by hand, regularly

| Tool | When | Why |
|---|---|---|
| `visual_qa.py` (no args) | after any change to tokens or layout | the 6-page deploy sample is a smoke test, not coverage |
| `perf_check.py` (no args) | after changing assets | measures every template, not just the homepage |
| `check_tls.py` | monthly | `/security` publishes a TLS claim; the policy lives at the edge and nothing here would notice it changing |
| `verify_live.py` | any time the site looks wrong | distinguishes a real failure from edge propagation |

## Content workflow

| Tool | Use |
|---|---|
| `make_page.py` | build a new page reusing the real chrome (imported by the builders below) |
| `publish.py <slug>` | move `scheduled/<slug>.html` into `blog/`, stamp today's date, rebuild index, sitemap, feed and llms.txt |
| `build_blog_index.py` | rebuild the index and the blog half of the sitemap |
| `build_feed.py` | regenerate `/feed.xml` from each post's own Article schema |
| `refresh_llms_txt.py` | regenerate the writing section of `/llms.txt` from the posts |
| `add_related.py` | add a curated related-reading block to a post (edit the map inside first) |
| `sync_schema.py` | rebuild FAQPage blocks from each page's visible questions |
| `bump_assets.py` | bump `?v=` on CSS/JS/images so a change takes effect immediately |

**There is a draft waiting**: `scheduled/open-source-gateway-continuity.html`.
It is finished and checked but deliberately unpublished — it names competitors,
which is a positioning decision. `python3 tools/publish.py
open-source-gateway-continuity` ships it. See `OSS-LANDSCAPE.md` for the
research behind it.

## One-shot builders (already applied; kept for reproducibility)

`add_closing_ctas.py` · `add_docs_nav.py` · `add_glossary.py` ·
`add_router_diagram.py` · `add_w4_pages.py` · `center_product_heroes.py` ·
`expand_about.py` · `fix_links.py` · `fix_orphans.py` · `fix_schema.py` ·
`wrap_tables.py` · `write_compat_post.py` · `write_deprecation_post.py` ·
`write_migration_post.py` · `write_regression_post.py` ·
`write_oss_risk_draft.py` · `build_subsites.py`

Each is idempotent and prints "nothing to do" on a second run. Read the
docstring before re-running one — several assert that a page still looks the
way they expect and will tell you if it does not.

---

## Two rules these tools were built under

**A check that cannot fail is worse than no check.** Two were shipped tonight
that looked green and tested nothing: the layout-shift gate scored 0 for a
page that visibly shifts, because headless Chrome completes layout before
painting; and every "phone width" test rendered at 500px, because Chrome
clamps its viewport and `--window-size=375` is silently ignored. Both were
found by deliberately breaking the thing the check was supposed to catch. Do
that for anything you add here.

**Measure before concluding.** Several findings tonight were artefacts of the
measurement, not the site: a contrast checker that read a 10%-alpha tint as a
solid fill and reported two perfectly legible elements as failures; a
sentence-scoped scan that reported three product-status inconsistencies that
did not exist, because card markup has no sentence punctuation; a lastmod
comparison that said all 45 pages changed, because the element it compared did
not exist in the baseline. Each would have caused a "fix" to something already
correct.
