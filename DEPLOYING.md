# Before you deploy this site

Production is a **direct upload of local files** — `./deploy.sh` runs
`wrangler pages deploy --branch=main`. It does not read a git branch, and no CI
publishes anything. Until 2026-10-31 that meant whichever machine deployed last
won, silently replacing whatever the previous deploy put there; the gate below
now refuses that case.

It had already happened. Two working lines of this repository were both
deployed to the same Pages project at different times during 2026-09:
`8bb0ca3`, `ab3e223`, `6eb8c1f`, `c3b67de` from one, and `75f8246`, `4d19bf3`,
`ae24dc4`, `e3c8495` from the other.

## What deploy.sh now enforces

`tools/deploy_provenance.py` keeps one rule: **origin/site is what production
serves.** `deploy.sh` calls it three times.

1. `check`, before anything is rewritten. Refuses when the working tree has
   changes, when origin/site has commits HEAD lacks, or when the live
   deployment was built from a commit HEAD does not contain (including one
   this copy has never seen, i.e. someone deployed without pushing).
2. `record`, after the builders and checks, before upload. Commits whatever
   the builders rewrote (`?v=`, social cards, lastmod, identity), so the
   commit stamped on the deployment is exactly the uploaded tree.
3. `push`, right after the upload. `git push origin HEAD:site`, never forced.
   A rejection means someone pushed meanwhile; the run ends non-zero. Reconcile
   with a merge, `git pull --no-rebase origin site && git push origin HEAD:site`.
   Never rebase there: it rewrites the commit production serves, and the next
   deploy's check refuses it (happened on 2026-10-31; the test covers it).

`DEPLOY_FORCE="<reason>" ./deploy.sh` downgrades check's refusals to
warnings, for emergencies. It does not force the push.
`tools/test_deploy_provenance.sh` exercises all of it against a throwaway
origin, without network.

The product sub-sites (`tools/deploy_subsites.sh`) upload from a temp
directory, so they pass the commit they were built from explicitly.

## Recovery

- To undo a bad deploy, use Cloudflare's rollback (Pages dashboard, or
  `POST .../pages/projects/runix-site/deployments/<id>/rollback`). It serves a
  previous build again without touching git; then fix forward on origin/site.
- `prod-2026-09-06` (tag) — the tree that served runixcloud.io on 2026-09-06,
  assets `?v=57`. Deploying it again needs `DEPLOY_FORCE`, because it is older
  than what is live.
- `site-legacy-0903` (branch and tag, `8bb0ca3`) — the other working line,
  kept because `site` was reconciled with `-s ours` on 2026-09-06 and did not
  take its content: `pricing.html`, the Inter subsets, and the home page's
  "AI for Science" copy are only there.

## Asset versions must only go up

`/assets/*` is served with a one-year immutable cache, so a `?v=` number that
production has served must never be reused for different bytes. On 2026-09-29
it nearly was: the 2026-09-07 deploy bumped `style.css` to v59 at deploy time
and never committed the bump, so the next working line bumped its own copy
from v58 to v59 as well. `deploy.sh` now compares the local number against
the live one and refuses to deploy a number production has already served
with other bytes.
