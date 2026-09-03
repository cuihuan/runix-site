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

echo "==> Bake the legal identity into every footer"
# Company name, registration number and contact details have to be visible in
# the served HTML, not injected by script — card acquirers check for them and a
# reviewer may read the page with JavaScript off. Runs before the asset bump so
# any page it rewrites gets a fresh hash.
python3 "$SRC/tools/render_identity.py" --write

echo "==> Bump ?v= on assets whose bytes changed"
# Must run before the checks, since it rewrites the pages. This is what makes
# the one-year cache on /assets/* safe: forgetting to bump is no longer possible.
python3 "$SRC/tools/bump_assets.py" --if-changed

echo "==> Render per-page social cards"
# Every page used to declare the same og:image, so a link shared anywhere
# previewed as the same untitled cover. Cards are content-hashed, so a retitled
# page gets a new URL under the year-long immutable cache.
python3 tools/make_og.py || { echo "    social cards failed"; exit 1; }
python3 tools/point_og.py || { echo "    pointing pages at cards failed"; exit 1; }

echo "==> Refresh sitemap lastmod for pages whose content changed"
python3 "$SRC/tools/update_lastmod.py" --write

echo "==> Code samples fit their container"
python3 tools/code_overflow.py || { echo "    a code sample is cut off"; exit 1; }

echo "==> The site still works with scripts off"
python3 tools/nojs_check.py || { echo "    the no-script nav fallback is broken"; exit 1; }

echo "==> The markup actually parses"
# qa.py is regex-based and reported a clean run on four pages whose <th> tags
# contained literal backslashes -- the pattern it greps for matched inside the
# damage. A parser sees what a pattern cannot.
python3 tools/html_structure.py || { echo "    the markup is structurally broken"; exit 1; }

echo "==> The pages run without errors"
python3 tools/console_check.py || { echo "    a page throws in the browser"; exit 1; }

echo "==> Every check can still be reached"
# A gate whose condition is never evaluated reports a clean run forever. Five
# written tonight were in that state. Costs a quarter of a second.
python3 tools/gate_coverage.py tools/qa.py || { echo "    an unexplained dead check"; exit 1; }
python3 tools/gate_coverage.py tools/perf_check.py || { echo "    an unexplained dead check"; exit 1; }

echo "==> Pre-deploy checks"
# Source-level checks are cheap, so everything gets them.
python3 "$SRC/tools/qa.py" || { echo "qa.py failed — not deploying." >&2; exit 1; }
# Rendering every page at three widths takes minutes, which is too slow to sit
# in front of every deploy. This sample covers one page of each template —
# split hero, centred hero, left hero, article, docs, blog — which is where a
# shared-stylesheet regression shows up first. Run the full sweep by hand
# (python3 tools/visual_qa.py) after a change to tokens or layout.
if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
  python3 "$SRC/tools/visual_qa.py" index.html plans.html pricing.html about.html \
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
  `# Check tools write temp pages into the site root and clean them up in a
   # finally block -- which SIGKILL skips. A killed visual_qa left a
   # zero-byte _vqa.html here tonight. qa.py catches it and aborts the
   # deploy, which is the real guard; this is the second line.` \
  --exclude '_*' \
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

# Check the URL the pages actually request, not the bare one. Since /assets/*
# became immutable for a year, the unversioned URL is frozen at whatever was
# cached when the policy landed — and nothing references it, so it can differ
# from the deployed file forever. Checking it reported a failed deploy on a
# deploy that was entirely correct.
css_ref=$(grep -o 'assets/style\.css?v=[0-9]*' "$SRC/index.html" | head -1)
check_content "assets/style.css size" \
  "$(wc -c < "$SRC/assets/style.css" | tr -d ' ')" \
  "curl -sL -o /dev/null -w '%{size_download}' --max-time 15 '$DOMAIN/$css_ref'" || fail=1

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

echo "==> Tell the search engines what changed"
# Placed after verification so the pages announced here have been seen serving.
# Submits what update_lastmod.py dated today, which it decides by content hash
# rather than mtime. Exit status is swallowed: the site is already live at this
# point, and a search-engine ping failing is not worth a red run.
python3 "$SRC/tools/indexnow.py" || true

echo "==> Keep the product sub-domains in step"
# They embed their own copy of assets/, so every stylesheet change here leaves
# them behind. Re-deploying them was a separate command someone had to remember,
# and it was missed twice -- five live domains served two-versions-old CSS.
if ! ./tools/subsite_drift.sh; then
  ./tools/deploy_subsites.sh || echo "    sub-domain re-deploy failed -- run tools/deploy_subsites.sh"
fi
