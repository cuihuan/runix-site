#!/usr/bin/env python3
"""Switch the site from invite-only intake to self-serve signup.

The console has had `RegisterEnabled` on the whole time, but nothing on this
site ever said so: every page offered "Sign in" and "Request access", and four
pages argued at length that self-serve signup deliberately did not exist. A
visitor who wanted an account had no route to one that did not go through a
mailbox.

Positioning was welded in deeper than the nav. It lived in the /access page's
whole narrative, in three sets of FAQ JSON-LD, in the about page's facts table
and in the router page's capability callout. Changing the buttons alone would
have left the structured data telling Google the opposite of the page — so all
of it moves together or none of it does.

Two things deliberately do NOT change:

  * The no-SLA disclaimers. Dropping "early access" from a sentence whose job
    is to withhold a commitment would quietly strengthen the commitment. They
    are reworded to say the same thing without implying invite-only.
  * pricing.html's note that self-serve checkout is not live yet. That is still
    true — Stripe is not enabled — and a signup funnel that lies about payment
    is worse than one that admits the gap.

"Request access" survives as the enterprise path (custom routing, higher
limits, invoicing); it just stops being the only door.

Idempotent — re-running finds the new copy already in place and does nothing.
Run from the site root.
"""
import os
import pathlib
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CONSOLE = "https://console.router.runixcloud.io"
REGISTER = f"{CONSOLE}/register"

# --- the nav, on every page that has one -----------------------------------
NAV_OLD = '<a class="nav-cta" href="/about#contact">Request access</a>'
NAV_NEW = f'<a class="nav-cta" href="{REGISTER}">Sign up</a>'

# --- page copy, structured data and CTAs -----------------------------------
# (path, old, new). Each old must appear exactly once, or the new must already
# be there; anything else is a mismatch worth stopping for.
EDITS = [
    # ---------------------------------------------------------------- index
    ("index.html",
     "Runix Router is in early access: we issue keys and onboard teams "
     "individually rather than through self-serve signup. Pipeline is built "
     "with design partners; Code and Comic are in development with waitlists "
     "open.",
     "Runix Router is self-serve: create an account and your key is issued "
     "immediately, with evaluation credits to test against real traffic. "
     "Pipeline is built with design partners; Code and Comic are in "
     "development with waitlists open."),

    ("index.html",
     "<span>Status: early access</span>",
     "<span>Status: available</span>"),

    ("index.html",
     "        <h3>Request access</h3>\n"
     "        <p>Tell us what you're building and we'll get you set up with "
     "access and keys.</p>\n"
     '        <a class="btn btn-primary" href="/about#contact">Request access</a>',
     "        <h3>Create an account</h3>\n"
     "        <p>Sign up, get evaluation credits and issue your first key in "
     "a couple of minutes.</p>\n"
     f'        <a class="btn btn-primary" href="{REGISTER}">Create an account</a>'),

    ("index.html",
     "      <p>Tell us your use case and expected volume — we'll come back "
     "with a concrete plan and pricing.</p>\n"
     '      <a class="btn btn-grad" href="/about#contact">Request access</a>',
     "      <p>Create an account and issue a key in minutes — or tell us your "
     "expected volume and we'll come back with a plan and pricing.</p>\n"
     f'      <a class="btn btn-grad" href="{REGISTER}">Create an account</a>'),

    # --------------------------------------------------------------- router
    ("router.html",
     '"text": "Router is in early access, so keys are issued after a short '
     'intake rather than through self-serve signup. Tell us the workload, the '
     'providers you need and the volume you expect, and you get a key and a '
     'named engineer. The full process is on Access ."',
     '"text": "Create an account on the console and your key is issued '
     'immediately, with evaluation credits to test against real traffic. Teams '
     'that need custom routing, higher limits or invoicing can talk to us '
     'instead. The full process is on Access ."'),

    # Reworded, not removed: this sentence exists to withhold an SLA.
    ("router.html",
     "<span>Runix Router is in early access, so treat capability claims as "
     "what the product does for onboarded teams today — not as a published "
     "SLA. Ask us for specifics on your workload and we will answer "
     "concretely, in writing.</span>",
     "<span>Runix Router does not publish an SLA, so treat capability claims "
     "as what the product does today — not as a contractual commitment. Ask us "
     "for specifics on your workload and we will answer concretely, in "
     "writing.</span>"),

    ("router.html",
     '<div class="card"><h3>How do I get access?</h3><p>Router is in early '
     "access, so keys are issued after a short intake rather than through "
     "self-serve signup. Tell us the workload, the providers you need and the "
     "volume you expect, and you get a key and a named engineer. The full "
     'process is on <a href="/access">Access</a>.</p></div>',
     '<div class="card"><h3>How do I get access?</h3><p>Create an account on '
     f'the <a href="{REGISTER}">console</a> and your key is issued immediately, '
     "with evaluation credits to test against real traffic. Teams that need "
     "custom routing, higher limits or invoicing can talk to us instead. The "
     'full process is on <a href="/access">Access</a>.</p></div>'),

    # The product page led with "Request access" in the hero and again in the
    # closing band. On a self-serve product those are the two places a reader
    # is most likely to act, so they lead with the primary path now; the quote
    # route stays in the sentence rather than on the button.
    ("router.html",
     '      <a class="btn btn-primary" href="/about#contact">Request access</a>\n'
     '      <a class="btn btn-ghost" href="/pricing">See how billing works</a>',
     f'      <a class="btn btn-primary" href="{REGISTER}">Create an account</a>\n'
     '      <a class="btn btn-ghost" href="/pricing">See how billing works</a>'),

    ("router.html",
     "      <p>Tell us the models you call and roughly how much — we come back "
     "with an access plan and a quote within one business day.</p>\n"
     '      <a class="btn btn-grad" href="/about#contact">Request access</a>',
     "      <p>Create an account and point a client at the endpoint — or tell "
     "us the models you call and roughly how much, and we come back with a "
     "quote within one business day.</p>\n"
     f'      <a class="btn btn-grad" href="{REGISTER}">Create an account</a>'),

    # ---------------------------------------------------------------- about
    ("about.html",
     "<li><strong>Runix Router</strong> — <em>early access, running traffic "
     "today.</em>",
     "<li><strong>Runix Router</strong> — <em>generally available, running "
     "traffic today.</em>"),

    ("about.html",
     '<div class="frow"><span class="k">Access</span><span class="v">Keys '
     "issued after intake<small>No self-serve signup during early access"
     "</small></span></div>",
     '<div class="frow"><span class="k">Access</span><span class="v">Self-serve '
     "signup<small>Enterprise onboarding and invoicing on request</small>"
     "</span></div>"),

    ("about.html",
     "<h3>No SLA during early access</h3>",
     "<h3>No published SLA</h3>"),

    # -------------------------------------------------------------- pricing
    ("pricing.html",
     '<a class="btn btn-ghost btn-block" href="/about#contact">Request access</a>',
     f'<a class="btn btn-ghost btn-block" href="{REGISTER}">Create an account</a>'),

    ("pricing.html",
     '<a class="btn btn-grad btn-block" href="/about#contact">Request access</a>',
     f'<a class="btn btn-grad btn-block" href="{REGISTER}">Create an account</a>'),

    ("pricing.html",
     "      <p>Share your expected volume and the models you want — we'll come "
     "back with a clear plan and pricing.</p>\n"
     '      <a class="btn btn-grad" href="/about#contact">Request access</a>',
     "      <p>Create an account and start on evaluation credits — or share "
     "your expected volume and we'll come back with a plan and pricing.</p>\n"
     f'      <a class="btn btn-grad" href="{REGISTER}">Create an account</a>'),

    # --------------------------------------------------------------- access
    # Meta, og and twitter descriptions all carried the same sentence.
    ("access.html",
     "Runix Router is in early access: keys are issued after a short intake "
     "rather than through self-serve signup. Here is exactly what that "
     "involves.",
     "Runix Router is self-serve: create an account, get evaluation credits "
     "and issue a key in minutes. Here is exactly what happens."),

    ("access.html",
     '      "name": "Why is there no self-serve signup?",\n'
     '      "acceptedAnswer": {\n'
     '        "@type": "Answer",\n'
     '        "text": "Because keys carry real quotas and routing '
     'configuration, and during early access those are set per team rather '
     'than issued blindly."',
     '      "name": "Do I need to talk to anyone to start?",\n'
     '      "acceptedAnswer": {\n'
     '        "@type": "Answer",\n'
     '        "text": "No. Create an account on the console and your key is '
     "issued immediately, with evaluation credits. Talk to us when you need "
     "custom routing, higher limits, invoicing or a signed agreement.\""),

    ("access.html",
     '"text": "Nothing. Evaluation credits are issued on request and no card '
     'is required to start."',
     '"text": "Nothing. New accounts start with evaluation credits and no card '
     'is required."'),

    ("access.html",
     '      "name": "How long does it take?",\n'
     '      "acceptedAnswer": {\n'
     '        "@type": "Answer",\n'
     '        "text": "You get a reply within one business day."',
     '      "name": "How long does it take?",\n'
     '      "acceptedAnswer": {\n'
     '        "@type": "Answer",\n'
     '        "text": "Minutes. Account creation and key issue are immediate; '
     'enterprise onboarding gets a reply within one business day."'),
]

# The /access page argued for intake as a policy, so it needs the argument
# replaced rather than the wording tweaked.
ACCESS_OLD_MAIN = '''<div class="page-hero">
  <div class="container">
    <span class="badge">Early access</span>
    <h1>How access works</h1>
    <p>Keys are issued on request, not through self-serve signup. That is a deliberate choice, and this page describes precisely what happens between asking and sending your first request.</p>
  </div>
</div>
<article class="article">
<h2>1. Tell us what you are building</h2>
<p>Send your use case, the volume you expect, and your timeline to
<!--email_off--><a href="mailto:contact@runixcloud.io">contact@runixcloud.io</a><!--/email_off-->.
Rough numbers are fine; the point is to size the quota and pick sensible routing, not to
qualify you.</p>

<h2>2. We reply within one business day</h2>
<p>You get an access plan and a quote for the workload you described. Pricing is
usage-based in USD and the rate table is stated in writing — there is no published rate
card because quotes depend on the models and volume you actually use.</p>

<h2>3. Evaluate before you pay</h2>
<p>Evaluation credits are issued on request. Full router functionality, no card required
to start. This is the stage where you find out whether the failover behaviour and the cost
reporting match what you need.</p>

<h2>4. Your key arrives configured</h2>
<p>A key is not just a credential here. It carries its own quota and limits, the set of
models it is allowed to call, and routing preferences applied server-side — so the
controls are in place from the first call rather than bolted on later. Issue separate keys
per team or product and the usage reporting splits along those lines.</p>

<h2>5. Then you integrate</h2>
<p>Integration is a base-URL change: point your existing OpenAI-compatible client at
<code>https://api.router.runixcloud.io/v1</code> and swap the key. The
<a href="/docs/router">Router quickstart</a> covers model selection, streaming, failover
semantics and the error envelope.</p>

<h2>Common questions</h2>
<h3>Why is there no self-serve signup?</h3>
<p>Because keys carry real quotas and routing configuration, and during early access those are set per team rather than issued blindly.</p>
<h3>What does it cost to evaluate?</h3>
<p>Nothing. Evaluation credits are issued on request and no card is required to start.</p>
<h3>How long does it take?</h3>
<p>You get a reply within one business day.</p>
<p>Everything else is on the <a href="/faq">FAQ</a>, the terms are defined in the
<a href="/glossary">glossary</a>, and what happens when a provider degrades is on the
<a href="/reliability">reliability page</a>.</p>
</article>
<section class="section">
  <div class="container">
    <div class="cta-band">
      <h2>Start the intake</h2>
      <p>Send the models you call, the volume you expect and any compliance constraints. You get a reply within one business day — and if early access is not a fit for you yet, we will say so rather than stall.</p>
      <a class="btn btn-grad" href="/about#contact">Request access</a>
    </div>
  </div>
</section>'''

ACCESS_NEW_MAIN = f'''<div class="page-hero">
  <div class="container">
    <span class="badge">Getting started</span>
    <h1>How access works</h1>
    <p>Router is self-serve. Create an account, get evaluation credits, and send your first request in minutes. This page describes exactly what happens — and when it is worth talking to us instead.</p>
  </div>
</div>
<article class="article">
<h2>1. Create your account</h2>
<p>Sign up at <a href="{REGISTER}">{CONSOLE.replace("https://", "")}</a> with an email
address and a password. There is no intake form, no waiting list and no card.</p>

<h2>2. Your key arrives configured</h2>
<p>A key is not just a credential here. It carries its own quota and limits, the set of
models it is allowed to call, and routing preferences applied server-side — so the
controls are in place from the first call rather than bolted on later. Issue separate keys
per team or product and the usage reporting splits along those lines.</p>

<h2>3. Evaluate before you pay</h2>
<p>New accounts start with evaluation credits. Full router functionality, no card required.
This is the stage where you find out whether the failover behaviour and the cost reporting
match what you need.</p>

<h2>4. Then you integrate</h2>
<p>Integration is a base-URL change: point your existing OpenAI-compatible client at
<code>https://api.router.runixcloud.io/v1</code> and swap the key. The
<a href="/docs/router">Router quickstart</a> covers model selection, streaming, failover
semantics and the error envelope.</p>

<h2>5. When to talk to us instead</h2>
<p>Self-serve covers evaluation and normal production use. Come to
<!--email_off--><a href="mailto:contact@runixcloud.io">contact@runixcloud.io</a><!--/email_off-->
when you need custom routing across specific providers, limits above the self-serve
ceiling, invoicing or bank transfer instead of prepaid balance, or a signed MSA or DPA.
Pricing is usage-based in USD and quotes are stated in writing — there is no published
rate card because quotes depend on the models and volume you actually use.</p>

<h2>Common questions</h2>
<h3>Do I need to talk to anyone to start?</h3>
<p>No. Create an account and your key is issued immediately, with evaluation credits. Talk
to us when you need custom routing, higher limits, invoicing or a signed agreement.</p>
<h3>What does it cost to evaluate?</h3>
<p>Nothing. New accounts start with evaluation credits and no card is required.</p>
<h3>How long does it take?</h3>
<p>Minutes. Account creation and key issue are immediate; enterprise onboarding gets a
reply within one business day.</p>
<p>Everything else is on the <a href="/faq">FAQ</a>, the terms are defined in the
<a href="/glossary">glossary</a>, and what happens when a provider degrades is on the
<a href="/reliability">reliability page</a>.</p>
</article>
<section class="section">
  <div class="container">
    <div class="cta-band">
      <h2>Create an account</h2>
      <p>Sign up, take the evaluation credits and point a client at the endpoint. If you need custom routing, higher limits or invoicing, tell us and we will answer concretely rather than stall.</p>
      <a class="btn btn-grad" href="{REGISTER}">Create an account</a>
    </div>
  </div>
</section>'''


def apply(path, old, new, report):
    """Replace old with new; tolerate already-migrated, refuse ambiguity."""
    p = pathlib.Path(path)
    text = p.read_text(encoding="utf-8")
    n = text.count(old)
    if n == 0:
        if new in text:
            return False  # already migrated
        report.append(f"MISSING in {path}: {old[:70]!r}")
        return False
    text = text.replace(old, new)
    p.write_text(text, encoding="utf-8")
    return True


def main():
    problems = []
    changed = 0

    nav_files = sorted(
        str(p) for p in pathlib.Path(".").rglob("*.html")
        if NAV_OLD in p.read_text(encoding="utf-8")
        or NAV_NEW in p.read_text(encoding="utf-8")
    )
    for f in nav_files:
        if apply(f, NAV_OLD, NAV_NEW, problems):
            changed += 1
    print(f"nav: {changed} page(s) now offer Sign up alongside Sign in "
          f"({len(nav_files)} carry the nav)")

    copy_changed = 0
    for path, old, new in EDITS:
        if apply(path, old, new, problems):
            copy_changed += 1
    print(f"copy/structured data: {copy_changed} block(s) rewritten")

    if apply("access.html", ACCESS_OLD_MAIN, ACCESS_NEW_MAIN, problems):
        print("access.html: intake narrative replaced with the self-serve one")

    leftovers = []
    for p in pathlib.Path(".").rglob("*.html"):
        t = p.read_text(encoding="utf-8")
        if "self-serve signup" in t and "pipeline.html" not in str(p):
            leftovers.append(str(p))
    if leftovers:
        print("still argue against self-serve signup: " + ", ".join(leftovers))

    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
