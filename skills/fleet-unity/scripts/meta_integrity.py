#!/usr/bin/env python3
"""Check that every .cs under Assets/ has a committed .meta, and that no .meta is orphaned. Programs started: git.

A script without a committed .meta gets a different GUID in every clone, which is how two
clones end up referencing different assets by the same path (#133, #357, #358 all hit this).
Run it against a ref before reviewing or merging a PR that adds scripts.

    python meta_integrity.py                       # origin/main
    python meta_integrity.py --ref <sha> --repo <path>
    python meta_integrity.py --staged              # what a PR would add, from the index

Exit codes: 0 clean, 1 findings, 2 unable to read the ref.
"""
import argparse
import subprocess
import sys


def native(path):
    """MSYS-style /f/... paths are not usable as a cwd or argument for native git on Windows."""
    import os
    import re
    m = re.fullmatch(r"/([A-Za-z])/(.*)", path or "")
    if os.name == "nt" and m:
        return f"{m.group(1).upper()}:/{m.group(2)}"
    return path


def git(repo, *args):
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=repo)


def tree_files(repo, ref):
    out = git(repo, "ls-tree", "-r", "--name-only", ref, "Assets/")
    if out.returncode != 0:
        return None
    return [line for line in out.stdout.split("\n") if line]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", default="origin/main", help="git ref to check (default origin/main)")
    ap.add_argument("--repo", default=".", help="repository path")
    ap.add_argument("--staged", action="store_true", help="check the index instead of a ref")
    args = ap.parse_args()
    args.repo = native(args.repo)

    if args.staged:
        out = git(args.repo, "diff", "--cached", "--name-only", "--diff-filter=AM")
        touched = [f for f in out.stdout.split("\n") if f]
        added_cs = [f for f in touched if f.endswith(".cs") and f.startswith("Assets/")]
        added_meta = set(f for f in touched if f.endswith(".cs.meta"))
        missing = [f for f in added_cs if f + ".meta" not in added_meta]
        print(f"staged .cs under Assets: {len(added_cs)}, staged without their .meta: {len(missing)}")
        for f in missing:
            print("  NO META", f)
        return 1 if missing else 0

    files = tree_files(args.repo, args.ref)
    if files is None:
        print(f"cannot read ref {args.ref}", file=sys.stderr)
        return 2

    cs = [f for f in files if f.endswith(".cs")]
    metas = set(f for f in files if f.endswith(".cs.meta"))
    missing = [f for f in cs if f + ".meta" not in metas]
    orphans = [m for m in metas if m[:-5] not in cs]

    print(f"{args.ref}: {len(cs)} .cs under Assets, {len(missing)} without a .meta, {len(orphans)} orphan .meta")
    for f in missing:
        print("  NO META", f)
    for m in orphans:
        print("  ORPHAN ", m)
    return 1 if (missing or orphans) else 0


if __name__ == "__main__":
    sys.exit(main())
