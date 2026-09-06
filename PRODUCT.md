# Product

<!-- impeccable:product-schema 1 -->

> Every fact below is **inferred from the shipped site, repo docs and deploy tooling**, not from a live interview: the owner authorised an unattended run while away. Nothing here is invented — each line traces to page copy, `deploy.sh`, `_headers`, or the payment integration in `payments/`. Confirm on the owner's return.

## Platform

web

## Users

Engineering teams putting LLM calls into production — the person who owns the integration, plus the legal and procurement people who have to sign for it. Their situation is not "does the model work" but "who holds the provider keys, what can legal sign, and what happens at 3am when a provider degrades" (`router.html`). Buyers are international B2B; the contracting entity is US-based so overseas teams can procure normally.

## Product Purpose

Runix sells AI infrastructure teams do not have to babysit. Four products, one live: **Router** (the gateway — one OpenAI-compatible endpoint in front of every model, in early access, invite-only), **Pipeline** (raw material into data models can read, built with design partners), **Code** (a repo agent that ships the fix, not a suggestion), **Comic** (scripts into published episodes). Success is a team pointing an existing OpenAI-compatible client at `api.router.runixcloud.io` and never touching provider plumbing again.

## Positioning

Two claims a neighbouring gateway could not truthfully copy-paste:

1. **Official first-party upstreams only** — OpenAI, Anthropic, Google Vertex, AWS Bedrock, Azure OpenAI. No resold grey-market keys.
2. **Contracts you can actually sign** — DPA/MSA/SLA, zero data retention, not used for training, US entity that invoices and takes purchase orders.

Both are positioning the site already states; both are load-bearing and must survive any redesign.

## Operating Context

- Integration is two lines: swap base URL and key on an existing OpenAI-compatible client; `"auto"` routes by cost and health, or name a model id.
- Provider credentials live in the gateway, not in a dozen repos and CI secrets.
- Evaluation credits are issued on request so a team can test against real traffic before paying.
- Onboarding is invite-only, account set up within one business day.

## Capabilities and Constraints

- Static HTML/CSS, **no build step**, ~22 root pages plus `docs/`, `blog/`, `payments/`, `scheduled/`. Any redesign lands in `assets/style.css` plus per-page markup; there is no component layer to lean on.
- Cloudflare Pages direct upload via `deploy.sh`; a strict CSP in `_headers` allows only self-hosted fonts (`font-src 'self'`), inline styles/scripts, and the Stripe/Airwallex/GA/Cloudflare-Insights origins already listed. **No external font CDN, no third-party asset host.**
- `/assets/*` carries a one-year immutable cache; every asset change must go through `tools/bump_assets.py --if-changed` (deploy.sh runs it).
- Deploy is gated: `qa.py`, `html_structure.py`, `console_check.py`, `nojs_check.py`, `code_overflow.py`, `perf_check.py`, `check_contrast.js`. A redesign that breaks any gate does not ship.
- Live payments: Stripe **and** Airwallex, both real (`payments/`). UnionPay rides on the Stripe tile.
- Legal identity must stay visible in served HTML for card acquirers: `Runix AI Inc`, Wyoming registration, contact addresses (`tools/render_identity.py` bakes it into every footer).

## Brand Commitments

- Name **Runix**; legal entity **Runix AI Inc**, incorporated in Wyoming, United States.
- Product names: Router, Pipeline, Code, Comic.
- Voice: literal and unflattering about its own maturity — "statuses above are literal", "no published SLA during early access", "what we do not claim". This candour is the brand; a redesign may not smooth it into marketing gloss.
- Existing assets: `assets/logo.svg`, favicon, self-hosted Archivo woff2 pair.
- Addresses: contact@ / support@ / sales@ / billing@runixcloud.io.
- **Privacy red line** (from owner's notes): the founder's personal name and EIN never appear on the site; only the legal entity name.

## Evidence on Hand

Real, usable as proof: the OpenAI-compatible curl example; the four-product status board with honest per-product state; the failure-behaviour explanation in `reliability.html`; the data-handling section; live Stripe/Airwallex checkout; five blog posts; a glossary; `docs/` for each product.

**Absent — must not be fabricated:** customer names or logos, testimonials, uptime percentages, published SLA numbers, latency or cost benchmarks, user counts, funding, team size, press.

## Product Principles

1. Say what is true today, including what is not built yet; the honesty is the differentiator, not a disclaimer.
2. The gateway earns its place on the bad days — design around failure behaviour, not feature lists.
3. Procurement is part of the product: what legal can sign matters as much as what the API returns.
4. Integration effort is the conversion barrier; keep "two lines" visible and provable.
5. No claim ships that the product cannot demonstrate on request.

## Accessibility & Inclusion

WCAG AA contrast is enforced mechanically before deploy (`tools/check_contrast.js`, a real-browser audit that resolves gradients and alpha compositing). Pages must work with JavaScript off — `nojs_check.py` gates the no-script nav fallback.
