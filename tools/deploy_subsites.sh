#!/usr/bin/env bash
# Rebuild and deploy the four product sub-sites.
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

# Same reason as deploy.sh: a Pages-scoped token cannot enumerate accounts,
# so wrangler needs the id handed to it. Not a credential.
export CLOUDFLARE_ACCOUNT_ID="${CLOUDFLARE_ACCOUNT_ID:-30005bd01771d6fc41408e2c5df43ffd}"
: "${CLOUDFLARE_API_TOKEN:?set CLOUDFLARE_API_TOKEN first}"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

echo "==> Build"
python3 tools/build_subsites.py "$OUT"

for s in gateway comic code data; do
  echo "==> Deploy runix-$s"
  npx --yes wrangler@4 pages deploy "$OUT/subsite-$s" \
    --project-name="runix-$s" --branch=main --commit-dirty=true 2>&1 | tail -1
done

echo "==> Verify"
sleep 20
fail=0
for h in gateway router comic code data; do
  hdr=$(curl -sI --max-time 15 "https://$h.runixcloud.io/assets/style.css")
  cache=$(printf '%s' "$hdr" | grep -i '^cache-control' | tr -d '\r')
  csp=$(curl -sI --max-time 15 "https://$h.runixcloud.io/" | grep -ic content-security)
  printf '    %-9s %s | CSP=%s\n' "$h" "${cache:-none}" "$csp"
  [ "$csp" = "1" ] || fail=1
done
[ $fail -eq 0 ] && echo "==> Sub-sites OK" || { echo "==> Sub-site verification FAILED"; exit 1; }
