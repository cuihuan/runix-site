#!/usr/bin/env python3
"""Give the pages that earn a qualified reader somewhere to go.

Profiling every page turned up a clean split: product and pricing pages all end
in a cta-band, and every article-template page ends mid-sentence and drops
straight into the footer. For the legal pages that is correct — they are
reference documents and a call to action would be out of place.

Three were not correct:

  * /access is the page about how to get access and did not ask anyone to.
  * /careers ends its role list and stops, with no instruction to apply.
  * /reliability tells the reader to "say so during intake" without linking to
    the intake.

Each band below says something specific to its page. A generic "Request
access" stamped on every page is how a CTA stops being read.

Idempotent. Run from the site root.
"""
import os
import pathlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def band(heading, body, label, href):
    return f"""<section class="section">
  <div class="container">
    <div class="cta-band">
      <h2>{heading}</h2>
      <p>{body}</p>
      <a class="btn btn-grad" href="{href}">{label}</a>
    </div>
  </div>
</section>
"""


BANDS = {
    "access.html": band(
        "Start the intake",
        "Send the models you call, the volume you expect and any compliance constraints. "
        "You get a reply within one business day — and if early access is not a fit for you "
        "yet, we will say so rather than stall.",
        "Request access", "/about#contact"),
    "careers.html": band(
        "None of these quite you?",
        "We would still rather hear from you than not. Tell us what you have built and what "
        "you want to work on — a short note about real work beats a formatted CV here.",
        "Write to us", "mailto:contact@runixcloud.io?subject=Runix%20-%20introduction"),
    "reliability.html": band(
        "Reliability requirements to check against",
        "If availability guarantees are part of your procurement, bring them to the intake. "
        "We will tell you plainly whether early access fits, before you spend time on an "
        "evaluation.",
        "Talk to us about it", "/about#contact"),
}

changed = []
for path, markup in BANDS.items():
    p = pathlib.Path(path)
    html = p.read_text()
    if "cta-band" in html:
        continue
    # Article pages close </article></main>; card pages close the last section.
    if "</article>\n</main>" in html:
        html = html.replace("</article>\n</main>", "</article>\n" + markup + "</main>", 1)
    elif "</main>" in html:
        html = html.replace("</main>", markup + "</main>", 1)
    else:
        print(f"  ! {path}: no </main> to anchor to")
        continue
    p.write_text(html)
    changed.append(path)

print(f"  added a closing band to {len(changed)} page(s): {', '.join(changed) or 'none'}")

# Legal pages deliberately have none; assert that stays true so a later sweep
# does not stamp a CTA onto the Terms.
for legal in ("terms.html", "privacy.html", "refund.html", "cancellation.html",
              "acceptable-use.html"):
    if "cta-band" in pathlib.Path(legal).read_text():
        raise SystemExit(f"  {legal} has a CTA band — legal pages should not")
print("  legal pages still have none, as intended")
