#!/usr/bin/env python3
"""Clean up formatting in extracted research markdown files."""

import sys
import re
from pathlib import Path

# The extracted markdown corpus lives at a global location independent of cwd /
# which project invoked /research. `Prepared` is the primary-source bundle and
# the default; `Articles` holds secondary material (tutorials, blog posts,
# community write-ups) and is reached with `--research-dir`, matching
# validate_research.py's flag of the same name.
DEFAULT_DIR = Path("/mnt/archive4/PAPERS/Prepared")

# Repeated footer/watermark lines to strip from PPTX-sourced slides
STRIP_LINES = [
    "Advances in Real-Time Rendering in 3D Graphics and Games - SIGGRAPH 2019",
    "Advances in Real-Time Rendering in 3D Graphics and Games",
    "Advances in Real-Time Rendering in Games Course",
    "Advances in Real-Time Rendering, Siggraph 2017",
]


def is_garbage_ocr(text: str) -> bool:
    """Detect OCR output that is mostly noise (short, mostly punctuation/whitespace)."""
    clean = re.sub(r'[^a-zA-Z0-9]', '', text)
    if len(clean) < 10 and len(text) > 5:
        return True
    return False


def cleanup_file(path: Path) -> tuple[str, int]:
    """Clean up a single markdown file. Returns (slug, change_count)."""
    content = path.read_text(encoding="utf-8")
    original = content
    changes = 0

    lines = content.split("\n")
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # 1. Remove repeated footer/watermark lines
        stripped = line.strip()
        if stripped in STRIP_LINES:
            changes += 1
            i += 1
            continue

        # 2. Remove duplicate heading text in body
        # Pattern: ## Slide N -- Title\n\nTitle\n...
        heading_match = re.match(r"## (?:Page|Slide) \d+ -- (.+)", line)
        if heading_match:
            heading_text = heading_match.group(1).strip()
            new_lines.append(line)
            i += 1
            # Skip blank line after heading
            while i < len(lines) and lines[i].strip() == "":
                new_lines.append(lines[i])
                i += 1
            # If next non-blank line duplicates the heading, skip it
            if i < len(lines) and lines[i].strip() == heading_text:
                changes += 1
                i += 1
            continue

        # 3. Remove garbage OCR blocks
        if line.startswith("> **OCR Text:**"):
            # Collect the OCR block
            ocr_lines = [line]
            j = i + 1
            while j < len(lines) and lines[j].startswith(">"):
                ocr_lines.append(lines[j])
                j += 1
            # Extract text content (strip > prefix)
            ocr_text = "\n".join(l.lstrip("> ").strip() for l in ocr_lines[1:])
            if is_garbage_ocr(ocr_text):
                changes += 1
                i = j
                # Skip trailing blank lines
                while i < len(lines) and lines[i].strip() == "":
                    i += 1
                continue
            else:
                # Keep good OCR
                new_lines.extend(ocr_lines)
                i = j
                continue

        # 4. Remove standalone page numbers (just a number on its own line)
        if re.match(r'^\d{1,3}$', stripped) and stripped != "0":
            # Check context: should be between text content, not in code blocks
            prev_non_blank = ""
            for k in range(len(new_lines) - 1, -1, -1):
                if new_lines[k].strip():
                    prev_non_blank = new_lines[k].strip()
                    break
            # Only strip if previous line is text (not a heading or image)
            if not prev_non_blank.startswith("#") and not prev_non_blank.startswith("!"):
                changes += 1
                i += 1
                continue

        new_lines.append(line)
        i += 1

    content = "\n".join(new_lines)

    # 5. Ensure blank line before ## headings
    content = re.sub(r'([^\n])\n(## )', r'\1\n\n\2', content)

    # 6. Collapse 3+ consecutive blank lines to 2
    content = re.sub(r'\n{4,}', '\n\n\n', content)

    # 7. Remove trailing whitespace on lines
    content = re.sub(r' +\n', '\n', content)

    if content != original:
        path.write_text(content, encoding="utf-8")

    return path.stem, changes


def main():
    # `--only=SLUG[,SLUG2]` scopes cleanup to specific docs (matches
    # validate_research.py). Absent, every per-slug `<slug>.md` is cleaned.
    only_slugs: set[str] | None = None
    research_dir = DEFAULT_DIR
    for arg in sys.argv[1:]:
        if arg.startswith("--only="):
            slugs = {s.strip() for s in arg.split("=", 1)[1].split(",") if s.strip()}
            only_slugs = slugs if slugs else None
        elif arg.startswith("--research-dir="):
            research_dir = Path(arg.split("=", 1)[1])
        elif arg.startswith("-"):
            raise SystemExit(f"cleanup_research.py: unknown flag {arg!r}")

    if not research_dir.is_dir():
        raise SystemExit(f"cleanup_research.py: no such directory: {research_dir}")

    total_changes = 0
    seen: set[str] = set()
    for md_file in sorted(research_dir.glob("*.md")):
        # Skip non-slug bookkeeping files (index*.md) and per-slug regen
        # sidecars — neither is a canonical extraction.
        if md_file.name.startswith("index") or ".regen-" in md_file.name:
            continue
        if only_slugs and md_file.stem not in only_slugs:
            continue
        seen.add(md_file.stem)
        slug, changes = cleanup_file(md_file)
        if changes:
            print(f"  {slug}: {changes} fixes")
            total_changes += changes
        else:
            print(f"  {slug}: clean")

    # A slug that matched nothing is a failure, not a clean run. Silently
    # reporting "0 fixes applied" for a document in the other bundle is
    # indistinguishable from success, and that is exactly how three documents
    # got shipped past this script without it ever having read them.
    if only_slugs and (missing := sorted(only_slugs - seen)):
        raise SystemExit(
            f"cleanup_research.py: no document found in {research_dir} for: {', '.join(missing)}\n"
            f"  (a doc in the other bundle needs --research-dir=/mnt/archive4/PAPERS/Articles)"
        )
    print(f"\nTotal: {total_changes} fixes applied")


if __name__ == "__main__":
    main()
