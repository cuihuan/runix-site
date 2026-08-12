#!/usr/bin/env python3
"""Make the product system legible: one numbered taxonomy instead of two.

The homepage described the same four products twice, in two different
groupings. First "One platform, three layers" -- a stack whose chips already
named Runix Code, Runix Comic and Runix Pipeline. Then, immediately below,
"Four products, four kinds of easy" -- four cards for those same products. A
reader had to hold both groupings in their head and map between them, and the
counts did not even agree: three layers, four products.

That is the whole reason the page did not read as a product system.

The fix is not to delete a section -- both are doing a real job -- it is to
make them share one taxonomy and let numbering carry the join:

  * #platform now presents FOUR numbered layers (01-04). Each band is just the
    number, the category, one sentence, and which products live there. No
    feature bullets, no status pills, no flow arrows: it answers "how does this
    fit together", nothing else.
  * #products keeps the full cards -- what each product does, its bullets, its
    literal status -- and every card is stamped with the layer number it
    belongs to.

Read the bands, then the cards, and the number does the mapping for you.

The layer order is the one the existing copy already claimed but never showed:
"in the order the work actually happens". 01 is the Router because it is the
only product running traffic today; leading a product system with three
in-development products would be selling vapour.

The nav shrinks from nine items to four (Platform, Products, Docs, Company)
plus the console pair. Pricing, Security and Blog are not lost -- all three
were already in the footer, verified before removal, which is also what
OpenRouter does: a product-only nav and a footer that absorbs everything
commercial and corporate. The console links gain target="_blank" so the
console opens as its own app rather than replacing the marketing site.

Idempotent. Run from the site root.
"""
import os
import re
import pathlib
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CONSOLE = "https://console.router.runixcloud.io"

# --------------------------------------------------------------- nav (52 pages)
# The block is not byte-identical across pages: each page marks its own item
# with class="active", and the indentation of the opening div varies. So the
# nav is rebuilt structurally rather than string-matched -- which also decides
# what happens to a page whose active item is being removed (/pricing,
# /security, /blog): it simply ends up with no active item, which is correct,
# because that page is no longer represented in the nav.
NAV_KEEP = [
    ("/#platform", "Platform"),
    ("/#products", "Products"),
    ("/docs/", "Docs"),
    ("/about", "Company"),
]
NAV_BLOCK_RE = re.compile(
    r'(<div class="nav-links">)(.*?)(\n\s*</div>)', re.S)


def active_for(path):
    """Which of the four surviving items this page belongs under.

    Derived from the page's own path rather than from whatever class="active"
    it happened to carry. Reading the old markup does not work: the docs pages
    linked Docs relatively (href="./"), so an href-based match silently missed
    all five of them. Path is also the honest source -- it is what the nav is
    describing -- and it makes the rebuild reproducible instead of dependent on
    the file's previous state.

    Pages whose old active item is being removed (/pricing, /security, the blog)
    correctly end up with no active item: they are no longer in the nav.
    """
    p = str(path).lstrip("./")
    if p.startswith("docs/"):
        return "/docs/"
    if p == "about.html":
        return "/about"
    if p in ("router.html", "pipeline.html", "code.html", "comic.html"):
        return "/#products"
    return None


def build_nav(path):
    """Rebuild the link list for one page."""
    active = active_for(path)
    out = []
    for href, label in NAV_KEEP:
        cls = ' class="active"' if href == active else ""
        out.append(f'      <a href="{href}"{cls}>{label}</a>')
    out.append(f'      <a class="nav-signin" href="{CONSOLE}"'
               f' target="_blank" rel="noopener">Sign in</a>')
    out.append(f'      <a class="nav-cta" href="{CONSOLE}/register"'
               f' target="_blank" rel="noopener">Get API key</a>')
    return "\n" + "\n".join(out)

# --------------------------------------------- #platform: four numbered layers
PLATFORM_OLD_HEAD = """      <h2>One platform, three layers</h2>
      <p>Runix is built as a stack. The <strong>Router</strong> sits in the middle — the control plane every request passes through. Below it, the models and compute it routes to. Above it, the tools your team actually builds and ships with.</p>"""

PLATFORM_NEW_HEAD = """      <h2>How Runix fits together</h2>
      <p>Four layers, in the order the work actually happens: get model access under control, make the data usable, then build and create on top.</p>"""


def band(num, tag, title, body, products, feature=False):
    cls = "layer layer-lead" if feature else "layer"
    return f"""      <div class="{cls}" id="layer-{num}">
        <div class="layer-num" aria-hidden="true">{num}</div>
        <div class="layer-body">
          <div class="layer-tag">{tag}</div>
          <h3>{title}</h3>
          <p>{body}</p>
          <p class="layer-prod">{products}</p>
        </div>
      </div>"""


PLATFORM_NEW_STACK = "\n".join([
    '    <div class="stack">',
    band("01", "Access", "Gateway &amp; routing",
         "One OpenAI-compatible endpoint in front of every provider: routing, "
         "mid-request failover, central key custody, per-key quotas and "
         "per-request cost.",
         '<a href="#router">Runix Router</a> '
         '<span class="layer-state on">Running traffic today</span>',
         feature=True),
    band("02", "Prepare", "Data &amp; models",
         "What the gateway points at, and what makes it worth pointing at — "
         "clean data, tuned models, dedicated deployment when a shared "
         "endpoint is not enough.",
         '<a href="#pipeline">Runix Pipeline</a> '
         '<span class="layer-side">Fine-tuning · Dedicated deployment · '
         'Frontier &amp; open models</span>'),
    band("03", "Build &amp; create", "Applications &amp; agents",
         "Where the work actually gets done — code that ships under review "
         "gates, and episodes that reach an audience.",
         '<a href="#code">Runix Code</a> · <a href="#comic">Runix Comic</a> '
         '<span class="layer-state soon">In development</span>'),
    band("04", "More", "Capabilities that ride along",
         "The pieces that are not products in their own right but come with "
         "the platform.",
         '<span class="layer-side">Skill library · Agent tools · '
         'GPU &amp; inference · Office &amp; workflow</span>'),
    '    </div>',
])

# ------------------------------------------- #products: stamp the layer number
PRODUCTS_OLD_HEAD = """      <h2>Four products, four kinds of easy</h2>
      <p>Runix is built in the order the work actually happens: get model access under control, make the data usable, then build and create with it.</p>"""

PRODUCTS_NEW_HEAD = """      <h2>The four products</h2>
      <p>Each one sits in a layer above. The statuses are literal, not roadmap language — only the Router is serving traffic today.</p>"""

# (anchor id, layer number, layer label) -- the stamp goes right under the icon
STAMPS = [
    ("router", "01", "Access"),
    ("pipeline", "02", "Prepare"),
    ("code", "03", "Build"),
    ("comic", "03", "Create"),
]

CSS = """

/* ---------- numbered product system -------------------------------------
   The page used to carry two taxonomies for one set of products: a
   three-band stack and a four-card grid, grouped differently, counts
   disagreeing. Numbering is what joins them now -- band 01 and the card
   stamped 01 are the same thing -- so the reader never has to map between
   two schemes. The bands lost their chips and flow arrows in the process:
   the chips duplicated the cards, and the arrows described a data flow the
   numbered sequence no longer claims. */
.layer {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 0 4px;
  align-items: start;
}
.layer + .layer { margin-top: 14px; }
.layer-num {
  font: 800 26px/1 var(--mono);
  letter-spacing: -0.02em;
  font-variant-numeric: tabular-nums;
  color: var(--line-2);
  padding-top: 2px;
}
/* 01 is the only layer a visitor can buy today, so it is the one that gets
   the brand weight -- the same treatment the old .layer-mid gave the Router. */
.layer-lead {
  border-color: rgba(107, 149, 255, 0.5);
  background: linear-gradient(180deg, rgba(107, 149, 255, 0.10), rgba(34, 211, 238, 0.05));
}
.layer-lead .layer-num { color: var(--cyan); }
.layer-lead .layer-tag { color: var(--cyan-text); }
.layer-lead .layer-body h3 {
  background: var(--grad);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.layer-prod {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  font-size: 15px;
}
.layer-prod a { color: var(--indigo); font-weight: 700; }
.layer-prod a:hover { color: var(--cyan-text); text-decoration: underline; }
.layer-side { color: var(--ink-3); font-size: 13.5px; }
/* Status reads as a fact, not a badge to be proud of: "in development" must
   not look like a feature. Only the shipping one gets colour. */
.layer-state {
  font: 600 12px/1 var(--mono);
  letter-spacing: 0.07em;
  text-transform: uppercase;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid var(--line-2);
  color: var(--ink-3);
}
.layer-state.on {
  color: var(--cyan-text);
  border-color: rgba(11, 150, 184, 0.45);
  background: rgba(11, 150, 184, 0.08);
}

/* The card stamp is the other half of the join. Monospace and muted so it
   reads as an index, not as a label competing with the product name. */
.card-layer {
  font: 700 12px/1 var(--mono);
  letter-spacing: 0.11em;
  text-transform: uppercase;
  color: var(--ink-3);
  margin-bottom: 8px;
}
.card-layer b { color: var(--cyan-text); font-weight: 800; }

@media (max-width: 920px) {
  .layer { grid-template-columns: 44px 1fr; }
  .layer-num { font-size: 20px; }
}
@media (max-width: 560px) {
  /* The number column costs a third of the width on a phone, so it goes
     above the tag instead of beside it. */
  .layer { grid-template-columns: 1fr; }
  .layer-num { padding-top: 0; margin-bottom: 6px; }
}
"""


def div_span(text, opener):
    """Byte span of `opener` through the </div> that actually closes it.

    The old stack was three nested levels deep, so "replace up to the next
    </div>" left three orphaned closers behind and html_structure.py caught it
    (index.html lines 185/186/188, "</div> with no open <div>"). Counting the
    tags is the only way to cut the right span.
    """
    start = text.find(opener)
    if start == -1:
        return None
    depth = 0
    for m in re.finditer(r"<div\b|</div>", text[start:]):
        depth += 1 if m.group(0) != "</div>" else -1
        if depth == 0:
            return start, start + m.end()
    return None


def sub(path, old, new, problems, label=""):
    p = pathlib.Path(path)
    t = p.read_text(encoding="utf-8")
    n = t.count(old)
    if n == 0:
        if new in t:
            return False
        problems.append(f"MISSING in {path} [{label}]: {old[:70]!r}")
        return False
    p.write_text(t.replace(old, new), encoding="utf-8")
    return True


def main():
    problems = []

    # ---- nav across every page that carries one
    pages = sorted(p for p in pathlib.Path(".").rglob("*.html"))
    changed = carriers = 0
    for p in pages:
        t = p.read_text(encoding="utf-8")
        m = NAV_BLOCK_RE.search(t)
        if not m:
            continue
        carriers += 1
        rebuilt = m.group(1) + build_nav(p) + m.group(3)
        if rebuilt == m.group(0):
            continue
        p.write_text(t[:m.start()] + rebuilt + t[m.end():], encoding="utf-8")
        changed += 1
    print(f"nav: {changed} page(s) rebuilt to four items + console "
          f"({carriers} carry a nav)")

    # ---- the four numbered bands
    idx = pathlib.Path("index.html").read_text(encoding="utf-8")
    if PLATFORM_NEW_STACK.strip() in idx:
        print("platform: already numbered")
    else:
        span = div_span(idx, '    <div class="stack">')
        if span is None:
            problems.append("MISSING: could not locate the old .stack block")
        else:
            start, end = span
            idx = idx[:start] + PLATFORM_NEW_STACK + idx[end:]
            pathlib.Path("index.html").write_text(idx, encoding="utf-8")
            print("platform: three-band stack replaced with four numbered layers")

    sub("index.html", PLATFORM_OLD_HEAD, PLATFORM_NEW_HEAD, problems, "platform head")
    sub("index.html", PRODUCTS_OLD_HEAD, PRODUCTS_NEW_HEAD, problems, "products head")

    # the old stack's closing note promised "adopt the whole stack"; the bands
    # no longer describe a stack you adopt wholesale.
    sub("index.html",
        '<p class="model-note">Adopt the whole stack, or start with the layer '
        'you need most. <a href="/about#contact">Tell us where you are.</a></p>',
        '<p class="model-note">Start at the layer you need — most teams start '
        'at 01. <a href="/about#contact">Tell us where you are.</a></p>',
        problems, "platform note")

    # ---- stamp each card with its layer
    stamped = 0
    for anchor, num, label in STAMPS:
        marker = f'<a class="card card-clickable" id="{anchor}"'
        t = pathlib.Path("index.html").read_text(encoding="utf-8")
        i = t.find(marker)
        if i == -1:
            problems.append(f"MISSING: product card #{anchor}")
            continue
        h3 = t.find("<h3>", i)
        stamp = f'<p class="card-layer">Layer <b>{num}</b> · {label}</p>\n        '
        if t[max(0, h3 - 200):h3].find('class="card-layer"') != -1:
            continue
        t = t[:h3] + stamp + t[h3:]
        pathlib.Path("index.html").write_text(t, encoding="utf-8")
        stamped += 1
    print(f"products: {stamped} card(s) stamped with their layer number")

    # ---- styles
    css_path = pathlib.Path("assets/style.css")
    css = css_path.read_text(encoding="utf-8")
    if "numbered product system" in css:
        print("css: already present")
    else:
        css_path.write_text(css.rstrip("\n") + "\n" + CSS, encoding="utf-8")
        print("css: numbered-layer rules appended")

    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
