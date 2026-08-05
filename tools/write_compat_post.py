#!/usr/bin/env python3
"""Write the OpenAI-compatibility post into scheduled/.

Grounded in the OpenAI API reference (parameter names and streaming semantics
read from it directly on 6 August 2026) plus the error envelopes measured
against our own endpoint the same day. No competitor is named — the piece is
about how to test a claim, not about who fails it — so unlike the licence draft
this one carries no positioning decision and is published.

No Runix latency, uptime or throughput figure appears in it.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "what-openai-compatible-actually-means"
TITLE = "What \"OpenAI-compatible\" actually guarantees — Runix"
H1 = "\"OpenAI-compatible\" is a surface, not a contract"
DESC = ("Compatibility claims cover the endpoint shape, rarely the details that break you: "
        "ignored parameters, missing usage, streaming that ends wrong. How to test one.")

REF = "https://developers.openai.com/api/docs/api-reference/chat/create"

BODY = f"""<p>Almost every gateway, proxy and inference host now claims to be OpenAI-compatible,
and the claim is usually true in the sense that matters least: you can point an OpenAI SDK at
it and get a completion back. What varies — and what costs you a day when it varies — is
everything after the happy path.</p>

<p>This is a list of the specific things "compatible" does not tell you, and a short set of
requests that answer each one. It takes about twenty minutes and is worth running before you
migrate anything, including against us.</p>

<h2>1. Which endpoints, not "the API"</h2>

<p>The OpenAI API is not one endpoint. Compatibility almost always means
<code>POST /chat/completions</code>, sometimes embeddings, and much more rarely anything
else — files, batch, moderation, or the newer Responses surface. That is a reasonable place
to stop; the problem is that the claim does not say where it stopped.</p>

<p><strong>Test it:</strong> call <code>GET /v1/models</code> first. If it 404s while chat
completions works, the surface is one endpoint wide, and you now know that before you write
code against anything else.</p>

<h2>2. Parameters that are accepted and ignored</h2>

<p>This is the one that actually hurts, because it fails silently. A request carrying
<code>temperature</code>, <code>top_p</code>, <code>seed</code>, <code>response_format</code>
or <code>tools</code> can be accepted with a 200 and served as though those fields were never
sent. Nothing errors. Your evaluation just quietly measures a different configuration than
you think it does.</p>

<p><strong>Test it:</strong> send the same prompt twice with <code>temperature</code> at 0 and
at 2, several times each. If the spread of outputs looks the same at both settings, the
parameter is not reaching the model. Do the same with <code>seed</code>: two identical
requests with the same seed should produce more similar output than two without it. For
<code>response_format</code>, ask for JSON and send a prompt that would naturally answer in
prose.</p>

<p>An implementation that rejects a parameter it does not support is being more honest than
one that accepts it — a 400 is information; a 200 is a wrong answer you will not notice.</p>

<h2>3. Whether you get usage back</h2>

<p>The non-streamed response object carries <code>usage</code> alongside <code>id</code>,
<code>choices</code>, <code>created</code>, <code>model</code> and <code>object</code>
(<a href="{REF}">reference</a>). If <code>usage</code> is missing or zeroed, you cannot
attribute cost per request, which means you cannot attribute it per team or per feature
either — you are back to reconciling one bill against a guess.</p>

<p>Streaming is where this most often breaks. Usage is not in the stream by default: you ask
for it with <code>stream_options</code> and its <code>include_usage</code> field, and the
documented behaviour is that <q>an additional chunk will be streamed before the
<code>data: [DONE]</code> message</q>, whose <code>usage</code> field covers the whole
request. Plenty of compatible implementations do not implement that chunk.</p>

<p><strong>Test it:</strong> make a streaming request with
<code>"stream_options": {{"include_usage": true}}</code> and check whether a usage chunk
arrives before <code>[DONE]</code>. If your cost attribution depends on streamed traffic and
that chunk never comes, you have found the gap before it becomes a billing dispute.</p>

<h2>4. Streaming framing, exactly</h2>

<p>Streaming responses are server-sent events, and the stream ends with
<code>data: [DONE]</code>. Three things go wrong often enough to check: the terminator is
missing, so a client waits for a close that never comes; chunks are buffered somewhere in the
middle so the whole response arrives at once — technically streaming, functionally not; or
an error mid-stream arrives as a broken frame rather than as anything a client can parse.</p>

<p><strong>Test it:</strong> use <code>curl -N</code> — without it curl buffers and you will
measure your own client. Watch whether tokens arrive progressively, and that the last line
is the terminator. Then make it fail: request a model that does not exist, or send an
oversized prompt, and see what a mid-stream failure actually looks like on the wire.</p>

<h2>5. Errors: status codes first, envelopes second</h2>

<p>The OpenAI SDKs map HTTP status codes to their exception classes. That means status codes
are the part of the error contract you can rely on, and the JSON envelope is the part that
varies. Write your error handling against the status.</p>

<p>For reference, here is what our own endpoint returns, measured rather than described:</p>

<pre><code>// missing or invalid key -> 401
{{"error": {{"code": "", "message": "Invalid token (request id: ...)", "type": "runix_error"}}}}

// unknown path under /v1 -> 404
{{"error": {{"message": "Invalid URL (POST /v1/nope)", "type": "invalid_request_error",
           "param": "", "code": ""}}}}</code></pre>

<p>Note the <code>type</code> values differ between the two, and one of them is not an
OpenAI-standard string. That is exactly the point: if your retry logic branches on
<code>error.type</code>, it is branching on the least stable field in the response. Branch on
401 and 429 instead.</p>

<p><strong>Test it:</strong> send a request with no key, with a bad key, to a path that does
not exist, and with a model id that does not exist. Four requests, four status codes. Write
them down — that table is your error handling.</p>

<h2>6. Whether the request id survives</h2>

<p>When something goes wrong in production, the only useful question is "what happened to
<em>this</em> request". That needs an identifier you can quote and the other side can find.
Some implementations return one in a header, some inside the error message, some not at all.</p>

<p><strong>Test it:</strong> trigger an error and look for an id anywhere in the response —
headers included. If there is not one, every future support conversation starts with both
sides guessing.</p>

<h2>7. Tool calling, if you use it</h2>

<p>Tool and function calling is the compatibility surface most likely to be partial, because
it is several behaviours rather than one: the shape of <code>tools</code> in the request,
whether <code>tool_choice</code> is honoured, whether arguments come back as valid JSON, and
whether parallel tool calls are supported or silently collapsed to one.</p>

<p><strong>Test it:</strong> define two tools that could both plausibly be called and see how
many come back. Then force one with <code>tool_choice</code> and confirm it is the one you
get.</p>

<h2>The twenty-minute version</h2>

<ol>
<li><code>GET /v1/models</code> — how wide is the surface?</li>
<li>Same prompt at temperature 0 and 2, several times — is the parameter reaching anything?</li>
<li>Non-streamed request — is <code>usage</code> present and non-zero?</li>
<li>Streamed request with <code>stream_options.include_usage</code> — does the usage chunk arrive before <code>[DONE]</code>?</li>
<li><code>curl -N</code> — do tokens actually arrive progressively?</li>
<li>No key / bad key / bad path / bad model — four status codes, written down.</li>
<li>Trigger an error — is there a request id you can quote?</li>
<li>Two tools, then <code>tool_choice</code> — is tool calling whole?</li>
</ol>

<p>None of this is exotic, and that is rather the point: the answers are cheap to get and
almost nobody gets them before committing. A provider that passes all eight has earned the
word compatible. One that passes six has not stopped being useful — you just know which two
to design around, which is a different position than finding out in production.</p>

<p>If you want to run this against <a href="/router">Runix Router</a>, ask for an evaluation
key and do exactly that. We would rather you test the claim than take it.</p>

<p class="note-line">Parameter names and streaming behaviour above are from the
<a href="{REF}">OpenAI chat completions reference</a>, read on 6 August 2026. The error
envelopes are what our endpoint returned on the same day. APIs change; re-run the checks
rather than trusting a list.</p>
"""

template = pathlib.Path("blog/model-deprecation-without-a-redeploy.html").read_text()
url = f"{SITE}/blog/{SLUG}"

page = template
page = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", page, count=1)
for attr in ('name="description"', 'property="og:description"', 'name="twitter:description"'):
    page = re.sub(rf'({re.escape(attr)} content=")[^"]*(")', lambda m: m.group(1) + DESC + m.group(2), page, count=1)
for attr, val in (('property="og:title"', TITLE), ('name="twitter:title"', TITLE)):
    page = re.sub(rf'({re.escape(attr)} content=")[^"]*(")', lambda m: m.group(1) + val + m.group(2), page, count=1)
page = re.sub(r'(<link rel="canonical" href=")[^"]*(">)', rf"\g<1>{url}\g<2>", page, count=1)
page = re.sub(r'(<meta property="og:url" content=")[^"]*(">)', rf"\g<1>{url}\g<2>", page, count=1)


def _fix_schema(block):
    data = json.loads(block)
    if data.get("@type") == "Article":
        data["headline"] = H1
        data["description"] = DESC
        data["url"] = url
        if isinstance(data.get("mainEntityOfPage"), dict):
            data["mainEntityOfPage"]["@id"] = url
    elif data.get("@type") == "BreadcrumbList":
        leaf = max(data["itemListElement"], key=lambda i: i["position"])
        leaf["name"] = H1
        leaf["item"] = url
    return json.dumps(data, ensure_ascii=False, indent=2)


page = re.sub(r'(<script type="application/ld\+json">\n)(.*?)(\n</script>)',
              lambda m: m.group(1) + _fix_schema(m.group(2)) + m.group(3), page, flags=re.S)

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
