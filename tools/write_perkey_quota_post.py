#!/usr/bin/env python3
"""Write the per-key quota post into scheduled/.

Nothing on the site covers the tenancy side of spend: llm-cost-control is about
token mechanics, llm-cost-attribution is about reporting after the fact, and
llm-rate-limits is about the provider throttling you. None of them answers the
question a team hits the first time they put more than one consumer behind one
pool -- what stops one of them taking all of it.

The argument that is not already written up elsewhere is the alerting one:
remaining balance is not a threshold, because the same number is comfortable in
a quiet week and an emergency in a busy one. Runway is the threshold, and the
rate it divides by has to react faster than a multi-day average.

Operational, from running a gateway. No customer data, no invented figures.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "per-key-llm-quotas"
TITLE = "Per-Key LLM Quotas: When One Client Drains the Pool | Runix"
H1 = "One key can drain a shared quota pool"
DESC = ("A shared quota pool with no per-key ceiling is first-come-first-served — one "
        "client's batch job empties it. Why runway beats balance as an alert threshold.")

BODY = """<p>The first time you put more than one consumer behind one set of provider
credentials, you have made a tenancy decision whether or not you noticed. A pool of prepaid
capacity with no per-key ceiling is first-come-first-served: whoever sends the most requests
gets the most capacity, and the question of who runs out is settled by traffic rather than by
you. That is fine right up until one consumer starts a backfill.</p>

<h2>Rate limits do not solve this</h2>

<p>The reflex is to point at the rate limiter, but a rate limit and a quota control different
things and you need both. A rate limit is about <em>instantaneous</em> load — requests per
minute, concurrent connections — and it protects your infrastructure from a spike. A quota is
about <em>cumulative</em> consumption over a billing period, and it protects your budget from
a marathon.</p>

<p>A client sitting politely under a 600-requests-per-minute limit, all day, every day, will
consume more capacity than a client that briefly bursts past it and gets throttled. The
limiter will report a clean week. The pool will still be empty.</p>

<h2>Failed requests spend too</h2>

<p>The arithmetic gets worse once errors enter it. An upstream failure that arrives after the
provider has already processed the prompt is billed, and the client retries — so the
consumer generating the most errors is often also the one generating the most spend per unit
of useful work. We have watched a single key account for the large majority of a day's
failures and a disproportionate share of its consumption at the same time, which is exactly
what retry amplification looks like from the billing side rather than the latency side.</p>

<p>If your metering counts only successful responses, this traffic is invisible in your own
dashboards while remaining perfectly visible on the invoice. Count attempts, not answers.
The gap between them is the number worth alerting on — see
<a href="/blog/llm-retry-budget">retry budgets</a> for the client-side half of the same
problem.</p>

<h2>Hard stop or overage — pick deliberately</h2>

<p>Prepaid pools fail in one of two ways when they empty, and the choice matters more than it
looks:</p>

<ul>
<li><strong>Hard stop.</strong> Consumption ends at the limit and no bill is generated. Your
    costs are bounded, which is the point — but every consumer sharing that pool stops at the
    same instant, including the internal ones you forgot were on it. The team that discovers
    this at 2am is usually discovering that their own tooling shared a pool with a
    customer.</li>
<li><strong>Overage.</strong> Service continues and the excess is billed. Nothing breaks,
    which is also the problem: a runaway loop has no ceiling except the one your finance team
    finds at the end of the month.</li>
</ul>

<p>Neither is wrong. What is wrong is not knowing which one you have configured, because the
two demand opposite monitoring: hard stop needs a <em>runway</em> alarm, overage needs a
<em>rate</em> alarm.</p>

<h2>Alert on runway, not on balance</h2>

<p>The most common quota alert is a percentage of the balance — tell me when the pool drops
below twenty percent. It is the wrong threshold, because the same balance means completely
different things at different consumption rates. Five thousand credits with a week to go is
comfortable if you are spending three hundred a day and an emergency if you are spending
three thousand.</p>

<p>The number that carries meaning is runway: remaining capacity divided by the current
consumption rate, expressed in days, compared against the days left before the quota resets.
When runway is shorter than the time to reset, you have a problem regardless of how healthy
the percentage looks. That single comparison replaces a table of per-tier thresholds nobody
maintains.</p>

<p>The subtlety is which rate to divide by. A multi-day average is stable but slow — a burst
that started an hour ago will not move a three-day mean until it has already done the damage.
An instantaneous rate is the opposite: it panics at every quiet hour and every busy one. Take
the faster of the two — the recent daily average and the last hour extrapolated forward — and
divide by that. It stays calm during normal variation and reacts within an hour to a step
change, which is the behaviour you actually want from something that pages you.</p>

<h2>Reserve before you allocate</h2>

<p>If any of the traffic on a shared pool is <em>yours</em> — internal tooling, evaluation
jobs, the assistant your own engineers use — that traffic deserves a floor rather than a fair
share. It is the traffic you notice last, because it fails quietly and nobody files a ticket
about it, and it is the traffic whose absence stops you from diagnosing the incident that
caused it.</p>

<p>A workable allocation looks like: a reserved floor for internal use, a per-key ceiling for
every external consumer that sums to less than the remaining pool, and the difference left
unallocated as headroom. The ceilings are not there to be hit in normal operation; they are
there so that one consumer's mistake is bounded by their own allocation rather than by the
pool.</p>

<h2>What to check on your own setup</h2>

<ul>
<li>Does any single key have an enforced ceiling, or does the pool limit apply only in
    aggregate?</li>
<li>Does your metering count failed attempts, or only successful responses?</li>
<li>Is your alert threshold a balance percentage or a runway in days?</li>
<li>When the pool empties, does it stop or does it bill — and does the answer match what
    you told your finance team?</li>
<li>Is any internal traffic sharing the pool with external consumers, and would you notice
    if it stopped?</li>
</ul>

<p>None of this requires a large system to get right; it requires the allocation to be
written down somewhere other than in the shape of last month's traffic. Runix Router enforces
per-key limits and itemizes usage per key, so the ceiling and the ledger come from the same
place — <a href="/router">how the router handles keys and limits</a>, and
<a href="/pricing">how the metering is priced</a>.</p>
"""

template = pathlib.Path("blog/did-the-model-change-make-it-worse.html").read_text()
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
# [^>]* — the aside carries aria-labelledby, and the pattern without it silently
# left the template's own related block on the new post. add_related.py rebuilds
# the block from its own map afterwards, which is what hid this.
page = re.sub(r'<aside class="related"[^>]*>.*?</aside>\s*', "", page, flags=re.S)

out = pathlib.Path("scheduled") / f"{SLUG}.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print(f"  wrote {out} — {words} words, {minutes} min read")
