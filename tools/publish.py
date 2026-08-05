#!/usr/bin/env python3
"""Publish a scheduled post: move it into blog/, stamp today's date, rebuild the index.

    python3 tools/publish.py prompt-caching-explained
    ./deploy.sh          # then ship it

The publication date is stamped at publish time rather than at writing time, so
the site never claims a post existed before it did.
"""
import datetime
import pathlib
import re
import sys
import zoneinfo

ROOT = pathlib.Path(__file__).resolve().parent.parent
TZ = zoneinfo.ZoneInfo("Asia/Shanghai")


def main(slug):
    src = ROOT / "scheduled" / f"{slug}.html"
    if not src.exists():
        sys.exit(f"no scheduled post named {slug} (looked in {src})")
    dst = ROOT / "blog" / f"{slug}.html"
    if dst.exists():
        sys.exit(f"{dst} already exists — is it already published?")

    now = datetime.datetime.now(TZ).date()
    iso = now.isoformat()
    human = f"{now:%B} {now.day}, {now.year}"

    s = src.read_text()
    s = re.sub(r'(<div class="post-meta"><span class="cat">[^<]*</span><span>)[^<]*(</span>)',
               rf"\g<1>{human}\g<2>", s, count=1)
    s = re.sub(r'"datePublished": "[^"]*"', f'"datePublished": "{iso}"', s)
    s = re.sub(r'"dateModified": "[^"]*"', f'"dateModified": "{iso}"', s)
    dst.write_text(s)
    src.unlink()
    print(f"published {slug} with date {human}")

    sys.path.insert(0, str(ROOT / "tools"))
    import build_blog_index as b
    posts = b.read_posts()
    b.write_index(posts)
    b.write_sitemap(posts)
    print(f"index and sitemap rebuilt: {len(posts)} posts live")

    # These two also list every post. Keeping them hand-maintained is how
    # llms.txt ended up advertising four posts out of nineteen.
    import subprocess
    for tool in ("build_feed.py", "refresh_llms_txt.py"):
        subprocess.run(["python3", str(ROOT / "tools" / tool)], check=True)
    print("next: ./deploy.sh")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
