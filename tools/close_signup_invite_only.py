#!/usr/bin/env python3
"""Switch the site back from self-serve signup to invite-only intake.

The console's registration was closed on 2026-08-20 (abuse control: accounts
are now created by us after a short exchange). Every page still selling
one-click signup would be sending visitors to a disabled register form.

This is the exact inverse of open_self_serve_signup.py: its EDITS/NAV tables
are imported and applied new->old, so the two migrations cannot drift apart.
Blocks that a later migration has already rewritten are reported, not forced.
Additions on top of the inverse:

  * docs/router.html §8 was written in the self-serve era and is not in the
    open script's tables — patched here explicitly.
  * A final sweep rewrites any remaining /register CTA to the contact path,
    because a button pointing at a disabled form is worse than no button.

Idempotent — re-running finds the invite-only copy in place and does nothing.
Run from the site root.
"""
import importlib.util
import os
import pathlib
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

spec = importlib.util.spec_from_file_location(
    "open_self_serve_signup", os.path.join(ROOT, "tools", "open_self_serve_signup.py"))
mod = importlib.util.module_from_spec(spec)
# The module runs main() only under __main__, so loading it is side-effect free.
spec.loader.exec_module(mod)

REGISTER = mod.REGISTER
NAV_OLD, NAV_NEW = mod.NAV_OLD, mod.NAV_NEW   # OLD = invite-only, NEW = self-serve
EDITS = mod.EDITS
ACCESS_OLD_MAIN, ACCESS_NEW_MAIN = mod.ACCESS_OLD_MAIN, mod.ACCESS_NEW_MAIN


def apply(path, current, target, problems):
    p = pathlib.Path(path)
    t = p.read_text(encoding="utf-8")
    if target in t:
        return False                      # already at invite-only state
    if current not in t:
        problems.append(path)             # a later migration rewrote this block
        return False
    if t.count(current) != 1:
        problems.append(path)
        return False
    p.write_text(t.replace(current, target), encoding="utf-8")
    return True


problems, changed = [], 0

nav_files = sorted(
    str(p) for p in pathlib.Path(".").rglob("*.html")
    if NAV_NEW in p.read_text(encoding="utf-8") or NAV_OLD in p.read_text(encoding="utf-8"))
for f in nav_files:
    if apply(f, NAV_NEW, NAV_OLD, problems):
        changed += 1
print(f"nav: {changed} page(s) back to Request access ({len(nav_files)} carry the nav)")

copy_changed = 0
for path, old, new in EDITS:              # invert: new -> old
    if apply(path, new, old, problems):
        copy_changed += 1
print(f"copy/structured data: {copy_changed} block(s) reverted")

if apply("access.html", ACCESS_NEW_MAIN, ACCESS_OLD_MAIN, problems):
    print("access.html: self-serve narrative replaced with the intake one")

# --- docs/router.html §8: not covered by the open script's tables ----------
DOCS = "docs/router.html"
DOCS_OLD = ('<p>Router is self-serve: <a href="https://console.router.runixcloud.io/register">'
            'create an account</a> and your key is issued immediately; evaluation credits are '
            'issued on request, so you can test against real traffic before you pay. For custom '
            'routing, limits above the self-serve ceiling, invoicing or a signed agreement, '
            '<a href="/about#contact">tell us what you are building</a> — models, expected '
            'volume, latency needs — and we reply within one business day. A complete API '
            'reference ships alongside; onboarded teams receive integration support directly.</p>')
DOCS_NEW = ('<p>Router is currently <strong>invite-only</strong>: '
            '<a href="/about#contact">tell us what you are building</a> — models, expected '
            'volume, latency needs — or email <a href="mailto:support@runixcloud.io">'
            'support@runixcloud.io</a>, and we reply within one business day and set the '
            'account up for you. Evaluation credits are issued on request, so you can test '
            'against real traffic before you pay. Existing accounts '
            '<a href="https://console.router.runixcloud.io">sign in here</a>.</p>')
if apply(DOCS, DOCS_OLD, DOCS_NEW, problems):
    print("docs/router.html: getting-a-key section now describes the intake path")

# --- sweep: no page may keep sending visitors to the disabled register form -
swept = 0
for p in pathlib.Path(".").rglob("*.html"):
    if "node_modules" in str(p):
        continue
    t = p.read_text(encoding="utf-8")
    if REGISTER not in t:
        continue
    n = t.count(REGISTER)
    t = t.replace(
        f'href="{REGISTER}" target="_blank" rel="noopener">Get API key<',
        'href="/about#contact">Request access<')
    t = t.replace(f'href="{REGISTER}">Create an account<', 'href="/about#contact">Request access<')
    t = t.replace(f'href="{REGISTER}">console<', 'href="https://console.router.runixcloud.io">console<')
    t = t.replace(REGISTER, "https://console.router.runixcloud.io")  # any stragglers: at least land on sign-in
    p.write_text(t, encoding="utf-8")
    swept += n
print(f"sweep: {swept} register link(s) rewritten across the site")

# --- copy written after the open migration (UX overhaul era) ---------------
# (path, old, new, expected_count) — these blocks postdate the open script's
# tables, so they need their own inverse entries.
EDITS2 = [
    ("access.html",
     "Runix Router is self-serve: create an account and issue a key in minutes; "
     "evaluation credits are issued on request. Here is exactly what happens.",
     "Runix Router is invite-only: tell us what you are building and your account "
     "is set up within one business day; evaluation credits are issued on request.",
     3),  # meta description, og:description, twitter:description
    ("access.html",
     "<p>Router is self-serve. Create an account and issue a key in minutes, then send "
     "your first request; evaluation credits are issued on request. This page describes "
     "exactly what happens — and when it is worth talking to us instead.</p>",
     "<p>Router is invite-only. Tell us what you are building and your account is set up "
     "within one business day; evaluation credits are issued on request. This page "
     "describes exactly what happens, from first message to first request.</p>",
     1),
    ("access.html",
     "<h2>1. Create your account</h2>\n"
     '<p>Sign up at <a href="https://console.router.runixcloud.io">console.router.runixcloud.io</a> with an email\n'
     "address and a password. There is no intake form, no waiting list and no card.</p>",
     "<h2>1. Ask for an account</h2>\n"
     '<p>Email <!--email_off--><a href="mailto:support@runixcloud.io">support@runixcloud.io</a><!--/email_off--> '
     'or use the <a href="/about#contact">contact form</a> with a line on what you are\n'
     "building — models, expected volume, latency needs. Access is invite-only; we reply and\n"
     "set the account up within one business day. No card, and nothing to install.</p>",
     1),
    ("access.html",
     "<p>Self-serve covers evaluation and normal production use. Come to",
     "<p>An account covers evaluation and normal production use. Come to",
     1),
    ("access.html",
     "No. Create an account and your key is issued immediately; evaluation credits are "
     "issued on request. Talk to us when you need custom routing, higher limits, invoicing "
     "or a signed agreement.",
     "Briefly, yes — access is invite-only. Send a line on what you are building and the "
     "account is set up within one business day; evaluation credits are issued on request. "
     "Mention custom routing, higher limits, invoicing or a signed agreement in the same message.",
     1),  # FAQ JSON-LD (single-line variant)
    ("access.html",
     "No. Create an account and your key is issued immediately; evaluation credits are issued on request. Talk\n"
     "to us when you need custom routing, higher limits, invoicing or a signed agreement.",
     "Briefly, yes — access is invite-only. Send a line on what you are building and the\n"
     "account is set up within one business day; evaluation credits are issued on request.\n"
     "Mention custom routing, higher limits, invoicing or a signed agreement in the same message.",
     1),  # same FAQ answer, body variant with line breaks
    ("access.html",
     "<p>Minutes. Account creation and key issue are immediate; enterprise onboarding gets a\n"
     "reply within one business day.</p>",
     "<p>One business day at most for the account reply; key issue and integration are\n"
     "immediate once you are in.</p>",
     1),
    ("access.html",
     "Minutes. Account creation and key issue are immediate; enterprise onboarding gets a reply within one business day.",
     "One business day at most for the account reply; key issue and integration are immediate once you are in.",
     0),  # JSON-LD variant if present; 0 = optional
    ("access.html",
     "<h2>Create an account</h2>\n"
     "      <p>Sign up, issue a key and point a client at the endpoint. If you need custom routing, higher limits or invoicing, tell us and we will answer concretely rather than stall.</p>",
     "<h2>Request an account</h2>\n"
     "      <p>Tell us what you are building and your account is set up within one business day — then point a client at the endpoint. If you need custom routing, higher limits or invoicing, say so in the same message and we will answer concretely rather than stall.</p>",
     1),
    ("index.html",
     "Runix Router is self-serve: create an account and your key is issued immediately. "
     "Evaluation credits are issued on request, so you can test against real traffic before "
     "you pay.",
     "Runix Router is invite-only: tell us what you are building and your account is set up "
     "within one business day. Evaluation credits are issued on request, so you can test "
     "against real traffic before you pay.",
     1),
    ("index.html",
     "<h3>Create an account</h3>\n"
     "        <p>Sign up and issue your first key in a couple of minutes.</p>",
     "<h3>Request access</h3>\n"
     "        <p>Tell us what you are building; accounts are set up within one business day.</p>",
     1),
    ("pricing.html",
     "<p>Three steps from this page to a working key. No sales call required, and nothing to install.</p>",
     "<p>Three steps from this page to a working key — nothing to install.</p>",
     1),
    ("pricing.html",
     "<h3>Create an account</h3><p>Register at the Runix console — free, instant, no card. "
     "You can issue and revoke API keys straight away, and ask for evaluation credits to try "
     "the router before paying anything.</p>",
     "<h3>Request access</h3><p>Email us or use the contact form — accounts are set up "
     "within one business day, free, no card. Once in, you issue and revoke API keys "
     "yourself, and evaluation credits are available before paying anything.</p>",
     1),
    ("pricing.html",
     "<p>Create an account and issue a key in minutes — or share your expected volume and "
     "we'll come back with a plan and pricing.</p>",
     "<p>Tell us what you are building — accounts are set up within one business day — or "
     "share your expected volume and we'll come back with a plan and pricing.</p>",
     1),
    ("router.html",
     "Create an account on the console and your key is issued immediately; evaluation "
     "credits are issued on request, so you can test against real traffic before you pay. "
     "Teams that need custom routing, higher limits or invoicing can talk to us instead. "
     "The full process is on Access .",
     "Access is invite-only: send a line on what you are building and your account is set "
     "up within one business day; evaluation credits are issued on request, so you can test "
     "against real traffic before you pay. The full process is on Access.",
     1),  # FAQ JSON-LD
    ("access.html",
     "limits above the self-serve\nceiling",
     "limits above the standard\nceiling",
     1),
    ("faq.html",
     "Create an account and your key is issued immediately; evaluation credits are issued "
     "on request, so you can test against real traffic before you pay. Talk to us when you "
     "need custom routing, higher limits, invoicing or a signed agreement — you get a reply "
     "within one business day.",
     "Access is invite-only: send a line on what you are building and your account is set "
     "up within one business day; evaluation credits are issued on request, so you can test "
     "against real traffic before you pay. Mention custom routing, higher limits, invoicing "
     "or a signed agreement in the same message.",
     2),  # FAQ JSON-LD + visible body carry the same single-line text
    ("router.html",
     '<p>Create an account on the <a href="https://console.router.runixcloud.io">console</a> '
     "and your key is issued immediately; evaluation credits are issued on request, so you "
     "can test against real traffic before you pay. Teams that need custom routing, higher "
     "limits or invoicing can talk to us instead. The full process is on "
     '<a href="/access">Access</a>.</p>',
     '<p>Access is invite-only: <a href="/about#contact">tell us what you are building</a> '
     "and your account is set up within one business day; evaluation credits are issued on "
     "request, so you can test against real traffic before you pay. The full process is on "
     '<a href="/access">Access</a>.</p>',
     1),
]

# JSON-LD answers must be substrings of the visible copy (qa.py enforces it).
EDITS2 += [
    ("access.html",
     '"text": "You get a reply within one business day."',
     '"text": "One business day at most for the account reply; key issue and integration are immediate once you are in."',
     1),
    ("router.html",
     '"text": "Access is invite-only: send a line on what you are building and your account is set '
     'up within one business day; evaluation credits are issued on request, so you can test '
     'against real traffic before you pay. The full process is on Access."',
     '"text": "Access is invite-only: tell us what you are building and your account is set up '
     'within one business day; evaluation credits are issued on request, so you can test against '
     'real traffic before you pay. The full process is on Access ."',
     1),
]

e2 = 0
for path, old, new, want in EDITS2:
    p = pathlib.Path(path)
    t = p.read_text(encoding="utf-8")
    if new in t:
        continue
    n = t.count(old)
    if n == 0 and want == 0:
        continue
    if n != max(want, 1) and not (want == 3 and n == 3):
        problems.append(f"{path} (count {n} for a block expecting {want})")
        continue
    p.write_text(t.replace(old, new), encoding="utf-8")
    e2 += 1
print(f"post-overhaul copy: {e2} block(s) moved to invite-only wording")

if problems:
    where = ", ".join(sorted(set(problems)))
    print(f"superseded by a later migration (check by hand): {where}")
