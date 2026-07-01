#!/usr/bin/env python3
"""Fold per-slide narration windows into an extracted slide-deck markdown doc.

Takes the windows file produced by `srt_to_windows.py` (one `## [MM:SS] (Ns)`
block per slide, in slide order) and inserts each slide's text as a
blockquote into the corresponding `## Slide N` section of the doc, placed
immediately after that section's `![sNNN-slide.png]` image reference.

Usage:
    tools/fold_narration.py <doc.md> <windows.txt> [--label "Narration (from talk)"] [--wrap 100]

Edits the doc in place. Idempotency: refuses to run if any `> **<label>:**`
blockquote already exists in the doc, so it is safe to re-run after fixing
the windows file without doubling up narration.
"""
import argparse
import re
import sys
import textwrap
from pathlib import Path


def parse_windows(p: Path) -> list[str]:
    blocks = re.split(r"\n\n+", p.read_text().strip())
    texts = []
    for b in blocks:
        lines = b.strip().split("\n")
        if not lines or not lines[0].startswith("## ["):
            continue
        texts.append(" ".join(lines[1:]).strip())
    return texts


def make_blockquote(label: str, text: str, wrap: int) -> list[str]:
    wrapped = textwrap.wrap(text, width=wrap) or [""]
    lines = [f"> **{label}:** {wrapped[0]}"]
    lines += [f"> {w}" for w in wrapped[1:]]
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("doc", type=Path)
    ap.add_argument("windows", type=Path)
    ap.add_argument("--label", default="Narration (from talk)")
    ap.add_argument("--wrap", type=int, default=100)
    args = ap.parse_args()

    if not args.doc.exists():
        raise SystemExit(f"FATAL: doc not found: {args.doc}")
    if not args.windows.exists():
        raise SystemExit(f"FATAL: windows file not found: {args.windows}")

    texts = parse_windows(args.windows)
    lines = args.doc.read_text().split("\n")

    if any(f"> **{args.label}:**" in l for l in lines):
        raise SystemExit(
            f"FATAL: doc already contains '> **{args.label}:**' blockquotes — "
            "refusing to fold again (would duplicate). Revert the doc first."
        )

    slide_heading_re = re.compile(r"^## Slide (\d+)\b")
    image_re = re.compile(r"^!\[s\d+-slide\.png\]")

    slide_indices = [
        i for i, l in enumerate(lines) if slide_heading_re.match(l)
    ]
    if len(slide_indices) != len(texts):
        raise SystemExit(
            f"FATAL: doc has {len(slide_indices)} '## Slide N' sections but "
            f"windows file has {len(texts)} blocks — counts must match exactly."
        )

    out = []
    slide_ptr = 0
    inserted = 0
    i = 0
    while i < len(lines):
        out.append(lines[i])
        if (
            slide_ptr < len(slide_indices)
            and i >= slide_indices[slide_ptr]
            and image_re.match(lines[i])
        ):
            text = texts[slide_ptr]
            if text:
                out.append("")
                out.extend(make_blockquote(args.label, text, args.wrap))
                inserted += 1
            slide_ptr += 1
        i += 1

    if slide_ptr != len(slide_indices):
        raise SystemExit(
            f"FATAL: only matched {slide_ptr}/{len(slide_indices)} slide image lines — "
            "doc structure doesn't match the one `![sNNN-slide.png]` per slide assumption."
        )

    args.doc.write_text("\n".join(out))
    print(f"Folded narration into {inserted}/{len(texts)} slides in {args.doc}", file=sys.stderr)


if __name__ == "__main__":
    main()
