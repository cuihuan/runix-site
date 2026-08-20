#!/usr/bin/env python3
"""Harden the privacy policy and terms for payment-processor review (Stripe).

Stripe's review reads the privacy policy itself, not the footer. What it looks
for and what was missing here:

  * the full legal identity of the data controller inside the policy
    (the contact section said only "Runix — Wyoming, United States"),
  * a cookie section that names the actual cookies, their class, and how to
    opt out of analytics specifically,
  * the payment processor named, with a pointer to its own privacy policy and
    a clear statement that card data never touches Runix,
  * the transfer mechanism named for international transfers,
  * a complaint/appeal route in the rights section.

Nothing here invents facts: the entity details are the registered ones already
in the site footer, the cookies listed are the ones the site actually sets
(session/preferences plus Google Analytics via gtag.js), and Stripe is named
because Stripe is the processor being onboarded.

Idempotent — re-running finds the new text in place and does nothing.
"""
import os
import pathlib
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

EDITS = [
    # -------------------------------------------------------------- privacy
    ("privacy.html",
     "Effective date: July 22, 2026&nbsp;&nbsp;|&nbsp;&nbsp;Last updated: July 22, 2026&nbsp;&nbsp;|&nbsp;&nbsp;Version 1.0",
     "Effective date: July 22, 2026&nbsp;&nbsp;|&nbsp;&nbsp;Last updated: August 20, 2026&nbsp;&nbsp;|&nbsp;&nbsp;Version 1.1"),

    # Controller identity up front, where a reviewer looks first.
    ("privacy.html",
     'This Privacy Policy explains how Runix AI Inc ("Runix", "we", "us") handles information '
     'in connection with our websites, APIs, and services (the "Services"). By using the Services, '
     "you agree to the practices described here. If you do not agree, please do not use the Services.</p>",
     'This Privacy Policy explains how Runix AI Inc ("Runix", "we", "us") handles information '
     'in connection with our websites, APIs, and services (the "Services"). Runix AI Inc, a company '
     "incorporated in Wyoming, United States (company number 2026-002036618) with its registered "
     "office at 30 N Gould St Ste R, Sheridan, WY 82801, United States, is the data controller "
     "for the personal information described in this Policy. By using the Services, "
     "you agree to the practices described here. If you do not agree, please do not use the Services.</p>"),

    # Name the processor in the billing bullet.
    ("privacy.html",
     "Payments are processed by licensed third-party payment processors; we do not collect or "
     "store your full card number or payment credentials.</li>",
     "Payments are processed by licensed third-party payment processors — including Stripe, Inc. "
     '(see the <a href="https://stripe.com/privacy" target="_blank" rel="noopener">Stripe Privacy '
     "Policy</a>) — which collect your card details directly on their own PCI&#8209;DSS&#8211;compliant pages. "
     "Runix never collects, sees, or stores your full card number or payment credentials; we receive "
     "only a payment confirmation, the transaction amount, and a reference token.</li>"),

    # Cookie section: from one paragraph to a concrete, reviewable inventory.
    ("privacy.html",
     "<p>We use cookies and similar technologies to keep the website functioning, remember "
     "preferences, maintain sessions, and understand aggregate usage so we can improve the "
     "Services. We use Google Analytics to measure aggregate site traffic; the data we receive "
     "from it is not tied to a named account. You can manage or delete cookies in your browser "
     "settings; some features may not work without them. We do not use cookies for third-party "
     "advertising.</p>",
     "<p>We use cookies and similar technologies in two categories, and no others:</p>\n"
     "  <ul>\n"
     "    <li><strong>Strictly necessary cookies</strong> — first-party cookies that keep the site and the\n"
     "        console functioning: session state, sign-in, and security (for example CSRF protection).\n"
     "        These cannot be switched off without breaking the service.</li>\n"
     "    <li><strong>Analytics cookies</strong> — we use Google Analytics 4 (Google LLC), which sets\n"
     "        first-party cookies such as <code>_ga</code> and <code>_ga_*</code> to measure aggregate site\n"
     "        traffic (pages visited, approximate region, browser type). We have not enabled advertising\n"
     "        features, we do not use this data to identify you, and the data we receive is not tied to a\n"
     "        named account. Google&#8217;s own practices are described in the\n"
     '        <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Google Privacy Policy</a>.</li>\n'
     "  </ul>\n"
     "  <p><strong>Your choices.</strong> You can manage or delete cookies in your browser settings (some\n"
     "  features may not work without the strictly necessary ones), block analytics cookies with any\n"
     "  content blocker, or install Google&#8217;s\n"
     '  <a href="https://tools.google.com/dlpage/gaoptout" target="_blank" rel="noopener">Analytics opt-out\n'
     "  browser add-on</a>. Where your jurisdiction requires consent for analytics cookies, we honour the\n"
     "  choice you make in your browser and any consent signal it sends. We do not use cookies for\n"
     "  third-party advertising, we do not run third-party ad networks on our sites, and we do not sell\n"
     "  information collected through cookies.</p>\n"
     "  <p>Payment pages are hosted by our payment processors on their own domains; any cookies set\n"
     "  there are governed by the processor&#8217;s policy (see Section 1.1).</p>"),

    # Transfers: name the mechanism.
    ("privacy.html",
     "<p>We are based in the United States and may process information on servers located in the "
     "United States or other jurisdictions. Where required, we use appropriate safeguards for "
     "cross-border transfers of personal information.</p>",
     "<p>We are based in the United States and may process information on servers located in the "
     "United States or other jurisdictions. Where personal information originating in the EEA, the "
     "United Kingdom, or Switzerland is transferred to a country without an adequacy decision, we "
     "rely on appropriate safeguards such as the European Commission&#8217;s Standard Contractual "
     "Clauses (and the UK equivalent), together with the technical measures described in "
     "Section&nbsp;4.</p>"),

    # Contact: full legal identity, matching the footer and the terms.
    ("privacy.html",
     '<li>Email: <!--email_off--><a href="mailto:contact@runixcloud.io">contact@runixcloud.io</a><!--/email_off--> (please include "Privacy" in the subject line)</li>\n'
     "    <li>Runix — Wyoming, United States</li>",
     '<li>Email: <!--email_off--><a href="mailto:contact@runixcloud.io">contact@runixcloud.io</a><!--/email_off--> (please include "Privacy" in the subject line)</li>\n'
     "    <li>Runix AI Inc &middot; company number 2026-002036618 (Wyoming, United States)</li>\n"
     "    <li>Registered office: 30 N Gould St Ste R, Sheridan, WY 82801, United States</li>\n"
     '    <li>Phone: <a href="tel:+13086890770">+1 (308) 689-0770</a></li>'),

    # Rights: add the complaint route reviewers look for.
    ("privacy.html",
     "We may verify your identity before acting on a request, and we respond within the "
     "timeframe required by applicable law (generally within 30 days).",
     "We may verify your identity before acting on a request, and we respond within the "
     "timeframe required by applicable law (generally within 30 days). If you are not "
     "satisfied with our response, you may lodge a complaint with the data-protection "
     "supervisory authority in your jurisdiction."),

    # ---------------------------------------------------------------- terms
    ("terms.html",
     "Effective date: July 22, 2026&nbsp;&nbsp;|&nbsp;&nbsp;Last updated: July 22, 2026&nbsp;&nbsp;|&nbsp;&nbsp;Version 1.0",
     "Effective date: July 22, 2026&nbsp;&nbsp;|&nbsp;&nbsp;Last updated: August 20, 2026&nbsp;&nbsp;|&nbsp;&nbsp;Version 1.1"),
]

problems = []
changed = 0
for path, old, new in EDITS:
    p = pathlib.Path(path)
    t = p.read_text(encoding="utf-8")
    if new in t:
        continue
    if t.count(old) != 1:
        problems.append(f"{path}: block not found exactly once ({t.count(old)}x)")
        continue
    p.write_text(t.replace(old, new), encoding="utf-8")
    changed += 1
print(f"legal pages: {changed} block(s) updated")
for pr in problems:
    print("  MISMATCH " + pr)
sys.exit(1 if problems else 0)
