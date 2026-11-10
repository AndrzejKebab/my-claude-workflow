#!/usr/bin/env python3
"""Park a repository's uncommitted changes outside the tree, then put them back byte for byte. Programs started: git.

The problem it solves: a branch switch refuses while tracked files are dirty, and the dirty files
belong to somebody else - the owner's own work in the main clone. Stashing or `checkout --` discards
them; this copies them out first, records an md5 per file, and restores only after verifying.

    python dirty_preserve.py save --repo <repo> --store <dir> [--paths Data/ ProjectSettings/]
    python dirty_preserve.py check --store <dir>        # store intact, nothing written
    python dirty_preserve.py restore --store <dir>      # copies back, then verifies every md5
    python dirty_preserve.py list --repo <repo>         # what is dirty right now

`save` records tracked modifications, staged modifications and untracked files (not ignored ones).
`restore` refuses to overwrite a file whose current content differs from the store unless --force,
so it cannot silently clobber newer work.

Exit codes: 0 ok, 1 verification failed, 2 unusable input.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys


def parse_args():
    ap = argparse.ArgumentParser(add_help=True)
    sub = ap.add_subparsers(dest="command", required=True)

    save = sub.add_parser("save")
    save.add_argument("--repo", required=True)
    save.add_argument("--store", required=True)
    save.add_argument("--paths", nargs="*", default=[],
                      help="only these pathspecs (default: everything dirty)")

    for name in ("check", "restore"):
        p = sub.add_parser(name)
        p.add_argument("--store", required=True)
        p.add_argument("--force", action="store_true", help="overwrite a file that changed since the save")

    lst = sub.add_parser("list")
    lst.add_argument("--repo", required=True)
    return ap.parse_args()


def git(repo, *args):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout


def dirty_paths(repo, paths):
    limited = list(paths)
    out = git(repo, "status", "--porcelain", "--", *limited) if limited else git(repo, "status", "--porcelain")
    found = []
    for line in out.splitlines():
        if not line.strip():
            continue
        rel = line[3:]
        if " -> " in rel:                       # rename: keep the new name
            rel = rel.split(" -> ", 1)[1]
        found.append(rel.strip().strip('"'))
    return found


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def cmd_save(args):
    repo = os.path.abspath(args.repo)
    store = os.path.abspath(args.store)
    if not os.path.isdir(os.path.join(repo, ".git")) and not os.path.isfile(os.path.join(repo, ".git")):
        print(f"not a git worktree: {repo}", file=sys.stderr)
        return 2

    paths = dirty_paths(repo, args.paths)
    if not paths:
        print("nothing dirty - nothing to save")
        return 0

    files_dir = os.path.join(store, "files")
    manifest = {}
    for rel in paths:
        source = os.path.join(repo, rel)
        if not os.path.exists(source):
            print(f"  skip (deleted in the tree): {rel}")
            continue
        target = os.path.join(files_dir, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(source, target)
        manifest[rel] = md5(source)
        print(f"  saved {rel}  {manifest[rel]}")

    os.makedirs(store, exist_ok=True)
    with open(os.path.join(store, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump({"repo": repo, "files": manifest}, handle, indent=2, sort_keys=True)

    print(f"saved {len(manifest)} file(s) to {store}")
    return 0


def load_store(store):
    path = os.path.join(store, "manifest.json")
    if not os.path.isfile(path):
        raise SystemExit(f"no manifest in {store}")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def cmd_check(args):
    store = os.path.abspath(args.store)
    data = load_store(store)
    bad = 0
    for rel, digest in sorted(data["files"].items()):
        path = os.path.join(store, "files", rel)
        if not os.path.isfile(path):
            print(f"  MISSING {rel}")
            bad += 1
            continue
        actual = md5(path)
        if actual != digest:
            print(f"  CHANGED {rel}  {digest} -> {actual}")
            bad += 1
    print(f"checked {len(data['files'])} file(s), {bad} bad")
    return 0 if bad == 0 else 1


def cmd_restore(args):
    store = os.path.abspath(args.store)
    data = load_store(store)
    repo = data["repo"]
    restored = 0
    for rel, digest in sorted(data["files"].items()):
        source = os.path.join(store, "files", rel)
        target = os.path.join(repo, rel)
        if not os.path.isfile(source):
            print(f"  MISSING in store: {rel}", file=sys.stderr)
            return 1
        if os.path.exists(target) and md5(target) != digest and not args.force:
            print(f"  REFUSING {rel}: the working copy changed since the save (use --force to overwrite)", file=sys.stderr)
            return 1
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(source, target)
        if md5(target) != digest:
            print(f"  VERIFY FAILED {rel}", file=sys.stderr)
            return 1
        restored += 1
        print(f"  restored {rel}  {digest}")
    print(f"restored {restored} file(s) into {repo}")
    return 0


def cmd_list(args):
    for rel in dirty_paths(os.path.abspath(args.repo), []):
        print(rel)
    return 0


def main():
    args = parse_args()
    return {"save": cmd_save, "check": cmd_check, "restore": cmd_restore, "list": cmd_list}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
