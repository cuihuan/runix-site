#!/usr/bin/env python3
"""Parse every page and report structural damage a regex check cannot see.

qa.py is regex-based, which is fine for policy questions -- does this page name
a model id, does that link have an aria-label -- and blind to whether the
markup is well formed at all. Tonight it reported "all checks passed" on four
pages whose <th> tags contained literal backslashes, because the pattern it
greps for still matched inside the damage.

This runs a real parser and checks the things a parser can see:

  - unclosed or mismatched elements
  - duplicate ids, which break every fragment link and every aria-labelledby
    pointing at them
  - attributes whose value contains a quote or a backslash, which is how a
    bad replacement string announces itself
  - aria-labelledby / aria-describedby / for / href="#..." pointing at an id
    that does not exist
"""
import collections
import glob
import html.parser
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
# Elements the parser will see unclosed in valid HTML.
OPTIONAL_CLOSE = {"li", "p", "td", "th", "tr", "thead", "tbody", "option"}


class Checker(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.ids = collections.Counter()
        self.refs = []      # (kind, value, line)
        self.problems = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        for k, v in attrs:
            if v is None:
                continue
            if "\\" in v:
                self.problems.append(
                    f"line {self.getpos()[0]}: <{tag} {k}> value contains a "
                    f"backslash -- {v[:40]!r}")
            if '"' in v:
                self.problems.append(
                    f"line {self.getpos()[0]}: <{tag} {k}> value contains a "
                    f"quote -- {v[:40]!r}")
        if "id" in d and d["id"]:
            self.ids[d["id"]] += 1
        for a in ("aria-labelledby", "aria-describedby", "for"):
            if d.get(a):
                for token in d[a].split():
                    self.refs.append((a, token, self.getpos()[0]))
        if d.get("href", "").startswith("#") and len(d["href"]) > 1:
            self.refs.append(("href", d["href"][1:], self.getpos()[0]))
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                for unclosed, line in self.stack[i + 1:]:
                    if unclosed not in OPTIONAL_CLOSE:
                        self.problems.append(
                            f"line {line}: <{unclosed}> is never closed "
                            f"(</{tag}> arrived first)")
                del self.stack[i:]
                return
        self.problems.append(f"line {self.getpos()[0]}: </{tag}> with no open <{tag}>")


def main():
    pages = sorted(set(glob.glob("*.html")) | set(glob.glob("blog/*.html"))
                   | set(glob.glob("docs/*.html")))
    bad = 0
    for page in pages:
        c = Checker()
        c.feed(open(page).read())
        for tag, line in c.stack:
            if tag not in OPTIONAL_CLOSE:
                c.problems.append(f"line {line}: <{tag}> is never closed")
        for _id, n in c.ids.items():
            if n > 1:
                c.problems.append(f'id="{_id}" appears {n} times -- fragment '
                                  f"links and aria references become ambiguous")
        for kind, ref, line in c.refs:
            if ref not in c.ids:
                c.problems.append(f"line {line}: {kind} points at #{ref}, "
                                  f"which is not an id on this page")
        for p in c.problems:
            print(f"  ✗ {page}: {p}")
        bad += len(c.problems)
    print(f"  parsed {len(pages)} page(s) -- {bad} structural problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
