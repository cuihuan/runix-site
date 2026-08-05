#!/usr/bin/env python3
"""Draft the open-source gateway continuity post into scheduled/ — NOT published.

Every claim here was read from a primary source: the project's own LICENSE
file, its own commit history, its own docs, or the acquirer's own press
release. Nothing comes from a secondary summary, and the one widely-repeated
claim that has no primary source (TensorZero returning capital) is left out.

Deliberately left unpublished. Naming competitors is a positioning decision,
not an engineering one, and this repo's standing rule puts competitor
comparison content behind founder approval. The draft is finished so that
publishing is one command if that approval comes:

    python3 tools/publish.py open-source-gateway-continuity

If it is never published, nothing is lost: OSS-LANDSCAPE.md keeps the research.
"""
import json
import os
import pathlib
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

SITE = "https://runixcloud.io"
SLUG = "open-source-gateway-continuity"
TITLE = "Will your gateway still be there in a year? — Runix"
H1 = "The licence on your gateway is a dependency"
DESC = ("Open-source AI gateways change licences, gate the features you need, and get "
        "acquired. Five checks to run before you build on one.")

L_ELASTIC = "https://github.com/vllora/vllora/blob/main/LICENSE.md"
L_LITELLM = "https://github.com/BerriAI/litellm/blob/main/LICENSE"
L_LITELLM_COMMIT = "https://github.com/BerriAI/litellm/commit/a9e79c8d4645f963c642387e2fef9b8c5474765e"
L_HELI_COMMIT = "https://github.com/Helicone/ai-gateway/commit/9649b27bdc9fb0907d359e899894102a15f3a085"
L_MINTLIFY = "https://www.mintlify.com/blog/mintlify-acquires-helicone"
L_PANW = "https://www.paloaltonetworks.com/company/press/2026/palo-alto-networks-completes-acquisition-of-portkey-to-secure-ai-agents"
L_TZ = "https://github.com/tensorzero/tensorzero"
L_KONG_PLUGINS = "https://github.com/Kong/kong/tree/master/kong/plugins"
L_KONG_ADV = "https://developer.konghq.com/plugins/ai-proxy-advanced/"
L_APISIX_MULTI = "https://apisix.apache.org/docs/apisix/plugins/ai-proxy-multi/"
L_HELI_SELFHOST = "https://www.helicone.ai/blog/self-hosting-journey"
L_LITELLM_PROD = "https://docs.litellm.ai/docs/proxy/prod"
L_ENVOY_PREREQ = "https://aigateway.envoyproxy.io/docs/getting-started/prerequisites"

BODY = f"""<p>Choosing an open-source gateway is usually framed as a feature question. It is
mostly a continuity question. The features you can evaluate in an afternoon; whether the
project will still be there, still be licensed the way it is today, and still ship the
capability you depend on — that is what actually decides whether the choice was right,
and it is much harder to check.</p>

<p>Here is what to check, and what checking it turns up right now. Every claim below links
to the licence file, commit or announcement it came from, because these things move.</p>

<h2>1. Read the licence file, not the badge</h2>

<p>The licence shown on a repository page is a guess made by a classifier. It is wrong often
enough to matter.</p>

<p><a href="{L_LITELLM}">LiteLLM's LICENSE</a> opens with: <q>Portions of this software are
licensed as follows: * All content that resides under the "enterprise/" directory of this
repository, if that directory exists, is licensed under the license defined in
"enterprise/LICENSE".</q> Everything else is MIT. The <code>enterprise/</code> licence is
proprietary and forbids production use without a subscription. GitHub cannot classify a
modified preamble, so it reports the repository as "Other" rather than MIT — which is
accurate, and easy to skim past. That carve-out was <a href="{L_LITELLM_COMMIT}">added in
February 2024</a>; the project was plain MIT before it.</p>

<p>The sharper case is a project whose licence forbids the thing you want to do with it. The
gateway formerly published as LangDB, now <a href="{L_ELASTIC}">vllora</a>, is under the
Elastic License 2.0, which states: <q>You may not provide the software to third parties as a
hosted or managed service, where the service provides users with access to any substantial
set of the features or functionality of the software.</q> If your plan is to run it for other
people, that is the plan disallowed. It is listed as Apache-2.0 in several widely-copied
"awesome" lists. The repository has never had an Apache licence at its root.</p>

<p><strong>What to do:</strong> open the LICENSE file itself, and check <code>git log</code>
on that file. A licence with a history is a licence that can have more history.</p>

<h2>2. Licences change, and they change in one direction</h2>

<p>In this category, over roughly two years: LiteLLM added a proprietary directory to an MIT
project. Helicone's Rust gateway went <a href="{L_HELI_COMMIT}">from Apache-2.0 to GPL-3.0 in
November 2025</a> — and that licence change is the last commit the repository has received.
new-api went MIT to Apache-2.0 to a custom dual licence to AGPL-3.0, four licences in two
years.</p>

<p>None of these is wrong of the project to do. Maintainers get to change terms on new
versions, and most of these changes were made to fund the work. The point is that a licence
is a term of your dependency, not a property of it, and the direction of travel is
consistently toward more restriction, not less.</p>

<p><strong>What to do:</strong> put a quarterly reminder on re-reading the LICENSE file of
anything you depend on commercially. It costs a minute and it is the only way you find out
before an upgrade forces the question.</p>

<h2>3. "Open source" and "the part you need is open source" are different claims</h2>

<p>Kong AI Gateway is genuinely Apache-2.0. The Apache-licensed tree ships
<a href="{L_KONG_PLUGINS}">six <code>ai-*</code> plugins</a>; the plugin catalogue lists
roughly twenty-three. The <a href="{L_KONG_ADV}">plugin that does multi-provider load
balancing and failover</a> — the thing most people mean when they say "AI gateway" — carries
an enterprise tier marker. So does semantic caching, and so does token-based rate limiting.</p>

<p>By contrast, Apache APISIX ships <a href="{L_APISIX_MULTI}"><code>ai-proxy-multi</code></a>
in its Apache-2.0 tree, described in its own docs as extending the basic proxy <q>with load
balancing, retries, fallbacks, and health checks</q>. Same capability, no tier.</p>

<p>Neither approach is dishonest. But "X is Apache-2.0" answers a question you were not
asking. The question is whether the specific capability you are adopting the project for is
in the tree you are licensed to use.</p>

<p><strong>What to do:</strong> list the three features you are actually adopting it for,
then find each one in the open-source source tree. Not the docs — the tree.</p>

<h2>4. Check whether the project and its paid edition are still the same software</h2>

<p>A subtler version of the same problem: the open-source edition and the commercial edition
can drift apart in version, not just in features. When the OSS changelog stops years behind
the enterprise changelog, "we're on the open-source build" starts to mean "we are on an old
build", and the security backport question becomes real.</p>

<p><strong>What to do:</strong> compare the newest OSS release tag with the newest enterprise
release, and the newest tag on the public container image with the commercial one. If they
have diverged by more than a minor version, ask what the OSS maintenance commitment actually
is, and get the answer in writing.</p>

<h2>5. Assume the vendor may not be independent next year</h2>

<p>Between March and June 2026, three projects in this category stopped being independent
concerns. <a href="{L_MINTLIFY}">Mintlify acquired Helicone</a>, stating that Helicone
<q>will continue operating in maintenance mode</q> and that they would <q>work closely with
every customer to support a smooth migration to another platform</q>.
<a href="{L_PANW}">Palo Alto Networks completed its acquisition of Portkey</a> in May.
<a href="{L_TZ}">TensorZero archived its repository</a> in June; its co-founder wrote that
the team <q>came to the difficult decision to wind down the project</q> and that the
repository <q>won't be actively maintained by the team moving forward</q>.</p>

<p>This is not a scandal. It is what a young, well-funded category does, and two of those
three are good outcomes for the people involved. But it does mean the question <em>"what
happens to us if this project stops moving"</em> is not hypothetical, and the honest answer
depends almost entirely on one thing: how much of your system knows it is talking to that
specific gateway.</p>

<p><strong>What to do:</strong> write down the exit. Not a plan — a paragraph. Which of your
services would need to change, how long the change takes, and whether you have the data to
reproduce your current routing and spend attribution somewhere else. If that paragraph is
hard to write, that difficulty <em>is</em> the lock-in, and it exists whether or not you
self-host.</p>

<h2>6. Cost the operation, not the licence</h2>

<p>Self-hosting is free in the sense that the software costs nothing. The operational floor
varies by more than an order of magnitude between projects, and the projects themselves are
the most reliable source on it.</p>

<p><a href="{L_HELI_SELFHOST}">Helicone</a>, describing its own rebuild: <q>Our original
self-hosting architecture required managing twelve separate containers with complex
configuration requirements.</q> They spent a month reducing it to four.
<a href="{L_LITELLM_PROD}">LiteLLM's production guide</a> is candid about where the ceiling
is: <q>At very high traffic (roughly 1000+ requests per second, or 10+ instances), spend
tracking itself becomes a database bottleneck.</q>
<a href="{L_ENVOY_PREREQ}">Envoy AI Gateway</a> requires <q>Kubernetes version 1.32 or
higher</q> and a matching Envoy Gateway version — there is no single-binary path at all.</p>

<p>Meanwhile several projects run from one container with an embedded database. The spread is
real, and it is knowable before you commit.</p>

<p><strong>What to do:</strong> before evaluating features, read the production deployment
page and write down every stateful component it requires. That list is your actual on-call
surface, and it is the number to compare against a managed price — not the licence fee,
which is zero on both sides of the comparison you are trying to make.</p>

<h2>The short version</h2>

<ol>
<li>Open the LICENSE file. Check its history.</li>
<li>Find your three must-have features in the open-source tree, not the docs.</li>
<li>Compare the OSS release cadence with the commercial one.</li>
<li>Write the exit paragraph. Its difficulty is your lock-in.</li>
<li>Count the stateful components before you count the features.</li>
</ol>

<p>None of this argues against self-hosting. Plenty of teams should self-host, and some of
these projects are excellent. It argues against choosing on features alone, because features
are the part that does not change when a licence does, when a capability turns out to be
enterprise-only, or when the company is acquired.</p>

<p>If you would rather not carry that evaluation at all, that is what a managed gateway is
for, and <a href="/router">Runix Router</a> is ours. But the checks above are worth running
either way — including on us. Ask what happens to your traffic and your usage history if you
leave, and expect a straight answer.</p>

<p class="note-line">Every licence, commit and announcement referenced above was read
directly from its primary source on 6 August 2026. Repositories and terms change; check the
links before relying on any of it.</p>
"""

template = pathlib.Path("blog/model-deprecation-without-a-redeploy.html").read_text()
url = f"{SITE}/blog/{SLUG}"

page = template
page = re.sub(r"<title>.*?</title>", f"<title>{TITLE}</title>", page, count=1)
for prop, val in (("description", DESC),):
    page = re.sub(rf'(<meta name="{prop}" content=")[^"]*(">)', rf"\g<1>{val}\g<2>", page, count=1)
page = re.sub(r'(<link rel="canonical" href=")[^"]*(">)', rf"\g<1>{url}\g<2>", page, count=1)
page = re.sub(r'(<meta property="og:title" content=")[^"]*(">)', rf"\g<1>{TITLE}\g<2>", page, count=1)
page = re.sub(r'(<meta property="og:description" content=")[^"]*(">)', rf"\g<1>{DESC}\g<2>", page, count=1)
page = re.sub(r'(<meta property="og:url" content=")[^"]*(">)', rf"\g<1>{url}\g<2>", page, count=1)
page = re.sub(r'(<meta name="twitter:title" content=")[^"]*(">)', rf"\g<1>{TITLE}\g<2>", page, count=1)
page = re.sub(r'(<meta name="twitter:description" content=")[^"]*(">)', rf"\g<1>{DESC}\g<2>", page, count=1)


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
print("  NOT published. Publishing names competitors, which is a founder decision.")
print(f"  when approved: python3 tools/publish.py {SLUG}")
