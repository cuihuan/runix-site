# Runix Website

Source of [runixcloud.io](https://runixcloud.io), the site of Runix AI Inc:
AI infrastructure for teams running AI in production.

Plain HTML and one stylesheet, no build step, served from Cloudflare Pages.

## Products on the site

| Page | Product | Status |
|---|---|---|
| `router.html` | Runix Router: one OpenAI-compatible endpoint for every model provider | Early access |
| `fs.html` | Runix FS: a POSIX file system and multi-tier cache over object storage, built on [Curvine](https://github.com/CurvineIO/curvine) | Early access |
| `pipeline.html` | Runix Pipeline: raw material into model-ready data | In development |
| `code.html`, `code-plans.html` | Runix Code: a reviewable AI agent in your repository | In development |
| `comic.html` | Runix Comic: scripts into published episodes | In development |

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
