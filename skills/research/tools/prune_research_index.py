#!/usr/bin/env python3
"""Strike rows from /mnt/archive4/PAPERS/Prepared/index_missing.md by 1-indexed line number.

Companion to `audit_research_index.py`. After /research dispatches add new
papers to the corpus, run the audit to find false-positive rows in
`index_missing.md`, then feed those line numbers here to prune them.

Usage
-----
    python3 tools/prune_research_index.py 115 121 122 140
    python3 tools/prune_research_index.py --dry-run 115 121

The line numbers refer to the CURRENT state of the file, so audit and
prune in the same session — re-run audit between batches to refresh the
numbering.
"""

import argparse
import sys
from pathlib import Path


def prune(index_path: Path, lines_to_remove: set[int], dry_run: bool):
    if not index_path.exists():
        print(f"error: {index_path} not found", file=sys.stderr)
        sys.exit(1)

    src_lines = index_path.read_text().splitlines(keepends=True)
    total = len(src_lines)

    out = []
    removed = []
    for i, line in enumerate(src_lines, start=1):
        if i in lines_to_remove:
            removed.append((i, line.rstrip("\n")))
        else:
            out.append(line)

    print(f"Source: {index_path} ({total} lines)")
    print(f"Removing {len(removed)} rows:")
    for i, text in removed:
        print(f"  L{i}: {text[:120]}")

    missing = lines_to_remove - {i for i, _ in removed}
    if missing:
        print(f"\nWARNING: requested lines not found in file: {sorted(missing)}", file=sys.stderr)

    if dry_run:
        print("\n(dry run — no changes written)")
        return

    index_path.write_text("".join(out))
    print(f"\nWrote {len(out)} lines to {index_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lines", nargs="+", type=int, help="1-indexed line numbers to strike")
    ap.add_argument(
        "--index",
        default="/mnt/archive4/PAPERS/Prepared/index_missing.md",
        type=Path,
        help="Path to index_missing.md (default: /mnt/archive4/PAPERS/Prepared/index_missing.md)",
    )
    ap.add_argument("--dry-run", action="store_true", help="Show what would be removed without writing")
    args = ap.parse_args()
    prune(args.index.resolve(), set(args.lines), args.dry_run)


if __name__ == "__main__":
    main()
