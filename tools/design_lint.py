#!/usr/bin/env python3
"""Fail on any design value the standard does not allow (DESIGN.md).

Checks assets/style.css outside :root, the inline <style> blocks and the
style="" attributes of every page:

  * font sizes: a --text-* token, or a relative unit (em, %), 0 or inherit;
    a px size inside a `font:` shorthand counts too;
  * letter-spacing: a --track-* token, 0 or normal;
  * border-radius: a --radius* token, 50%, 0, or a 1-2px hairline corner;
  * colour: no hex value at all (mask-image's #000 is a mask, not a colour);
  * breakpoints: max-width 560/920/1200px, min-width 561/921/1201px;
  * every var(--x) names a property that is defined somewhere (an undefined
    one silently falls back to inherit: --muted did, for months);
  * label colour: the mono caps labels listed in LABELS_ACCENT are indigo,
    the ones in LABELS_NEUTRAL are ink-3, and no label is cyan.

Exit 1 with one line per violation. `--self-test` injects one violation of
each kind into a copy and proves every check fires.
"""
import glob
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BREAKS_MAX = {560, 920, 1200}
BREAKS_MIN = {561, 921, 1201}

# Mono caps labels (DESIGN.md section 6). Accent: numbers or introduces a
# section. Neutral: names a structure.
LABELS_ACCENT = [".sec-no", ".lpath-label", ".thesis .k", ".adom .k", ".fcell .fno", ".pstep-n"]
LABELS_NEUTRAL = [".glance-title", ".nav-layer-name", ".site-footer .footer-sub", ".doc-side-h"]


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def split_root(css):
    i = css.find(":root {")
    if i < 0:
        return "", css
    j = css.index("\n}", i) + 2
    return css[i:j], css[:i] + css[j:]


def check_css(css, where, defined):
    errs = []
    for m in re.finditer(r"font-size:\s*([^;}]+)", css):
        v = m.group(1).strip().replace("!important", "").strip()
        if not re.fullmatch(r"var\(--text-[a-z0-9]+\)|\d*\.?\d+(em|%)|0|inherit|smaller|larger", v):
            errs.append(f"{where}: font-size {v!r} is not on the type scale")
    for m in re.finditer(r"\bfont:\s*([^;}]+)", css):
        if re.search(r"\d+(\.\d+)?px", re.sub(r"/\s*[\d.]+(px)?", "", m.group(1))):
            errs.append(f"{where}: font shorthand {m.group(1).strip()!r} uses a raw px size")
    for m in re.finditer(r"letter-spacing:\s*([^;}]+)", css):
        v = m.group(1).strip()
        if not re.fullmatch(r"var\(--track-[a-z]+\)|0|normal|inherit", v):
            errs.append(f"{where}: letter-spacing {v!r} is not a --track-* token")
    for m in re.finditer(r"border-radius:\s*([^;}]+)", css):
        for part in m.group(1).split():
            if not re.fullmatch(r"var\(--radius(-[a-z]+)?\)|50%|0|[12]px|inherit", part):
                errs.append(f"{where}: border-radius {part!r} is not a --radius* token")
    for m in re.finditer(r"([a-z-]+)\s*:[^;{}]*?(#[0-9a-fA-F]{3,8})\b", css):
        if m.group(1) in ("mask-image", "-webkit-mask-image") and m.group(2).lower() in ("#000", "#000000"):
            continue
        errs.append(f"{where}: raw colour {m.group(2)} in {m.group(1)}")
    for m in re.finditer(r"@media[^{]*", css):
        for kind, px in re.findall(r"(max|min)-width:\s*(\d+)px", m.group(0)):
            ok = BREAKS_MAX if kind == "max" else BREAKS_MIN
            if int(px) not in ok:
                errs.append(f"{where}: breakpoint {kind}-width {px}px is not 560/920/1200")
    for m in re.finditer(r"var\((--[a-z0-9-]+)", css):
        if m.group(1) not in defined:
            errs.append(f"{where}: var({m.group(1)}) is never defined")
    return errs


def rule_colour(css, selector):
    found = None
    for m in re.finditer(r"(?:^|(?<=\}))\s*([^{}@]+)\{([^}]*)\}", css, re.M):
        sels = [s.strip() for s in m.group(1).split(",")]
        if selector in sels:
            c = re.search(r"(?:^|;)\s*color:\s*([^;]+)", m.group(2))
            if c:
                found = c.group(1).strip()
    return found


def check_labels(css):
    errs = []
    for sel in LABELS_ACCENT:
        c = rule_colour(css, sel)
        if c and c != "var(--indigo-ink)":
            errs.append(f"style.css: label {sel} is {c}, accent labels are var(--indigo-ink)")
    for sel in LABELS_NEUTRAL:
        c = rule_colour(css, sel)
        if c and c != "var(--ink-3)":
            errs.append(f"style.css: label {sel} is {c}, structural labels are var(--ink-3)")
    return errs


def lint(root=ROOT):
    css_path = root / "assets" / "style.css"
    css = strip_comments(css_path.read_text(encoding="utf-8"))
    rootblock, rest = split_root(css)
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", css))
    errs = check_css(rest, "style.css", defined) + check_labels(rest)
    pages = [p for p in glob.glob(str(root / "**" / "*.html"), recursive=True)
             if "/tools/" not in p and "/node_modules/" not in p and not pathlib.Path(p).name.startswith("_")]
    for p in sorted(pages):
        doc = pathlib.Path(p).read_text(encoding="utf-8")
        rel = str(pathlib.Path(p).relative_to(root))
        for m in re.finditer(r"<style[^>]*>(.*?)</style>", doc, re.S):
            errs += check_css(strip_comments(m.group(1)), rel + " <style>", defined)
        for m in re.finditer(r'\sstyle="([^"]*)"', doc):
            errs += [e for e in check_css(m.group(1), rel + " style=", defined) if "breakpoint" not in e]
    return errs


def self_test():
    import shutil
    import subprocess
    import tempfile
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        (tmp / "assets").mkdir()
        shutil.copy(ROOT / "assets" / "style.css", tmp / "assets" / "style.css")
        base = lint(tmp)
        if base:
            print("self-test: the real stylesheet already fails; fix that first")
            return 1
        cases = {
            "font-size": ".x { font-size: 17px; }",
            "font shorthand": ".x { font: 600 11px/1 var(--mono); }",
            "letter-spacing": ".x { letter-spacing: 0.3em; }",
            "border-radius": ".x { border-radius: 7px; }",
            "raw colour": ".x { color: #123456; }",
            "breakpoint": "@media (max-width: 700px) { .x { color: var(--ink); } }",
            "never defined": ".x { color: var(--nope); }",
            "label": ".sec-no { color: var(--cyan-text); }",
        }
        failed = 0
        for name, inject in cases.items():
            (tmp / "assets" / "style.css").write_text((ROOT / "assets" / "style.css").read_text() + "\n" + inject + "\n")
            got = lint(tmp)
            hit = any(name.split()[0] in e or name in e for e in got)
            print(f"  {'ok  ' if hit else 'MISS'} {name}: {got[:1]}")
            failed += not hit
        return 1 if failed else 0
    finally:
        shutil.rmtree(tmp)


def main():
    if "--self-test" in sys.argv:
        return self_test()
    errs = lint()
    for e in errs:
        print("  " + e)
    print(f"design lint: {len(errs)} violation(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
