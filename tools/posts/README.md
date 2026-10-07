# Post specs

One JSON file per post written since 2026-10-07, in the shape `tools/write_post.py`
takes: title, h1, description, category, layer, the product page the post sends
readers to, three related posts, the body as HTML and a short FAQ. The renderer
refuses a spec that breaks the site's rules before a gate ever sees it.

    python3 tools/write_post.py tools/posts/<slug>.json   # draft in scheduled/
    python3 tools/publish.py <slug>                        # date it, rebuild every surface

The published page is the record once it is live; a spec here is the reproducible
source of the first version, kept the way the earlier write_*_post.py scripts were.
Every spec in this directory was checked by an independent reviewer against the
product facts and the cited sources before publishing (2026-10-07), and the
corrections were applied here, not to the rendered HTML.
