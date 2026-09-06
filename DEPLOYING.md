# Before you deploy this site

Production is a **direct upload of local files** — `./deploy.sh` runs
`wrangler pages deploy --branch=main`. It does not read a git branch, and no CI
publishes anything. Whichever machine deploys last wins, and it silently
replaces whatever the previous deploy put there.

That has already happened. Two working lines of this repository were both
deployed to the same Pages project at different times during 2026-09:
`8bb0ca3`, `ab3e223`, `6eb8c1f`, `c3b67de` from one, and `75f8246`, `4d19bf3`,
`ae24dc4`, `e3c8495` from the other.

## So, before running ./deploy.sh

1. `git fetch origin && git log --oneline origin/site -1` — if that commit is
   not an ancestor of your HEAD, someone else's work is ahead of you and your
   deploy will overwrite it.
2. Check what is actually live before you replace it:
   `curl -s https://runixcloud.io/ | grep -o 'assets/style.css?v=[0-9]*'`
   and compare with your own `index.html`.

## Recovery

- `prod-2026-09-06` (tag) — the tree that served runixcloud.io on 2026-09-06,
  assets `?v=57`. `git checkout prod-2026-09-06 && ./deploy.sh` restores it.
- `site-legacy-0903` (branch and tag, `8bb0ca3`) — the other working line,
  kept because `site` was reconciled with `-s ours` on 2026-09-06 and did not
  take its content: `pricing.html`, the Inter subsets, and the home page's
  "AI for Science" copy are only there.
