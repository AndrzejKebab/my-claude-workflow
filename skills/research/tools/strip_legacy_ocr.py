#!/usr/bin/env python3
"""Strip raw OCR-dump blocks from legacy research_video markdown.

Pre-2026-07 `research_video.py` wrote `scene.ocr_text` verbatim into the
document body under every slide. OpenOCR reads top-to-bottom with no column
awareness, so multi-column slides come out interleaved row-by-row into
mangled, sense-losing text. The current tool no longer emits it (the vision
pass owns slide content); this migrates documents produced by the old tool.

The OCR dump is the run of plain-text lines immediately after a section
metadata line (`*[HH:MM] (Ns)*` or `*(Ns)*`), up to the first STRUCTURAL line
(vision block `**`, image `![`, transcript `>`, comment `<!--`, heading `##`,
code fence ```, or table `|`). Those structural lines are preserved verbatim;
only the plain OCR lines are removed, leaving a single blank after the metadata.

Usage:
    strip_legacy_ocr.py --only=<slug>[,<slug>...] [--apply]
    strip_legacy_ocr.py <path.md> [...] [--apply]
Dry-run by default; pass --apply to write in place.
"""
import re
import sys
from pathlib import Path
from research_paths import PREPARED_DIR

PREPARED = PREPARED_DIR

META = re.compile(r'^\*(\[\d{1,2}:\d{2}\][^*]*|\(\d+s\))\*\s*$')
STRUCT_PREFIX = ('**', '![', '>', '<!--', '## ', '### ', '```', '|', '#')


def _is_struct(line: str) -> bool:
    s = line.lstrip()
    return any(s.startswith(p) for p in STRUCT_PREFIX)


def strip_doc(path: Path, apply: bool) -> int:
    lines = path.read_text(encoding='utf-8').split('\n')
    out: list[str] = []
    removed = 0
    i = 0
    while i < len(lines):
        out.append(lines[i])
        if META.match(lines[i]):
            j = i + 1
            ocr = 0
            while j < len(lines):
                if lines[j].strip() == '':
                    j += 1
                    continue
                if _is_struct(lines[j]):
                    break
                ocr += 1
                j += 1
            removed += ocr
            out.append('')          # single blank separator after metadata
            i = j
            continue
        i += 1
    if apply and removed:
        path.write_text('\n'.join(out), encoding='utf-8')
    return removed


def _resolve(args: list[str]) -> list[Path]:
    paths: list[Path] = []
    for a in args:
        if a.startswith('--only='):
            paths += [PREPARED / f"{s}.md" for s in a.split('=', 1)[1].split(',') if s]
        elif not a.startswith('--'):
            paths.append(Path(a))
    return paths


def main() -> None:
    apply = '--apply' in sys.argv
    paths = _resolve(sys.argv[1:])
    if not paths:
        print(__doc__)
        sys.exit(1)
    for p in paths:
        if not p.exists():
            print(f"  MISSING {p}")
            continue
        n = strip_doc(p, apply)
        verb = "stripped" if apply else "would strip"
        print(f"  {verb} {n} OCR line(s) from {p.name}")


if __name__ == '__main__':
    main()
