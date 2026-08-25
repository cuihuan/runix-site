#!/usr/bin/env python3
"""Tell Bing, Yandex, Seznam and Naver which pages changed, on every deploy.

IndexNow was set up by hand once, in July, and never run again -- so three
engineering posts published in August sat waiting for a crawler to notice them.
This runs as a deploy step instead.

What it submits is what update_lastmod.py decided actually changed: that script
compares normalised page *content*, not file mtimes, and stamps today's date
into sitemap.xml for the pages that really moved. Reading the freshly-written
sitemap back means this never claims a page changed when only an asset version
was bumped -- the same discipline that keeps lastmod trustworthy keeps these
submissions trustworthy, and an endpoint that is fed noise starts ignoring the
host.

The key is public by design: IndexNow verifies ownership by fetching it from
the site root, so it lives in the repo the same way robots.txt does.

Usage:
    python3 tools/indexnow.py            # submit pages whose lastmod is today
    python3 tools/indexnow.py --all      # submit every URL in the sitemap
    python3 tools/indexnow.py --dry-run  # print what would be submitted
"""
import datetime
import json
import os
import re
import sys
import urllib.error
import urllib.request
import zoneinfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

TZ = zoneinfo.ZoneInfo("Asia/Shanghai")
HOST = "runixcloud.io"
KEY = "dbac2c6ee9f40bfd3147a123d56e23c9"
ENDPOINT = "https://api.indexnow.org/indexnow"
# One submission reaches every participating engine; they share the feed.
UA = "runix-site-indexnow/1.0 (+https://runixcloud.io/)"


def sitemap_entries():
    """[(url, lastmod)] straight out of the sitemap the deploy just wrote."""
    xml = open("sitemap.xml").read()
    out = []
    for block in re.findall(r"<url>(.*?)</url>", xml, re.S):
        loc = re.search(r"<loc>([^<]+)</loc>", block)
        mod = re.search(r"<lastmod>([^<]+)</lastmod>", block)
        if loc:
            out.append((loc.group(1).strip(), mod.group(1).strip() if mod else ""))
    return out


def submit(urls):
    body = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt",
        "urlList": urls,
    }).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status


def main():
    every = "--all" in sys.argv
    dry = "--dry-run" in sys.argv
    today = datetime.datetime.now(TZ).date().isoformat()

    entries = sitemap_entries()
    if not entries:
        print("  !! sitemap.xml has no URLs — not submitting")
        return 1
    urls = [u for u, m in entries] if every else [u for u, m in entries if m == today]

    if not urls:
        print(f"  nothing changed today ({today}) — nothing to submit")
        return 0
    if dry:
        print(f"  would submit {len(urls)} URL(s):")
        for u in urls:
            print(f"    {u}")
        return 0

    try:
        status = submit(urls)
    except urllib.error.HTTPError as e:
        # 422 means the key or host was rejected; 4xx here is worth seeing, but
        # a search-engine ping is not a reason to fail a deploy that is already
        # live, so this reports and returns success.
        print(f"  !! IndexNow rejected the submission: HTTP {e.code} {e.reason}")
        print(f"     body: {e.read()[:300].decode(errors='replace')}")
        return 0
    except urllib.error.URLError as e:
        print(f"  !! IndexNow unreachable: {e.reason}")
        return 0

    # 200 = accepted, 202 = accepted, key validation pending.
    print(f"  submitted {len(urls)} changed URL(s) to IndexNow — HTTP {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
