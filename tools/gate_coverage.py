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
TARGET = os.path.abspath("tools/qa.py")


def guards(tree):
    """Map every fail() line to the line of the `if` that guards it."""
    out = {}

    def walk(node, guard):
        for child in ast.iter_child_nodes(node):
            g = guard
            if isinstance(child, ast.If):
                g = child.lineno
            if (isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                    and child.func.id == "fail"):
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
    sys.argv = ["qa.py"]
    sys.stdout = open(os.devnull, "w")
    sys.settrace(tracer)
    try:
        runpy.run_path(TARGET, run_name="__qa_traced__")
    except SystemExit:
        pass
    finally:
        sys.settrace(None)
        sys.stdout.close()
        sys.stdout, sys.argv = out, argv

    lines = src.split("\n")
    dead = []
    for fail_line, guard_line in sorted(fails.items()):
        if guard_line is None:
            continue
        if guard_line not in seen:
            msg = lines[fail_line - 1].strip()[:74]
            dead.append((guard_line, fail_line, msg))

    print(f"  {len(fails)} fail point(s); {len(fails) - len(dead)} had their "
          f"condition evaluated against the current site")
    for guard_line, fail_line, msg in dead:
        print(f"  ✗ qa.py:{fail_line} never reached (guard at line {guard_line})")
        print(f"      {msg}")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())
