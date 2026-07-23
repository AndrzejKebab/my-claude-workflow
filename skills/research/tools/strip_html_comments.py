#!/usr/bin/env python3
"""Mechanically strip every HTML comment from a prepared research document.

The /research passes use `<!-- … -->` comments as an inter-pass channel:
`<!-- FIXME(extract) -->` (Pass 1 work-list), `<!-- FIXME(vision) -->` (Pass 2
uncertainty), `<!-- vision: reconstructed … -->` (provenance anchors),
`<!-- vision-skip … -->`. They are scaffolding, not deliverable content — the
finished document should carry none of them.

Deleting them is a mechanical regex sweep, so it does NOT belong in an agent's
Edit loop: an agent removing ~90 markers one call at a time is pure token spend
for a transformation a script does deterministically and reversibly. The
refiner's job is the *judgment* — resolving what each FIXME flags against the
render — not the bookkeeping of removing the marker afterward. This tool is the
bookkeeping.

Auditability is not lost by stripping the provenance markers: every vision
reconstruction keeps its `![sNNN-slide.png]` frame embedded directly below it,
so "verify this reconstruction against the image" still works — the marker was
a convenience anchor, the frame is the ground truth.

Safety / recoverability (the "recovered in case of error" requirement):
  * a timestamped backup is written next to the file before any change, unless
    --no-backup;
  * --dry-run reports what would be removed and writes nothing;
  * a unified diff is printed so the change is auditable at a glance;
  * the sweep only removes comment spans — it never touches a line's
    non-comment text, and it refuses (exit 3) if the post-strip text differs
    from the input by anything other than removed `<!-- … -->` spans and the
    whitespace/blank-line collapse that leaves behind.

Usage:
    strip_html_comments.py --only=<slug> [--dry-run] [--no-backup]
    strip_html_comments.py <path.md>     [--dry-run] [--no-backup]

Exit codes:
    0  stripped (or already clean, or dry-run)
    2  file not found / bad args
    3  self-check failed (would have changed non-comment text) — nothing written
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
import time

PREPARED = "/mnt/archive4/PAPERS/Prepared"

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"(?m)^[ \t]*<!--.*?-->[ \t]*\n", re.DOTALL)


def strip_comments(text: str) -> str:
    # First remove comments that occupy whole lines (single- or multi-line
    # blocks), taking their trailing newline so no blank line is left behind.
    without = LINE_COMMENT_RE.sub("", text)
    # Then remove any remaining inline comments, keeping the rest of the line.
    without = COMMENT_RE.sub("", without)
    without = re.sub(r"[ \t]+\n", "\n", without)
    without = re.sub(r"\n{3,}", "\n\n", without)
    return without


def verify_only_comments_removed(original: str, stripped: str) -> bool:
    """Non-comment content must be byte-for-byte preserved (whitespace aside).

    Strip the comment spans from the original, drop ALL whitespace from both
    sides, and require the remaining character streams to be identical — so the
    sweep cannot have dropped, reordered, or altered a single non-comment,
    non-whitespace character (e.g. a `-->` embedded in real prose, or code that
    happens to contain `<!--`).
    """
    core_original = re.sub(r"\s+", "", COMMENT_RE.sub("", original))
    core_stripped = re.sub(r"\s+", "", stripped)
    return core_original == core_stripped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", nargs="?", help="path to <slug>.md")
    ap.add_argument("--only", help="slug under /mnt/archive4/PAPERS/Prepared/")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    args = ap.parse_args()

    if args.only:
        path = os.path.join(PREPARED, f"{args.only}.md")
    elif args.path:
        path = args.path
    else:
        print("give --only=<slug> or a path", file=sys.stderr)
        return 2
    if not os.path.isfile(path):
        print(f"not found: {path}", file=sys.stderr)
        return 2

    original = open(path, encoding="utf-8").read()
    n_comments = len(COMMENT_RE.findall(original))
    if n_comments == 0:
        print(f"[strip] {path}: already clean (0 comments)")
        return 0

    stripped = strip_comments(original)
    if not verify_only_comments_removed(original, stripped):
        print("[strip] SELF-CHECK FAILED — would alter non-comment text; wrote nothing", file=sys.stderr)
        return 3

    diff = difflib.unified_diff(
        original.splitlines(), stripped.splitlines(),
        fromfile=f"{path} (before)", tofile=f"{path} (after)", lineterm="",
    )
    removed = [l for l in diff if l.startswith("-") and not l.startswith("---")]
    print(f"[strip] {path}: {n_comments} comment span(s), {len(removed)} line(s) changed")
    for l in removed[:40]:
        print("   " + l)
    if len(removed) > 40:
        print(f"   … +{len(removed) - 40} more")

    if args.dry_run:
        print("[strip] --dry-run: no changes written")
        return 0

    if not args.no_backup:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = f"{path}.prestrip-{stamp}.bak"
        with open(backup, "w", encoding="utf-8") as fh:
            fh.write(original)
        print(f"[strip] backup: {backup}  (delete after verifying; `cp` it back to restore)")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(stripped)
    print(f"[strip] wrote {path} — {len(COMMENT_RE.findall(open(path, encoding='utf-8').read()))} comments remain")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
