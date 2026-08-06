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

# A sub-domain mirrors one page of the main site. Comparing only the stylesheet
# misses the case that matters more: a copy edit ships, the CSS does not change,
# so ?v= stays put, so this reports no drift and the sub-sites keep serving the
# old words. Compare the mirrored page's visible text too. Mapping is the same
# one tools/build_subsites.py uses.
# Compared against the local source file, not the live main site. Comparing two
# live URLs looked right and was not: this check runs immediately after a
# deploy, when Cloudflare's edge may still be serving the previous build of the
# main site -- so it compared a stale main page against a stale sub-domain and
# reported agreement. Proved by editing router.html, deploying, and watching it
# say "all match" while the sub-domain still had the old sentence. The file on
# disk is the thing that was just deployed, so it cannot be stale.
declare -a MIRROR=("gateway:router.html" "comic:comic.html" "code:code.html" "data:pipeline.html")

normalise() {  # stdin: html -> 16 hex chars of <main>'s visible text
  python3 -c '
import html, re, sys
s = sys.stdin.read()
# Everything between </header> and <footer>, not just <main>: the hero sits
# outside <main> on every product page, so a <main>-only comparison silently
# ignored the headline, the subtitle and the buttons -- the part of the page a
# copy edit is most likely to touch. Proved by editing the router subtitle and
# watching the hash not move.
i = s.find("</header>")
j = s.rfind("<footer")
t = s[i + 9:j] if i >= 0 and j > i else s
t = re.sub(r"<(script|style)\b.*?</\1>", " ", t, flags=re.S)
sys.stdout.write(" ".join(html.unescape(re.sub(r"<[^>]+>", " ", t)).split()))
' | shasum -a 256 | cut -c1-16
}

bodytext() { curl -s --max-time 25 "$1?b=$RANDOM$$" | normalise; }

main=$(probe runixcloud.io)
[ "${main%% *}" = "--" ] && { echo "    could not read the main site stylesheet reference"; exit 0; }

drifted=""
for h in $HOSTS; do
  [ "$(probe "$h.runixcloud.io")" = "$main" ] && continue
  # Second opinion after the other hosts have been probed, which is the gap.
  [ "$(probe "$h.runixcloud.io")" = "$main" ] && continue
  drifted="$drifted $h"
done

for pair in "${MIRROR[@]}"; do
  h=${pair%%:*}; src=${pair##*:}
  [ -f "$src" ] || continue
  case " $HOSTS " in *" $h "*) ;; *) continue ;; esac
  case " $drifted " in *" $h "*) continue ;; esac   # already flagged on CSS
  a=$(normalise < "$src")
  b=$(bodytext "https://$h.runixcloud.io/")
  [ "$a" = "$b" ] && continue
  # Second opinion, same reason as above.
  b=$(bodytext "https://$h.runixcloud.io/")
  [ "$a" = "$b" ] || drifted="$drifted $h"
done

if [ -n "$drifted" ]; then
  echo "    sub-domains behind the main site (css $main):$drifted"
  exit 1
fi
echo "    all sub-domains match the main site (stylesheet and mirrored copy)"
exit 0
