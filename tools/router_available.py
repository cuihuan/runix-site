#!/usr/bin/env python3
"""Runix Router goes from early access to available (2026-10-30).

Three changes, recorded here so they can be re-run and read:

  * Hostnames. The product is Router and every host starts with it:
    router-api.runixcloud.io is the API base, router-console.runixcloud.io the
    console. The old names (one level deeper, the router label in the middle)
    still answer -- the API one is still proxied, the console one redirects --
    but nothing on the site points at them any more.
  * Status. Router is "available": a production service, with accounts opened
    by the team rather than by a signup form. General availability stays
    defined as it was (self-serve signup and checkout, a published service
    level, a full API reference), and none of those is claimed.
  * Claims. The gateway was checked on 2026-10-30. Every model is served by one
    provider and retries across providers are not configured, and "auto" is not
    a routing policy -- it is passed through as a model name. So the site stops
    describing mid-request failover, circuit breakers, health-aware routing,
    "auto" and per-key rate limits as things Router does. What it says instead
    was each seen working that day: the OpenAI-compatible API (chat
    completions, Responses, model listing, streaming), per-key quota, expiry,
    allowed models and IP allowlist, the request log, the usage object, the
    request id header and error envelope, and the TLS floor. Failover between
    providers is described as something set up per account, in writing.

Idempotent: an edit whose result is already there is skipped; one whose
source text is gone and whose result is absent fails loudly. Run from the
site root, then the generator chain (tools/check_idempotent.sh lists it).
"""
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from router_available_data import EDITS, BLOCKS  # noqa: E402

OLD_HOSTS = {"api" + ".router.runixcloud.io": "router-api.runixcloud.io",
             "console" + ".router.runixcloud.io": "router-console.runixcloud.io"}
SKIP = {"tools/router_available.py", "tools/router_available_data.py"}
TEXT = (".html", ".py", ".md", ".txt", ".json", ".xml", ".sh", ".js", ".css")

problems, changed = [], set()


def pattern(old):
    """Match `old` with any run of whitespace where it has one (line wraps differ)."""
    return re.compile(r"\s+".join(re.escape(w) for w in old.split()))
def apply_edit(path, old, new):
    p = pathlib.Path(path)
    t = p.read_text(encoding="utf-8")
    rx = pattern(old)
    if rx.search(t):
        # A replacement must not recreate its own source, or a re-run loops.
        assert not rx.search(new), f"{path}: replacement contains its source"
        t2 = rx.sub(lambda _m: new, t)
        p.write_text(t2, encoding="utf-8")
        changed.add(path)
    elif not pattern(new).search(t):
        problems.append(f"{path}: neither the source nor the result of an edit is present: "
                        f"“{old[:70]}”")


def apply_block(path, start, end, new, marker):
    """Replace from `start` up to and including the first `end` after it."""
    p = pathlib.Path(path)
    t = p.read_text(encoding="utf-8")
    if marker in t:
        return
    a = t.find(start)
    b = t.find(end, a + len(start)) if a >= 0 else -1
    if a < 0 or b < 0:
        problems.append(f"{path}: block start or end not found: “{start[:60]}”")
        return
    p.write_text(t[:a] + new + t[b + len(end):], encoding="utf-8")
    changed.add(path)


def rename_hosts():
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True,
                           check=True).stdout.split()
    for f in files:
        if f in SKIP or not f.endswith(TEXT):
            continue
        p = pathlib.Path(f)
        t = p.read_text(encoding="utf-8")
        t2 = t
        for old, new in OLD_HOSTS.items():
            t2 = t2.replace(old, new)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            changed.add(f)


def apply_after(path, anchor, addition):
    """Insert `addition` right after the exact text `anchor`, once."""
    p = pathlib.Path(path)
    t = p.read_text(encoding="utf-8")
    if anchor + addition in t:
        return
    if anchor not in t:
        problems.append(f"{path}: anchor not found: “{anchor[:70]}”")
        return
    p.write_text(t.replace(anchor, anchor + addition, 1), encoding="utf-8")
    changed.add(path)


def main():
    for path, start, end, new, marker in BLOCKS:
        apply_block(path, start, end, new, marker)
    for e in EDITS:
        if e[0] == "after":
            apply_after(*e[1:])
        else:
            apply_edit(*e)
    rename_hosts()
    print(f"router available: {len(changed)} file(s) changed")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
