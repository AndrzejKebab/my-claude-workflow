#!/usr/bin/env python3
"""Audit /mnt/archive4/PAPERS/Prepared/index_missing.md against the actual corpus.

Reads every row in the "missing" tables of `/mnt/archive4/PAPERS/Prepared/index_missing.md`,
extracts the (first-author surname, year) key, and checks whether a corpus
file in `/mnt/archive4/PAPERS/Prepared/` already starts with `<surname>-<year>-`.

When a match is found, the row is a likely false positive — the paper has
been ingested but never struck from the missing list. Use this after a
batch of /research dispatches to find rows you can prune.

Usage
-----
    python3 tools/audit_research_index.py
    python3 tools/audit_research_index.py --research-dir /mnt/archive4/PAPERS/Prepared

Same-surname collisions (e.g. Annen 2007 vs Annen 2008) are reported but
require human triage — only matches where surname AND year both align with
a corpus filename are flagged as "year_match"; surname-only hits are
"surname_only" and are usually different works by the same author.
"""

import argparse
import os
import re
import sys
from pathlib import Path


def normalise_surname(s: str) -> str:
    return (
        s.lower()
        .replace("ö", "o")
        .replace("é", "e")
        .replace("ü", "u")
        .replace("ä", "a")
        .replace("á", "a")
        .replace("í", "i")
        .replace("ñ", "n")
    )


def extract_first_surname(author_field: str) -> str:
    return re.split(r"[,;&]| et al\.| and ", author_field)[0].strip()


def first_year(year_field: str) -> str:
    m = re.search(r"\b(19|20)\d{2}\b", year_field)
    return m.group(0) if m else ""


def parse_table_rows(lines):
    """Yield (line_no, author, year, title, cited_by) for each missing-table row."""
    for idx, line in enumerate(lines, start=1):
        if not line.startswith("| "):
            continue
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 4:
            continue
        author, year, title, cited_by = cols[0], cols[1], cols[2], cols[3]
        if author in ("Authors", "Current") or author.startswith("---"):
            continue
        yield idx, author, year, title, cited_by


def audit(research_dir: Path):
    index = research_dir / "index_missing.md"
    if not index.exists():
        print(f"error: {index} not found", file=sys.stderr)
        sys.exit(1)

    corpus = sorted(
        p.name.lower()
        for p in research_dir.glob("*.md")
        if p.name not in {"index.md", "index_missing.md", "renames.md"}
        and not p.name.startswith("index_extracted_pending-")
    )

    year_matches = []
    surname_only = []

    for line_no, author, year, title, cited_by in parse_table_rows(index.read_text().splitlines(keepends=True)):
        surname = normalise_surname(extract_first_surname(author))
        if not surname:
            continue
        yr = first_year(year)
        candidates = [
            c for c in corpus if c.startswith(surname + "-") or c.startswith(surname + "_")
        ]
        if not candidates:
            continue
        year_hits = [c for c in candidates if yr and yr in c]
        if year_hits:
            year_matches.append((line_no, author, year, title[:90], year_hits))
        else:
            surname_only.append((line_no, author, year, title[:90], candidates))

    print("=" * 72)
    print(f"YEAR + SURNAME matches ({len(year_matches)}) — likely false positives")
    print("=" * 72)
    for line_no, author, year, title, hits in year_matches:
        print(f"L{line_no}: {author} ({year}) — {title}")
        for h in hits:
            print(f"    -> {h}")
        print()

    print("=" * 72)
    print(f"SURNAME-only matches ({len(surname_only)}) — usually different works, verify manually")
    print("=" * 72)
    for line_no, author, year, title, hits in surname_only:
        print(f"L{line_no}: {author} ({year}) — {title}")
        for h in hits:
            print(f"    -> {h}")
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--research-dir",
        default="/mnt/archive4/PAPERS/Prepared",
        type=Path,
        help="Path to the research corpus (default: /mnt/archive4/PAPERS/Prepared)",
    )
    args = ap.parse_args()
    audit(args.research_dir.resolve())


if __name__ == "__main__":
    main()
