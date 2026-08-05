#!/usr/bin/env python3
"""Write the data-flow post into scheduled/.

Fills the thinnest category on the blog (Compliance, one post) with the
question an enterprise security review actually opens with: where does the
text go. Written as a method for tracing it in any integration — no claim
about Runix's own infrastructure that is not already on /security, and no
figure.

Deliberately NOT written: the piece about how to read provider resale terms,
which the research tonight would support well. Publishing it while our own
resale authorisation is unresolved invites a question we cannot yet answer —
see SUPPLY-COMPLIANCE.md.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "where-your-prompts-actually-go"
TITLE = "Tracing where your prompts go — Runix"
H1 = "Where your prompts actually go"
DESC = ("Every security review opens with this and most teams cannot answer it. How to trace "
        "the path text takes through an LLM integration, hop by hop.")

BODY = """<p>The first question in an enterprise security review is some version of "where does
our text go". It sounds simple. Most teams answer it with the name of one provider, and most
of those answers are incomplete — not because anyone is hiding anything, but because nobody
traced the path.</p>

<p>This is how to trace it, and what each hop obliges you to be able to say.</p>

<h2>The hops, in order</h2>

<p>For a typical integration the text crosses more boundaries than the architecture diagram
suggests:</p>

<ol>
<li><strong>Your application.</strong> Where the prompt is assembled — and where it may be
    logged before anything else sees it.</li>
<li><strong>Your logs and error tracking.</strong> The hop teams forget. An exception handler
    that serialises the request body has just copied a prompt into whatever SaaS receives your
    stack traces.</li>
<li><strong>Your gateway or proxy, if any.</strong> Its own logs, its own retention, its own
    region.</li>
<li><strong>The model provider.</strong> Named in the answer everyone gives.</li>
<li><strong>The provider's own sub-processors.</strong> The hop nobody asks about, and the one
    an auditor will.</li>
<li><strong>Anything reading the response on the way back.</strong> Evaluation harnesses,
    moderation services, analytics that capture output text.</li>
</ol>

<p>A complete answer names every hop, says what is retained at each, and says for how long.
If you cannot fill that table today, that is the finding — not the review.</p>

<h2>Trace it, do not diagram it</h2>

<p>Architecture diagrams describe intent. Find the actual path:</p>

<p><strong>Grep for what logs the request.</strong> Any line that logs a request body, an
exception with context, or a "debug" dump of an outgoing call. Include your framework's
defaults — several log request bodies on error without being asked.</p>

<p><strong>Read the SDK's own logging settings.</strong> Provider SDKs frequently have a debug
mode that prints full request and response. If it can be turned on by an environment variable,
assume it has been on somewhere at some point.</p>

<p><strong>Check what your observability vendor captures.</strong> Traces with attributes,
error payloads, session replay. Session replay is the sharpest edge: if a user typed the
prompt into a text field, replay may have recorded the keystrokes, and that store is usually
governed by nobody's data policy in particular.</p>

<p><strong>Ask the provider for its sub-processor list.</strong> It is a published document at
every serious vendor. If asking feels like an unusual request, that is itself information.</p>

<h2>Three answers worth getting in writing</h2>

<p><strong>1. Is content used for training?</strong> Ask specifically about the tier you are
on — the answer often differs between consumer, standard API and enterprise agreements at the
same vendor. Get the sentence, not the marketing page.</p>

<p><strong>2. How long is content retained, and where?</strong> Most providers retain inputs
and outputs for some abuse-monitoring window even when they do not train on them. That window
is the number your auditor wants, and it is rarely on the front page.</p>

<p><strong>3. What is kept when you delete?</strong> Deletion usually means the primary store.
Backups, audit logs and abuse-monitoring copies have their own clocks. "Deleted" and "gone"
are different words.</p>

<h2>The distinction that makes this tractable</h2>

<p>Separate <strong>content</strong> from <strong>operational metadata</strong> and the
conversation gets much easier.</p>

<p>Content is the prompt and the completion — the highest-risk data in the system, needed only
to serve the request. Operational metadata is token counts, latency, model, error code,
request id — needed to bill, to debug, and to notice a provider degrading, and carrying almost
none of the risk.</p>

<p>A system that keeps metadata indefinitely and content not at all is easy to explain and
easy to defend. One that keeps "logs" without distinguishing the two is neither, and that is
the shape most integrations start in. It is also the argument for
<a href="/blog/llm-observability">deciding what to log deliberately</a> rather than logging
whatever the framework does by default.</p>

<h2>What a good answer looks like</h2>

<p>Not "a major provider, and they hold SOC&nbsp;2". Something closer to:</p>

<blockquote><p>Prompts go from our service to one gateway, which forwards to one of three
named providers depending on the model requested. We log token counts, latency, model and a
request id; we do not log prompt or completion content. The gateway retains those metadata
records for N days. Each provider's retention and training terms are in their DPA, which we
hold. Error tracking is configured to strip request bodies, and we verify that quarterly.</p></blockquote>

<p>Every clause there is checkable, which is the point. The verifiability is what makes it a
good answer, not the content of any individual claim.</p>

<h2>Where to start if you have none of this</h2>

<ol>
<li>Write down the hops. Just the list — most teams discover one they had forgotten while
    writing it.</li>
<li>Grep for content in logs. Fix what you find before documenting anything.</li>
<li>Collect the DPAs and sub-processor lists you already have the right to.</li>
<li>Write the paragraph above for your own system, with the blanks filled.</li>
</ol>

<p>That paragraph is the deliverable. It answers the security review, it tells your own team
what the rules are, and writing it usually surfaces one thing worth fixing — which is the real
reason to do it before someone asks.</p>

<p>The questions a buyer will put to <em>you</em> are covered in
<a href="/blog/ai-vendor-data-questions">twelve data questions to ask an AI vendor</a>; ours
are answered on <a href="/security">the security page</a>, in the same shape.</p>
"""

template = pathlib.Path("blog/llm-feature-pre-launch-checklist.html").read_text()
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
              rf"\g<1>Compliance\g<2>PENDING\g<3>{minutes} min read\g<4>", page, count=1)
page = re.sub(r'(<h1 style="margin-top: 14px;">).*?(</h1>)', rf"\g<1>{H1}\g<2>", page, count=1, flags=re.S)

start = page.index('<article class="article">') + len('<article class="article">')
end = page.index("</article>")
page = page[:start] + "\n" + BODY.strip() + "\n" + page[end:]
page = re.sub(r'<aside class="related">.*?</aside>\s*', "", page, flags=re.S)

out = pathlib.Path("scheduled") / f"{SLUG}.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page)
print(f"  wrote {out} — {words} words, {minutes} min read")
