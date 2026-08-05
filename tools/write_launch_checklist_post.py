#!/usr/bin/env python3
"""Write the pre-launch checklist post into scheduled/.

A hub piece: the operational decisions that have to be made before an LLM
feature carries real traffic, each one linking to the post that covers it in
depth. Useful on its own and it gives the other twenty-three somewhere to be
found from.

Nothing here is a Runix capability claim and no figure appears.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "llm-feature-pre-launch-checklist"
TITLE = "Pre-launch checklist for an LLM feature — Runix"
H1 = "What to settle before an LLM feature carries real traffic"
DESC = ("Twelve decisions that are cheap before launch and expensive after: cost ceilings, "
        "timeouts, failover, what you log, and how you roll back.")

BODY = """<p>The demo works. Someone has asked when it ships. This is the point at which a list
is more useful than an opinion, because every item below is cheap to decide now and expensive
to retrofit once traffic is on it.</p>

<p>Twelve things, grouped by the conversation each one belongs to. If an item makes you say
"we should check that", that is the item.</p>

<h2>Money</h2>

<p><strong>1. A ceiling that stops spending, not one that emails you.</strong> Budget alerts
tell you after the money is gone. What you want is a limit that refuses requests — per key,
per team, or per feature — and you want to have seen it trigger at least once in staging.
Which means deliberately blowing a small budget before launch rather than hoping.</p>

<p><strong>2. Attribution decided before, not reconstructed after.</strong> If you cannot
answer "what did this feature cost last month" without a spreadsheet, the boundary was not in
the credential. Issue a separate key per boundary you will be asked about —
<a href="/blog/llm-cost-attribution">the reasoning is here</a> — because retrofitting
attribution means reconstructing it from logs and arguing about the result.</p>

<p><strong>3. Know what a retry costs.</strong> Every retry is a second full-price request.
A retry policy set without a budget can multiply spend during exactly the incident when
nobody is watching the bill.</p>

<h2>Failure</h2>

<p><strong>4. A timeout chain, written on one line.</strong> Four numbers — connect, first
byte, inter-token, total — that decrease as you move inward from the user.
<a href="/blog/how-long-should-an-llm-request-wait">Ordered the other way</a>, your outer
layer gives up while the inner one is still generating and you pay for output nobody
received.</p>

<p><strong>5. A failover target and a retry budget.</strong> Not "retry three times" — a cap
on what share of your traffic may be retries, so a provider's bad hour cannot become a
self-inflicted load spike. <a href="/blog/model-failover">The failure taxonomy is here</a>.</p>

<p><strong>6. A decision about streaming failure.</strong> If you stream, work out now what
happens when a stream dies at token 200. Restart? Show partial? Fail? Whatever it is, decide
it before it happens — <a href="/blog/streaming-llm-failover">the edge cases are worse than
they look</a>.</p>

<p><strong>7. A degraded mode that is not an error page.</strong> A smaller model, a cached
answer, a form. Something that keeps the feature usable when the ideal path is unavailable.</p>

<h2>Change</h2>

<p><strong>8. The model id out of your application code.</strong> Providers retire model
versions on their own schedule — <a href="/blog/model-deprecation-without-a-redeploy">two
months' notice is normal</a> — so the id will change on a date you did not choose. If it lives
in configuration, that is a config change; if it lives in a binary, it is a release under time
pressure.</p>

<p><strong>9. Baselines recorded before you need them.</strong> Parse rate on structured
routes, output length distribution, refusal rate. <a href="/blog/did-the-model-change-make-it-worse">
Without a before, you cannot tell whether a model change hurt</a> — and you cannot collect a
before retroactively.</p>

<p><strong>10. A rollback you have actually run.</strong> Not a documented one. Flip back,
confirm traffic serves, flip forward. A rollback nobody has exercised is a hypothesis.</p>

<h2>Evidence</h2>

<p><strong>11. Logs that answer the question you will be asked.</strong> The question is
always "what happened to this request", so you need a request id you can quote, the model
that served it, the token counts, and the outcome. <a href="/blog/llm-observability">What not
to log matters as much</a>: prompts and completions are the highest-risk data in the system
and the least often the field you needed.</p>

<p><strong>12. A written answer to the data question.</strong> Someone will ask what happens
to the content users send — internally before launch if you are lucky, by a customer's
security team if you are not. <a href="/blog/ai-vendor-data-questions">The questions worth
being ready for</a> are known in advance.</p>

<h2>What this list deliberately leaves out</h2>

<p>Evaluation quality, prompt engineering and model choice are not here. Not because they do
not matter — they are most of the product — but because they are the part teams already spend
their time on. The twelve above are the ones that get discovered in production, and every one
of them is a decision rather than an implementation.</p>

<p>A useful test: pick any three and ask who would make the change and how long it would take.
If the answer involves a deploy, that item is not settled yet.</p>

<p>Several of these land in the same place, which is the argument for a gateway rather than a
library: the spend ceiling, the retry budget, the timeout chain, the model pin and the request
log are one decision each, and either they live in one place or they live in every service
that calls a model. <a href="/router">Runix Router</a> is where ours live. The list is worth
running whatever you decide.</p>
"""

template = pathlib.Path("blog/how-long-should-an-llm-request-wait.html").read_text()
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
              rf"\g<1>Buyer's guide\g<2>PENDING\g<3>{minutes} min read\g<4>", page, count=1)
page = re.sub(r'(<h1 style="margin-top: 14px;">).*?(</h1>)', rf"\g<1>{H1}\g<2>", page, count=1, flags=re.S)

start = page.index('<article class="article">') + len('<article class="article">')
end = page.index("</article>")
page = page[:start] + "\n" + BODY.strip() + "\n" + page[end:]
page = re.sub(r'<aside class="related">.*?</aside>\s*', "", page, flags=re.S)

out = pathlib.Path("scheduled") / f"{SLUG}.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print(f"  wrote {out} — {words} words, {minutes} min read")
