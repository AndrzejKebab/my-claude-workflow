#!/usr/bin/env python
"""Clear Unity's script-compile caches after an Editor upgrade, refusing to descend through links.

An Editor version bump leaves `Library/Bee`, `Library/ScriptAssemblies` and `Library/BuildPlayerData`
stale, and the next batch run then stalls with the Editor idle. This clears exactly those three.

It refuses to run if any of them contains a symlink or junction, and it never touches `Library` as a
whole and never anything under `Packages/`: recursive deletes through this project's package links
have destroyed neighbouring content before.

Usage:
    python clear_caches.py --project F:/Unity/Projects/VoxelGame-worker-5
    python clear_caches.py --project ... --dry-run
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

TARGETS = ["Library/Bee", "Library/ScriptAssemblies", "Library/BuildPlayerData"]


def has_link(root: str) -> str | None:
    for dirpath, dirnames, _ in os.walk(root):
        for name in dirnames:
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                return full
            if os.name == "nt" and hasattr(os.path, "isjunction") and os.path.isjunction(full):
                return full
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, help="Unity project root (the folder holding Library)")
    parser.add_argument("--dry-run", action="store_true", help="say what would be cleared and stop")
    args = parser.parse_args()

    library = os.path.join(args.project, "Library")
    if not os.path.isdir(library):
        print("no Library under", args.project)
        return 1

    for target in TARGETS:
        path = os.path.join(args.project, *target.split("/"))
        if not os.path.exists(path):
            print("absent", target)
            continue
        link = has_link(path)
        if link:
            print(f"REFUSING to delete {target}: it contains a link ({link})")
            return 3
        if args.dry_run:
            print("would clear", target)
            continue
        shutil.rmtree(path)
        print("cleared", target)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
