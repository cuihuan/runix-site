#!/usr/bin/env python3
"""Say what the console actually does: credits are issued on request.

The self-serve rewrite promised that a new account arrives with evaluation
credits already in it. Self-serve signup is real -- registration is open and a
key issues immediately, both verified against the live console -- but the
automatic grant is not: QuotaForNewUser is 0, and raising it is held behind a
funds review and a compliance question about which upstream a free anonymous
account would be allowed to reach.

So every sentence that promises credits on signup is currently false, and this
branch is about to ship. The claim is narrowed rather than removed: the account
and the key really are immediate, and credits really are available -- on
request, which is exactly what /pricing already said in the one line nobody
changed ("Free evaluation credits on request").

Reverse this file if the automatic grant lands: the wording it replaces is the
wording that becomes true again.

Idempotent. Run from the site root.
"""
import os
import pathlib
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# Ordered longest-first so a broad phrasing never eats a narrower one.
EDITS = [
    ("Runix Router is self-serve: create an account and your key is issued "
     "immediately, with evaluation credits to test against real traffic.",
     "Runix Router is self-serve: create an account and your key is issued "
     "immediately. Evaluation credits are issued on request, so you can test "
     "against real traffic before you pay."),

    ("Create an account on the console and your key is issued immediately, "
     "with evaluation credits to test against real traffic.",
     "Create an account on the console and your key is issued immediately; "
     "evaluation credits are issued on request, so you can test against real "
     "traffic before you pay."),

    ("Create an account and your key is issued immediately, with evaluation "
     "credits to test against real traffic.",
     "Create an account and your key is issued immediately; evaluation credits "
     "are issued on request, so you can test against real traffic before you "
     "pay."),

    # Two of these are wrapped around an <a>, so the sentence is split by
    # markup and the plain-prose variants above cannot reach them.
    ('<a href="https://console.router.runixcloud.io/register">console</a> and '
     "your key is issued immediately, with evaluation credits to test against "
     "real traffic.",
     '<a href="https://console.router.runixcloud.io/register">console</a> and '
     "your key is issued immediately; evaluation credits are issued on "
     "request, so you can test against real traffic before you pay."),

    ('<a href="https://console.router.runixcloud.io/register">create an '
     "account</a> and your key is issued immediately, with evaluation credits "
     "to test against real traffic.",
     '<a href="https://console.router.runixcloud.io/register">create an '
     "account</a> and your key is issued immediately; evaluation credits are "
     "issued on request, so you can test against real traffic before you pay."),

    ("Create an account on the console and your key is issued immediately, "
     "with evaluation credits.",
     "Create an account on the console and your key is issued immediately; "
     "evaluation credits are issued on request."),

    ("Create an account and your key is issued immediately, with evaluation "
     "credits.",
     "Create an account and your key is issued immediately; evaluation credits "
     "are issued on request."),

    ("Runix Router is self-serve: create an account, get evaluation credits "
     "and issue a key in minutes.",
     "Runix Router is self-serve: create an account and issue a key in "
     "minutes; evaluation credits are issued on request."),

    ("Router is self-serve. Create an account, get evaluation credits, and "
     "send your first request in minutes.",
     "Router is self-serve. Create an account and issue a key in minutes, then "
     "send your first request; evaluation credits are issued on request."),

    ("New accounts start with evaluation credits and no card is required.",
     "Evaluation credits are issued on request, and no card is required."),

    ("New accounts start with evaluation credits. Full router functionality, "
     "no card required.",
     "Evaluation credits are issued on request. Full router functionality, no "
     "card required."),

    ("Sign up, get evaluation credits and issue your first key in a couple of "
     "minutes.",
     "Sign up and issue your first key in a couple of minutes."),

    ("Sign up, take the evaluation credits and point a client at the endpoint.",
     "Sign up, issue a key and point a client at the endpoint."),

    ("start with free evaluation credits, then pay for what you use",
     "evaluation credits are issued on request, then you pay for what you use"),

    ("Start with free evaluation credits, then pay for what you use.",
     "Evaluation credits are issued on request; after that you pay for what "
     "you use."),

    ("Create an account and start on evaluation credits — or share your "
     "expected volume and we'll come back with a plan and pricing.",
     "Create an account and issue a key in minutes — or share your expected "
     "volume and we'll come back with a plan and pricing."),
]


def main():
    total = 0
    per_file = {}
    for p in sorted(pathlib.Path(".").rglob("*.html")):
        t = original = p.read_text(encoding="utf-8")
        for old, new in EDITS:
            if old in t:
                per_file[str(p)] = per_file.get(str(p), 0) + t.count(old)
                t = t.replace(old, new)
        if t != original:
            p.write_text(t, encoding="utf-8")
            total += 1

    for f, n in sorted(per_file.items()):
        print(f"  {f}: {n} claim(s) narrowed")
    print(f"credits: {total} page(s) updated")

    # Nothing may still promise credits arrive with the account.
    leftovers = []
    for p in pathlib.Path(".").rglob("*.html"):
        t = p.read_text(encoding="utf-8")
        for bad in ("start with evaluation credits",
                    "start with free evaluation credits",
                    "with evaluation credits to test",
                    "get evaluation credits",
                    "take the evaluation credits",
                    "New accounts start with evaluation credits"):
            if bad in t:
                leftovers.append(f"{p}: {bad!r}")
    if leftovers:
        print("STILL PROMISES AN AUTOMATIC GRANT:", file=sys.stderr)
        print("\n".join("  " + x for x in leftovers), file=sys.stderr)
        sys.exit(1)
    print("check: no page still promises credits arrive with the account")


if __name__ == "__main__":
    main()
