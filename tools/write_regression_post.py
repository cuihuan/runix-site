#!/usr/bin/env python3
"""Write the model-regression post into scheduled/.

The natural next question after the deprecation piece: you are being moved off
a model whether you like it or not — how do you know the replacement is not
worse for your workload? Written from operational practice, no vendor named,
no Runix figure.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "did-the-model-change-make-it-worse"
TITLE = "Telling whether a model change made things worse — Runix"
H1 = "How to tell whether a model change made things worse"
DESC = ("Output varies run to run, so a quality regression does not announce itself. "
        "Four signals that move before anyone files a ticket.")

BODY = """<p>A model swap is the one production change where the system keeps returning 200s and
the thing that broke is the part no monitor watches. Latency is fine. Error rate is fine.
The answers are just... worse, in a way nobody can point at for another three weeks, by which
time nobody remembers the change.</p>

<p>This is not a hypothetical problem to plan for. Providers retire model versions on their
own schedule — <a href="/blog/model-deprecation-without-a-redeploy">two months' notice is
normal</a> — so you will be moved off a model that works, on a date somebody else chose. The
question is not whether to change models. It is how you will know if the change hurt.</p>

<h2>Why the obvious approach does not work</h2>

<p>The instinct is to run both models on the same prompts and compare the outputs. That fails
for a specific reason: identical inputs do not produce identical outputs, so a diff of two
responses shows differences on every single request. You end up reading them by hand,
concluding "seems fine", and shipping on a sample of thirty.</p>

<p>Human review is not useless — it is the only thing that catches a subtly wrong tone or a
misread instruction — but it does not scale and it cannot run continuously. It belongs at the
end, on the cases the automated signals flag, not at the start on a random sample.</p>

<h2>Four signals that do not require reading the output</h2>

<p>Each of these is cheap, computable on live traffic, and moves before a human notices
anything.</p>

<p><strong>1. Structured-output parse rate.</strong> If any route asks for JSON, the fraction
of responses that parse is a direct quality measurement with no judgement in it. A model that
is slightly worse at instruction-following shows up here first and unambiguously. If you have
one signal, have this one — and if no route currently asks for structured output, consider
adding a small one that does purely as a canary.</p>

<p><strong>2. Output length distribution, per route.</strong> Not the average — the shape.
A replacement model that is more verbose, more terse, or more prone to truncation moves the
distribution in a way an average hides. Watch particularly for a wall at the top of the
histogram: that is <code>finish_reason: length</code>, and it means answers are being cut off
mid-sentence. Track the share of length-finishes as its own number.</p>

<p><strong>3. Refusal and hedge rate.</strong> Count responses matching a small set of
refusal-shaped and hedge-shaped patterns — "I cannot", "I'm not able to", "As an AI", "it
depends on". You are not trying to judge the content; you are watching a rate that should be
stable. A jump means the new model draws a policy line somewhere the old one did not, which
is the single most common way a model swap breaks a product without breaking anything.</p>

<p><strong>4. Downstream acceptance, if you have it.</strong> The best signal is always the
one from the next step: retry rate, edit rate, thumbs-down, "regenerate" clicks, the share of
generated code that gets committed. If your product has any such action, it is worth more
than the other three combined, because it measures what users did rather than what the
response looked like.</p>

<h2>Establish the baseline before you need it</h2>

<p>All four are only useful against a before. Two weeks of the old model's numbers is worth
more than any amount of pre-launch evaluation, and you cannot collect it retroactively.</p>

<p>The practical consequence: start recording these the day you learn a model is being
retired, not the day you switch. Sixty days' notice is enough time to build a baseline; it is
not enough time to build a baseline after you have already migrated.</p>

<h2>Run both models, but not on the same request</h2>

<p>Rather than shadowing every request through both models — which doubles your spend and
still leaves you diffing non-deterministic text — split traffic. Send a slice to the new
model and compare the four signals between the two populations rather than between two
responses.</p>

<p>This is an A/B test on operational metrics rather than on outputs, and it has three
advantages: it costs a percentage rather than a duplicate, the comparison is statistical
rather than anecdotal, and it keeps running after you have stopped paying attention.</p>

<p>Give it a real sample. Refusal rate and parse rate are proportions, and a proportion
measured over a few hundred requests moves around enough to hide a change worth acting on.
If your volume is low, hold the split for longer rather than reading a small sample early.</p>

<h2>What to do when a signal moves</h2>

<ol>
<li><strong>Confirm it is the model.</strong> Check whether the same signal moved on routes
    that did not change. If it moved everywhere, something else did — a prompt template, a
    context change, a seasonal shift in what users are asking.</li>
<li><strong>Pull the affected requests and read them.</strong> This is where human review
    earns its cost, because you now have twenty specific cases rather than a random
    sample.</li>
<li><strong>Try the prompt before you try another model.</strong> Most regressions after a
    model swap are instruction-following differences that a slightly more explicit prompt
    fixes. Changing models again is a bigger change with its own unknowns.</li>
<li><strong>Keep the option to move.</strong> If the pin lives in configuration rather than in
    code, reverting or trying a third model is a config change and a re-measure. If it lives
    in a binary, every hypothesis costs a deploy — which is the argument for
    <a href="/blog/model-deprecation-without-a-redeploy">keeping the model id out of your
    application</a> in the first place.</li>
</ol>

<h2>The short version</h2>

<p>You will be moved off a working model on someone else's schedule. Output diffs cannot tell
you whether the replacement is worse, because output varies anyway. Parse rate, length
distribution, refusal rate and downstream acceptance can — and they need a baseline that only
exists if you started collecting it before the migration. Split traffic rather than shadowing,
compare populations rather than responses, and keep the model id somewhere you can change
without shipping code.</p>

<p>The observability side of this is covered in
<a href="/blog/llm-observability">what to log for LLM traffic</a>; the mechanics of moving
traffic are in <a href="/blog/migrating-to-an-llm-gateway-without-downtime">migrating without
a maintenance window</a>. If you would rather the routing layer hold the pin,
<a href="/router">that is what Runix Router does</a> — but the four signals are yours to
watch either way, and nobody else can tell you what "worse" means for your product.</p>
"""

template = pathlib.Path("blog/migrating-to-an-llm-gateway-without-downtime.html").read_text()
url = f"{SITE}/blog/{SLUG}"

page = template
page = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", page, count=1)
for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
    page = re.sub(rf'({re.escape(attr)} content=")[^"]*(")', lambda m: m.group(1) + DESC + m.group(2), page, count=1)
for attr in ('property="og:title"', 'name="twitter:title"'):
    page = re.sub(rf'({re.escape(attr)} content=")[^"]*(")', lambda m: m.group(1) + TITLE + m.group(2), page, count=1)
page = re.sub(r'(<link rel="canonical" href=")[^"]*(">)', rf"\g<1>{url}\g<2>", page, count=1)
page = re.sub(r'(<meta property="og:url" content=")[^"]*(">)', rf"\g<1>{url}\g<2>", page, count=1)


def _fix(block):
    d = json.loads(block)
    if d.get("@type") == "Article":
        d["headline"], d["description"], d["url"] = H1, DESC, url
        if isinstance(d.get("mainEntityOfPage"), dict):
            d["mainEntityOfPage"]["@id"] = url
    elif d.get("@type") == "BreadcrumbList":
        leaf = max(d["itemListElement"], key=lambda i: i["position"])
        leaf["name"], leaf["item"] = H1, url
    return json.dumps(d, ensure_ascii=False, indent=2)


page = re.sub(r'(<script type="application/ld\+json">\n)(.*?)(\n</script>)',
              lambda m: m.group(1) + _fix(m.group(2)) + m.group(3), page, flags=re.S)

words = len(re.sub(r"<[^>]+>", " ", BODY).split())
minutes = max(1, round(words / 200))
page = re.sub(r'(<div class="post-meta"><span class="cat">)[^<]*(</span><span>)[^<]*(</span><span>·</span><span>)[^<]*(</span></div>)',
              rf"\g<1>Engineering\g<2>PENDING\g<3>{minutes} min read\g<4>", page, count=1)
page = re.sub(r'(<h1 style="margin-top: 14px;">).*?(</h1>)', rf"\g<1>{H1}\g<2>", page, count=1, flags=re.S)

start = page.index('<article class="article">') + len('<article class="article">')
end = page.index("</article>")
page = page[:start] + "\n" + BODY.strip() + "\n" + page[end:]
page = re.sub(r'<aside class="related">.*?</aside>\s*', "", page, flags=re.S)

out = pathlib.Path("scheduled") / f"{SLUG}.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print(f"  wrote {out} — {words} words, {minutes} min read")
