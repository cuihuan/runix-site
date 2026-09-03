#!/usr/bin/env bash
# Re-run every applied builder and fail if any of them changes anything.
#
# These tools are documented as idempotent and that property is load-bearing:
# they are the reproducible record of how the site got to its current shape, so
# running one must never be dangerous. fix_orphans.py was not idempotent — its
# guard checked for the anchor it attaches to, which is still present after the
# edit, so it duplicated a bullet on /about every time it ran. Nothing would
# have noticed.
#
# Requires a clean working tree, because that is how it detects a change.
# Usage: tools/check_idempotent.sh

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

if [ -n "$(git status --porcelain)" ]; then
  echo "working tree is not clean — commit or stash first, this test needs a baseline" >&2
  exit 2
fi

# open_self_serve_signup is deliberately absent: it is not a builder but one half
# of a pair of switches (with close_signup_invite_only), so running it changes the
# site by design. Registration was closed on 2026-08-20 and the console reports
# register_enabled=false, so running it would also be wrong, not merely noisy.
BUILDERS="add_closing_ctas add_docs_nav add_router_diagram center_product_heroes
          expand_about fix_orphans wrap_tables sync_schema add_related add_glossary
          credits_on_request numbered_product_system"

fail=0
for t in $BUILDERS; do
  out=$(python3 "tools/$t.py" 2>&1)
  if [ $? -ne 0 ]; then
    echo "  ERROR $t"
    echo "$out" | tail -3 | sed 's/^/          /'
    fail=1
    continue
  fi
  dirty=$(git status --porcelain)
  if [ -n "$dirty" ]; then
    echo "  NOT IDEMPOTENT  $t changed:"
    echo "$dirty" | sed 's/^/          /'
    # Show the diff before reverting. The first version reverted first and
    # destroyed the evidence, which made the finding useless.
    git --no-pager diff --stat | sed 's/^/          /'
    git --no-pager diff | head -20 | cut -c1-140 | sed 's/^/          /'
    git checkout -- . 2>/dev/null
    fail=1
  else
    echo "  ok  $t"
  fi
done

[ $fail -eq 0 ] && echo "every builder is idempotent" || echo "ATTENTION: see above"
exit $fail
