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
| `visual_qa.py` (6-page sample) | Renders in Chrome at 375/768/1440 — overflow, sub-12px text, target size, anchors under the sticky header, WCAG AA contrast, link distinguishability. Also counts how many elements each selector-based detector examined and fails if any examined none: a detector that matches nothing reports nothing and reads as coverage. | **yes** |
| `perf_check.py index.html` | Page weight, request count, LCP, and images without reserved space. | **yes** |
| `make_og.py` | Renders each page's own 1200x630 social card in Chrome, only for cards whose text changed. Measures every card's layout in one batch run first and refuses to ship a set where every card measures identically. | **yes** |
| `point_og.py` | Rewrites `og:image`/`twitter:image` to that card, versioned by the card's content hash. | **yes** |
| `subsite_drift.sh` | Probes each product sub-domain twice and exits 1 if it serves a different stylesheet, or different copy, from the main site. Copy is compared against the local source file rather than the live main site, because this runs straight after a deploy when the edge may still be serving the previous build — comparing two live URLs compared stale against stale. The compared range is `</header>` to `<footer>`, not `<main>`: the hero sits outside `<main>` on every product page. `deploy.sh` re-deploys them itself when it fires, so the mirror stays a mirror without anyone remembering a second command. | no (triggers a fix) |
| `code_overflow.py` | Renders every page with a `<pre>` at 1440px and fails on any code sample cut off by its container. Desktop only — horizontal scroll is the right answer on a phone. | **yes** |
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

## Product sub-sites (five live subdomains)

`build_subsites.py <outdir>` rebuilds the four product landing pages as
standalone sites. They are **not** covered by `deploy.sh` — refreshing them is
a separate step that is easy to forget, and they were three days stale while
the main site changed all night.

    CLOUDFLARE_API_TOKEN=... tools/deploy_subsites.sh

That builds all four, deploys them, and verifies the five domains afterwards.
`daily_check.sh` compares each subdomain's CSP and cache headers against the
main site's and tells you when they have drifted, so this is not something you
have to remember.

| Project | Domains |
|---|---|
| `runix-gateway` | gateway.runixcloud.io, **router.runixcloud.io** (one project, two domains) |
| `runix-comic` | comic.runixcloud.io |
| `runix-code` | code.runixcloud.io |
| `runix-data` | data.runixcloud.io |

**They also carry `_headers`, so a change to the CSP or cache policy on the main
site does not reach them until they are rebuilt.** That gap was live for about
fifteen minutes after the CSP went in.

Each is one page whose canonical points at the main site, so they never compete
with it in search. The builder exits non-zero if any internal link is left
pointing at the subdomain — which is what caught it after the main site moved
to clean URLs and every rewrite pattern silently stopped matching.

## Run by hand, regularly

| Tool | What it does |
|---|---|
| `nojs_check.py` | Lifts the `<noscript>` nav stylesheet out of each page, applies it as an ordinary stylesheet, and checks at 375px that every nav link becomes visible, the hamburger is hidden, and nothing scrolls sideways. Verifies the part we wrote; `<noscript>` activation itself is browser behaviour. Blocking scripts with CSP does **not** test this — CSP stops execution while the scripting-enabled flag stays on, so `<noscript>` remains inert. |
| `falsify_suite.sh` | Re-proves all eleven gates added tonight through `falsify.py` in one run, leaving the tree clean. "It fired once when I wrote it" is not durable evidence — roughly a quarter of tonight's hand injections did not land where I assumed. Run after touching `qa.py`, or when a gate starts looking suspiciously quiet. |
| `falsify.py` | Injects a defect, runs a check, restores the file, and refuses to call it a success unless the gate actually fired for the right reason. Enforces the three rules tonight's failures needed: the file must really change, the change must land inside the region the check scans, and a non-zero exit caused by a port clash or a traceback is reported as environment noise rather than a finding. Usage: `tools/falsify.py <file> <old> <new> --check "<cmd>" [--scope-start S --scope-end E] [--expect TEXT]`. |
| `gate_coverage.py` (also on every deploy) | Traces a check script (`qa.py` by default, any script as an argument) and reports any check whose condition is never evaluated against the current site. Five gates written tonight could not fire when first written and every one reported a clean run; hand-falsification catches that for new gates, this is the net for the ones already in the file. Unreachable checks that are dead by absence rather than defect go in `gate_coverage_allow.txt` with the reason; anything else fails the deploy. Reaching a condition is not the same as being able to fail it, so this narrows where to look — it does not replace injection. |


| Tool | When | Why |
|---|---|---|
| `visual_qa.py` (no args) | after any change to tokens or layout | the 6-page deploy sample is a smoke test, not coverage |
| `perf_check.py` (no args) | after changing assets | measures every template, not just the homepage |
| `check_tls.py` | monthly | `/security` publishes a TLS claim; the policy lives at the edge and nothing here would notice it changing |
| `verify_live.py` | any time the site looks wrong | distinguishes a real failure from edge propagation |
| `check_idempotent.sh` | Re-runs every applied builder and fails if any of them changes anything. Idempotence is load-bearing here: a builder that edits on every run silently reverts later work. |

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
| `bump_assets.py --if-changed` | bump `?v=` only on assets whose bytes moved (deploy.sh runs this); plain `bump_assets.py` still bumps everything |

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
`write_migration_post.py` · `write_regression_post.py` · `write_timeout_post.py` · `write_launch_checklist_post.py` · `write_dataflow_post.py` ·
`write_oss_risk_draft.py` · `build_subsites.py` · `add_crosslinks.py` ·
`add_related.py`

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
