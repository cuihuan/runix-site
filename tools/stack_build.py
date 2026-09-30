#!/usr/bin/env python3
"""Draw the Runix Lab stack from tools/stack.py, in the two places it appears.

  * The home page's stack diagram (#platform), between the <!--stack--> and
    <!--/stack--> markers: five numbered layers, each product in its layer with
    its literal status, standing on the customer's compute.
  * The locator at the top of every product page: which layer the product sits
    in, linked back to the stack, beside the product's status badge. It goes
    above the <h1> on every page, so all seven heroes open the same way.

Generated rather than typed, so a product that changes layer or status changes
in one file. Idempotent: a second run changes nothing. Run from the site root.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from stack import LAYERS, PRODUCTS, LAYER_OF, DOMAINS, products_in  # noqa: E402

START, END = "<!--stack-->", "<!--/stack-->"
GROUND = ("GPUs, power and cloud capacity in your own account, with the "
          "object storage and Kubernetes you already run. The stack runs on "
          "them and replaces none of them.")


def home_stack(indent):
    i1, i2, i3, i4 = (indent + "  " * n for n in (1, 2, 3, 4))
    n_products = len(PRODUCTS)
    words = {5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
    out = [f'{indent}<div class="pmap pstack" id="platform">',
           f'{i1}<div class="pmap-cap"><p>Runix Lab &middot; the AI operating system</p>'
           f'<p>{words[len(LAYERS)].capitalize()} layers, {words[n_products]} products</p></div>']
    for key, num, name, role in LAYERS:
        extra = " has-domains" if key == "data" else ""
        out.append(f'{i1}<div class="pmap-row{extra}" id="layer-{key}-map" data-layer="{key}">')
        out.append(f'{i2}<p class="pmap-layer"><span class="pl-no">{num:02d}</span>'
                   f'<span class="pl-name">{name}</span><span class="pl-role">{role}</span></p>')
        out.append(f'{i2}<ul class="pmap-cells">')
        for pk in products_in(key):
            _, href, pname, line, _l, status, tag = PRODUCTS[pk]
            live = " pmap-live" if status == "early access" else ""
            new = f" <i>{tag}</i>" if tag else ""
            out.append(f'{i3}<li><a class="pmap-cell{live}" href="{href}"><b>{pname}{new}</b>'
                       f'<span>{line}</span><em class="pmap-st">{status.capitalize()}</em></a></li>')
        out.append(f'{i2}</ul>')
        if key == "data":
            # The domains the data layer works in, each a link to its own page. Drawn under the layer's products because they belong to the
            # layer's work, not to one product's tile.
            out.append(f'{i2}<div class="pmap-domains"><p class="pd-label">Domains</p>')
            out.append(f'{i3}<ul>')
            for slug, label, focus in DOMAINS:
                cls = "pd-chip pd-focus" if focus else "pd-chip"
                tag = " <i>Focus</i>" if focus else ""
                out.append(f'{i4}<li><a class="{cls}" href="/{slug}">{label}{tag}</a></li>')
            out.append(f'{i3}</ul>')
            out.append(f'{i2}</div>')
        out.append(f'{i1}</div>')
    out += [f'{i1}<div class="pmap-row pmap-base">',
            f'{i2}<p class="pmap-layer"><span class="pl-no">00</span>'
            f'<span class="pl-name">Compute &amp; energy</span><span class="pl-role">Yours, not ours</span></p>',
            f'{i2}<p class="pmap-ground">{GROUND}</p>',
            f'{i1}</div>',
            f'{indent}</div>']
    return "\n".join(out)


def eyebrow(key):
    # A literal middle dot, not &middot;: qa.py reads the status out of the
    # badge by splitting on the character, and an entity would make the status
    # gate skip the badge without saying so.
    _, _, name, _, layer, status, _ = PRODUCTS[key]
    num, lname = LAYER_OF[layer]
    bars = "".join('<i class="on"></i>' if n == num else "<i></i>"
                   for _k, n, *_ in LAYERS)
    # The link sits in a wrapper of its own: it is a standalone pill, not a
    # link inside a sentence, and the wrapper is how the render check tells the
    # two apart (it measures a link against its parent's text colour).
    return (f'<div class="prod-eyebrow"><span class="sl-row"><a class="stack-loc" href="/#platform">'
            f'<span class="sl-mini" aria-hidden="true">{bars}</span>'
            f'Layer {num:02d} \u00b7 {lname}'
            f'<span class="visually-hidden">: see the whole stack</span></a></span>'
            f'<span class="badge">{name} \u00b7 {status.capitalize()}</span></div>')


def place_eyebrow(t, key, rel, problems):
    new = eyebrow(key)
    m = re.search(r'<div class="prod-eyebrow">.*?</span></div>', t)
    if m:
        return t[:m.start()] + new + t[m.end():]
    name = PRODUCTS[key][2]
    h = re.search(r'<section class="split-hero">|<div class="page-hero\b', t)
    if not h:
        problems.append(f"{rel}: no hero to put the locator in")
        return t
    h1 = t.find("<h1", h.start())
    badge = re.compile(r'[ \t]*<span class="badge">' + re.escape(name)
                       + r' (?:·|&middot;) [^<]*</span>\n?')
    b = badge.search(t, h.start())
    # The badge has to be the hero's own, not one further down the page.
    nxt = t.find("<section", h.end())
    if h1 < 0 or not b or (nxt > 0 and b.start() > nxt):
        problems.append(f"{rel}: hero has no <h1> or no {name} badge")
        return t
    t = t[:b.start()] + t[b.end():]
    h1 = t.find("<h1", h.start())
    line_start = t.rfind("\n", 0, h1) + 1
    ind = t[line_start:h1]
    return t[:line_start] + ind + new + "\n" + t[line_start:]


def main():
    problems, changed = [], 0
    home = pathlib.Path("index.html")
    t = home.read_text(encoding="utf-8")
    a, b = t.find(START), t.find(END)
    if a < 0 or b < a:
        problems.append("index.html: no <!--stack--> markers")
    else:
        line_start = t.rfind("\n", 0, a) + 1
        indent = t[line_start:a]
        new = t[:a] + START + "\n" + home_stack(indent) + "\n" + indent + t[b:]
        if new != t:
            home.write_text(new, encoding="utf-8")
            changed += 1
    for key, (page, *_rest) in PRODUCTS.items():
        p = pathlib.Path(page)
        if not p.exists():
            problems.append(f"{page}: product page missing")
            continue
        t = p.read_text(encoding="utf-8")
        new = place_eyebrow(t, key, page, problems)
        if new != t:
            p.write_text(new, encoding="utf-8")
            changed += 1
    print(f"stack build: {changed} page(s) changed")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
