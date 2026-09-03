#!/usr/bin/env python3
"""Give /about enough substance to answer the question it exists to answer.

Measured before writing this: /about carried 191 words of body copy, against
351 on /security, 669 on /careers, 771 on /pricing and 852 on /router. It is
the thinnest page on the site, and it is the one a buyer opens to decide
whether the company on the other end of the contract is real.

Two things are added, both assembled from statements the site already makes
elsewhere rather than invented here:

  * "What Runix is" — the entity, and the four products with their literal
    statuses, worded identically to /llms.txt and the product pages.
  * "What we do not claim" — certifications, SLA, customer names. The site
    already takes this position on /security, /reliability and /faq; /about is
    where a buyer looks for it, and stating it plainly is worth more than
    another paragraph of belief.

One existing line is tightened. "We design for failure and measure ourselves
on uptime" implies a number the site deliberately does not publish —
/reliability says so in as many words. It now says what is actually true.

Idempotent. Run from the site root.
"""
import os
import pathlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

WHAT_IT_IS = """<section class="section">
  <div class="container">
    <div class="section-head"><h2>What Runix is</h2>
      <p>The entity you would contract with, and what it actually operates today.</p></div>
    <div class="feature">
      <div>
        <p>Runix AI Inc is a company incorporated in Wyoming, United States. It builds and
        operates infrastructure for teams putting AI into production, and sells it directly —
        there is no reseller between you and the people who run the service.</p>
        <p style="margin-top: 12px;">Four products, at deliberately different stages. The
        statuses below are literal, and they are the same statuses used everywhere else on
        this site; none of them is aspirational.</p>
        <ul class="status-list">
          <li><strong>Runix Router</strong> — <em>early access, running traffic today.</em>
            One OpenAI-compatible endpoint across many providers, with central key custody,
            per-key quotas, request-level audit and failover between providers.
            <a href="/router">What Router does</a>.</li>
          <li><strong>Runix Pipeline</strong> — <em>in development with design partners.</em>
            Managed data preparation: ingestion, deduplication, schema-validated extraction,
            PII masking that fails closed. <a href="/pipeline">The five Pipeline stages</a>.</li>
          <li><strong>Runix Code</strong> — <em>in development, waitlist open.</em> An AI
            coding agent for teams. Not generally available. <a href="/code">Code and its waitlist</a>.</li>
          <li><strong>Runix Comic</strong> — <em>in development, waitlist open.</em> An
            end-to-end studio for comic dramas. Not generally available.
            <a href="/comic">Comic and its waitlist</a>.</li>
        </ul>
      </div>
      <div class="facts">
        <div class="facts-head">Company facts</div>
        <div class="frow"><span class="k">Legal entity</span><span class="v">Runix AI Inc<small>Wyoming, United States</small></span></div>
        <div class="frow"><span class="k">Contracting</span><span class="v">MSA &amp; DPA on request<small>Reviewed per engagement; an order form overrides the standard Terms</small></span></div>
        <div class="frow"><span class="k">Billing</span><span class="v">USD · usage-based<small>Itemised statements, invoicing available</small></span></div>
        <div class="frow"><span class="k">Data handling</span><span class="v">Content is not used for training<small>Operational metadata is kept to run billing and support</small></span></div>
        <div class="frow"><span class="k">Access</span><span class="v">Keys issued after intake<small>No self-serve signup during early access</small></span></div>
        <div class="frow"><span class="k">Support</span><span class="v">Within 1 business day<small>Replies come from the engineers who run the service</small></span></div>
      </div>
    </div>
  </div>
</section>

"""

NOT_CLAIMED = """<section class="section alt">
  <div class="container">
    <div class="section-head center">
      <h2>What we do not claim</h2>
      <p>A short list, kept deliberately. Every item on it is something we could quietly imply and have chosen not to.</p>
    </div>
    <div class="pillars">
      <div class="pillar">
        <span class="k">Certifications</span>
        <h3>No badges we have not earned</h3>
        <p class="lead-line">Runix does not hold, and does not assert, SOC&nbsp;2, ISO&nbsp;27001 or PCI status.</p>
        <p style="margin-top:10px;">If your procurement process requires one of these, say so early
        and we will tell you plainly where we stand rather than pointing at a roadmap.
        <a href="/security">What we do document</a>.</p>
      </div>
      <div class="pillar">
        <span class="k">Availability</span>
        <h3>No SLA during early access</h3>
        <p class="lead-line">No uptime percentage, no availability chart, no historical graph.</p>
        <p style="margin-top:10px;">Publishing a number means standing behind it, and the honest
        version of that commitment comes with a contract, not a marketing page.
        <a href="/reliability">How failover actually works</a>.</p>
      </div>
      <div class="pillar">
        <span class="k">Customers</span>
        <h3>No logos, no invented case studies</h3>
        <p class="lead-line">You will not find a customer wall or a case study on this site.</p>
        <p style="margin-top:10px;">References will appear here when there are customers we are
        permitted to name. Until then the space stays empty rather than being filled — we would
        rather show you the mechanism and let you test it. <a href="/access">How access works</a>.</p>
      </div>
    </div>
  </div>
</section>

"""

page = pathlib.Path("about.html")
html = page.read_text()

# The uptime line promises a measurement the site deliberately does not publish.
loose = ("<li><strong>Reliability is a feature.</strong> We design for failure and measure "
         "ourselves on uptime.</li>")
tight = ("<li><strong>Reliability is a feature.</strong> We design for failure first and "
         "publish no availability number we have not yet earned.</li>")
if loose in html:
    html = html.replace(loose, tight)
    print("  tightened the uptime claim to match /reliability")

if "What Runix is" in html:
    print("  /about already expanded")
else:
    anchor = '<section class="section">\n  <div class="container">\n    <div class="section-head"><h2>How we work</h2></div>'
    assert anchor in html, "could not find the 'How we work' section"
    html = html.replace(anchor, WHAT_IT_IS + anchor, 1)

    cta = '<section class="section" style="padding-top: 0;">\n  <div class="container">\n    <div class="cta-band">'
    assert cta in html, "could not find the closing CTA band"
    html = html.replace(cta, NOT_CLAIMED + cta, 1)
    print("  added 'What Runix is' and 'What we do not claim'")

page.write_text(html)

import re
body = html[html.index("<main"):html.index("</main>")]
print(f"  /about body is now {len(re.sub(r'<[^>]+>', ' ', body).split())} words")
