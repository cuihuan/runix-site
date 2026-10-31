#!/usr/bin/env python3
"""Keep production, origin/site and the deploying working copy the same tree.

Production is a direct upload from whichever working copy runs ./deploy.sh, so
nothing else stops a deploy from replacing newer work. That happened: on
2026-10-31 two deploys went live from commits that were not on origin yet, and
the 2026-09-07 deploy rewrote assets at deploy time without committing them,
which is how style.css?v=59 came to exist twice with different bytes.

The rule this enforces: origin/site is what production serves.

    deploy_provenance.py check    before anything rewrites the tree
    deploy_provenance.py record   after the rewrites and checks, before upload
    deploy_provenance.py push     right after the upload succeeds

check refuses when
  - the working tree has changes (they would ship without being in git),
  - origin/site has commits HEAD does not (you would deploy over them),
  - the live deployment was built from a commit HEAD does not contain.
record commits whatever the deploy-time builders rewrote, so the commit that
wrangler stamps on the deployment is exactly what was uploaded.
push sends HEAD to origin/site without force.

DEPLOY_FORCE="<reason>" turns check's refusals into warnings (rollbacks,
emergencies). It never forces a push. To roll back, prefer Cloudflare's own
rollback (dashboard, or POST .../deployments/<id>/rollback): it redeploys a
previous build without touching git.

Reads CLOUDFLARE_API_TOKEN (the same one wrangler uses) and
CLOUDFLARE_ACCOUNT_ID from the environment.
"""
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

PROJECT = os.environ.get("PAGES_PROJECT", "runix-site")
REMOTE = "origin"
BRANCH = "site"
UPSTREAM = f"{REMOTE}/{BRANCH}"


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def is_ancestor(a, b):
    return git("merge-base", "--is-ancestor", a, b, check=False).returncode == 0


def has_commit(sha):
    return git("cat-file", "-e", f"{sha}^{{commit}}", check=False).returncode == 0


def live_deployment():
    # For tools/test_deploy_provenance.sh only. Loud on purpose: it replaces the
    # one fact this check exists to read.
    fake = os.environ.get("DEPLOY_PROVENANCE_TEST_LIVE_COMMIT")
    if fake:
        print(f"    TEST MODE: pretending production serves {fake[:10]}", file=sys.stderr)
        return {"id": "test", "created": "test", "commit": fake, "dirty": False, "message": "test"}
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    account = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    if not token or not account:
        raise RuntimeError("CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID must be set")
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/pages/projects/{PROJECT}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.load(resp)["result"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Pages API {e.code} for {PROJECT}") from None
    dep = result.get("canonical_deployment") or {}
    meta = (dep.get("deployment_trigger") or {}).get("metadata") or {}
    return {
        "id": dep.get("short_id"),
        "created": (dep.get("created_on") or "")[:16],
        "commit": meta.get("commit_hash") or "",
        "dirty": bool(meta.get("commit_dirty")),
        "message": (meta.get("commit_message") or "").splitlines()[0][:72] if meta.get("commit_message") else "",
    }


def check():
    force = os.environ.get("DEPLOY_FORCE", "").strip()
    problems, notes = [], []

    if git("fetch", "--quiet", REMOTE, BRANCH, check=False).returncode != 0:
        problems.append(f"could not fetch {UPSTREAM}; cannot tell whether someone else is ahead")

    dirty = [l for l in git("status", "--porcelain").stdout.splitlines() if l.strip()]
    if dirty:
        shown = ", ".join(l[3:] for l in dirty[:5]) + (" ..." if len(dirty) > 5 else "")
        problems.append(f"working tree has {len(dirty)} uncommitted change(s): {shown}. "
                        "Commit them or stash them; a deploy ships the tree, not the commit")

    if git("rev-parse", "--verify", "--quiet", UPSTREAM, check=False).returncode == 0:
        if not is_ancestor(UPSTREAM, "HEAD"):
            behind = git("rev-list", "--count", f"HEAD..{UPSTREAM}").stdout.strip()
            problems.append(f"{UPSTREAM} has {behind} commit(s) HEAD does not. "
                            f"Run: git pull --ff-only {REMOTE} {BRANCH}")
    else:
        problems.append(f"{UPSTREAM} does not exist locally")

    try:
        live = live_deployment()
    except RuntimeError as e:
        live = None
        problems.append(f"could not read the live deployment ({e})")
    if live:
        label = f"live {live['id']} ({live['created']}) from {live['commit'][:10] or 'unknown commit'}"
        if not live["commit"]:
            notes.append(f"{label}: the deployment records no commit, so it cannot be compared")
        elif not has_commit(live["commit"]):
            problems.append(f"{label} '{live['message']}' is a commit this clone has never seen. "
                            "It was deployed from another working copy and not pushed; "
                            "get it from whoever deployed it before replacing it")
        elif not is_ancestor(live["commit"], "HEAD"):
            problems.append(f"{label} '{live['message']}' is not in HEAD's history; "
                            "deploying now would remove that work from production")
        else:
            notes.append(f"{label}: contained in HEAD")
        if live["dirty"]:
            notes.append("the live build was made from a dirty tree, so files it rewrote at deploy "
                         "time may not be in git; check that ?v= numbers only go up")

    print(f"    HEAD {git('rev-parse', '--short', 'HEAD').stdout.strip()} "
          f"on {git('rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()}")
    for n in notes:
        print(f"    note: {n}")
    for p in problems:
        print(f"    {'WARNING' if force else 'REFUSED'}: {p}", file=sys.stderr)
    if problems and not force:
        print("    Not deploying. DEPLOY_FORCE='<reason>' overrides this check "
              "(it does not force the push).", file=sys.stderr)
        return 1
    if problems:
        print(f"    DEPLOY_FORCE set: {force}", file=sys.stderr)
    return 0


def record():
    changed = [l for l in git("status", "--porcelain").stdout.splitlines() if l.strip()]
    if not changed:
        print("    deploy-time builders changed nothing; HEAD is what ships")
        return 0
    git("add", "-A")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = "\n".join(f"  {l}" for l in changed[:40])
    if len(changed) > 40:
        body += f"\n  ... and {len(changed) - 40} more"
    git("commit", "--quiet", "-m", f"Deploy {stamp}: files rewritten at deploy time\n\n"
        "Recorded by tools/deploy_provenance.py before upload, so the deployed\n"
        f"commit is the uploaded tree.\n\n{body}")
    print(f"    recorded {len(changed)} rewritten file(s) as {git('rev-parse', '--short', 'HEAD').stdout.strip()}")
    return 0


def push():
    r = git("push", "--quiet", REMOTE, f"HEAD:{BRANCH}", check=False)
    head = git("rev-parse", "--short", "HEAD").stdout.strip()
    if r.returncode == 0:
        print(f"    {UPSTREAM} is now {head}, the commit production serves")
        return 0
    print(f"    PUSH FAILED: production now serves {head}, but {UPSTREAM} was not updated:\n"
          f"      {r.stderr.strip()}\n"
          f"    Someone pushed in the meantime. Run git pull --rebase {REMOTE} {BRANCH}, "
          "then git push and ./deploy.sh again, or the next deploy from another copy "
          "will be refused against this one.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        sys.exit({"check": check, "record": record, "push": push}[cmd]())
    except KeyError:
        sys.exit(__doc__)
    except RuntimeError as e:
        print(f"    {e}", file=sys.stderr)
        sys.exit(1)
