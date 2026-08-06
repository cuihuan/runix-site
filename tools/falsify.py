#!/usr/bin/env python3
"""Inject a defect, run a check, restore -- and refuse to lie about any of it.

Every gate in this repo is supposed to be proved by injecting the defect it
should catch. Tonight roughly a quarter of those injections did not land where
I assumed, and each time the gate looked broken (or looked fine) for reasons
that had nothing to do with the gate:

  - the same string appeared earlier in the file, so a count=1 replace edited
    the table of contents, or the <meta description>, instead of the visible copy
  - the injection landed outside the range the gate scans (the hero is outside
    <main> on every product page)
  - a leftover background process held a port, so a non-zero exit was a bind
    error rather than a finding

This encodes the three rules that would have caught all of those:

  1. assert the file actually changed
  2. assert the change landed inside the region the check looks at
  3. read the output, not just the exit code, and restore no matter what

Usage:
  tools/falsify.py <file> <old> <new> --check "<command>" [--scope-start S]
                   [--scope-end E] [--expect TEXT]

  --scope-start/--scope-end  literal markers bounding where the edit must land
  --expect                   text the check's output must contain to count

Exit 0 means the gate behaved: it failed while the defect was present, said what
was expected, and the file is back to how it started.
"""
import argparse
import pathlib
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("--check", required=True)
    ap.add_argument("--scope-start")
    ap.add_argument("--scope-end")
    ap.add_argument("--expect")
    a = ap.parse_args()

    path = pathlib.Path(a.file)
    original = path.read_text()

    # Rule 2 first: decide where the edit is allowed to land, then edit only there.
    lo = original.find(a.scope_start) if a.scope_start else 0
    hi = original.find(a.scope_end, lo + 1) if a.scope_end else len(original)
    if lo < 0 or hi < 0 or hi <= lo:
        print(f"  scope markers not found in {path} -- nothing was changed")
        return 1
    region = original[lo:hi]
    if a.old not in region:
        print(f"  “{a.old[:50]}” does not appear inside the scope "
              f"({len(region)} chars) -- nothing was changed")
        return 1

    injected = original[:lo] + region.replace(a.old, a.new, 1) + original[hi:]
    # Rule 1: the file must actually differ.
    if injected == original:
        print("  the replacement produced an identical file -- nothing was changed")
        return 1

    path.write_text(injected)
    try:
        r = subprocess.run(a.check, shell=True, capture_output=True, text=True, timeout=1800)
        out = (r.stdout or "") + (r.stderr or "")
    finally:
        # Rule 3, second half: restore whatever happened.
        path.write_text(original)

    # Rule 3, first half: a non-zero exit is not proof. Ports, missing temp
    # files and syntax errors all exit non-zero without the gate having fired.
    for noise in ("Address already in use", "Traceback (most recent call last)",
                  "No such file or directory"):
        if noise in out:
            print(f"  the check died on “{noise}” -- that is the environment, "
                  f"not the gate")
            print("\n".join("    " + l for l in out.strip().split("\n")[-6:]))
            return 1

    if r.returncode == 0:
        print("  the check passed with the defect present -- the gate did not fire")
        return 1
    if a.expect and a.expect not in out:
        print(f"  the check failed, but not with “{a.expect}” -- it may be "
              f"failing for another reason")
        print("\n".join("    " + l for l in out.strip().split("\n")[:6]))
        return 1

    hit = [l.strip() for l in out.split("\n") if a.expect and a.expect in l] or \
          [l.strip() for l in out.split("\n") if l.strip().startswith("✗")]
    print(f"  gate fired: {hit[0][:110] if hit else 'non-zero exit'}")
    print(f"  {path} restored")
    return 0


if __name__ == "__main__":
    sys.exit(main())
