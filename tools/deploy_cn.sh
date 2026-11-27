#!/usr/bin/env bash
# Render and deploy the Chinese edition (runixcloud.com) from this checkout.
#
# deploy.sh calls this after the English site is live, so both editions ship
# from the same commit; it can also be run on its own. The edition is the
# Cloudflare Pages project runix-cn (created on first run). Until the domain
# points at it, it serves at https://runix-cn.pages.dev, which Cloudflare marks
# noindex, so it never competes with either domain in search.
#
# Usage: CLOUDFLARE_API_TOKEN=<token> tools/deploy_cn.sh
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

: "${CLOUDFLARE_API_TOKEN:?set CLOUDFLARE_API_TOKEN first}"
export CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-30005bd01771d6fc41408e2c5df43ffd}"
PROJECT="runix-cn"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

echo "==> Render the Chinese edition"
python3 tools/build_cn.py --out "$OUT"

echo "==> Its markup parses"
python3 - "$OUT" <<'PY'
import pathlib, sys
sys.path.insert(0, "tools")
from html_structure import Checker, OPTIONAL_CLOSE
bad = 0
for p in sorted(pathlib.Path(sys.argv[1]).glob("*.html")):
    c = Checker()
    c.feed(p.read_text(encoding="utf-8"))
    probs = c.problems + [f"<{t}> never closed (line {l})" for t, l in c.stack if t not in OPTIONAL_CLOSE]
    probs += [f'id="{i}" appears {n} times' for i, n in c.ids.items() if n > 1]
    probs += [f"{k} points at missing #{r}" for k, r, _l in c.refs if r not in c.ids]
    for x in probs:
        print(f"    {p.name}: {x}")
    bad += len(probs)
print(f"    {bad} structural problem(s)")
sys.exit(1 if bad else 0)
PY

# Create the project on first use. wrangler's own create fails with code 8000000
# on this account; the API call does not (see the cloudflare-pages notes).
api="https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/pages/projects"
if ! curl -sf -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" "$api/$PROJECT" >/dev/null; then
  echo "==> Create Pages project $PROJECT"
  curl -sf -X POST -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H "Content-Type: application/json" \
    -d "{\"name\":\"$PROJECT\",\"production_branch\":\"main\"}" "$api" >/dev/null
fi

commit=$(git rev-parse HEAD)
subject=$(git log -1 --format=%s)
dirty=false
[ -z "$(git status --porcelain)" ] || dirty=true
echo "==> Deploy $PROJECT"
# From inside the build directory, so wrangler finds no ./functions to compile
# (the checkout function belongs to the English site only).
(cd "$OUT" && npx --yes wrangler@4 pages deploy . --project-name="$PROJECT" --branch=main \
  --commit-hash="$commit" --commit-message="$subject" --commit-dirty="$dirty" 2>&1 | tail -2)

echo "==> Verify"
sleep 15
base="https://$PROJECT.pages.dev"
fail=0
for path in / /bench /fs /router /about; do
  body=$(curl -s --max-time 20 "$base$path")
  lang=$(printf '%s' "$body" | grep -o '<html lang="[^"]*"' | head -1)
  canon=$(printf '%s' "$body" | grep -o '<link rel="canonical" href="[^"]*"' | head -1 | sed 's/.*href="//;s/"//')
  printf '    %-8s %s %s\n' "$path" "${lang:-no lang}" "${canon:-no canonical}"
  [ "$lang" = '<html lang="zh-CN"' ] || fail=1
done
loc=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' --max-time 15 "$base/plans")
printf '    /plans   -> %s\n' "$loc"
case "$loc" in 302\ https://runixcloud.io/plans) ;; *) fail=1 ;; esac
[ "$fail" -eq 0 ] && echo "==> Chinese edition OK" || { echo "==> Chinese edition verification FAILED"; exit 1; }
