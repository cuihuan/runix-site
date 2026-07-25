#!/usr/bin/env bash
# Publish the Runix marketing site to Cloudflare Pages (direct upload).
#
# Usage:  CLOUDFLARE_API_TOKEN=<token> ./deploy.sh
#
# Everything public ships; the reserved commerce layer, package manifest and
# repo docs stay out of the deployment. Verifies the live site afterwards.
set -euo pipefail

PROJECT="runix-site"
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

echo "==> Deploy to Cloudflare Pages project $PROJECT"
npx --yes wrangler@4 pages deploy "$STAGE" --project-name="$PROJECT" --commit-dirty=true

echo "==> Verify from outside"
sleep 3
fail=0
for path in / /pricing /about /security /blog/ /terms /privacy /refund /cancellation /acceptable-use /careers; do
  code=$(curl -sL -o /dev/null -w '%{http_code}' --max-time 15 "$DOMAIN$path")
  printf '    %-20s %s\n' "$path" "$code"
  [ "$code" = "200" ] || fail=1
done
# the reserved commerce layer must not be reachable
for path in /payments/money.js /package.json; do
  code=$(curl -sL -o /dev/null -w '%{http_code}' --max-time 15 "$DOMAIN$path")
  printf '    %-20s %s (expect 404)\n' "$path" "$code"
  [ "$code" = "404" ] || fail=1
done

[ "$fail" = "0" ] && echo "==> Deploy OK" || { echo "==> Deploy FAILED verification"; exit 1; }
