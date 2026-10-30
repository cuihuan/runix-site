"""Text for tools/router_available.py: whole blocks, then sentence-level edits.

EDITS entries are (path, old, new), matched with any whitespace where `old`
has some, or ("after", path, anchor, addition) to insert text once.
"""

ROUTER_HOW = '''<section class="section" id="how">
  <div class="container">
    <div class="section-head center">
      <p class="sec-no">04 &middot; How it works</p>
      <h2>What happens to one request</h2>
      <p>Your application holds one base URL and one key. This is everything Router does with a call, in order.</p>
    </div>

    <figure class="diagram">
      <svg viewBox="0 0 880 330" role="img" aria-labelledby="fd-t fd-d" class="diagram-svg">
        <title id="fd-t">What Runix Router does with one request</title>
        <desc id="fd-d">Your application sends a request to one Runix endpoint with its key. Router checks the key, its expiry, its IP allowlist, the models it may call and its remaining quota, forwards the request to the provider that serves the model, streams the answer back, then meters the tokens and records the call in the request log.</desc>
        <defs>
          <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
            <path d="M0 0 L10 5 L0 10 z" fill="currentColor"/>
          </marker>
        </defs>
        <g class="d-node">
          <rect x="6" y="122" width="168" height="86" rx="12"/>
          <text x="90" y="155" class="d-title">Your application</text>
          <text x="90" y="177" class="d-sub">one base URL</text>
          <text x="90" y="194" class="d-sub">one key</text>
        </g>
        <g class="d-flow">
          <line x1="180" y1="165" x2="252" y2="165" marker-end="url(#ar)"/>
          <text x="216" y="152" class="d-edge">request</text>
        </g>
        <g class="d-node d-gw">
          <rect x="258" y="54" width="212" height="222" rx="12"/>
          <text x="364" y="86" class="d-title">Runix Router</text>
          <g class="d-chip">
            <rect x="278" y="104" width="172" height="30" rx="8"/>
            <text x="364" y="124">key and expiry</text>
            <rect x="278" y="142" width="172" height="30" rx="8"/>
            <text x="364" y="162">IP allowlist</text>
            <rect x="278" y="180" width="172" height="30" rx="8"/>
            <text x="364" y="200">model and quota</text>
            <rect x="278" y="218" width="172" height="30" rx="8"/>
            <text x="364" y="238">meter and log</text>
          </g>
        </g>
        <g class="d-flow d-ok">
          <path d="M476 150 C 530 150, 540 104, 596 104" marker-end="url(#ar)" fill="none"/>
          <text x="540" y="118" class="d-edge">forwarded</text>
        </g>
        <g class="d-flow d-idle">
          <path d="M476 200 C 530 200, 540 236, 596 236" marker-end="url(#ar)" fill="none" stroke-dasharray="2 6"/>
          <text x="540" y="246" class="d-edge">recorded</text>
        </g>
        <g class="d-node d-prov">
          <rect x="602" y="76" width="272" height="56" rx="10"/>
          <text x="622" y="100" class="d-title d-left">Model provider</text>
          <text x="622" y="119" class="d-sub d-left">answers, streamed straight back</text>
        </g>
        <g class="d-node d-prov">
          <rect x="602" y="208" width="272" height="56" rx="10"/>
          <text x="622" y="232" class="d-title d-left">Request log</text>
          <text x="622" y="251" class="d-sub d-left">model, tokens, cost, request id</text>
        </g>
      </svg>

      <ol class="diagram-steps">
        <li><b>Your application</b> sends the request to one Runix base URL with its key, in the OpenAI format it already speaks.</li>
        <li><b>Runix Router checks the key</b>: that it is active and not expired, that the call comes from an allowed IP, that the key may call this model, and that it has quota left. A call that fails a check is refused before it reaches a provider.</li>
        <li><b>The request is forwarded</b> to the provider that serves the model, and a streamed answer is passed through as it arrives, not buffered.</li>
        <li><b>The tokens are metered</b> at the model's price, and the response carries its usage, so a single call can be checked against the rate card.</li>
        <li><b>The call is recorded</b> in the request log with its key, model, tokens, cost and request id, which is what support traces a question with.</li>
      </ol>

      <figcaption>Your code holds the same base URL and key whichever model it calls. Changing models is a different string in the request, not a different integration.</figcaption>
    </figure>
  </div>
</section>'''
RELIABILITY = '''<h2 id="service-levels-are-agreed-per-account">Service levels are agreed per account</h2>
<p>Start with what this page is not. There is no published uptime percentage and no
historical availability chart, because a number on a marketing page has no contract behind
it. The service level for an account is written into its order form. What follows is how
Router behaves today, which is the claim we can stand behind for everyone.</p>

<h2 id="what-router-does-when-a-provider-fails">What Router does when a provider fails</h2>
<p>Each model is served by one provider today, so when that provider fails, the failure
reaches your application. Router makes it a failure you can handle:</p>
<ul>
<li><strong>Errors keep the OpenAI shape and HTTP status.</strong> The retry and fallback
logic your SDK already has keeps working, because what arrives is what an OpenAI-compatible
client expects.</li>
<li><strong>Every response carries a request id</strong>, in the
<code>X-Runix-Request-Id</code> header and inside error messages, so a failed call can be
traced to one request rather than argued about.</li>
<li><strong>Streams pass through, not buffered.</strong> A stream that stops at the provider
stops for you at the same moment, instead of after a replay, and Router waits up to 15
minutes for an answer, so a slow-thinking model is not cut off at the gateway.</li>
</ul>

<h2 id="failover-between-providers">Failover between providers</h2>
<p>Moving a request to a second provider is only safe when that provider serves the same
model under terms you would accept. Where an account needs it, failover between providers
is set up for that account, with the models it covers and the providers it may use named in
writing. Until that is in place for yours, treat each model as served by one provider and
keep your own retry logic.</p>

<h2 id="what-you-can-verify-yourself">What you can verify yourself</h2>
<p>The request id, the <code>usage</code> object on every response and the request log in
the console are the same records we use. The <a href="/docs/router">Router quickstart</a>
documents the error shape, the limits a key carries and what happens when a provider fails.</p>

<h2 id="what-is-not-here-yet">What is not here yet</h2>
<p>A continuously updated public status feed is not live. When it is, it will report
measured availability rather than an aspiration. Until then, the honest answer to "what is
your uptime" is that we will tell you what we have measured for your workload, and we will
not quote a number we cannot evidence. If availability guarantees are a procurement
requirement for you, say so in your <a href="/access">first message</a>.</p>
</article>'''
DOCS = '''<p>Runix Router is an OpenAI-compatible endpoint in front of many model providers. If your code already calls an OpenAI-compatible API, integration is a configuration change: point the client at Runix and swap the key. This guide covers the quickstart, model selection, streaming, what happens when a provider fails, and the operational details teams ask about. Router is <a href="/router">available</a>, with accounts opened by our team, and support comes directly from the engineers.</p>

<h2 id="quickstart">1. Quickstart</h2>
<p>Set your client's base URL to <code>https://router-api.runixcloud.io/v1</code> and use a key from the <b>Tokens</b> page of the <a href="https://router-console.runixcloud.io/">console</a>. Everything else about your existing integration stays the same.</p>
<pre><code># cURL
curl https://router-api.runixcloud.io/v1/chat/completions \\
  -H "Authorization: Bearer $RUNIX_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "your-model-id",
    "messages": [{"role": "user", "content": "Hello"}]
  }'</code></pre>
<pre><code># OpenAI SDK (Python)
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://router-api.runixcloud.io/v1",
    api_key=os.environ["RUNIX_API_KEY"],
)
resp = client.chat.completions.create(
    model="your-model-id",
    messages=[{"role": "user", "content": "Hello"}],
)</code></pre>
<p>The same base-URL swap works for any tool that speaks the OpenAI API: LangChain, LlamaIndex, the Vercel AI SDK, or plain HTTP. Replace <code>your-model-id</code> with an id from <code>GET /v1/models</code> or the <a href="/router-models">models catalogue</a>. The Responses API is served at the same base URL, under <code>/v1/responses</code>.</p>

<h2 id="model-selection">2. Model selection</h2>
<p>Every request names its model in the <code>model</code> field, and Router sends it to the provider that serves that model.</p>
<ul>
<li><strong>Model ids are the vendors' own.</strong> Anthropic models answer to their official hyphenated ids (<code>claude-opus-5</code>, <code>claude-sonnet-5</code>), and other vendors' models keep their catalogue names: there is no Runix-specific alias table to maintain, so an id copied from a vendor's announcement works as-is.</li>
<li><strong>Discover what a key can call</strong>: <code>GET /v1/models</code> with your key returns the model ids that key is allowed to use, so you can list them from code instead of asking us. A request for a model outside that list is refused before it reaches a provider.</li>
<li><strong>Prices</strong> are on the <a href="/router-models">models catalogue</a>, at each vendor's public list price.</li>
</ul>

<h2 id="streaming">3. Streaming</h2>
<p>Pass <code>"stream": true</code> and responses arrive as standard server-sent events, exactly as your SDK already expects. Streaming passes through the router rather than being buffered and replayed, including tool-call deltas, so the first token is forwarded as soon as the provider emits it rather than after the response completes. That is a statement about the mechanism, not a performance claim: measure time to first token against the provider directly and you will see what the router costs you.</p>
'''
DOCS += '''
<h2 id="when-a-provider-fails">4. When a provider fails</h2>
<p>Each model is served by one provider today, so a provider's failure reaches you, in a form your client already handles:</p>
<ul>
<li><strong>The error keeps the OpenAI shape and HTTP status</strong>, so the retry and fallback logic in your SDK keeps working unchanged.</li>
<li><strong>Every response carries a request id</strong> (section 6), so a failed call can be traced to that exact request.</li>
<li><strong>Long answers are not cut off at the gateway</strong>: Router waits up to 15 minutes for a response, and a stream that stops at the provider stops for you at the same moment.</li>
<li><strong>Failover to a second provider</strong> is set up per account where it is needed, with the models it covers and the providers it may use named in writing. Without it, keep your own retries.</li>
</ul>
<p>For the background on failure taxonomy, read <a href="/blog/model-failover">Model failover for production LLM traffic</a>; why retries should be a spend budget rather than a count (and which errors deserve one at all) is covered in <a href="/blog/llm-retry-budget">Retry budgets for LLM APIs</a>. How Router behaves today is on <a href="/reliability">Reliability</a>.</p>

<h2 id="limits-usage-and-cost">5. Limits, usage and cost</h2>
<ul>
<li><strong>Per-key limits</strong>: each key can carry a spending quota, an expiry date, a list of allowed models and an IP allowlist, set on the <b>Tokens</b> page of the console and changed without a redeploy. A call outside them is refused before it reaches a provider.</li>
<li><strong>List-price metering</strong> (requests are metered per token at the upstream
    vendors' published rates, with input, output, cached-read and cache-write tokens priced
    separately) the same structure the vendors themselves publish. We audit the rate table
    against the vendors' own pricing pages; the mechanics of why token bills diverge from
    price lists, and how to check one by hand, are in
    <a href="/blog/why-your-llm-bill-doesnt-match-the-price-list">Why your LLM bill doesn't
    match the price list</a>.</li>
<li><strong>Usage on every response</strong>: the <code>usage</code> object carries the full
    token breakdown, cached tokens included, so any single request can be reconciled against
    the rate card without asking us. Billing is usage-based in USD with itemised statements;
    see <a href="/plans">Pricing</a> for how quotes work.</li>
<li><strong>The request log</strong>: every call is listed on the <b>Logs</b> page of the console with its key, model, tokens and cost.</li>
<li><strong>Attribution</strong>: issue separate keys per team or product to get cost attribution along the lines your finance team actually asks about; the reasoning is covered in <a href="/blog/llm-cost-attribution">LLM cost attribution</a>.</li>
</ul>
'''
DOCS += '''
<h2 id="errors-and-request-ids">6. Errors and request ids</h2>
<p>Errors come back as JSON in the shape your OpenAI-compatible client already parses: an <code>error</code> object carrying <code>message</code>, <code>type</code> and <code>code</code>.</p>
<pre><code>// missing or invalid key -> HTTP 401
{
  "error": {
    "code": "",
    "message": "Invalid token (request id: 20261030145933...)",
    "type": "runix_error"
  }
}

// a path under /v1 that does not exist -> HTTP 404
{
  "error": {
    "message": "Invalid URL (POST /v1/nope)",
    "type": "invalid_request_error",
    "param": "",
    "code": ""
  }
}</code></pre>
<p>Two things worth knowing before you write error handling. First, branch on the HTTP status
rather than on <code>error.type</code>: the status is what the OpenAI SDKs already map to
their own exception classes, and it is the part that will not surprise you. Second, every
response carries its request id in the <code>X-Runix-Request-Id</code> header, and an error
repeats it inside <code>message</code>; quote it when you contact us and we can trace that
exact call.</p>
<p>Paths outside <code>/v1</code> on this host are not part of the API surface and do not
return this envelope. A call refused by a key's limits (section 5) and a call a provider
failed (section 4) both arrive in this shape.</p>

<h2 id="data-handling">7. Data handling</h2>
<p>Prompt and response content is processed to serve your request; it is not used to train models and not sold. Operational metadata (usage counts, latency, error codes) is kept to run billing, reliability and support. The full statement is in the <a href="/privacy">Privacy Policy</a>, and the security posture in <a href="/security">Security</a>.</p>
<p>If you are evaluating us — or any gateway — <a href="/blog/llm-gateway-security-review">the security review an LLM gateway should survive</a> is the list of questions we think you should ask, including of Runix.</p>

<h2 id="getting-a-key">8. Getting a key</h2>
<p>Accounts are opened by our team: <a href="/about#contact">tell us what you are building</a> — models, expected volume, latency needs — or email <a href="mailto:sales@runixcloud.io">sales@runixcloud.io</a>, and we reply within one business day and set the account up for you. Evaluation credits are issued on request, so you can test against real traffic before you pay. Once the account exists, keys are created on the <b>Tokens</b> page of the <a href="https://router-console.runixcloud.io/">console</a>.</p>

<div class="callout" style="margin-top:40px;">'''

BLOCKS = [
    ("router.html", '<section class="section" id="how">', "</section>", ROUTER_HOW,
     "<h2>What happens to one request</h2>"),
    ("reliability.html", '<h2 id="no-published-sla-during-early-access">', "</article>", RELIABILITY,
     'id="service-levels-are-agreed-per-account"'),
    ("docs/router.html", "<p>Runix Router is an OpenAI-compatible endpoint in front of many model providers.",
     '<div class="callout" style="margin-top:40px;">', DOCS, 'id="when-a-provider-fails"'),
]
SITES = '''

# Each product's own subdomain, linked from its tile on the home page stack
# (2026-10-30: "put the links on the home page, with the stack"). The product
# pages' canonicals stay on the main site; a subdomain is the short address.
SITES = {
    "code": "code.runixcloud.io", "comic": "comic.runixcloud.io",
    "router": "router.runixcloud.io", "models": "models.runixcloud.io",
    "data": "data.runixcloud.io", "fs": "fs.runixcloud.io",
}
'''

HOST_CSS = '''.pmap-host { padding: 6px 4px 0; font: 500 12.5px/1.4 var(--mono); }
.pmap-host a { color: var(--ink-3); text-decoration: underline; text-underline-offset: 3px; }
.pmap-host a:hover { color: var(--indigo); }
'''

GATEWAY_REDIRECT = '''

# gateway.runixcloud.io is the old name of router.runixcloud.io, and both are
# custom domains of one Pages project. _redirects cannot match on hostname, so
# a Pages Function sends the old name over, path and query kept.
GATEWAY_REDIRECT = """export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.hostname === "gateway.runixcloud.io") {
    url.hostname = "router.runixcloud.io";
    return Response.redirect(url.toString(), 301);
  }
  return next();
}
"""
'''

GATEWAY_FN = '''        if sub == "gateway":
            os.makedirs(os.path.join(out, "functions"))
            open(os.path.join(out, "functions", "_middleware.js"), "w").write(GATEWAY_REDIRECT)
'''

GATEWAY_CHECK = '''# gateway.* is the old name of router.*: it must redirect, not serve a copy.
loc=$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' --max-time 15 "https://gateway.runixcloud.io/x?y=1")
if [ "$loc" != "301 https://router.runixcloud.io/x?y=1" ]; then
  printf '    gateway   -> %s (expected a 301 to router.runixcloud.io)\\n' "$loc"
  fail=1
fi
[ "$fail" -eq 0 ] && echo "==> Sub-sites OK"'''

SUPERSEDED = '''import sys

# SUPERSEDED 2026-10-30 by tools/router_available.py. This figure showed
# failover between providers, which Router does not do by default; the figure
# on /router is now the path of one request. Re-running this would add nothing
# (it skips a page that has a figure), but its text is no longer the page's.
print("add_router_diagram: superseded by router_available.py; nothing to do")
sys.exit(0)
'''
def j(s):
    """The same text as it sits inside a JSON post spec (double quotes escaped)."""
    return s.replace('"', '\\"')


EDITS = [
    # --- builders: the status, the live marker, the home-page subdomain links
    ("tools/stack.py", '"gateway", "early access", ""),', '"gateway", "available", ""),'),
    ("tools/stack.py", '"router": "running traffic",', '"router": "set up by our team",'),
    ("after", "tools/stack.py", "LAYER_OF = {key: (num, name) for key, num, name, _ in LAYERS}\n", SITES),
    ("tools/stack_build.py", "QUALIFIER, products_in  # noqa: E402", "QUALIFIER, SITES, products_in  # noqa: E402"),
    ("tools/stack_build.py", 'live = " pmap-live" if status == "early access" else ""',
     'live = " pmap-live" if status in ("available", "early access") else ""'),
    ("tools/stack_build.py",
     """out.append(f'{i3}<li><a class="pmap-cell{live}" href="{href}"><b>{pname}{new}</b>'
                       f'<span>{line}</span><em class="pmap-st">{status.capitalize()}{qual}</em></a></li>')""",
     """site = SITES.get(pk)
            host = (f'<span class="pmap-host"><a href="https://{site}/">{site}</a></span>'
                    if site else "")
            out.append(f'{i3}<li><a class="pmap-cell{live}" href="{href}"><b>{pname}{new}</b>'
                       f'<span>{line}</span><em class="pmap-st">{status.capitalize()}{qual}</em></a>{host}</li>')"""),
    ("after", "assets/style.css", ".pmap-cells li { display: grid; min-width: 0; }\n", HOST_CSS),
    ("tools/product_template.py", 'live = " pbar-live" if status == "early access" else ""',
     'live = " pbar-live" if status in ("available", "early access") else ""'),
    ("tools/build_solutions.py", """live = f' class="{cls}"' if st == "early access" else \"\"""",
     """live = f' class="{cls}"' if st in ("available", "early access") else \"\""""),
    ("tools/build_solutions.py", 'for st in ("early access", "in development"))',
     'for st in ("available", "early access", "in development"))'),
    ("tools/build_solutions.py", 'ea = [v for v in PRODUCTS.values() if v[5] == "early access"]',
     'ea = [v for v in PRODUCTS.values() if v[5] in ("available", "early access")]'),
    ("tools/build_solutions.py", '<p class="card-layer"><b>Now</b> &middot; early access</p>',
     '<p class="card-layer"><b>Now</b> &middot; available and early access</p>'),
    ("tools/build_solutions.py", "<p>Router, FS, Models and Data are in early access; Pipeline, Code and Comic are in",
     "<p>Router is available; FS, Models and Data are in early access; Pipeline, Code and Comic are in"),
    # --- the old failover drawing, the subdomain deploy and its checks
    ("after", "tools/add_router_diagram.py", "import pathlib\n", SUPERSEDED),
    ("tools/check_idempotent.sh", 'BUILDERS="add_closing_ctas add_docs_nav add_router_diagram',
     'BUILDERS="add_closing_ctas add_docs_nav router_available'),
    ("after", "tools/build_subsites.py", '"acceptable-use"]\n', GATEWAY_REDIRECT),
    ("after", "tools/build_subsites.py", '            NOT_FOUND.replace("MAIN_SITE", MAIN))\n', GATEWAY_FN),
    ("tools/deploy_subsites.sh", "for h in gateway router comic code data fs models; do",
     "for h in router comic code data fs models; do"),
    ("tools/deploy_subsites.sh", '[ $fail -eq 0 ] && echo "==> Sub-sites OK"', GATEWAY_CHECK),
    ("tools/subsite_drift.sh", 'HOSTS=${HOSTS:-"gateway comic code data fs models"}',
     'HOSTS=${HOSTS:-"router comic code data fs models"}'),
    ("tools/subsite_drift.sh", '"gateway:router.html"', '"router:router.html"'),
    ("tools/README.md", "| `runix-gateway` | gateway.runixcloud.io, **router.runixcloud.io** (one project, two domains) |",
     "| `runix-gateway` | **router.runixcloud.io**; gateway.runixcloud.io 301s to it through a Pages Function, because `_redirects` cannot match a hostname |"),
]
EDITS += [
    # --- tools/product_template.py: the Router hero, glance, example and specs
    ("tools/product_template.py", '''"model": "auto",''', '''"model": "your-model-id",'''),
    ("tools/product_template.py",
     "central key custody, written data terms, and failover that fires mid-request, behind one OpenAI-compatible API.",
     "one OpenAI-compatible API and one key, with per-key quotas and allowlists, written data terms, and a log of every request with its cost."),
    ("tools/product_template.py", '("Keys", "Per key: quota, limits, allowed models, routing"),',
     '("Keys", "Per key: quota, expiry, allowed models, IP allowlist"),'),
    ("tools/product_template.py", '("Failover", "Mid-request, streaming preserved"),',
     '("Request log", "Model, tokens, cost and request id, per call"),'),
    ("tools/product_template.py", '("Status", "Early access, running traffic"),',
     '("Status", "Available; accounts opened by our team"),'),
    ("tools/product_template.py", r"""<code>"auto"</code> lets Router choose by cost, health and your key\'s policy; an explicit model id pins the model, and failover stays within the providers that serve it.""",
     r"""The model is named by its vendor\'s own id, and <code>GET /v1/models</code> lists every id a key may call."""),
    ("tools/product_template.py", '("API surface", "Chat completions and model listing, with server-sent events for streaming",',
     '("API surface", "Chat completions, Responses and model listing, with server-sent events for streaming",'),
    ("tools/product_template.py", """("Model selection", '<code>"auto"</code>, or an explicit model id',""",
     """("Model selection", 'The vendor\\'s own model id; <code>GET /v1/models</code> lists what a key may call',"""),
    ("tools/product_template.py", '("Failover", "Provider to provider, mid-request, streaming preserved",',
     '("Provider failure", "OpenAI-style error with a request id; failover between providers set up per account",'),
    ("tools/product_template.py", '"Per key: rate limits, quotas and allowed models, revocable without a redeploy"',
     '"Per key: quota, expiry, allowed models and IP allowlist, changed without a redeploy"'),
    ("tools/product_template.py", '"No published SLA during early access; the failover mechanism is documented"',
     '"No public uptime figure; service levels agreed per account in the order form"'),
    ("tools/product_template.py", '"bad hour": "How it works"', '"one request": "How it works"'),
    ("tools/product_template.py", '"Evaluation credits on request, full router functionality, no card. Integration is a base-URL change."',
     '"Evaluation credits on request, the full product, no card. Integration is a base-URL change."'),
]
S = "tools/solutions.py"
EDITS += [
    (S, "per-key limits and mid-request ' 'failover, and Runix FS where",
     "per-key limits and usage by '\n                 'key, and Runix FS where"),
    (S, "'per-key limits and failover beneath it. Where training", "'per-key limits and usage by key beneath it. Where training"),
    (S, """['A provider outage is your outage',
                  'When a provider degrades, every product that calls it directly degrades with it. Failover '
                  'written into each application is written differently each time, and a failure mid-stream '
                  "is the case nobody tested. The platform team ends up on call for other people's "
                  'integrations.'],""",
     """['Every provider is integrated differently',
                  'Each provider has its own API, SDK, keys and invoice, and every team that calls one builds '
                  'its own integration. Nobody sees total spend in one place, and moving a product to another '
                  'model is a code change instead of a configuration change.'],"""),
    (S, """'carries its quota, rate limits, allowed models and routing, revocable without a redeploy. '
              'Failover between providers fires mid-request, with streaming preserved.'],""",
     """'carries its quota, expiry, allowed models and IP allowlist, changed without a redeploy. '
              'Every call is logged with its model, tokens and cost, and billed in USD on one statement.'],"""),
    (S, "Router is ' 'invite-only during early access; a person replies within one business day and sets the account ' 'up after a short intake.'],",
     "Router accounts '\n             'are opened by our team: a person replies within one business day and sets the account '\n             'up.'],"),
    (S, "'Runix Router is in early access and running traffic, with no published SLA; the failover ' 'mechanism is documented instead. Runix FS",
     "'Runix Router is available, with service levels agreed in the order form and no public uptime '\n                'figure. Runix FS"),
    (S, "Runix Router is in early access and ' 'running traffic, with no published SLA.']],",
     "Runix Router is available, with '\n                'service levels agreed in the order form.']],"),
    (S, "Runix Router is in early access, with no published SLA.']],",
     "Runix Router is available, with service levels agreed in the order form.']],"),
    (S, "You ' 'choose a model with an explicit id, or with auto.'],",
     "You '\n            'choose a model by its vendor id, and GET /v1/models lists what a key may call.'],"),
    (S, """['What happens when a provider fails mid-stream?',
            'Failover is provider to provider and fires mid-request, with streaming preserved. The mechanism '
            'is documented under Reliability; there is no published SLA during early access.'],""",
     """['What happens when a provider fails?',
            'The error reaches you in the OpenAI shape, with its HTTP status and a request id, so the retry '
            'logic in your client keeps working. Failover between providers is set up per account where it '
            'is needed, and Reliability says what Router does today.'],"""),
    (S, "the contracting entity and the failover mechanism in ' 'writing.",
     "the contracting entity and the service level in '\n         'writing."),
    (S, "'say plainly whether early access fits.'],", "'say plainly what we can commit to.'],"),
    (S, """'No service level is published during early access; the failover mechanism is documented '
                'instead. Where your procurement requires a guarantee, say so at intake and we will say '
                'plainly whether early access fits.']],""",
     """'No uptime figure is published; service levels are agreed per account in the order form, and '
                'failover between providers is set up per account where it is needed. Where your procurement '
                'requires a guarantee, say so in the first message and we will say plainly what we can commit to.']],"""),
    (S, """"Not during early access. Runix Router's failover fires mid-request with streaming preserved, and "
            'the mechanism is documented; a published number would need a contract behind it.'],""",
     """'Per account, in the order form. No uptime figure is published, because a number on a page has '
            'no contract behind it; Reliability describes what Router does when a provider fails.'],"""),
]
EDITS += [
    # --- tools/solutions.py: the roadmap
    (S, "product, in literal terms: what early access and in development ' 'mean,",
     "product in literal terms: available, early access or in '\n                'development,"),
    (S, "everywhere else on the site: Router, Models, Data and FS are in early access; Pipeline, '",
     "everywhere else on the site: Router is available; Models, Data and FS are in early access; Pipeline, '"),
    (S, """'now': 'Early access means a product you can use today, set up by the team rather than bought off a shelf. '""",
     """'now': 'Available means a production service, with the account opened by our team rather than by a signup '
        'form: Runix Router is available. Early access means a product you can use today, set up by the team '
        'rather than bought off a shelf. '"""),
    (S, """'with the plan and the price agreed before any work starts. No service level is published during '
        'early access; the failover mechanism is documented instead, and if your procurement needs a '
        'guarantee, say so at intake and we will say plainly whether early access fits.',""",
     """'with the plan and the price agreed before any work starts. Service levels are agreed per account in '
        'the order form; if your procurement needs a guarantee, say so in the first message and we will say '
        'plainly what we can commit to.',"""),
    (S, "'during early access the mechanism is documented and no number is.'],",
     "'until then, service levels are agreed per account in the order form.'],"),
    (S, "'Self-serve signup and checkout arrive with general availability; until then accounts and keys are ' 'set up by the team after a short intake.']],",
     "'Self-serve signup and checkout arrive with general availability; until then accounts are opened by '\n          'the team, and keys are created in the console.']],"),
    (S, "'Early access and in development mean the same thing on every page",
     "'Available, early access and in development mean the same thing on every page"),
    (S, "'status_line': {'early access':",
     "'status_line': {'available': 'a production service today, with the account opened by our team and service '\n                               'levels agreed in the order form',\n                 'early access':"),
    (S, """'router': ('Running traffic. Accounts set up after a short intake; evaluation credits on '
                         'request with no card; one OpenAI-compatible endpoint, per-key limits, failover '
                         "mid-request, every model at its vendor's public list price.",""",
     """'router': ('Available. Accounts opened by our team within one business day; evaluation '
                         'credits on request with no card; one OpenAI-compatible endpoint, per-key quotas and '
                         "allowlists, a log of every request with its cost, every model at its vendor's public "
                         'list price.',"""),
    ("after", S, "              '/solutions', 'Solutions by team')",
     ",\n             ('October 30, 2026',\n              'Runix Router moves from early access to available, at router-api.runixcloud.io and '\n              'router-console.runixcloud.io.',\n              '/router', 'Runix Router')"),
]
EDITS += [
    # --- the home page
    ("index.html", "one OpenAI-compatible endpoint in front of every model provider, running traffic today in early access. Beneath it, the file system, data and model layers are in early access;",
     "one OpenAI-compatible endpoint in front of every model provider, available today. Beneath it, the file system, data and model layers are in early access;"),
    ("index.html", "The statuses are literal: Router, Models, Data and FS are in early access; Pipeline, Code and Comic are in development. Early access means a team can be onboarded today, and the qualifier on each tile says what that looks like: a key for Router, a deployment for FS, a scoped engagement for Data and Models.",
     "The statuses are literal: Router is available, a production service with accounts opened by our team; Models, Data and FS are in early access; Pipeline, Code and Comic are in development. Early access means a team can be onboarded today, and the qualifier on each tile says what that looks like: a deployment for FS, a scoped engagement for Data and Models."),
    ("index.html", "with the key custody, contracts and failover your legal and on-call teams ask for.",
     "with the key custody, per-key controls and contracts your legal and finance teams ask for."),
    ("index.html", "<li>Failover mid-request, streaming preserved</li>", "<li>Every request logged with its model, tokens and cost</li>"),
    ("index.html", "<span>Status: early access</span> · <span>Hosted API</span>", "<span>Status: available</span> · <span>Hosted API</span>"),
    # --- about, faq, plans
    ("about.html", "<strong>Runix Router</strong>: <em>early access, running traffic today.</em>",
     "<strong>Runix Router</strong>: <em>available, with accounts opened by our team.</em>"),
    ("about.html", "per-key quotas, request-level audit and failover between providers.",
     "per-key quotas and allowlists, and a log of every request with its cost."),
    ("about.html", "<h3>No SLA during early access</h3>", "<h3>No published uptime figure</h3>"),
    ("about.html", '<a href="/reliability">How failover actually works</a>',
     '<a href="/reliability">What Router does when a provider fails</a>'),
    ("faq.html", "Runix Router is in early access and running traffic.", "Runix Router is available, with accounts opened by our team."),
    ("faq.html", "Not during early access. The Router is built to route around provider failure, and the reliability page describes exactly how — but that is a description of the mechanism, not a published SLA.",
     "Per account, in the order form. No uptime figure is published, because a number on a page has no contract behind it; the reliability page describes what Router does when a provider fails."),
    ("faq.html", 'Not during early access. The Router is built to route around provider failure, and the <a href="/reliability">reliability page</a> describes exactly how — but that is a description of the mechanism, not a published SLA.',
     'Per account, in the order form. No uptime figure is published, because a number on a page has no contract behind it; the <a href="/reliability">reliability page</a> describes what Router does when a provider fails.'),
    ("plans.html", "<td>Gateway</td><td>Early access</td>", "<td>Gateway</td><td>Available</td>"),
    # --- docs
    ("docs/index.html", "<span>Status: early access</span> · <span>Integration guide</span>",
     "<span>Status: available</span> · <span>Integration guide</span>"),
    ("docs/index.html", "Router and FS are in early access and have quick starts;",
     "Router is available and FS is in early access, and both have quick starts;"),
    ("docs/index.html", 'model selection with <code>"auto"</code>, streaming, failover semantics,',
     "model selection by vendor id, streaming, provider errors,"),
    ("docs/router.html", '<li><a href="#failover-semantics">4. Failover semantics</a></li>',
     '<li><a href="#when-a-provider-fails">4. When a provider fails</a></li>'),
    ("docs/router.html", "model selection, streaming, failover semantics, limits and data handling",
     "model selection, streaming, provider errors, limits and data handling"),
    # --- access
    ("access.html", "Runix Router is invite-only: tell us what you are building and your account is set up within one business day; evaluation credits are issued on request.",
     "Runix Router accounts are opened by our team: tell us what you are building and it is set up within one business day, with evaluation credits on request."),
    ("access.html", "Runix Router is invite-only: tell us", "Runix Router accounts are opened by our team: tell us"),
    ("access.html", "Briefly, yes — access is invite-only.", "Briefly, yes — accounts are opened by our team."),
    ("access.html", "<p>Router is invite-only. Tell us", "<p>Router accounts are opened by our team. Tell us"),
    ("access.html", "Access is invite-only; we reply and set the account up", "We reply and set the account up"),
    ("access.html", "whether the failover behaviour and the cost reporting match", "whether the models, the limits and the cost reporting match"),
    ("access.html", "streaming, failover semantics and the error envelope", "streaming, provider errors and the error envelope"),
    ("access.html", "models it is allowed to call, and routing preferences applied server-side",
     "models it is allowed to call, an expiry date and an IP allowlist"),
    ("access.html", "Mention custom routing, higher limits,", "Mention failover between providers, higher limits,"),
    # --- llms.txt
    ("llms.txt", "*status: early access, running traffic today.* One OpenAI-compatible",
     "*status: available, with accounts opened by our team.* One OpenAI-compatible"),
    ("llms.txt", "automatic failover between providers with streaming preserved, and routing by cost, health and configuration.",
     "a log of every request with its cost, and streaming passed through unbuffered. API base https://router-api.runixcloud.io/v1."),
    ("llms.txt", "model selection, streaming, failover semantics, limits.", "model selection, streaming, provider errors, limits."),
]
R = "router.html"
EDITS += [
    # --- /router: head, structured data, capabilities, FAQ, close
    (R, "Runix Router — LLM Routing, Failover &amp; Cost Control", "Runix Router — One LLM API Key for Every Model"),
    (R, "One OpenAI-compatible endpoint that routes across model providers: mid-request failover, central key custody, per-key quotas and cost tracking.",
     "One OpenAI-compatible endpoint across model providers: central key custody, per-key quotas and allowlists, and a log of every request with its cost."),
    (R, "An OpenAI-compatible LLM gateway with central key custody, routing, automatic failover between providers, per-key quotas and per-request cost attribution.",
     "An OpenAI-compatible LLM gateway with central key custody, per-key quotas and allowlists, and per-request cost attribution."),
    (R, "They stall on who holds the keys, what legal can sign, and what happens at 3am when a provider degrades.",
     "They stall on who holds the keys, what legal can sign, and who can say what the models cost."),
    (R, """<h3>A bad provider hour is not your outage</h3>
        <p class="lead-line">The gateway is on the hot path, so it is built to get out of the way and to recover without you.</p>
        <ul>
          <li><b>Failover mid-request</b> — errors, rate limits and timeouts re-issue upstream under a retry budget</li>
          <li><b>Circuit breakers</b> — a degrading provider is taken out of rotation before it drags latency</li>
          <li><b>Streaming preserved</b> — token streaming and tool calls pass through intact, not buffered and replayed</li>
          <li><b>Routing you control</b> — pin a model, or let the router choose on cost, health and configuration</li>
        </ul>""",
     """<h3>Spend you can see and cap</h3>
        <p class="lead-line">Every key has a budget, and every call says what it cost.</p>
        <ul>
          <li><b>Per-key quotas</b> — a spending limit, an expiry date, the models a key may call and the IPs it may call from</li>
          <li><b>Usage on every response</b> — the token breakdown comes back with the answer, so one call can be checked against the rate card</li>
          <li><b>One bill</b> — every model at its vendor's public list price, billed in USD by Runix AI Inc, itemised</li>
          <li><b>Streaming preserved</b> — token streaming and tool calls pass through intact, not buffered and replayed</li>
        </ul>"""),
    (R, "Runix Router is in early access, so treat capability claims as what the product does for onboarded teams today — not as a published SLA. Ask us for specifics on your workload and we will answer concretely, in writing.",
     "Everything above is what Router does for every account today. Service levels are agreed per account in the order form; ask us for specifics on your workload and we will answer concretely, in writing."),
    (R, '<li>Pin a model id, or send <code>"model": "auto"</code> and let routing decide</li>',
     "<li>Name the model by its vendor id; <code>GET /v1/models</code> lists what a key may call</li>"),
    (R, "<p>Errors, rate limits and timeouts trip a circuit breaker and the request is re-issued to a healthy provider under a retry budget, so one provider's bad hour does not become your outage.</p>",
     '<p>The error reaches you in the OpenAI shape, with its HTTP status and a request id, so the retry logic in your client keeps working. Failover between providers is set up per account where it is needed; <a href="/reliability">Reliability</a> says what Router does today.</p>'),
    (R, "Errors, rate limits and timeouts trip a circuit breaker and the request is re-issued to a healthy provider under a retry budget, so one provider's bad hour does not become your outage.",
     "The error reaches you in the OpenAI shape, with its HTTP status and a request id, so the retry logic in your client keeps working. Failover between providers is set up per account where it is needed; Reliability says what Router does today."),
    (R, "Access is invite-only: <a", "Accounts are opened by our team: <a"),
    (R, "Access is invite-only: tell us", "Accounts are opened by our team: tell us"),
    (R, "we come back with an access plan and a quote", "we come back with an account and a quote"),
    (R, '<a class="btn btn-grad" href="/about#contact">Request access</a>', '<a class="btn btn-grad" href="/about#contact">Open an account</a>'),
    (R, '<a class="btn btn-primary" href="/about#contact">Request access</a>', '<a class="btn btn-primary" href="/about#contact">Open an account</a>'),
    (R, '<a class="pbar-cta" href="/about#contact">Request access</a>', '<a class="pbar-cta" href="/about#contact">Open an account</a>'),
    # --- /reliability
    ("reliability.html", "LLM Failover: How Runix Handles Provider Outages | Runix", "When a Provider Fails: Runix Router Reliability | Runix"),
    ("reliability.html", "How Runix Router handles a failing provider: circuit breakers, retry budgets and mid-stream failover. No published SLA during early access.",
     "What Runix Router does when a provider fails: OpenAI-style errors with request ids, pass-through streams, per-account failover. No public uptime figure."),
    ("reliability.html", "A gateway earns its place on the bad days. This is the mechanism, described plainly, not a status page, and not a service level agreement.",
     "What Router does when a model provider has a bad hour, described plainly: not a status page, and not a service level agreement."),
    ("reliability.html", "bring them to the intake. We will tell you plainly whether early access fits, before you spend time on an evaluation.",
     "bring them to the first conversation. We will tell you plainly what we can commit to, before you spend time on an evaluation."),
]
FIVE_OLD = ("in early access and running traffic, is one OpenAI-compatible API in front of every provider, "
            "with central key custody, per-key quotas, and failover that fires mid-request with streaming preserved.")
FIVE_NEW = ("available today, is one OpenAI-compatible API in front of every provider, with central key "
            "custody, per-key quotas, and a log of every request with its cost.")
AUTO1_OLD = "an explicit id pins the model, and failover stays within the providers that serve it."
AUTO1_NEW = "every request names its model by the vendor's id, and failover between providers is set up per account."
AUTO2_OLD = "On Router, <code>auto</code> chooses by cost, health and the policy attached to the key,"
AUTO2_NEW = "On a router that offers it, <code>auto</code> chooses by cost, health and the policy attached to the key,"
AUTO3_OLD = "Whether a router does this is a question to ask it; Runix documents failover as provider to provider."
AUTO3_NEW = "Whether a router does this is a question to ask it; Runix Router does not choose a model for you."
AUTO4_OLD = ("Runix Router is in early access. It accepts <code>auto</code> or an explicit model id on every request, "
             "applies allowed models and routing per key,")
AUTO4_NEW = "Runix Router is available. It takes the vendor's model id on every request, applies allowed models per key,"
AUTO5_OLD = "There is no published SLA during early access; the failover mechanism is documented rather than promised."
AUTO5_NEW = "Service levels are agreed per account in the order form."
B = "blog/"
EDITS += [
    (B + "why-five-layers.html", FIVE_OLD, FIVE_NEW),
    ("tools/posts/why-five-layers.json", j(FIVE_OLD), j(FIVE_NEW)),
    (B + "llm-router-vs-llm-gateway.html",
     "model selection, health-aware dispatch and mid-request failover on the decision side.",
     "the model named on every request, sent to the provider that serves it, and failover between providers where an account sets it up, on the decision side."),
    (B + "llm-router-vs-llm-gateway.html",
     "anyone can store a key; keeping a stream alive through a provider's bad hour is the part that earns the name.",
     "anyone can store a key; getting each request to the provider that serves its model, and saying plainly what happened when it fails, is the part that earns the name."),
    (B + "llm-router-vs-llm-gateway.html",
     "is in early access — one OpenAI-compatible endpoint with routing, mid-request failover and per-request cost tracking.",
     "is available — one OpenAI-compatible endpoint with per-key controls and per-request cost tracking."),
    (B + "introducing-runix.html",
     "and you get automatic retries, provider failover, model routing, rate-limit handling, and per-key usage and cost tracking. When a provider degrades, the gateway routes around it.",
     "and you get one key for every model, per-key quotas and allowlists, and per-key usage and cost tracking."),
    (B + "introducing-runix.html", "We run the gateway to a high-availability target, and a public status page is on the roadmap.",
     "A public status page is on the roadmap."),
]
for f in (B + "auto-routing-versus-a-pinned-model-id.html", "tools/posts/auto-routing-versus-a-pinned-model-id.json"):
    q = j if f.endswith(".json") else (lambda s: s)
    EDITS += [(f, q(o), q(n)) for o, n in ((AUTO1_OLD, AUTO1_NEW), (AUTO2_OLD, AUTO2_NEW), (AUTO3_OLD, AUTO3_NEW),
                                           (AUTO4_OLD, AUTO4_NEW), (AUTO5_OLD, AUTO5_NEW))]
