#!/usr/bin/env bash
# Exercise tools/deploy_provenance.py against a throwaway bare origin.
# No network, no Cloudflare: the live deployment is faked through
# DEPLOY_PROVENANCE_TEST_LIVE_COMMIT. Every case states what it expects.
set -uo pipefail
TOOL="$(cd "$(dirname "$0")" && pwd)/deploy_provenance.py"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
fails=0
expect() {  # expect <label> <want-exit> <want-text> -- cmd...
  local label="$1" want="$2" text="$3"; shift 4
  out=$("$@" 2>&1); got=$?
  if [ "$got" = "$want" ] && { [ -z "$text" ] || grep -qF -- "$text" <<<"$out"; }; then
    echo "  ok    $label"
  else
    echo "  FAIL  $label (exit $got, want $want; text '$text')"; echo "$out" | sed 's/^/        /'
    fails=$((fails+1))
  fi
}

git init -q --bare "$T/origin.git"
git clone -q "$T/origin.git" "$T/a" 2>/dev/null
cd "$T/a" && git config user.email t@x.invalid && git config user.name t
git checkout -q -b site && echo one > page.html && git add . && git commit -qm one && git push -q origin site
first=$(git rev-parse HEAD)
echo two > page.html && git commit -qam two
export CLOUDFLARE_API_TOKEN=unused CLOUDFLARE_ACCOUNT_ID=unused

export DEPLOY_PROVENANCE_TEST_LIVE_COMMIT=$first
expect "clean, ahead of origin, live is an ancestor" 0 "contained in HEAD" -- python3 "$TOOL" check

export DEPLOY_PROVENANCE_TEST_LIVE_COMMIT=0123456789abcdef0123456789abcdef01234567
expect "live built from a commit this copy never saw" 1 "never seen" -- python3 "$TOOL" check
expect "same, overridden with DEPLOY_FORCE" 0 "DEPLOY_FORCE set" -- env DEPLOY_FORCE=test python3 "$TOOL" check

export DEPLOY_PROVENANCE_TEST_LIVE_COMMIT=$first
echo dirty >> page.html
expect "uncommitted change in the tree" 1 "uncommitted" -- python3 "$TOOL" check
expect "record commits the rewrite" 0 "recorded 1" -- python3 "$TOOL" record
expect "record again changes nothing" 0 "changed nothing" -- python3 "$TOOL" record
expect "push fast-forwards origin/site" 0 "is now" -- python3 "$TOOL" push

git clone -q --branch site "$T/origin.git" "$T/b" && (cd "$T/b" && git config user.email b@x.invalid && git config user.name b \
  && echo other > other.html && git add . && git commit -qm other && git push -q origin site)
expect "someone pushed meanwhile: refuse to deploy over it" 1 "pull --ff-only" -- python3 "$TOOL" check
echo three > page.html && git commit -qam three
expect "push after a concurrent push is rejected, not forced" 1 "PUSH FAILED" -- python3 "$TOOL" push

deployed=$(git rev-parse HEAD)
# What the old hint said (pull --rebase) rewrites the deployed commit:
git branch -q rebased HEAD && git checkout -q rebased && git pull -q --rebase origin site
export DEPLOY_PROVENANCE_TEST_LIVE_COMMIT=$deployed
expect "rebasing instead rewrites the deployed commit and is refused" 1 "not in HEAD's history" -- python3 "$TOOL" check
git checkout -q site
git pull -q --no-rebase --no-edit origin site && git push -q origin HEAD:site
export DEPLOY_PROVENANCE_TEST_LIVE_COMMIT=$deployed
expect "after merging the concurrent push, the deployed commit is accepted" 0 "contained in HEAD" -- python3 "$TOOL" check

git checkout -q -b elsewhere "$first"
export DEPLOY_PROVENANCE_TEST_LIVE_COMMIT=$(git -C "$T/a" rev-parse site)
expect "live commit known but not in HEAD's history" 1 "not in HEAD's history" -- python3 "$TOOL" check

[ "$fails" = "0" ] && echo "deploy_provenance: all cases pass" || { echo "deploy_provenance: $fails case(s) failed"; exit 1; }
