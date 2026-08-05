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

echo "==> Refresh sitemap lastmod for pages whose content changed"
python3 "$SRC/tools/update_lastmod.py" --write

echo "==> Pre-deploy checks"
# Source-level checks are cheap, so everything gets them.
python3 "$SRC/tools/qa.py" || { echo "qa.py failed — not deploying." >&2; exit 1; }
# Rendering every page at three widths takes minutes, which is too slow to sit
# in front of every deploy. This sample covers one page of each template —
# split hero, centred hero, left hero, article, docs, blog — which is where a
# shared-stylesheet regression shows up first. Run the full sweep by hand
# (python3 tools/visual_qa.py) after a change to tokens or layout.
if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
  python3 "$SRC/tools/visual_qa.py" index.html pricing.html about.html \
    docs/router.html blog/model-failover.html terms.html \
    || { echo "visual_qa.py failed — not deploying." >&2; exit 1; }
  # Homepage only: enough to catch a gross regression (an image without
  # dimensions, a stylesheet that doubled) without adding half a minute to
  # every deploy. Run the full set by hand after a change to assets.
  python3 "$SRC/tools/perf_check.py" index.html \
    || { echo "perf_check.py failed — not deploying." >&2; exit 1; }
else
  echo "    (no Chrome here — skipping the render checks)"
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

fail=0
echo "==> Verify from outside"
# This used to be a per-path retry loop that called a 404 a failure the moment
# it saw one. Cloudflare edge nodes pick up a build at different times, so a
# single probe disagrees with the next one for about a minute after upload, and
# the loop cried wolf on four separate deploys tonight. tools/verify_live.py
# probes every path three times with a gap and only reports a failure when the
# answer is consistently wrong — a flicker is reported as propagation, which is
# what it is. A gate that is wrong this often gets ignored, which is worse than
# not having it.
python3 "$SRC/tools/verify_live.py" || fail=1

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
