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
    ("applications", 5, "Agents", "Domain agents, and the harnesses that run them"),
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
             "An independent coding agent, reviewable in your repository",
             "applications", "in development", ""),
    "comic": ("comic.html", "/comic", "Runix Comic",
              "An independent agent for comic dramas, script to episode",
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

# What the status looks like in practice, drawn under it on the home stack
# (2026-10-07): "early access" covers a key, a deployment and a scoped
# engagement, and an investor or a buyer should see which from the first screen.
QUALIFIER = {
    "router": "running traffic", "fs": "deployed per customer",
    "models": "by engagement", "data": "by engagement",
    "pipeline": "design partners", "code": "waitlist open", "comic": "waitlist open",
}

LAYER_OF = {key: (num, name) for key, num, name, _ in LAYERS}

# A layer hub: one page that presents a whole layer, for the layer that is
# asked about by domain rather than by product (2026-10-07: "the application
# layer should be divided by professional domain, for coding, for work, ...").
# layer key -> (href, label, one line)
HUBS = {
    "applications": ("/agents", "Agents by domain",
                     "Software engineering, media, and what comes next"),
}

# The Agents layer's domains, the way a buyer asks for an agent. Each entry is
# an anchor on the hub page, its label, and the product that serves it today.
# Two domains have an agent; the hub says so literally and names the domains
# the Data layer already has rules for as the candidates, without a promise.
# (anchor, label, product key)
AGENT_DOMAINS = [
    ("engineering", "Software engineering", "code"),
    ("media", "Media and entertainment", "comic"),
]


def products_in(layer):
    return [k for k, v in PRODUCTS.items() if v[4] == layer]


def product_pages():
    return [v[0] for v in PRODUCTS.values()]
