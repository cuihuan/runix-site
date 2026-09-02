#!/usr/bin/env python3
"""Check that the live site actually serves what _headers and _redirects declare.

Why this exists: deploy.sh excluded every filename starting with an underscore,
to sweep up temp pages a killed QA tool leaves in the site root. _headers and
_redirects both start with one, and they are the only two filenames Cloudflare
Pages reads, so neither had ever reached a deployment. The site served no
Content-Security-Policy, no HSTS, no X-Frame-Options, no Referrer-Policy, no
Permissions-Policy and no immutable cache on /assets, and all four redirects
answered 404 instead of 301 -- including /gateway, the product's address before
it was renamed, so old inbound links landed on nothing.

Every other gate in the pipeline passed throughout. They check the built files;
none of them asked whether the deployed site carries the headers those files
declare. That gap is what this closes: it reads both config files and verifies
each claim against the live origin, so the two can never again be silently
absent while the checks stay green.

Data-driven on purpose. Add a header to _headers or a rule to _redirects and it
gets verified without touching this file.

    python3 tools/verify_headers.py [--base https://runixcloud.io]

Exit 0 when every declared header and redirect is live, 1 otherwise.
"""
from __future__ import annotations

import argparse
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
ATTEMPTS = 6          # the edge takes up to a minute to pick up a build
GAP = 10


def parse_headers(path: pathlib.Path) -> dict[str, list[str]]:
    """_headers -> {path pattern: [header names]}. Comments and blanks ignored."""
    out: dict[str, list[str]] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            current = line.strip()
            out.setdefault(current, [])
            continue
        if current and ":" in line:
            out[current].append(line.strip().split(":", 1)[0].strip().lower())
    return out


def parse_redirects(path: pathlib.Path) -> list[tuple[str, str, int]]:
    """_redirects -> [(from, to, status)]. Skips rules Pages cannot honour."""
    rules: list[tuple[str, str, int]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        src, dst = parts[0], parts[1]
        status = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 301
        # Skip rules whose source carries a hostname or a splat. _redirects
        # records that Pages lists domain-level redirects as unsupported and
        # accepts such a rule at deploy time without applying it; asserting on
        # one here would report a failure the deploy cannot fix.
        if "://" in src or "*" in src:
            continue
        rules.append((src, dst, status))
    return rules


def probe(url: str, follow: bool = False):
    """Return (status, headers) or (None, None) if the request could not be made."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None

    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": "runix-verify-headers"})
    try:
        with opener.open(req, timeout=20) as resp:
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}
    except Exception:                                   # noqa: BLE001
        return None, None


def retry(fn):
    """Run fn until it returns True, tolerating edge propagation lag."""
    for attempt in range(ATTEMPTS):
        if fn():
            return True
        if attempt < ATTEMPTS - 1:
            time.sleep(GAP)
    return False


def main() -> int:
    global ATTEMPTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="https://runixcloud.io")
    ap.add_argument("--attempts", type=int, default=ATTEMPTS,
                    help="probes per claim before calling it a failure; 1 for a fast "
                         "negative-control run against a host that should fail")
    args = ap.parse_args()
    ATTEMPTS = max(1, args.attempts)
    base = args.base.rstrip("/")
    failures: list[str] = []

    # -- headers -----------------------------------------------------------
    declared = parse_headers(ROOT / "_headers")
    # One representative URL per pattern; a pattern with no sample is reported
    # rather than skipped, so a new pattern cannot slip through unverified.
    samples = {"/*": "/pricing", "/assets/*": "/assets/style.css", "/feed.xml": "/feed.xml"}

    for pattern, names in declared.items():
        if not names:
            continue
        url = base + samples.get(pattern, "")
        if pattern not in samples:
            failures.append(f"{pattern}: no sample URL in this script -- add one")
            print(f"  ? {pattern:12} unverified: add a sample URL")
            continue

        missing: list[str] = []

        def check() -> bool:
            nonlocal missing
            status, hdrs = probe(url)
            if hdrs is None:
                missing = ["<unreachable>"]
                return False
            missing = [n for n in names if n not in hdrs]
            return not missing

        if retry(check):
            print(f"  ✓ {pattern:12} {len(names)} header(s) live  ({samples[pattern]})")
        else:
            failures.append(f"{pattern}: missing {', '.join(missing)}")
            print(f"  ✗ {pattern:12} missing: {', '.join(missing)}")

    # -- redirects ---------------------------------------------------------
    for src, dst, status in parse_redirects(ROOT / "_redirects"):
        want = dst if dst.startswith("http") else base + dst
        got: tuple = (None, None)

        def check() -> bool:
            nonlocal got
            code, hdrs = probe(base + src)
            loc = (hdrs or {}).get("location", "")
            got = (code, loc)
            # Cloudflare answers with a relative Location ("/router"), so
            # compare resolved forms rather than the raw strings — otherwise a
            # working redirect reads as a mismatch, which is what the first run
            # of this script reported.
            resolved = urllib.parse.urljoin(base + src, loc) if loc else ""
            return code == status and resolved.rstrip("/") == want.rstrip("/")

        if retry(check):
            print(f"  ✓ {src:16} {status} -> {dst}")
        else:
            failures.append(f"{src}: got {got[0]} -> {got[1] or '(no Location)'}, want {status} -> {want}")
            print(f"  ✗ {src:16} got {got[0]} -> {got[1] or '(no Location)'}")

    if failures:
        print(f"\n  {len(failures)} declared behaviour(s) not live:")
        for f in failures:
            print(f"    - {f}")
        return 1
    print("\n  every declared header and redirect is live")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
