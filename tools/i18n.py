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
    # second wave (2026-11-27): the rest of the stack, pricing, the docs a buyer
    # opens first, and the writing the content pass leads with
    "pipeline.html", "code.html", "comic.html", "solutions.html", "plans.html",
    "docs/index.html", "docs/fs.html",
    "blog/rebuild-ai-unix.html", "blog/how-to-benchmark-an-llm-gateway.html",
    "blog/juicefs-alluxio-mountpoint-and-runix-fs.html", "blog/introducing-runix-fs.html",
    # third wave (2026-11-27): what a buyer and their legal team read before talking to us
    "faq.html", "security.html", "access.html", "reliability.html", "roadmap.html",
    "code-data.html", "docs/router.html",
]


def path_of(page):
    """index.html -> /, fs.html -> /fs, docs/index.html -> /docs/."""
    if page == "index.html":
        return "/"
    if page.endswith("/index.html"):
        return "/" + page[: -len("index.html")]
    return "/" + page[: -len(".html")]


# Hosting (崔涣 2026-11-27): runixcloud.com is to be served from the Alibaba
# Cloud server in Hangzhou once its ICP filing is approved. A site filed in
# mainland China carries the "mainland" profile: the pages that sell access to
# overseas model providers are left out of it (their links go to the English
# site), and Router is not offered in mainland China in any case. The
# runix-cn.pages.dev preview carries the full edition.
MAINLAND_EXCLUDE = ["router.html", "docs/router.html"]
# The approved ICP filing number for runixcloud.com. Empty until the filing is
# approved; once set, deploy.sh also publishes the mainland edition to the
# Hangzhou server (tools/deploy_cn_aliyun.sh) and every footer carries it.
ICP_NUMBER = ""


def pages_for(profile):
    if profile == "mainland":
        return [p for p in CN_PAGES if p not in MAINLAND_EXCLUDE]
    return list(CN_PAGES)


CN_PATHS = {path_of(p) for p in CN_PAGES if p != "404.html"}


def counterpart(path, to):
    """The URL of `path` in the other edition, or that edition's home page when
    the page has no Chinese edition."""
    base = ZH if to == "zh" else EN
    if to == "zh" and path not in CN_PATHS:
        return ZH + "/"
    return base + path
