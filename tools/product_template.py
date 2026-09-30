#!/usr/bin/env python3
"""One template for the seven product pages (2026-09-30 redesign, v2).

Design: the canvas "Runix Lab Site Redesign", artboard 04. Every product page
gets the same shell around the copy it already has:

  * a product bar under the header: name, layer, status, the page's sections,
    the primary action (sticky, so the reader always knows where they are);
  * one hero: copy on the left, an at-a-glance panel on the right; the code
    sample a page used to carry in its hero moves to an example band below;
  * numbered sections, in one order: overview, capabilities, how it works,
    specifications, works with, how to start, questions, close;
  * a specifications table and a works-with block (the layers above and
    below, linked) on every page; a how-to-start block on the pages that
    lacked one.

The prose sections that were fact-checked stay where they are; the template
adds around them. Content comes from PRODUCTS below and is written only from
what the site already states elsewhere. Idempotent: generated blocks carry
markers and are re-rendered on every run. Run from the site root, after
flagship_nav.py and stack_build.py.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from stack import PRODUCTS as STACK, LAYER_OF  # noqa: E402

CURL = '''<div class="term">
        <div class="term-bar"><i></i><i></i><i></i><b>one request, any model</b></div>
<pre>$ curl https://api.router.runixcloud.io/v1/chat/completions \\
    -H <span class="g">"Authorization: Bearer $RUNIX_API_KEY"</span> \\
    -d <span class="g">'{"model": "auto",
         "messages": [{"role": "user", "content": "Hello"}]}'</span></pre>
      </div>'''

PRODUCTS = {
    "router": {
        "sub": "The control plane between your product and the model providers: central key custody, written data terms, and failover that fires mid-request, behind one OpenAI-compatible API.",
        "note": 'Evaluation credits on request; no card, nothing to install. Billing is usage-based in USD, <a href="/plans">quoted per workload</a>.',
        "glance": [
            ("Interface", "OpenAI-compatible API"),
            ("Endpoint", '<code>api.router.runixcloud.io/v1</code>'),
            ("Keys", "Per key: quota, limits, allowed models, routing"),
            ("Failover", "Mid-request, streaming preserved"),
            ("Data terms", "Content never used for training"),
            ("Billing", "Usage-based, USD, itemised"),
            ("Contracting", "Runix AI Inc &middot; MSA &amp; DPA on request"),
            ("Status", "Early access, running traffic"),
        ],
        "example": (CURL, "one request, any model",
                    'An OpenAI-compatible request. <code>"auto"</code> lets Router choose by cost, health and your key\'s policy; an explicit model id pins the model, and failover stays within the providers that serve it.'),
        "specs": [
            ("API surface", "Chat completions and model listing, with server-sent events for streaming", '<a href="/docs/router">Router quickstart</a>'),
            ("Model selection", '<code>"auto"</code>, or an explicit model id', '<a href="/docs/router">Router quickstart</a>'),
            ("Failover", "Provider to provider, mid-request, streaming preserved", '<a href="/reliability">Reliability</a>'),
            ("Limits", "Per key: rate limits, quotas and allowed models, revocable without a redeploy", '<a href="/access">Access</a>'),
            ("Errors", "OpenAI-style error envelope, with a request id on every response", '<a href="/docs/router">Router quickstart</a>'),
            ("Data handling", "Content processed to serve the request; operational metadata kept for billing and support", '<a href="/privacy">Privacy Policy</a> and <a href="/security">Security</a>'),
            ("Transport", "TLS 1.3 and 1.2; 1.0 and 1.1 refused", '<a href="/security">Security</a>'),
            ("Service level", "No published SLA during early access; the failover mechanism is documented", '<a href="/reliability">Reliability</a>'),
            ("Billing", "Usage-based in USD, per token or per request by model; prepaid balance or invoice", '<a href="/plans">Pricing</a>'),
        ],
        "with": [
            ("Above &middot; 05 Applications", "Runix Code and Runix Comic", "Call every model through Router, so the application never changes when a provider does.", "/#layer-applications", "See the applications"),
            ("Below &middot; 03 Models", "Runix Models", "A model tuned on your data sits behind Router next to the hosted providers, on dedicated capacity.", "/models", "Explore Runix Models"),
            ("The whole stack", "Five layers, seven products", "How Router fits with data, storage and the applications on top.", "/#platform", "See the stack"),
        ],
        "start": [
            ("Tell us what you are building", "Models, expected volume, latency needs. We reply within one business day and set the account up."),
            ("Evaluate before you pay", "Evaluation credits on request, full router functionality, no card. Integration is a base-URL change."),
            ("Go to production in writing", "Rates stated before you commit; MSA and DPA on request; prepaid balance or invoice, in USD."),
        ],
        "labels": {"three things that block": "Capabilities", "bad hour": "How it works"},
    },
    "models": {
        "glance": [
            ("What", "Fine-tuning and dedicated serving of open-weight models"),
            ("Base models", "Qwen, Llama, Mistral, Gemma, DeepSeek; licence checked first"),
            ("Methods", "Supervised fine-tuning, LoRA and QLoRA, DPO"),
            ("Evaluation", "Held-out set, against the model you run today"),
            ("Serving", "Single-tenant, OpenAI-compatible; behind Runix Router if you use it"),
            ("Runs in", "Your cloud account, or capacity arranged per engagement"),
            ("Your data", "Trains the model you commission, and nothing else"),
            ("Status", "Early access, by engagement"),
        ],
        "example": (None, "engagement spec (example)", "An illustrative spec, not a product API. Every field is agreed per engagement before any training starts: the base model and its licence, the method, where the data comes from, the baseline the evaluation is measured against, and where the model is served."),
        "specs": [
            ("Base model families", "Open-weight families whose licences permit your use, for example Qwen, Llama, Mistral, Gemma and DeepSeek", '<a href="/models#what-we-tune">What we tune</a>'),
            ("Tuning methods", "Supervised fine-tuning; LoRA and QLoRA; preference tuning with DPO", "This page"),
            ("Evaluation", "Task-specific held-out sets; before-and-after against the model you run today", "This page"),
            ("Serving", "Dedicated, single-tenant; quantised variants only where the evaluation shows quality holds", "This page"),
            ("Interface", "OpenAI-compatible API; can sit behind Runix Router next to hosted providers", '<a href="/router">Runix Router</a>'),
            ("Weights and access", "Set in the engagement contract before training starts", "This page"),
            ("Data use", "The data you provide trains and evaluates the model you commission, and nothing else", '<a href="/terms">Terms of Service, section 5</a>'),
            ("Pricing", "Per engagement, quoted after scoping and before any training starts", '<a href="/plans">Pricing</a>'),
        ],
        "with": [
            ("Above &middot; 04 Gateway", "Runix Router", "The tuned model answers through the same OpenAI-compatible endpoint as the hosted providers.", "/router", "Explore Runix Router"),
            ("Below &middot; 02 Data", "Runix Data", "Training and evaluation sets in six domains, delivered with provenance and a quality report.", "/data", "Explore Runix Data"),
            ("The whole stack", "Five layers, seven products", "How Models fits between the data it learns from and the gateway it answers through.", "/#platform", "See the stack"),
        ],
        "labels": {"From base model": "Capabilities", "Where it sits": "How it works", "What we tune": "Models", "When a tuned model": "Fit", "early access works": "How to start"},
    },
    "data": {
        "glance": [
            ("Domains", "Code (the focus), finance, cybersecurity, legal, embodied AI, AI for Science"),
            ("Every record", "Provenance and licence recorded"),
            ("Every delivery", "A quality report: coverage, duplication, what was dropped and why"),
            ("Personal data", "Masked before training; fails closed"),
            ("Evaluation", "Split from training data by source"),
            ("Tooling", "Runix Pipeline"),
            ("Pricing", "Per project or by volume, quoted first"),
            ("Status", "Early access, by engagement"),
        ],
        "example": (None, "example record", "An illustrative record. Every accepted record carries its source, its licence, the deduplication decision and the checks it passed; a dropped record carries the reason, and the quality report counts both."),
        "specs": [
            ("Domains", "Six, each with its own rules and the public standards they follow", '<a href="/data#domains">The domains</a>'),
            ("Inputs", "Data you provide or have the rights to use, or public sources whose licences permit your use", "This page"),
            ("Code tasks", "Run in a clean container: target tests pass with the patch and fail without it, and the rest of the suite still passes", '<a href="/code-data">Code data</a>'),
            ("Deliverables", "Files, a database or an endpoint; batch or continuous", "This page"),
            ("Quality report", "Coverage, duplication, extraction confidence, the checks each record passed, and what was dropped and why", "This page"),
            ("Personal data", "Identified and masked before a training set; a record that cannot be cleared is held back", "This page"),
            ("Evaluation data", "Split from training data by source, so near-duplicates cannot sit on both sides", "This page"),
            ("Pricing", "Per project or by volume, quoted before any work starts", '<a href="/plans">Pricing</a>'),
        ],
        "with": [
            ("Above &middot; 03 Models", "Runix Models", "The training and evaluation sets go into a model tuned to your task.", "/models", "Explore Runix Models"),
            ("Same layer &middot; 02 Data", "Runix Pipeline", "The tooling every Data engagement runs on: six stages, each one auditable.", "/pipeline", "Explore Runix Pipeline"),
            ("Below &middot; 01 Infrastructure", "Runix FS", "Where the raw material is read from: one path over the object storage you already run.", "/fs", "Explore Runix FS"),
        ],
        "labels": {"Six domains": "Domains", "Domain judgement": "How it works", "every delivery": "Deliverables", "early access works": "How to start"},
    },
    "pipeline": {
        "sub": "The tooling behind Runix Data: six auditable stages that turn raw, duplicated, half-structured source material into something a model reads without choking, with a quality report at the end.",
        "note": 'Want the work done for you? That is <a href="/data">Runix Data</a>, the service built on this tooling.',
        "glance": [
            ("Stages", "Ingest, clean and dedupe, structure, mask, report, deliver"),
            ("Deduplication", "Exact, near and semantic"),
            ("Extraction", "LLM-assisted, into your schema, validated on the way out"),
            ("Masking", "Personal data masked before a model or a training set; fails closed"),
            ("Delivery", "Files, a database or an endpoint; batch or continuous"),
            ("Role", "The tooling Runix Data engagements run on"),
            ("Pricing", "Per project or by volume, quoted first"),
            ("Status", "In development, with design partners"),
        ],
        "specs": [
            ("Stages", "Ingest, clean and dedupe, structure, mask, report, deliver: each one leaves something you can inspect", '<a href="/docs/pipeline">Engagement guide</a>'),
            ("Deduplication", "Exact, near and semantic, with counts you can check", "This page"),
            ("Extraction", "LLM-assisted extraction into a schema you define, validated on the way out so malformed records fail loudly", "This page"),
            ("Masking", "Personal data identified and masked before it reaches a model or a training set; fails closed when detection is uncertain", "This page"),
            ("Quality report", "One per delivery: coverage, duplication rates, extraction confidence, and what was dropped and why", '<a href="/docs/pipeline">Engagement guide</a>'),
            ("Delivery", "Files, a database or an endpoint; batch or continuous", "This page"),
            ("Pricing", "Per project or by volume, quoted before work starts", '<a href="/plans">Pricing</a>'),
        ],
        "with": [
            ("Same layer &middot; 02 Data", "Runix Data", "The service built on this tooling, with the rules for six domains on top.", "/data", "Explore Runix Data"),
            ("Above &middot; 03 Models", "Runix Models", "Where model-ready data goes next: a model tuned to your task.", "/models", "Explore Runix Models"),
            ("Below &middot; 01 Infrastructure", "Runix FS", "Where the raw material is read from: one path over your object storage.", "/fs", "Explore Runix FS"),
        ],
        "start": [
            ("Send a sample and what you need", "A slice of the real data, not a description of it, and what has to come out. We reply within one business day."),
            ("Get a scoped plan", "Stages, trade-offs and what we will not attempt, with the price, before any work starts."),
            ("Receive the data and the report", "Batch or continuous, in the form your downstream consumes, with a quality report every time."),
        ],
        "labels": {"Six stages": "Capabilities"},
    },
    "fs": {
        "glance": [
            ("Interfaces", "FUSE, Hadoop-compatible client, Java, Python and Rust SDKs, Kubernetes CSI"),
            ("Storage", "S3-compatible object storage; paths map one-to-one to object keys"),
            ("Cache", "Memory, SSD and HDD tiers on the workers"),
            ("Metadata", "Masters replicated with Raft"),
            ("Mount modes", "Cache mode, or file-system mode with background sync"),
            ("Runs in", "Your AWS, Google Cloud or Azure account"),
            ("Built on", "Curvine: Apache 2.0, CNCF Sandbox"),
            ("Status", "Early access, per deployment"),
        ],
        "example": (None, "mount an existing bucket", "Three commands: attach the bucket to the namespace, expose it as a local directory, and read it as a path. Nothing in the training code changes."),
        "specs": [
            ("Interfaces", "FUSE mount; Hadoop-compatible client; Java, Python and Rust SDKs; Kubernetes CSI driver", '<a href="/docs/fs">Quick start</a>'),
            ("Object storage", "S3-compatible; the bucket keeps its layout and stays independently readable", "This page"),
            ("Cache tiers", "Memory, SSD and HDD, written to the fastest available tier first", "This page"),
            ("Metadata", "Masters replicated with Raft", "This page"),
            ("Mount modes", "Cache mode: the bucket is the source of truth and writes pass through. File-system mode: operations complete in the cluster, then sync to the bucket", '<a href="/docs/fs">Quick start</a>'),
            ("Kubernetes", "The CSI driver provisions ReadWriteMany volumes by creating a directory, not by calling a cloud API", '<a href="/docs/fs">Quick start</a>'),
            ("Deployment", "Sized and deployed with you, in your own cloud account; supported under contract with Runix AI Inc", "This page"),
            ("Published results", "The Curvine project's own figures, labelled as such; not a Runix service level", '<a href="/fs#published-results">Published results</a>'),
            ("Pricing", "Quoted per deployment during early access", '<a href="/plans">Pricing</a>'),
        ],
        "with": [
            ("Above &middot; 02 Data", "Runix Data and Runix Pipeline", "Raw material is read through the file system before it is cleaned.", "/data", "Explore Runix Data"),
            ("Above &middot; 03 Models", "Runix Models", "Training reads datasets and checkpoints through one path instead of waiting on the bucket.", "/models", "Explore Runix Models"),
            ("Below &middot; 00 Compute", "Your own cloud", "GPUs, object storage and Kubernetes in your account. The file system runs on them and replaces none of them.", "/#platform", "See the stack"),
        ],
        "labels": {"Object-storage economics": "Capabilities", "Where it sits": "How it works", "Your code does not change": "Integration", "workloads that stall": "Workloads", "project has measured": "Results", "Open source": "Open source", "early access works": "How to start"},
    },
    "code": {
        "sub": "An AI coding agent being built for teams: grounded in your repository, agentic where that saves time, gated by human review where it must be, with the controls an organisation needs to roll it out safely.",
        "note": 'Team plans are set out on <a href="/code-plans">the Code plans page</a>.',
        "glance": [
            ("What", "An AI coding agent for teams"),
            ("Grounding", "Your repository: modules, idioms, the versions you run"),
            ("Changes", "Every change lands as a reviewable diff"),
            ("Team controls", "Seats, per-key limits, usage attribution by developer"),
            ("Models", "Reached through Runix Router"),
            ("Plans", "Four team plans, on the Code plans page"),
            ("Status", "In development, waitlist open"),
        ],
        "specs": [
            ("Assistance", "Codebase-aware completion and chat, in the editor and on the command line", '<a href="/docs/code">Rollout guide</a>'),
            ("Tasks", "Multi-file implement, refactor and test from one instruction", "This page"),
            ("Review gates", "Every change lands as a reviewable diff, never a silent write", "This page"),
            ("Team controls", "Seats, per-key limits, usage attribution by developer", '<a href="/docs/code">Rollout guide</a>'),
            ("Models", "Reached through Runix Router, so a provider change does not touch the tool", '<a href="/router">Runix Router</a>'),
            ("Plans", "Four team plans", '<a href="/code-plans">Code plans</a>'),
            ("Availability", "In development; waitlist cohorts", '<a href="/docs/code">Rollout guide</a>'),
        ],
        "with": [
            ("Below &middot; 04 Gateway", "Runix Router", "Every model call goes through one endpoint, with keys and quotas beneath it.", "/router", "Explore Runix Router"),
            ("Same layer &middot; 05 Applications", "Runix Comic", "The other application on the stack: a studio for comic dramas.", "/comic", "Explore Runix Comic"),
            ("The whole stack", "Five layers, seven products", "How the applications sit on the gateway, models, data and storage beneath them.", "/#platform", "See the stack"),
        ],
        "start": [
            ("Join the waitlist", "Tell us the team size and the repositories. Cohorts are invited in order."),
            ("Set up seats and policies", "Seats, per-key limits and review gates configured with you, following the rollout guide."),
            ("Roll out under review", "Every change lands as a reviewable diff, so the team keeps its review habits from day one."),
        ],
        "labels": {"Assistance, agency": "Capabilities", "Who it is for": "Fit"},
    },
    "comic": {
        "sub": "An AI studio for comic dramas that is being built around the whole job: writing and boarding the story, producing the episode, and getting it published and seen. Not just generating pictures.",
        "note": 'Built stage by stage with waitlist cohorts; the <a href="/docs/comic">workflow guide</a> says what you bring and what the studio generates.',
        "glance": [
            ("What", "An AI studio for comic dramas"),
            ("Stages", "Pre-production, production, publishing"),
            ("Pre-production", "Scripts, episode plans, consistent characters, storyboards"),
            ("Production", "Styled panels, motion and camera, voice, music, subtitles"),
            ("Publishing", "Vertical cuts and full episodes, for the platforms you name"),
            ("Models", "Reached through Runix Router"),
            ("Status", "In development, waitlist open"),
        ],
        "specs": [
            ("Pre-production", "Script and episode planning, character sheets that hold across scenes, storyboards from the script", '<a href="/docs/comic">Workflow guide</a>'),
            ("Production", "Styled panels that keep one look, motion and camera, AI voice-over, music, multi-language subtitles", "This page"),
            ("Publishing", "Vertical short-video cuts and full episodes from one project", "This page"),
            ("Models", "Reached through Runix Router", '<a href="/router">Runix Router</a>'),
            ("Availability", "In development; waitlist cohorts", '<a href="/docs/comic">Workflow guide</a>'),
        ],
        "with": [
            ("Below &middot; 04 Gateway", "Runix Router", "Every model call goes through one endpoint, with keys and quotas beneath it.", "/router", "Explore Runix Router"),
            ("Same layer &middot; 05 Applications", "Runix Code", "The other application on the stack: a reviewable coding agent.", "/code", "Explore Runix Code"),
            ("The whole stack", "Five layers, seven products", "How the applications sit on the gateway, models, data and storage beneath them.", "/#platform", "See the stack"),
        ],
        "start": [
            ("Join the waitlist", "Tell us what you make and where it is published."),
            ("Bring a script", "Cohorts start from a real script; the workflow guide says what you bring and what the studio generates."),
            ("Produce and publish", "Episodes are built stage by stage and exported for the platforms you name."),
        ],
        "labels": {"whole production line": "Capabilities", "Who it is for": "Fit"},
    },
}


def block(name, body):
    return f"<!--pt:{name}-->\n{body}\n<!--/pt:{name}-->"


def strip_blocks(doc):
    return re.sub(r"[ \t]*<!--pt:([a-z-]+)-->.*?<!--/pt:\1-->\n?", "", doc, flags=re.S)


def div_end(text, start):
    depth = 0
    for m in re.finditer(r"<div\b|</div>", text[start:]):
        depth += 1 if m.group(0) != "</div>" else -1
        if depth == 0:
            return start + m.end()
    raise ValueError("unbalanced div")


def glance_html(rows):
    dl = "\n".join(f'        <div><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows)
    return block("glance", f'''      <div class="glance">
        <p class="glance-title">At a glance</p>
        <dl>
{dl}
        </dl>
      </div>''')


def hero_from_page_hero(doc, key, c):
    """Turn the centred page hero into the split hero of the template."""
    i = doc.find('<div class="page-hero center">')
    if i < 0:
        return doc, False
    j = div_end(doc, i)
    hero = doc[i:j]
    eyebrow = re.search(r'<div class="prod-eyebrow">.*?</span></div>', hero, re.S).group(0)
    h1 = re.search(r"<h1>.*?</h1>", hero, re.S).group(0)
    primary = re.search(r'(<!--email_off-->)?<a class="btn btn-primary"[^>]*>[^<]*</a>(<!--/email_off-->)?', hero).group(0)
    docs = re.search(r'<a class="btn btn-ghost" href="/docs/[^"]*">[^<]*</a>', hero).group(0)
    new = f'''<section class="split-hero" id="overview">
  <div class="container">
    <div>
      {eyebrow}
      {h1}
      <p class="sub">{c["sub"]}</p>
      <div class="actions">
        {primary}
        {docs}
      </div>
      <p class="hero-note">{c["note"]}</p>
    </div>
    <div>
{glance_html(c["glance"])}
    </div>
  </div>
</section>'''
    return doc[:i] + new + doc[j:], True


def hero_from_split(doc, key, c):
    """Replace the split hero's right column with the panel; return the old one."""
    i = doc.find('<section class="split-hero"')
    if i < 0:
        raise ValueError(f"{key}: no hero")
    if 'id="overview"' not in doc[i:i + 60]:
        doc = doc[:i] + '<section class="split-hero" id="overview">' + doc[doc.index(">", i) + 1:]
    end = doc.index("</section>", i)
    cont = doc.index('<div class="container">', i)
    # the two columns are the container's direct children
    first = doc.index("\n    <div>", cont)
    first_end = div_end(doc, first + 1)
    second = doc.index("\n    <div>", first_end)
    second_end = div_end(doc, second + 1)
    old = doc[second + 1:second_end]
    inner = old[old.index(">") + 1:old.rindex("</div>")]
    term = re.search(r'<div class="term">.*?</pre>\n\s*</div>', inner, re.S)
    term = term.group(0) if term else None
    new = f'    <div>\n{glance_html(c["glance"])}\n    </div>'
    doc = doc[:second + 1] + new + doc[second_end:]
    return doc, term


def example_html(term, title, caption, num):
    return block("example", f'''<section class="section example-band" id="example">
  <div class="container">
    <div class="example-grid">
      {term}
      <div class="example-note">
        <p class="sec-no">{num:02d} &middot; Example</p>
        <p class="example-title">{title}</p>
        <p>{caption}</p>
      </div>
    </div>
  </div>
</section>''')


def specs_html(rows, name):
    trs = "\n".join(f"          <tr><th scope=\"row\">{k}</th><td>{v}</td><td>{w}</td></tr>" for k, v, w in rows)
    return block("specs", f'''<section class="section alt" id="specs">
  <div class="container">
    <div class="section-head center">
      <h2>The details a review asks for</h2>
      <p>One table, the same shape on every product page, kept current with the pages it points to.</p>
    </div>
    <div class="dsheet plain specs" tabindex="0" role="region" aria-label="{name} specifications">
      <table aria-label="{name} specifications">
        <thead><tr><th scope="col">Item</th><th scope="col">Value</th><th scope="col">Where it is documented</th></tr></thead>
        <tbody>
{trs}
        </tbody>
      </table>
    </div>
  </div>
</section>''')


def with_html(rows, name):
    cards = "\n".join(f'''      <a class="card card-clickable" href="{href}" aria-label="{cta}">
        <p class="card-layer">{layer}</p>
        <h3>{title}</h3>
        <p>{text}</p>
        <span class="read-more">{cta} &rarr;</span>
      </a>''' for layer, title, text, href, cta in rows)
    return block("with", f'''<section class="section" id="works-with">
  <div class="container">
    <div class="section-head center">
      <h2>The layers on either side</h2>
      <p>{name} hands off to its neighbours in the stack and works on its own. The same block sits on every product page, with the neighbours changed.</p>
    </div>
    <div class="grid cols-3 works">
{cards}
    </div>
  </div>
</section>''')


def start_html(steps, name):
    items = "\n".join(f'''      <div class="pstep">
        <h3><span class="pstep-n">{i:02d}</span>{t}</h3>
        <p>{p}</p>
      </div>''' for i, (t, p) in enumerate(steps, 1))
    return block("start", f'''<section class="section alt" id="start">
  <div class="container">
    <div class="section-head center">
      <h2>How to start</h2>
      <p>Three steps, each with a person on the other end: {name} is not self-serve.</p>
    </div>
    <div class="prun">
{items}
    </div>
  </div>
</section>''')


def bar_html(key, c, doc, primary):
    _, href, name, _line, layer, status, _tag = STACK[key]
    num, lname = LAYER_OF[layer]
    links = [("#capabilities", "Capabilities")]
    if 'id="how"' in doc:
        links.append(("#how", "How it works"))
    links += [("#specs", "Specs"), ("#works-with", "Works with")]
    links.append(("#early-access", "How to start") if 'id="early-access"' in doc else ("#start", "How to start"))
    links.append(("#faq", "Questions"))
    lis = "".join(f'<li><a href="{h}">{t}</a></li>' for h, t in links)
    live = " pbar-live" if status == "early access" else ""
    p_href, p_label = primary
    cta = f'<a class="pbar-cta" href="{p_href}">{p_label}</a>'
    if p_href.startswith("mailto:"):
        cta = f"<!--email_off-->{cta}<!--/email_off-->"
    return block("bar", f'''<nav class="pbar" aria-label="{name} on this page">
  <div class="container pbar-inner">
    <a class="pbar-name" href="#overview">{name}</a>
    <a class="pbar-layer" href="/#platform">{num:02d} &middot; {lname}</a>
    <span class="pbar-status{live}">{status.capitalize()}</span>
    <ul class="pbar-links">{lis}</ul>
    {cta}
  </div>
</nav>''')


def number_sections(doc, c):
    """A numbered label on every section head, in page order; 01 is the hero."""
    doc = re.sub(r'[ \t]*<p class="sec-no">[^<]*</p>\n', "", doc)
    main_a = doc.index('<main id="main">')
    main_b = doc.index("</main>")
    body = doc[main_a:main_b]
    n = 1
    out, pos = [], 0
    for m in re.finditer(r'<section class="([^"]*)"[^>]*>', body):
        sec_end = body.find("</section>", m.end())
        sec = body[m.start():sec_end]
        if "example-band" in m.group(1):
            n += 1
            sec = sec.replace('<p class="sec-no">', f'<p class="sec-no">', 1)
            sec = re.sub(r'<p class="sec-no">\d\d &middot;', f'<p class="sec-no">{n:02d} &middot;', sec)
        elif '<div class="section-head' in sec:
            n += 1
            h2 = re.search(r"<h2[^>]*>(.*?)</h2>", sec, re.S)
            text = re.sub(r"<[^>]+>", "", h2.group(1)) if h2 else ""
            label = None
            for needle, lab in c.get("labels", {}).items():
                if needle.lower() in text.lower():
                    label = lab
            if label is None:
                if "details a review" in text:
                    label = "Specifications"
                elif "either side" in text:
                    label = "Works with"
                elif text.startswith("How to start") or "early access works" in text:
                    label = "How to start"
                elif "Common questions" in text:
                    label = "Questions"
                elif "cta-band" in sec:
                    label = "Close"
                else:
                    label = "Capabilities" if n == 2 else text.split(",")[0][:24]
            head = re.search(r'<div class="section-head[^"]*">\n?', sec)
            ins = head.end()
            sec = sec[:ins] + f'      <p class="sec-no">{n:02d} &middot; {label}</p>\n' + sec[ins:]
        out.append(body[pos:m.start()])
        out.append(sec)
        pos = m.start() + len(sec)
    out.append(body[pos:])
    return doc[:main_a] + "".join(out) + doc[main_b:]


def main():
    changed = 0
    for key, c in PRODUCTS.items():
        page, href, name, *_ = STACK[key]
        p = pathlib.Path(page)
        doc = p.read_text(encoding="utf-8")
        orig = doc
        doc = strip_blocks(doc)
        doc = re.sub(r'[ \t]*<p class="sec-no">[^<]*</p>\n', "", doc)
        # hero
        term = None
        if '<div class="page-hero center">' in doc:
            doc, _ = hero_from_page_hero(doc, key, c)
        else:
            doc, term = hero_from_split(doc, key, c)
        if "example" in c:
            t, title, caption = c["example"]
            term = t or term
            if term:
                # after the strip that follows the hero, else right after the hero
                hero_end = doc.index("</section>", doc.index('<section class="split-hero"')) + len("</section>")
                strip = re.search(r'<div class="oss-strip".*?\n</div>\n', doc[hero_end:], re.S)
                ins = hero_end + strip.end() if strip and strip.start() < 10 else hero_end
                doc = doc[:ins] + "\n\n" + example_html(term, title, caption, 0) + doc[ins:]
        # section ids
        m = re.search(r'<section class="section[^"]*"(?![^>]*\bid=)>(?=\s*<div class="container">\s*<div class="section-head[^"]*">\s*<h2>Common questions</h2>)', doc)
        if m:
            doc = doc[:m.start()] + m.group(0)[:-1] + ' id="faq">' + doc[m.end():]
        for needle, sid in (("Where it sits", "how"), ("bad hour", "how"), ("Domain judgement", "how")):
            h = re.search(r'<section class="section[^"]*"(?![^>]*\bid=)>(?=\s*<div class="container">\s*<div class="section-head[^"]*">\s*<h2>[^<]*' + needle, doc)
            if h:
                doc = doc[:h.start()] + h.group(0)[:-1] + f' id="{sid}">' + doc[h.end():]
        # first content section after hero: capabilities
        hero_end = doc.index("</section>", doc.index('<section class="split-hero"')) + len("</section>")
        first = re.search(r'<section class="section(?: alt)?"(?![^>]*\bid=)>', doc[hero_end:])
        if first and 'id="capabilities"' not in doc:
            a = hero_end + first.start()
            doc = doc[:a] + first.group(0)[:-1] + ' id="capabilities">' + doc[hero_end + first.end():]
        # generated sections before the start section or the FAQ
        anchor = re.search(r'<section class="section[^"]*" id="early-access">', doc) or \
            re.search(r'<section class="section[^"]*" id="faq">', doc)
        gen = specs_html(c["specs"], name) + "\n\n" + with_html(c["with"], name)
        if "start" in c and 'id="early-access"' not in doc:
            gen += "\n\n" + start_html(c["start"], name)
        doc = doc[:anchor.start()] + gen + "\n\n" + doc[anchor.start():]
        # product bar, right after <main>
        primary = re.search(r'<a class="btn btn-primary" href="([^"]*)">([^<]*)</a>', doc)
        bar = bar_html(key, c, doc, (primary.group(1), primary.group(2)))
        doc = doc.replace('<main id="main">', '<main id="main" class="has-pbar">\n' + bar, 1) if 'class="has-pbar"' not in doc \
            else doc.replace('<main id="main" class="has-pbar">', '<main id="main" class="has-pbar">\n' + bar, 1)
        doc = number_sections(doc, c)
        if doc != orig:
            p.write_text(doc, encoding="utf-8")
            changed += 1
    print(f"product template: {changed} of {len(PRODUCTS)} page(s) changed")


if __name__ == "__main__":
    main()
