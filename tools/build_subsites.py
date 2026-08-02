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
    html = html.replace('href="index.html#products"', f'href="{MAIN}/#products"')
    html = html.replace('href="index.html"', f'href="{MAIN}/"')
    html = html.replace('href="blog/"', f'href="{MAIN}/blog/"')
    html = re.sub(r'href="blog/([A-Za-z0-9_-]+)\.html"',
                  rf'href="{MAIN}/blog/\1"', html)
    for p in PAGES:
        html = re.sub(rf'href="{re.escape(p)}\.html(#[A-Za-z0-9_-]+)?"',
                      lambda m, p=p: f'href="{MAIN}/{p}{m.group(1) or ""}"', html)
    return html


def main(outdir):
    for sub, src in MAP.items():
        out = os.path.join(outdir, f"subsite-{sub}")
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(out)
        html = absolutize(open(os.path.join(ROOT, src)).read())
        open(os.path.join(out, "index.html"), "w").write(html)
        shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(out, "assets"))
        shutil.copy(os.path.join(ROOT, "_headers"), os.path.join(out, "_headers"))
        left = re.findall(r'href="(?!https?://|mailto:|#|assets/)[^"]+"', html)
        status = "OK" if not left else f"UNRESOLVED: {left}"
        print(f"{sub}: {status}")
    if any(re.findall(r'href="(?!https?://|mailto:|#|assets/)[^"]+"',
                      open(os.path.join(outdir, f"subsite-{s}", "index.html")).read())
           for s in MAP):
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/tmp/runix-subsites")
