#!/usr/bin/env python3
"""Content pass 2026-11-27: AI Unix, rebuilt by AI; the benchmark and the FS up front.

The owner's brief: present Runix Lab as an AI-native company that rebuilds the
infrastructure AI runs on, with AI, as one simple system in the way Unix was
one; and give the open benchmark and Runix FS the weight in search they have
in the product. What changes:

  * the home page title, description, h1 and deck say "AI Unix" and
    "rebuilt by AI" in words a search engine and a buyer both read;
  * a home section puts the two things a team can try without talking to us,
    Runix Bench and Runix FS, side by side;
  * the Gateway band on the home page carries the Bench card, and every page
    that counts the products says eight;
  * the "How we are doing it" column and /about say what AI-native means
    here, literally: agents write, test and run most of the engineering, under
    human review and the same gates;
  * Runix FS gets a title and description written for the searches it should
    answer ("AI file system", "S3 cache for training").

Nothing here is a figure the site did not already publish or link. Idempotent:
every replacement checks its target first.
"""
import pathlib
import re
import sys

CHANGED = []


def edit(path, pairs):
    p = pathlib.Path(path)
    s = p.read_text(encoding="utf-8")
    o = s
    for old, new in pairs:
        if new in s:
            continue
        if old not in s:
            print(f"  {path}: target not found: {old[:70]!r}")
            continue
        s = s.replace(old, new)
    if s != o:
        p.write_text(s, encoding="utf-8")
        CHANGED.append(path)


HOME_TITLE_OLD = "Runix Lab — Runix, the Operating System for Enterprise AI"
HOME_TITLE = "Runix Lab — AI Unix: AI Infrastructure, Rebuilt by AI"
HOME_DESC_OLD = "Runix is the operating system for enterprise AI: five layers from the file system that keeps GPUs fed to the apps on top. Efficient, stable, enterprise-grade."
HOME_DESC = "Runix Lab is an AI-native company rebuilding AI infrastructure as one simple system, like Unix: file system, data, models, gateway, agents, open benchmark."

H1_OLD = '''<h1><span class="line">Runix. The operating system</span>
<span class="line">for enterprise AI.</span></h1>'''
H1 = '''<h1><span class="line">AI Unix.</span>
<span class="line">Infrastructure for AI, rebuilt by AI.</span></h1>'''
SUB_OLD = '''<p class="sub">Most teams start at the gateway: one OpenAI-compatible endpoint in front of every model provider, available today. Beneath it, the file system, data and model layers are in early access; the agents on top are in development. Use one layer, or run the whole stack.</p>'''
SUB = '''<p class="sub">Runix Lab is an AI-native company: agents write, test and run most of our engineering, under human review. We use them to rebuild the stack AI runs on as one simple system, the way Unix was one: a file system, data, models, one gateway and the agents on top, each small and each usable on its own. Start with the gateway, available today, or measure any gateway with our open benchmark.</p>'''

HOW_OLD = '''<p>What is in writing is linked, not promised: data terms, contracting, the price catalogue and the roadmap. Three of the tools we built to run a gateway are open source, including a benchmark you can run against us.</p>'''
HOW = '''<p>What is in writing is linked, not promised: data terms, contracting, the price catalogue and the roadmap. Three of the tools we built to run a gateway are open source, including <a href="/bench">a benchmark you can run against us</a>.</p>
        <p>And we build it AI-native. Agents write, test and operate most of this stack, under human review, and they face the same gates a person would: a change that breaks a check does not ship.</p>'''

BENCH_CARD = '''          <a class="card pcard" id="bench" href="/bench" aria-label="Explore Runix Bench">
            <h4>Runix Bench <span class="card-new">New</span></h4>
            <p>The open benchmark for LLM gateways: trust, price against list, 30-day uptime, speed and cache, measured from outside and published in full.</p>
            <ul>
            <li>Every endpoint probed every six hours</li>
            <li>Self-test with your own key, kept on your machine</li>
            <li>Open source under MIT, raw results public</li>
            </ul>
            <p class="card-meta"><span>Status: available</span> · <span>Open source</span> · <span>Free</span></p>
            <span class="read-more">Explore Runix Bench&nbsp;&rarr;</span>
          </a>
'''
ROUTER_CARD_END = '''            <span class="read-more">Explore Runix Router&nbsp;&rarr;</span>
          </a>
'''

OPEN_SECTION = '''<section class="section alt" id="open">
  <div class="container">
    <div class="section-head center">
      <h2>Two things to try before you talk to us</h2>
      <p>Runix Bench measures LLM gateways from the outside, and Runix FS puts a file system over the bucket you already have. Both are open source, so a team can check the work before it signs anything.</p>
    </div>
    <div class="grid cols-2 open-two">
      <a class="card card-clickable" href="/bench" aria-label="Explore Runix Bench">
        <p class="card-layer">04 &middot; Gateway &middot; Open benchmark</p>
        <h3>Runix Bench</h3>
        <p>Is the gateway you use any good, and where does it lag the best? Eleven endpoints, eight gateways and three official baselines, probed every six hours on price against list, time to first token, 30-day success rate, cache and whether the model is the one on the label. Run the same probe on your own gateway with one command.</p>
        <span class="read-more">Explore Runix Bench&nbsp;&rarr;</span>
      </a>
      <a class="card card-clickable" href="/fs" aria-label="Explore Runix FS">
        <p class="card-layer">01 &middot; Infrastructure &middot; AI file system</p>
        <h3>Runix FS</h3>
        <p>A POSIX file system and a memory, SSD and HDD cache in front of S3-compatible storage, so training jobs, inference servers and agents read the bucket as a local path, with no copies and no rewritten I/O code. Built on Curvine, Apache 2.0, deployed in your own cloud account.</p>
        <span class="read-more">Explore Runix FS&nbsp;&rarr;</span>
      </a>
    </div>
  </div>
</section>

'''

PRODUCTS_LEDE_OLD = "The statuses are literal: Router is available, a production service with accounts opened by our team; Models, Data and FS are in early access;"
PRODUCTS_LEDE = "The statuses are literal: Router is available, a production service with accounts opened by our team, and Bench is available as open source; Models, Data and FS are in early access;"


def realternate(s):
    """Home sections alternate white and grey from #why down; the hero and the
    closing band keep their own classes."""
    out, grey = [], False
    pos = 0
    for m in re.finditer(r'<section class="section( alt)?"( id="[^"]+")>', s):
        if 'id="start"' in m.group(0):
            continue
        cls = "section alt" if grey else "section"
        out.append(s[pos:m.start()] + f'<section class="{cls}"{m.group(2)}>')
        pos = m.end()
        grey = not grey
    out.append(s[pos:])
    return "".join(out)


def main():
    edit("index.html", [
        (HOME_TITLE_OLD, HOME_TITLE),
        (HOME_DESC_OLD, HOME_DESC),
        (H1_OLD, H1), (SUB_OLD, SUB), (HOW_OLD, HOW),
        ("<h2>Seven products, one stack</h2>", "<h2>Eight products, one stack</h2>"),
        (PRODUCTS_LEDE_OLD, PRODUCTS_LEDE),
    ])
    p = pathlib.Path("index.html")
    s = p.read_text(encoding="utf-8")
    o = s
    if 'id="bench" href="/bench"' not in s:
        band = s.index('<div class="lband" id="layer-gateway">')
        end = s.index(ROUTER_CARD_END, band) + len(ROUTER_CARD_END)
        s = s[:end] + BENCH_CARD + s[end:]
    if 'id="open"' not in s:
        at = s.index('<section class="section" id="connect">') if '<section class="section" id="connect">' in s \
            else s.index('<section class="section alt" id="connect">')
        s = s[:at] + OPEN_SECTION + s[at:]
    s = realternate(s)
    if s != o:
        p.write_text(s, encoding="utf-8")
        CHANGED.append("index.html")

    # Every prose count of the products. "Seven" only ever counts products here.
    for f in ["about.html", "solutions.html", "router.html", "roadmap.html", "models.html", "llms.txt"]:
        t = pathlib.Path(f).read_text(encoding="utf-8")
        n = re.sub(r"\b([Ss])even products\b", lambda m: ("E" if m.group(1) == "S" else "e") + "ight products", t)
        if n != t:
            pathlib.Path(f).write_text(n, encoding="utf-8")
            CHANGED.append(f)

    edit("fs.html", [
        ("<title>Runix FS — AI-Native File System on Object Storage</title>",
         "<title>Runix FS — AI File System and S3 Cache for Training</title>"),
        ('content="Runix FS — AI-Native File System on Object Storage"', 'content="Runix FS — AI File System and S3 Cache for Training"'),
        ('content="Runix FS puts a POSIX file system and a multi-tier cache over your S3-compatible storage, so training, inference and agents read data without copying it."',
         'content="Runix FS is an AI file system: POSIX and a memory, SSD and HDD cache over S3-compatible storage, so training and agents read data without copies."'),
    ])
    print("ai unix copy: " + (", ".join(sorted(set(CHANGED))) if CHANGED else "nothing to do"))


if __name__ == "__main__":
    sys.exit(main())
