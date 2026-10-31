#!/usr/bin/env python3
"""Runix Router on one host (2026-10-31): router.runixcloud.io.

The owner's rule: no hyphenated hostnames. The console moved from
router-console.runixcloud.io to router.runixcloud.io/console, the API from
router-api.runixcloud.io/v1 to router.runixcloud.io/v1, and the account pages
(/register, /login) to the same host. router.runixcloud.io stops being a Pages
mirror of /router; gateway.runixcloud.io now 301s to runixcloud.io/router.

Supersedes tools/router_available.py for hostnames (that tool now exits early:
re-running it would bring the hyphenated names back). Idempotent: a second run
changes nothing. Run from the site root, then the generator chain.
"""
import pathlib
import re
import subprocess
import sys

SKIP = {"tools/router_one_host.py", "tools/router_available.py", "tools/router_available_data.py"}
TEXT = (".html", ".py", ".md", ".txt", ".json", ".xml", ".sh", ".js", ".css")
OLD_API, OLD_CON = "router-" + "api.runixcloud.io", "router-" + "console.runixcloud.io"

# Most specific first. A bare console address means the dashboard; a console
# address with a path keeps the path (the account pages live at the root).
RULES = [
    ("Runix Router moves from early access to available, at " + OLD_API + " and '\n              '" + OLD_CON + ".",
     "Runix Router moves from early access to available, at router.runixcloud.io: the console and '\n              'the API on one host."),
    ("Runix Router moves from early access to available, at " + OLD_API + " and " + OLD_CON + ".",
     "Runix Router moves from early access to available, at router.runixcloud.io: the console and the API on one host."),
    ('HOSTS = ["runixcloud.io", "' + OLD_API + '", "' + OLD_CON + '"]', 'HOSTS = ["runixcloud.io", "router.runixcloud.io"]'),
]
REGEX = [
    (re.compile(r"https://" + re.escape(OLD_CON) + r"/?(?=[\"'<\s)`.,;]|$)"), "https://router.runixcloud.io/console"),
    (re.compile(r"https://" + re.escape(OLD_CON) + r"(?=/)"), "https://router.runixcloud.io"),
    (re.compile(re.escape(OLD_API)), "router.runixcloud.io"),
    (re.compile(re.escape(OLD_CON)), "router.runixcloud.io/console"),
]

# The sub-site builder and its checks: router.runixcloud.io is no longer a Pages mirror.
EDITS = [
    ("tools/build_subsites.py",
     '''  if (url.hostname === "gateway.runixcloud.io") {
    url.hostname = "router.runixcloud.io";
    return Response.redirect(url.toString(), 301);
  }''',
     '''  if (url.hostname === "gateway.runixcloud.io") {
    return Response.redirect("https://runixcloud.io/router", 301);
  }'''),
    ("tools/build_subsites.py",
     "# gateway.runixcloud.io is the old name of router.runixcloud.io, and both are\n# custom domains of one Pages project.",
     "# gateway.runixcloud.io is the old name of the Router product page; router.runixcloud.io\n# is now the console and API host itself, not this Pages project."),
    ("tools/deploy_subsites.sh", "for h in router comic code data fs models; do", "for h in comic code data fs models; do"),
    ("tools/deploy_subsites.sh", 'if [ "$loc" != "301 https://router.runixcloud.io/x?y=1" ]; then',
     'if [ "$loc" != "301 https://runixcloud.io/router" ]; then'),
    ("tools/deploy_subsites.sh", "(expected a 301 to router.runixcloud.io)", "(expected a 301 to runixcloud.io/router)"),
    ("tools/deploy_subsites.sh", "# gateway.* is the old name of router.*: it must redirect, not serve a copy.",
     "# gateway.* is the old name of the Router product page: it must redirect, not serve a copy."),
    ("tools/subsite_drift.sh", 'HOSTS=${HOSTS:-"router comic code data fs models"}', 'HOSTS=${HOSTS:-"comic code data fs models"}'),
    ("tools/subsite_drift.sh", 'declare -a MIRROR=("router:router.html" "comic:comic.html"', 'declare -a MIRROR=("comic:comic.html"'),
    ("tools/README.md",
     "| `runix-gateway` | **router.runixcloud.io**; gateway.runixcloud.io 301s to it through a Pages Function, because `_redirects` cannot match a hostname |",
     "| `runix-gateway` | gateway.runixcloud.io only, which 301s to runixcloud.io/router through a Pages Function (`_redirects` cannot match a hostname). router.runixcloud.io is the console and API host, not a Pages project. |"),
]


def main():
    problems, changed = [], set()
    for path, old, new in EDITS:
        p = pathlib.Path(path); t = p.read_text(encoding="utf-8")
        if old in t:
            p.write_text(t.replace(old, new), encoding="utf-8"); changed.add(path)
        elif new not in t:
            problems.append(f"{path}: neither source nor result present: {old[:60]!r}")
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split()
    for f in files:
        if f in SKIP or not f.endswith(TEXT):
            continue
        p = pathlib.Path(f); t = p.read_text(encoding="utf-8"); t2 = t
        for old, new in RULES:
            t2 = t2.replace(old, new)
        for rx, new in REGEX:
            t2 = rx.sub(new, t2)
        if t2 != t:
            p.write_text(t2, encoding="utf-8"); changed.add(f)
    print(f"router one host: {len(changed)} file(s) changed")
    if problems:
        print("\n".join(problems), file=sys.stderr); sys.exit(1)


if __name__ == "__main__":
    main()
