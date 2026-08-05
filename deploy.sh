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
  --exclude 'scheduled' --exclude 'tools' \
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
# Edge nodes pick up a new build at slightly different times, so a single probe
# straight after upload can report a 404 for a page that is served fine a few
# seconds later. Retry the same way the content checks below already do, and
# only call it a failure when it stays wrong.
for path in / /pricing /about /security /blog/ /terms /privacy /refund /cancellation /acceptable-use /careers /faq /access /reliability; do
  for attempt in 1 2 3 4 5 6; do
    code=$(curl -sL -o /dev/null -w '%{http_code}' --max-time 15 "$DOMAIN$path")
    [ "$code" = "200" ] && break
    sleep 10
  done
  printf '    %-20s %s\n' "$path" "$code"
  [ "$code" = "200" ] || fail=1
done

# A 200 only proves something is served. Compare what is served with what was
# built — and retry, because the edge takes up to a minute to catch up and a
# check run immediately after upload reports the previous build.
check_content() {
  local label="$1" expected="$2" actual_cmd="$3" actual
  for attempt in 1 2 3 4 5 6; do
    actual=$(eval "$actual_cmd")
    if [ "$actual" = "$expected" ]; then
      printf '    %-22s match\n' "$label"
      return 0
    fi
    sleep 10
  done
  printf '    %-22s MISMATCH after 60s\n      expected: %s\n      live:     %s\n' \
    "$label" "$expected" "$actual"
  return 1
}

check_content "index <title>" \
  "$(grep -o '<title>[^<]*</title>' "$SRC/index.html" | head -1)" \
  "curl -sL --max-time 15 '$DOMAIN/' | grep -o '<title>[^<]*</title>' | head -1" || fail=1

check_content "index <h1>" \
  "$(grep -o '<h1>.*</h1>' "$SRC/index.html" | head -1)" \
  "curl -sL --max-time 15 '$DOMAIN/' | grep -o '<h1>.*</h1>' | head -1" || fail=1

check_content "assets/style.css size" \
  "$(wc -c < "$SRC/assets/style.css" | tr -d ' ')" \
  "curl -sL -o /dev/null -w '%{size_download}' --max-time 15 '$DOMAIN/assets/style.css'" || fail=1

# whatever the pages point at socially has to actually exist
og=$(grep -o 'og:image" content="[^"]*"' "$SRC/index.html" | head -1 | sed 's/.*content="//;s/"$//')
if [ -n "$og" ]; then
  check_content "og:image reachable" "200" \
    "curl -sL -o /dev/null -w '%{http_code}' --max-time 15 '$og'" || fail=1
fi
# the reserved commerce layer must not be reachable
for path in /payments/money.js /package.json; do
  code=$(curl -sL -o /dev/null -w '%{http_code}' --max-time 15 "$DOMAIN$path")
  printf '    %-20s %s (expect 404)\n' "$path" "$code"
  [ "$code" = "404" ] || fail=1
done

[ "$fail" = "0" ] && echo "==> Deploy OK" || { echo "==> Deploy FAILED verification"; exit 1; }
