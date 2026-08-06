#!/usr/bin/env python3
"""Check that the external links we cite still resolve.

Every factual claim on the blog links to the source it came from, which is
worth nothing once the source moves. Link rot happens on someone else's
schedule, not ours, so this belongs in the daily watchdog rather than the
deploy pipeline -- a deploy cannot break a link on another company's site.

Two probes before reporting, for the same reason the sub-domain check probes
twice: a single timeout is noise, and a watchdog that cries wolf is one people
stop reading. Drafts are included -- a draft's sources should still be good on
the day someone decides to publish it.
"""
import collections
import concurrent.futures
import glob
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
UA = "Mozilla/5.0 (compatible; RunixLinkCheck/1.0; +https://runixcloud.io)"


def probe(url):
    r = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-L",
         "--max-time", "25", "-A", UA, url],
        capture_output=True, text=True)
    return r.stdout.strip()


def main():
    where = collections.defaultdict(list)
    for p in sorted(set([_p for _p in glob.glob("*.html") if not os.path.basename(_p).startswith("_")]) | set([_p for _p in glob.glob("blog/*.html") if not os.path.basename(_p).startswith("_")])
                    | set([_p for _p in glob.glob("docs/*.html") if not os.path.basename(_p).startswith("_")]) | set([_p for _p in glob.glob("scheduled/*.html") if not os.path.basename(_p).startswith("_")])):
        s = open(p).read()
        body = s[s.find("</header>"):s.rfind("<footer")]
        for u in re.findall(r'href="(https?://[^"]+)"', body):
            if "runixcloud.io" not in u:
                where[u].append(p)

    def check(u):
        c = probe(u)
        if c.startswith(("2", "3")):
            return None
        c2 = probe(u)          # second opinion
        return None if c2.startswith(("2", "3")) else (u, c, c2)

    bad = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(check, sorted(where)):
            if r:
                bad.append(r)

    for u, c1, c2 in bad:
        print(f"  FAIL cited source returns {c1}/{c2}: {u}")
        print(f"         cited on: {', '.join(where[u][:3])}")
    print(f"  {'OK   ' if not bad else '     '}checked {len(where)} cited source(s) "
          f"-- {len(bad)} unreachable")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
