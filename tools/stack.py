"""The Runix Lab product stack: five layers and the seven products in them.

One definition, read by every builder that draws the stack: the header's
Products menu (flagship_nav.py), the layer locator on each product page
(stack_locator.py) and the status gate in qa.py. The home page draws the same
stack by hand, and qa.py checks that its drawing agrees with this file.

Layers are numbered bottom-up, the way the industry's layered view of AI is
drawn (energy and chips at the bottom, applications at the top). Runix builds
the five software layers; the compute and energy underneath are the
customer's own cloud, which the home page shows as the ground the stack
stands on rather than as a sixth product layer.
"""

# (key, number, name, role) -- top to bottom, the order they are drawn in.
LAYERS = [
    ("applications", 5, "Applications", "Products where AI does the work"),
    ("gateway", 4, "Gateway", "One way in to every model"),
    ("models", 3, "Models", "Open-weight models, tuned and served"),
    ("data", 2, "Data", "Domain data, cleaned for training and evaluation"),
    ("infrastructure", 1, "Infrastructure", "Storage that keeps GPUs fed"),
]

# key -> (page, href, name, one-line description, layer, status, tag)
# `status` is the literal label the site uses everywhere; qa.py fails a page
# whose badge or card says anything else.
PRODUCTS = {
    "code": ("code.html", "/code", "Runix Code",
             "A reviewable AI agent in your repository",
             "applications", "in development", ""),
    "comic": ("comic.html", "/comic", "Runix Comic",
              "Scripts into published episodes",
              "applications", "in development", ""),
    "router": ("router.html", "/router", "Runix Router",
               "One compliant endpoint for every model",
               "gateway", "early access", ""),
    "models": ("models.html", "/models", "Runix Models",
               "Fine-tune and serve open-weight models",
               "models", "early access", "New"),
    "data": ("data.html", "/data", "Runix Data",
             "Domain data for training and evaluation",
             "data", "early access", "New"),
    "pipeline": ("pipeline.html", "/pipeline", "Runix Pipeline",
                 "The tooling that makes data model-ready",
                 "data", "in development", ""),
    "fs": ("fs.html", "/fs", "Runix FS",
           "AI-native file system on your object storage",
           "infrastructure", "early access", ""),
}

# The Data layer's domains, from tools/domains.py (which also holds each
# domain page's content). Code is the focus (2026-09-30: "coding data is an
# important part of the business") -- the one marked, not the largest; nothing
# on the site claims a size.  (page slug, label, focus)
from domains import DOMAINS as _DOMAIN_PAGES  # noqa: E402
DOMAINS = [(d["slug"], d["name"], d["key"] == "code") for d in _DOMAIN_PAGES]

LAYER_OF = {key: (num, name) for key, num, name, _ in LAYERS}


def products_in(layer):
    return [k for k, v in PRODUCTS.items() if v[4] == layer]


def product_pages():
    return [v[0] for v in PRODUCTS.values()]
