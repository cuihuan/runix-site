#!/usr/bin/env bash
# Rebuild and deploy the product sub-sites.
#
# They are separate Cloudflare Pages projects and deploy.sh does not touch
# them. They also embed a copy of _headers taken at build time, so any change
# to the CSP or the cache policy on the main site does not reach them until
# this runs. That gap has been live twice in one night; tools/daily_check.sh
# now detects it rather than relying on anyone remembering.
#
# Usage: CLOUDFLARE_API_TOKEN=<token> tools/deploy_subsites.sh
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

: "${CLOUDFLARE_API_TOKEN:?set CLOUDFLARE_API_TOKEN first}"
# A Pages-scoped token cannot list accounts, so without this wrangler fails with
# "Failed to automatically retrieve account IDs" -- unless it happens to find
# the id cached in ./.wrangler, which is only true in the repository root. The
# id identifies the account; it authorises nothing, so it belongs in the script.
export CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-30005bd01771d6fc41408e2c5df43ffd}"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

echo "==> Build"
python3 tools/build_subsites.py "$OUT"

# wrangler compiles Pages Functions from ./functions in the directory it runs
# in, not from the directory it uploads. Run from the repository root, every
# sub-site shipped the main site's checkout function: POST /api/airwallex/intent
# answered on all four product subdomains (503, unconfigured -- the projects hold
# no payment secrets) until 2026-09-29. A sub-site is one static page, so each
# deploy runs from inside its own build directory, where there is nothing to
# compile.
for s in gateway comic code data fs models; do
  echo "==> Deploy runix-$s"
  (cd "$OUT/subsite-$s" && npx --yes wrangler@4 pages deploy . \
    --project-name="runix-$s" --branch=main --commit-dirty=true 2>&1 | tail -1)
done

echo "==> Verify"
sleep 20
fail=0
for h in gateway router comic code data fs models; do
  hdr=$(curl -sI --max-time 15 "https://$h.runixcloud.io/assets/style.css")
  cache=$(printf '%s' "$hdr" | grep -i '^cache-control' | tr -d '\r')
  csp=$(curl -sI --max-time 15 "https://$h.runixcloud.io/" | grep -ic content-security)
  printf '    %-9s %s | CSP=%s\n' "$h" "${cache:-none}" "$csp"
  [ "$csp" = "1" ] || fail=1
done
# No sub-site may answer on the checkout route; it belongs to the main site.
for h in gateway router comic code data fs models; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST --max-time 15 "https://$h.runixcloud.io/api/airwallex/intent")
  if [ "$code" != "404" ] && [ "$code" != "405" ]; then
    printf '    %-9s POST /api/airwallex/intent -> %s (expected no function here)\n' "$h" "$code"
    fail=1
  fi
done
[ $fail -eq 0 ] && echo "==> Sub-sites OK" || { echo "==> Sub-site verification FAILED"; exit 1; }
