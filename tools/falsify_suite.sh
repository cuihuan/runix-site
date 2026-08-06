#!/usr/bin/env bash
# Re-prove every gate added tonight, using tools/falsify.py so the injection
# itself is trustworthy.
#
# Each of these was falsified by hand when written, but roughly a quarter of
# those hand injections did not land where I assumed, so "it fired once" is not
# durable evidence. This re-runs them all through the harness, which refuses to
# report success unless the edit really landed inside the named region and the
# check really failed for the stated reason.
#
# Run after touching qa.py, or when a gate starts looking suspiciously quiet.
set -uo pipefail
cd "$(dirname "$0")/.."
QA="python3 tools/qa.py"
pass=0; fail=0

try() {  # label file old new expect [scope-start scope-end]
  local label=$1 file=$2 old=$3 new=$4 expect=$5
  shift 5
  local scope=()
  [ $# -ge 2 ] && scope=(--scope-start "$1" --scope-end "$2")
  local out rc
  # ${scope[@]+...} because set -u treats an empty array as unbound in bash 3,
  # which is what ships on macOS. Without it every case failed on the harness
  # rather than on the gate -- the exact class of noise falsify.py exists to
  # stop, reproduced in the runner around it.
  out=$(python3 tools/falsify.py "$file" "$old" "$new" --check "$QA" \
        --expect "$expect" ${scope[@]+"${scope[@]}"} 2>&1)
  rc=$?
  if [ $rc -eq 0 ]; then
    printf "  ok   %s\n" "$label"; pass=$((pass+1))
  else
    printf "  FAIL %s\n       %s\n" "$label" "$(echo "$out" | head -1 | sed 's/^ *//')"
    fail=$((fail+1))
  fi
}

try "retired model id in an example" \
    blog/llm-gateway-guide.html '"model": "your-model-id"' '"model": "gpt-4o-2024-05-13"' \
    "will be retired on someone else"

try "two pages sharing one social card" \
    router.html "assets/og/router.png" "assets/og/pricing.png" \
    "pages share the share card"

try "aria-hidden link still focusable" \
    blog/index.html ' aria-hidden="true" tabindex="-1"' ' aria-hidden="true"' \
    "aria-hidden but still focusable"

try "a card hiding its only link" \
    docs/index.html '<h3><a href="/docs/comic">Runix Comic</a></h3>' '<h3>Runix Comic</h3>' \
    "unreachable by keyboard"

try "same link text, two destinations" \
    router.html '<a class="btn btn-ghost" href="/docs/router"' \
    '<a class="btn btn-ghost" href="/pricing">Read the docs</a> <a class="btn btn-ghost" href="/docs/router"' \
    "different destinations"

try "hero button repeating a header link" \
    router.html '<a class="btn btn-ghost" href="/docs/router"' \
    '<a class="btn btn-ghost" href="https://console.router.runixcloud.io">Sign in to console</a> <a class="btn btn-ghost" href="/docs/router"' \
    "the header already links to"

try "pipeline stage count disagreeing" \
    about.html "The six Pipeline stages" "The five Pipeline stages" \
    "five stages"

try "product count disagreeing" \
    about.html "Four products" "Five products" \
    "product pages"

try "our own page named but not linked" \
    faq.html '<a href="/security">Security page</a>' 'Security page' \
    "without linking it"

try "article byline disagreeing with schema" \
    blog/llm-observability.html '"datePublished": "2026-07-27' '"datePublished": "2026-07-20' \
    "Article.datePublished"

try "ruled list without a last-child reset" \
    assets/style.css ".plan ul li:last-child { border-bottom: none; }" "" \
    "rules every row including the last"

try "incomplete social preview tags" \
    router.html '<meta property="og:type"' '<meta property="og:TYPO"' \
    "will preview incompletely"

try "twitter:card too small for a 1200x630 image" \
    router.html 'name="twitter:card" content="summary_large_image"' \
    'name="twitter:card" content="summary"' \
    "renders as a thumbnail"

QA_HS="python3 tools/html_structure.py"
QA_SAVE0=$QA
QA=$QA_HS
try "markup with an unclosed element" \
    router.html '</main>' '<section>' "never closed"
try "a duplicate id" \
    blog/llm-observability.html '<aside class="related"' \
    '<div id="related-reading"></div><aside class="related"' "appears 2 times"
try "a fragment link pointing nowhere" \
    docs/router.html 'href="#quickstart"' 'href="#does-not-exist"' "not an id"
QA=$QA_SAVE0

try "a relative asset path with the wrong depth" \
    blog/llm-observability.html '../assets/style.css' 'assets/style.css' \
    "is not a file here"

try "an asset reference to a file that does not exist" \
    router.html 'assets/site-config.js' 'assets/site-config-renamed.js' \
    "is not a file here"

try "header cells without scope" \
    privacy.html ' scope="col"' '' "have no scope"

try "an attribute value with a literal backslash" \
    privacy.html '<th scope="col">' '<th scope=\"col\">' "literal backslash"

try "an unnamed complementary landmark" \
    blog/llm-observability.html '<aside class="related" aria-labelledby="related-reading">' \
    '<aside class="related">' "no name"

try "two navs sharing one name" \
    docs/router.html 'aria-labelledby="toc-heading"' 'aria-labelledby="more-docs"' \
    "share the name"

try "skip link that skips the page title" \
    router.html '</header>
<main id="main">' '</header>' \
    "skips the title of the page"

try "a gap in the heading outline" \
    docs/router.html '<h2 id=' '<h4 id=' \
    "heading outline jumps"

try "a link whose name is a paragraph" \
    index.html ' aria-label="Explore Runix Router"' '' \
    "accessible name is"

QA_SAVE=$QA
QA="python3 tools/nojs_check.py"
try "no-script nav fallback removed" \
    index.html '<noscript><style>' '<noscript><style-disabled>' \
    "no <noscript> nav fallback"
try "no-script fallback that reveals nothing" \
    index.html '.nav-links{display:flex!important' '.nav-links{display:none!important' \
    "nav link(s) visible"
QA=$QA_SAVE

echo
echo "  $pass gate(s) proved, $fail unproved"
[ "$fail" -eq 0 ]
