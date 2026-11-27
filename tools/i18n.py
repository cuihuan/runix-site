"""The two editions of the site: English at runixcloud.io, Chinese at runixcloud.com.

One definition, read by flagship_nav.py (the language link in the header),
build_cn.py (which pages ship in Chinese) and deploy_cn.sh. A page ships in
Chinese only when it is listed here; every other path on runixcloud.com
redirects to the English page, and links to it from a Chinese page point at
runixcloud.io directly.
"""

EN = "https://runixcloud.io"
# Whether runixcloud.com serves the Chinese edition yet. Until it does, the
# English pages carry no language link and no hreflang to it: a link to a
# domain that does not answer is worse than no link. Flip to True once the
# domain points at the runix-cn Pages project, then run flagship_nav.py and
# build_cn.py --alternates.
ZH_LIVE = False
ZH = "https://runixcloud.com"
ZH_LANG = "zh-CN"

# Pages with a Chinese edition (2026-11-27, first wave): the brand, the two
# products the content pass leads with, the gateway, and the company.
CN_PAGES = [
    "index.html", "bench.html", "fs.html", "router.html", "models.html", "data.html",
    "agents.html", "about.html", "404.html",
]


def path_of(page):
    """index.html -> /, fs.html -> /fs, docs/index.html -> /docs/."""
    if page == "index.html":
        return "/"
    if page.endswith("/index.html"):
        return "/" + page[: -len("index.html")]
    return "/" + page[: -len(".html")]


CN_PATHS = {path_of(p) for p in CN_PAGES if p != "404.html"}


def counterpart(path, to):
    """The URL of `path` in the other edition, or that edition's home page when
    the page has no Chinese edition."""
    base = ZH if to == "zh" else EN
    if to == "zh" and path not in CN_PATHS:
        return ZH + "/"
    return base + path
