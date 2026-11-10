#!/usr/bin/env python3
"""Empty a worktree's .scratch, leaving the directory itself.

    empty_worktree_scratch.py <worktree> [--dry-run]

Refuses a folder that is not a git worktree, so a stray argument cannot empty anything else. Programs started: none.
"""
import argparse
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('worktree', help='the worktree whose .scratch is emptied')
    parser.add_argument('--dry-run', action='store_true', help='count what would go, delete nothing')
    args = parser.parse_args()
    tree = Path(args.worktree)
    root = tree / '.scratch'
    if not (tree / '.git').exists():
        print(f'refused: {tree} is not a git worktree')
        return 2
    if not root.is_dir():
        print(f'no .scratch at {root}')
        return 1
    files = [p for p in root.rglob('*') if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    if args.dry_run:
        print(f'would delete {len(files)} file(s), {size / 1024 / 1024:.0f} MiB')
        return 0
    for child in root.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child, ignore_errors=True)
        else:
            try:
                child.unlink()
            except OSError:
                pass
    left = sum(1 for p in root.rglob('*') if p.is_file())
    print(f'deleted {len(files)} file(s), {size / 1024 / 1024:.0f} MiB; left {left}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
