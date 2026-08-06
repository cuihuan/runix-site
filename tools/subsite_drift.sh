#!/usr/bin/env bash
# Exit 1 when a product sub-domain is serving a different stylesheet from the
# main site. Exit 0 when they agree.
#
# The sub-sites embed their own copy of assets/, so every main-site CSS change
# leaves them behind until tools/deploy_subsites.sh runs. That is a step which
# depends on someone remembering, and it has been missed twice. deploy.sh calls
# this and re-deploys them itself when it fires.
#
# Probes twice with a gap: Cloudflare edge nodes pick up a build at different
# times, and a single probe right after a deploy reports drift that is really
# propagation. Two disagreements are drift; one is the edge catching up.
set -uo pipefail
HOSTS=${HOSTS:-"gateway comic code data"}

probe() {  # host -> "<ref> <bytes>"
  local host=$1 ref bytes
  ref=$(curl -s --max-time 15 "https://$host/?b=$RANDOM$$" \
        | grep -o 'assets/style\.css?v=[0-9]*' | head -1)
  [ -z "$ref" ] && { echo "-- 0"; return; }
  bytes=$(curl -sL --max-time 15 -o /dev/null -w '%{size_download}' "https://$host/$ref")
  echo "$ref $bytes"
}

main=$(probe runixcloud.io)
[ "${main%% *}" = "--" ] && { echo "    could not read the main site stylesheet reference"; exit 0; }

drifted=""
for h in $HOSTS; do
  [ "$(probe "$h.runixcloud.io")" = "$main" ] && continue
  # Second opinion after the other hosts have been probed, which is the gap.
  [ "$(probe "$h.runixcloud.io")" = "$main" ] && continue
  drifted="$drifted $h"
done

if [ -n "$drifted" ]; then
  echo "    sub-domains behind the main site ($main):$drifted"
  exit 1
fi
echo "    all sub-domains serve the same stylesheet as the main site"
exit 0
