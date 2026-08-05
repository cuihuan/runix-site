#!/usr/bin/env python3
"""Build the four product sub-sites from their main-site pages.

Each product page becomes the index of its subdomain, with internal links
rewritten to absolute main-site URLs. Canonicals already point at the main
site, which keeps the subdomains from competing with it in search.

    python3 tools/build_subsites.py [outdir]      # build only
    # then per project:
    #   npx wrangler pages deploy <outdir>/subsite-<sub> \
    #       --project-name=runix-<sub> --branch=main --commit-dirty=true
"""
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN = "https://runixcloud.io"
MAP = {"gateway": "router.html", "comic": "comic.html",
       "code": "code.html", "data": "pipeline.html"}
PAGES = ["pricing", "security", "about", "careers", "router", "pipeline",
         "code", "comic", "terms", "privacy", "refund", "cancellation",
         "acceptable-use"]


def absolutize(html):
    """Point every internal link at the main site.

    These patterns used to match href="pricing.html" -- the link style the site
    had when this was written. The site now uses clean absolute paths
    (href="/pricing"), so every pattern stopped matching and the builder left
    links pointing at the subdomain, where they resolve back to the product
    page under a wrong URL. It failed loudly rather than shipping that, which
    is the only reason this was never deployed.

    A subsite is one page, so every internal link belongs on the main site and
    the rule is simply: any root-relative href becomes absolute.
    """
    return re.sub(r'href="/(?!/)([^"]*)"', lambda m: 'href="%s/%s"' % (MAIN, m.group(1)), html)


NOT_FOUND = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Not found</title>
<style>body{font:16px/1.6 system-ui,sans-serif;margin:0;display:grid;place-items:center;
min-height:100vh;color:#0d1117}a{color:#4a5bd6}main{text-align:center;padding:24px}</style>
</head>
<body>
<main>
<h1>Not found</h1>
<p>This subdomain hosts a single page. Everything else lives on the main site.</p>
<p><a href="MAIN_SITE/">Go to runixcloud.io</a></p>
</main>
</body>
</html>
"""


def main(outdir):
    for sub, src in MAP.items():
        out = os.path.join(outdir, f"subsite-{sub}")
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(out)
        html = absolutize(open(os.path.join(ROOT, src)).read())
        open(os.path.join(out, "index.html"), "w").write(html)
        shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(out, "assets"))
        shutil.copy(os.path.join(ROOT, "_headers"), os.path.join(out, "_headers"))
        # Without this an unknown path on the subdomain answers 200 with the
        # product page -- a soft 404, which search engines treat as a quality
        # problem even when the canonical is correct.
        open(os.path.join(out, "404.html"), "w").write(
            NOT_FOUND.replace("MAIN_SITE", MAIN))
        left = re.findall(r'href="(?!https?://|mailto:|#|assets/)[^"]+"', html)
        status = "OK" if not left else f"UNRESOLVED: {left}"
        print(f"{sub}: {status}")
    if any(re.findall(r'href="(?!https?://|mailto:|#|assets/)[^"]+"',
                      open(os.path.join(outdir, f"subsite-{s}", "index.html")).read())
           for s in MAP):
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/runix-subsites")
