# Runix Website

Source of [runixcloud.io](https://runixcloud.io), the site of Runix AI Inc:
AI infrastructure for teams running AI in production.

Plain HTML and one stylesheet, no build step, served from Cloudflare Pages.

## Products on the site

The products, their layer and their status are defined once, in
`tools/stack.py`; the navigation, the home page stack and `qa.py`'s status
gate all read it. As of 2026-10-31:

| Layer | Page | Product | Status |
|---|---|---|---|
| 05 Agents | `code.html`, `code-plans.html` | Runix Code: an independent coding agent, reviewable in your repository | In development |
| 05 Agents | `comic.html` | Runix Comic: an agent for comic dramas, script to episode | In development |
| 04 Gateway | `router.html`, `router-models.html` | Runix Router: one OpenAI-compatible endpoint for every model | Available |
| 03 Models | `models.html` | Runix Models: fine-tune and serve open-weight models | Early access |
| 02 Data | `data.html`, six `*-data.html` domain pages | Runix Data: domain data for training and evaluation | Early access |
| 02 Data | `pipeline.html` | Runix Pipeline: the tooling that makes data model-ready | In development |
| 01 Infrastructure | `fs.html` | Runix FS: a POSIX file system and multi-tier cache over object storage, built on [Curvine](https://github.com/CurvineIO/curvine) | Early access |

Also: `plans.html` (pricing and checkout; `/pricing` redirects here), `docs/`
(one guide per product), `blog/`, `glossary.html`, `faq.html`, and the legal
pages the payment providers review.

## Working on it

- `assets/style.css` is the whole design system. `/assets/*` is cached for a
  year, so asset URLs carry `?v=`, and `tools/bump_assets.py` moves it.
- The header nav, footer product column and no-script fallback are owned by
  `tools/flagship_nav.py`: edit its lists and run it, never hand-edit sixty
  pages.
- `./deploy.sh` runs every gate (structure, links, render checks at three
  widths, contrast, no-script nav, performance), uploads, verifies the live
  site and re-deploys the product sub-domains. Read `DEPLOYING.md` first.
- `tools/README.md` lists every check and builder and why each exists.

Public repository: everything here, including comments and commit messages,
is written in English.
