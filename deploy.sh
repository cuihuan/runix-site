#!/usr/bin/env bash
# Publish the Runix marketing site to Cloudflare Pages (direct upload).
#
# Usage:  CLOUDFLARE_API_TOKEN=<token> ./deploy.sh
#
# Everything public ships; the reserved commerce layer, package manifest and
# repo docs stay out of the deployment. Verifies the live site afterwards.
set -euo pipefail

PROJECT="runix-site"
PROD_BRANCH="main"   # the project's production branch; anything else is a preview
DOMAIN="https://runixcloud.io"
SRC="$(cd "$(dirname "$0")" && pwd)"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo "CLOUDFLARE_API_TOKEN is not set. Create a scoped token with Pages:Edit and re-run." >&2
  exit 1
fi

echo "==> Stage public files"
rsync -a \
  --exclude '.git' --exclude '.wrangler' --exclude 'node_modules' \
  --exclude 'payments' --exclude 'package.json' --exclude 'package-lock.json' \
  --exclude 'README.md' --exclude 'deploy.sh' --exclude '.DS_Store' --exclude '.gitignore' \
  "$SRC/" "$STAGE/"
echo "    $(find "$STAGE" -type f | wc -l | tr -d ' ') files"

echo "==> Deploy to Cloudflare Pages project $PROJECT (branch $PROD_BRANCH)"
# Without an explicit branch wrangler uses the checked-out git branch, which
# lands on a preview URL and leaves the custom domain on the old build.
npx --yes wrangler@4 pages deploy "$STAGE" --project-name="$PROJECT" \
  --branch="$PROD_BRANCH" --commit-dirty=true

echo "==> Verify from outside"
sleep 3
fail=0
for path in / /pricing /about /security /blog/ /terms /privacy /refund /cancellation /acceptable-use /careers; do
  code=$(curl -sL -o /dev/null -w '%{http_code}' --max-time 15 "$DOMAIN$path")
  printf '    %-20s %s\n' "$path" "$code"
  [ "$code" = "200" ] || fail=1
done

# a 200 only proves something is served — compare what is served with what we built
local_css=$(wc -c < "$SRC/assets/style.css" | tr -d ' ')
live_css=$(curl -sL -o /dev/null -w '%{size_download}' --max-time 15 "$DOMAIN/assets/style.css")
printf '    %-20s local=%s live=%s\n' "assets/style.css" "$local_css" "$live_css"
[ "$local_css" = "$live_css" ] || { echo "    stylesheet mismatch — the custom domain is serving an older build"; fail=1; }

local_h1=$(grep -o '<h1>.*</h1>' "$SRC/index.html" | head -1)
live_h1=$(curl -sL --max-time 15 "$DOMAIN/" | grep -o '<h1>.*</h1>' | head -1)
[ "$local_h1" = "$live_h1" ] || { echo "    homepage headline mismatch — the custom domain is serving an older build"; fail=1; }
# the reserved commerce layer must not be reachable
for path in /payments/money.js /package.json; do
  code=$(curl -sL -o /dev/null -w '%{http_code}' --max-time 15 "$DOMAIN$path")
  printf '    %-20s %s (expect 404)\n' "$path" "$code"
  [ "$code" = "404" ] || fail=1
done

[ "$fail" = "0" ] && echo "==> Deploy OK" || { echo "==> Deploy FAILED verification"; exit 1; }
