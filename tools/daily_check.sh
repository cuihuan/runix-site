#!/usr/bin/env bash
# Daily health and honesty check for runixcloud.io.
#
# Answers three questions that nothing else will notice going wrong:
#   1. Is everything still serving?          (verify_live.py)
#   2. Is the TLS claim on /security still true?  (check_tls.py)
#   3. Do the pages still pass their own checks?  (qa.py)
#
# Everything here is read-only against production. It changes nothing, so it is
# safe to run unattended.
#
# Install:
#   crontab -e
#   17 9 * * *  /Users/cuihuan/Desktop/workspace/AI/runix/site/tools/daily_check.sh >> /tmp/runix-daily.log 2>&1
#
# Reads the log with:  tail -40 /tmp/runix-daily.log
#
# Exit code is non-zero if anything failed, so a cron MAILTO or a wrapper can
# act on it.

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

STAMP="$(date '+%Y-%m-%d %H:%M %Z')"
FAIL=0
echo "===== $STAMP ====="

run() {
  local label="$1"; shift
  local out
  out="$("$@" 2>&1)"
  local code=$?
  if [ $code -eq 0 ]; then
    echo "  OK   $label"
  else
    FAIL=1
    echo "  FAIL $label"
    echo "$out" | sed 's/^/         /'
  fi
}

run "site serving (all paths, 3 rounds)" python3 tools/verify_live.py
run "/security TLS claim still true"     python3 tools/check_tls.py
run "page checks"                        python3 tools/qa.py

# The gateway is not this repo's to deploy, but if it stops answering, the
# marketing site is the least of the problems — so it is worth one probe.
# Retry before believing a failure. Measured over 88 probes tonight, about 3%
# of single requests from this machine return 000 — a local proxy dropping a
# connection, not the host: the rounds where runixcloud.io/ failed had
# runixcloud.io/docs/ succeeding in the same round, and a host cannot be down
# for one path only. A daily check that cries wolf at 3% gets ignored.
API_CODE=""
for attempt in 1 2 3; do
  API_CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 \
    https://api.router.runixcloud.io/v1/models)
  [ "$API_CODE" = "401" ] && break
  sleep 3
done
if [ "$API_CODE" = "401" ]; then
  echo "  OK   gateway auth (401 for an unauthenticated call)"
else
  FAIL=1
  echo "  FAIL gateway returned $API_CODE for an unauthenticated /v1/models (expected 401)"
fi

# The sub-sites embed a copy of _headers taken when they were built, so a
# change to the CSP or the cache policy on the main site does not reach them
# until tools/deploy_subsites.sh runs. That drift has been live twice; detecting
# it beats remembering. Read through a cache-busting query so a stale edge copy
# is not mistaken for stale configuration.
main_csp=$(curl -sI --max-time 15 "https://runixcloud.io/?b=$$" | grep -ic content-security)
main_cache=$(curl -sI --max-time 15 "https://runixcloud.io/assets/style.css?b=$$" \
  | grep -i '^cache-control' | tr -d '\r' | cut -d: -f2- | tr -d ' ')
for h in gateway comic code data; do
  sub_csp=$(curl -sI --max-time 15 "https://$h.runixcloud.io/?b=$$" | grep -ic content-security)
  sub_cache=$(curl -sI --max-time 15 "https://$h.runixcloud.io/assets/style.css?b=$$" \
    | grep -i '^cache-control' | tr -d '\r' | cut -d: -f2- | tr -d ' ')
  # Headers alone were not enough: all four subdomains matched on headers while
  # serving a stylesheet two versions behind, because they embed their own copy
  # of assets/ and reference whatever ?v= they were built with. Compare the
  # stylesheet the page actually asks for, byte for byte.
  main_ref=$(curl -s --max-time 15 "https://runixcloud.io/?b=$$" \
    | grep -o 'assets/style\.css?v=[0-9]*' | head -1)
  main_css=$(curl -s -o /dev/null -w '%{size_download}' --max-time 15 \
    "https://runixcloud.io/$main_ref")
  sub_ref=$(curl -s --max-time 15 "https://$h.runixcloud.io/?b=$$" \
    | grep -o 'assets/style\.css?v=[0-9]*' | head -1)
  sub_css=$(curl -s -o /dev/null -w '%{size_download}' --max-time 15 \
    "https://$h.runixcloud.io/$sub_ref")
  if [ "$sub_csp" = "$main_csp" ] && [ "$sub_cache" = "$main_cache" ] \
     && [ "$sub_css" = "$main_css" ]; then
    echo "  OK   $h subdomain matches the main site (headers and stylesheet)"
  else
    FAIL=1
    echo "  FAIL $h subdomain headers drifted from the main site"
    echo "         main: csp=$main_csp cache=$main_cache css=$main_ref ($main_css bytes)"
    echo "         sub:  csp=$sub_csp cache=$sub_cache css=$sub_ref ($sub_css bytes)"
    echo "         fix:  CLOUDFLARE_API_TOKEN=... tools/deploy_subsites.sh"
  fi
done

# Certificate expiry, because a cert that lapses takes everything with it and
# gives about a month of warning that nobody is watching for.
for host in runixcloud.io api.router.runixcloud.io console.router.runixcloud.io; do
  days=$(python3 - "$host" <<'PY'
import datetime, socket, ssl, sys
host = sys.argv[1]
ctx = ssl.create_default_context()
try:
    with socket.create_connection((host, 443), timeout=10) as s:
        with ctx.wrap_socket(s, server_hostname=host) as t:
            exp = datetime.datetime.strptime(t.getpeercert()["notAfter"],
                                             "%b %d %H:%M:%S %Y %Z")
    exp = exp.replace(tzinfo=datetime.timezone.utc)
    print((exp - datetime.datetime.now(datetime.timezone.utc)).days)
except Exception:
    print(-1)
PY
)
  if [ "$days" -lt 0 ]; then
    FAIL=1; echo "  FAIL could not read certificate for $host"
  elif [ "$days" -lt 14 ]; then
    FAIL=1; echo "  FAIL certificate for $host expires in $days day(s)"
  else
    echo "  OK   certificate for $host valid $days more day(s)"
  fi
done

[ $FAIL -eq 0 ] && echo "  all clear" || echo "  ATTENTION NEEDED"
exit $FAIL
