#!/usr/bin/env python3
"""Report qa.py checks whose condition never gets evaluated.

Tonight five separate gates I wrote could not fire when first written: a regex
that matched no page, a label tested against markup that never contains it, a
source page with no such section, an item tag that appears zero times, a
case-sensitive match against text that is capitalised. Every one of them
reported a clean run. A check that cannot fail is worse than no check, because
it reads as coverage.

Falsifying each new gate by hand catches this, and remains the rule. This is
the safety net for the ones already in the file: it traces qa.py and reports
any `fail(...)` whose guarding `if` was never reached, which means that check
did not run at all against the current site.

Reaching a condition is not the same as being able to fail it -- a condition
that is evaluated but structurally always false still passes this. So this
narrows where to look; it does not replace injection.
"""
import ast
import os
import pathlib
import runpy
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
# Any of the check scripts can be measured; qa.py is the default because it
# holds most of the fail points.
TARGET = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "tools/qa.py")
REPORTERS = {"fail", "problem"}


def guards(tree):
    """Map every fail() line to the line of the `if` that guards it."""
    out = {}

    def walk(node, guard):
        for child in ast.iter_child_nodes(node):
            g = guard
            if isinstance(child, ast.If):
                g = child.lineno
            _is_fail = (isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                        and child.func.id in REPORTERS)
            # perf_check and visual_qa collect into a list instead of calling a
            # helper, so problems.append(...) is the same thing by another name.
            _is_append = (isinstance(child, ast.Call)
                          and isinstance(child.func, ast.Attribute)
                          and child.func.attr == "append"
                          and isinstance(child.func.value, ast.Name)
                          and child.func.value.id in ("problems", "issues", "notes"))
            if _is_fail or _is_append:
                out[child.lineno] = guard
            walk(child, g)

    walk(tree, None)
    return out


def main():
    src = pathlib.Path(TARGET).read_text()
    fails = guards(ast.parse(src))

    seen = set()

    def tracer(frame, event, arg):
        if event == "line" and frame.f_code.co_filename == TARGET:
            seen.add(frame.f_lineno)
        return tracer

    argv, out = sys.argv[:], sys.stdout
    sys.argv = [os.path.basename(TARGET)] + (["index.html"] if "perf" in TARGET else [])
    sys.stdout = open(os.devnull, "w")
    sys.settrace(tracer)
    try:
        runpy.run_path(TARGET, run_name="__traced__")
    except SystemExit:
        pass
    finally:
        sys.settrace(None)
        sys.stdout.close()
        sys.stdout, sys.argv = out, argv

    allow = []
    _af = pathlib.Path("tools/gate_coverage_allow.txt")
    if _af.exists():
        allow = [l.split(":", 1) for l in _af.read_text().split("\n")
                 if l.strip() and not l.startswith("#") and ":" in l]

    lines = src.split("\n")
    dead, excused = [], []
    for fail_line, guard_line in sorted(fails.items()):
        if guard_line is None:
            continue
        if guard_line not in seen:
            msg = lines[fail_line - 1].strip()[:74]
            _name = os.path.basename(TARGET)
            if any(a[0].strip() == _name and a[1].strip() in lines[fail_line - 1]
                   for a in allow):
                excused.append((fail_line, msg))
            else:
                dead.append((guard_line, fail_line, msg))

    print(f"  {len(fails)} fail point(s); "
          f"{len(fails) - len(dead) - len(excused)} evaluated, "
          f"{len(excused)} unreachable but accounted for, {len(dead)} unexplained")
    for guard_line, fail_line, msg in dead:
        print(f"  ✗ {os.path.basename(TARGET)}:{fail_line} never reached (guard at line {guard_line})")
        print(f"      {msg}")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
