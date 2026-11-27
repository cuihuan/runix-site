#!/usr/bin/env python3
"""Move every raw design value in style.css onto the tokens (2026-11-27).

Before this pass the stylesheet carried 40-odd font sizes, 20-odd radii, 30
letter-spacings, ten breakpoints and 30 raw colours outside :root -- the
residue of six design passes, each correct when it landed. DESIGN.md now
fixes one scale for each; this builder rewrites the stylesheet onto it once,
and design_lint.py keeps it there.

Mapping rules, in order:
  * headline sizes are set deliberately (HEADINGS below), not rounded: the
    nearest step is not always the right rung of the hierarchy;
  * every other px size goes to the nearest step of the twelve-step scale,
    ties to the smaller step (a smaller size cannot newly overflow a box);
  * tracking goes to the nearest of six values, radii to five, breakpoints to
    three; colours to named tokens with the same value, except four near-black
    panels and three near-identical greys that are merged.

Idempotent: a second run finds nothing left to rewrite. Run from the site root.
"""
import pathlib
import re
import sys

CSS = pathlib.Path("assets/style.css")

SCALE = [(12, "2xs"), (13, "xs"), (14, "sm"), (15, "md"), (16, "base"), (18, "lg"),
         (20, "xl"), (24, "2xl"), (30, "3xl"), (38, "4xl"), (48, "5xl"), (60, "6xl")]

# Headline sizes by selector, chosen for the hierarchy: page h1 48, centred
# hub h1 60, section h2 38, closing h2 38; one step down per breakpoint.
HEADINGS = [
    (".hero h1 {", "62px", "var(--text-6xl)"),
    ("  .hero h1 {", "38px", "var(--text-4xl)"),
    (".section-head h2 {", "44px", "var(--text-4xl)"),
    ("  .section-head h2 {", "30px", "var(--text-3xl)"),
    ("  .section-head h2 {", "31px", "var(--text-3xl)"),
    (".cta-band h2 {", "40px", "var(--text-4xl)"),
    (".page-hero h1 {", "52px", "var(--text-5xl)"),
    ("  .page-hero h1 {", "42px", "var(--text-4xl)"),
    ("  .page-hero h1 {", "32px", "var(--text-3xl)"),
    (".hero-split h1 {", "52px", "var(--text-5xl)"),
    ("  .hero-split h1 {", "38px", "var(--text-4xl)"),
    (".page-hero.center h1 {", "60px", "var(--text-6xl)"),
    ("  .page-hero.center h1 {", "46px", "var(--text-5xl)"),
    ("  .page-hero.center h1 {", "34px", "var(--text-3xl)"),
    (".plan .price {", "34px", "var(--text-3xl)"),
    (".plans-4 .price {", "33px", "var(--text-3xl)"),
    (".mult b {", "34px", "var(--text-3xl)"),
    (".stats dt {", "44px", "var(--text-5xl)"),
    ("  .stats dt {", "38px", "var(--text-4xl)"),
]
CLAMPS = {
    "clamp(42px, 5.8vw, 80px)": "var(--text-display)",
    "clamp(40px, 5vw, 60px)": "var(--text-hero)",
    "clamp(40px, 4vw, 52px)": "var(--text-page)",
    "clamp(26px, 3vw, 34px)": "var(--text-h2)",
    "clamp(23px, 2.6vw, 30px)": "var(--text-h3)",
}
# Headings that used 700/800 where every other headline uses the display weight.
WEIGHTS = [".plan-hero h1 {", ".psec-head h2 {", ".pclose h2 {"]

TRACK = [(-0.035, "display"), (-0.025, "heading"), (-0.015, "title"), (0.0, None),
         (0.04, "caps"), (0.08, "label")]

RADII = [(6, "xs"), (10, "sm"), (14, ""), (20, "lg")]

COLOURS = {
    "#262b36": "--ink-hover", "#05080f": "--panel", "#0b1018": "--panel",
    "#151a23": "--panel-raised", "#2a3441": "--panel-line", "#2c3846": "--panel-dot",
    "#e9edf6": "--on-panel", "#c9d1d9": "--on-panel-2", "#c9d3e0": "--on-panel-2",
    "#b9c1cd": "--on-panel-3", "#8b95a1": "--on-panel-4", "#8b95a9": "--on-panel-4",
    "#7d8a99": "--on-panel-4", "#78828f": "--on-panel-4", "#d4dbff": "--on-panel-link",
    "#e6e9ef": "--on-panel-hover", "#7ee2a8": "--code-green", "#5fb98b": "--code-green",
    "#79b8ff": "--code-blue", "#22d3ee": "--code-cyan", "#b3261e": "--danger",
    "#c2410c": "--warn", "#5b636f": "--ink-meta", "#63707f": "--on-panel-4",
    "#fbfbfc": "--layer-5", "#f7f7f9": "--layer-4", "#f3f4f6": "--layer-3",
    "#eff0f3": "--layer-2", "#ebecf0": "--layer-1", "#9aa3af": "--ink-4",
}

BREAKS = {"(max-width: 640px)": "(max-width: 560px)", "(max-width: 820px)": "(max-width: 920px)",
          "(max-width: 940px)": "(max-width: 920px)", "(min-width: 768px)": "(min-width: 561px)",
          "(min-width: 1101px)": "(min-width: 1201px)", "(min-width: 1200px)": "(min-width: 1201px)",
          "(max-width: 719px)": "(max-width: 920px)", "(max-width: 900px)": "(max-width: 920px)",
          "(max-width: 1080px)": "(max-width: 1200px)", "(max-width: 1199px)": "(max-width: 1200px)"}


def nearest(value, table):
    best = min(table, key=lambda t: (abs(t[0] - value), t[0]))
    return best


def size_token(px):
    n, name = nearest(px, SCALE)
    return f"var(--text-{name})"


def track_token(em):
    n, name = nearest(em, TRACK)
    return "0" if name is None else f"var(--track-{name})"


def radius_token(px):
    if px >= 900:
        return "var(--radius-pill)"
    if px <= 2:
        return f"{px:g}px"
    n, name = nearest(px, RADII)
    return "var(--radius)" if name == "" else f"var(--radius-{name})"


def split_root(css):
    i = css.index(":root {")
    j = css.index("\n}\n", i) + 3
    return css[:i], css[i:j], css[j:]


def rewrite(body):
    lines = body.split("\n")
    out = []
    for line in lines:
        for sel, raw, tok in HEADINGS:
            if line.startswith(sel) and f"font-size: {raw}" in line:
                line = line.replace(f"font-size: {raw}", f"font-size: {tok}")
        if any(line.startswith(sel) for sel in WEIGHTS):
            line = re.sub(r"font-weight: (700|800)", "font-weight: var(--display-weight)", line)
        out.append(line)
    body = "\n".join(out)
    for raw, tok in CLAMPS.items():
        body = body.replace(raw, tok)
    # font-size: Npx (incl. !important)
    body = re.sub(r"font-size:\s*(\d+(?:\.\d+)?)px", lambda m: "font-size: " + size_token(float(m.group(1))), body)
    # font shorthand: font: <weight> <size>px/<lh> ...
    body = re.sub(r"(font:\s*(?:\d{3}\s+)?)(\d+(?:\.\d+)?)px", lambda m: m.group(1) + size_token(float(m.group(2))), body)
    body = re.sub(r"letter-spacing:\s*(-?\d*\.?\d+)em", lambda m: "letter-spacing: " + track_token(float(m.group(1))), body)
    body = re.sub(r"letter-spacing:\s*0(?=[;\s}])", "letter-spacing: 0", body)

    def radius(m):
        parts = m.group(1).split()
        conv = []
        for p in parts:
            pm = re.fullmatch(r"(\d+(?:\.\d+)?)px", p)
            conv.append(radius_token(float(pm.group(1))) if pm else p)
        return "border-radius: " + " ".join(conv)
    body = re.sub(r"border-radius:\s*([^;}]+?)(?=\s*[;}])", radius, body)
    # colours: #fff by role, then the named table
    body = re.sub(r"\bvar\(--ink-4, #9aa3af\)", "var(--ink-4)", body)
    body = re.sub(r"((?:^|[;{\s])(?:background|background-color|border(?:-[a-z]+)*-color|border(?:-[a-z]+)?|outline)\s*:[^;}]*?)#fff(?:fff)?\b",
                  lambda m: m.group(1) + "var(--surface)", body)
    body = re.sub(r"((?:^|[;{\s])(?:color|fill|stroke|caret-color|text-decoration-color)\s*:[^;}]*?)#fff(?:fff)?\b",
                  lambda m: m.group(1) + "var(--on-accent)", body)
    for hexv, tok in COLOURS.items():
        body = re.sub(re.escape(hexv) + r"\b", f"var({tok})", body, flags=re.I)
    for a, b in BREAKS.items():
        body = body.replace("@media " + a, "@media " + b)
    body = body.replace("var(--muted)", "var(--ink-3)")
    return body


def main():
    css = CSS.read_text(encoding="utf-8")
    head, root, tail = split_root(css)
    # Comments keep their measured values as written: they are the record.
    parts = re.split(r"(/\*.*?\*/)", tail, flags=re.S)
    tail = "".join(p if p.startswith("/*") else rewrite(p) for p in parts)
    new = head + root + tail
    # the body font stack is a token now
    new = new.replace('font-family: "Archivo", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;',
                      "font-family: var(--sans);")
    if new != css:
        CSS.write_text(new, encoding="utf-8")
        print("design tokens: style.css rewritten")
    else:
        print("design tokens: nothing to do")


if __name__ == "__main__":
    sys.exit(main())
