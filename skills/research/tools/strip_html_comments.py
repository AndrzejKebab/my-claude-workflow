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
from research_paths import PREPARED_DIR

PREPARED = str(PREPARED_DIR)

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


def strip_comments(text: str) -> str:
    """Remove every <!-- ... --> span.

    A comment that occupies its own line (nothing but whitespace before it and
    after it, up to the surrounding newlines) has its whole line — including
    the trailing newline — removed, so no blank line is left behind. A comment
    sharing its line with real content (e.g. inserted mid-sentence, splitting
    a paragraph) has just the comment span removed, leaving the surrounding
    prose untouched.

    Deliberately NOT implemented as a second whole-line regex pass: an anchored
    `^[ \t]*<!--.*?-->[ \t]*\n` pattern backtracks past a comment whose own
    `-->` is followed by same-line trailing text, and keeps searching for the
    next `-->` that IS immediately followed by end-of-line — silently
    swallowing every real line in between (headings, images, whole sections)
    as "comment". Matching once via the plain non-backtracking COMMENT_RE and
    then classifying each match's own line post-hoc avoids that hazard
    entirely. (Observed 2026-07-29 on a real document: a FIXME(vision) comment
    inserted mid-sentence — `<!-- ... --> trailing prose` — caused the old
    regex to swallow the rest of that section, the next heading, and the start
    of the following comment before finding a line-terminating `-->`. The
    self-check correctly refused to write, but the root cause was in this
    function, not the document.)
    """
    out = []
    last = 0
    for m in COMMENT_RE.finditer(text):
        start, end = m.span()
        line_start = text.rfind("\n", 0, start) + 1
        nl = text.find("\n", end)
        line_end = nl if nl != -1 else len(text)
        whole_line = text[line_start:start].strip() == "" and text[end:line_end].strip() == ""
        if whole_line:
            out.append(text[last:line_start])
            last = line_end + 1 if nl != -1 else line_end
        else:
            out.append(text[last:start])
            last = end
    out.append(text[last:])
    without = "".join(out)
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
    ap.add_argument("--only", help="slug under <RESEARCH_ROOT>/Prepared/")
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
