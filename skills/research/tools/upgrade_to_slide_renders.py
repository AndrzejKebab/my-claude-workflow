#!/usr/bin/env python3
"""Upgrade an already-extracted slide-deck research entry from per-figure cutouts
to per-page rendered slide images, in place, without clobbering curated content.

Why this exists: extract_research.py's old behaviour pulled embedded image
objects out of slide-deck PDFs / PPTXs, producing many useless cutouts per
slide (chart chrome split from plot, photo split from frame, decorative banner
separated from photo, etc.). The new behaviour renders each slide once. This
script migrates entries that were extracted under the old rules to the new
layout — without touching summaries, vision-pass
LaTeX, fixed headings, speaker-notes blockquotes, or any other curated content.

Usage:
    uv run --project <research-skill-dir> python tools/upgrade_to_slide_renders.py SLUG \\
        --source /path/to/source.pdf [--scale 2.0] [--no-delete-cutouts]

What it does:
    1. Render every page of the source PDF (or PPTX → PDF via LibreOffice) as
       a single PNG at <scale>× resolution into assets/<slug>/pNNN-slide.png.
    2. Walk the markdown section by section. Inside each `## Page N -- ...`
       section, find every `![...](assets/<slug>/pNNN-figXX.png)` line
       (possibly separated by blank lines) and replace the whole block with
       one `![pNNN-slide.png](assets/<slug>/pNNN-slide.png)` line.
    3. Update the YAML frontmatter to record `slide_deck: true`.
    4. Delete the old `pNNN-figXX.png` cutouts (unless --no-delete-cutouts).

Sections that already use `pNNN-slide.png` (or have no image refs at all) are
left alone.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import fitz
from research_paths import PREPARED_DIR

# The extracted markdown corpus lives at a single hardcoded global location,
# independent of cwd / which project invoked /research.
RESEARCH_DIR = PREPARED_DIR
PROJECT_ROOT = RESEARCH_DIR  # display base for relative_to() in log output
ASSETS_DIR = RESEARCH_DIR / "assets"


def find_libreoffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        which = shutil.which(name)
        if which:
            return which
    for candidate in (
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ):
        if os.path.exists(candidate):
            return candidate
    return None


def pptx_to_pdf(pptx_path: str) -> str:
    soffice = find_libreoffice()
    if not soffice:
        raise SystemExit(
            "LibreOffice (soffice) not found. Install: pacman -S libreoffice-fresh "
            "(Arch) / apt install libreoffice (Debian) / brew install --cask libreoffice (macOS)."
        )
    out_dir = tempfile.mkdtemp(prefix="research-pptx-render-")
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, pptx_path],
        check=True,
        capture_output=True,
    )
    pdf_path = os.path.join(out_dir, Path(pptx_path).stem + ".pdf")
    if not os.path.exists(pdf_path):
        raise SystemExit(f"LibreOffice did not produce expected PDF at {pdf_path}")
    return pdf_path


def render_slides(source_path: str, slug: str, scale: float) -> int:
    """Render every page of the (PDF or PPTX) source as pNNN-slide.png. Returns page count."""
    if source_path.lower().endswith(".pptx"):
        print(f"  converting PPTX → PDF via LibreOffice (this may take 30-60s)...")
        pdf_path = pptx_to_pdf(source_path)
    else:
        pdf_path = source_path

    doc = fitz.open(pdf_path)
    slug_assets = ASSETS_DIR / slug
    slug_assets.mkdir(parents=True, exist_ok=True)

    n = len(doc)
    for i in range(n):
        page = doc[i]
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        out_path = slug_assets / f"p{i+1:03d}-slide.png"
        pix.save(str(out_path))
        if (i + 1) % 50 == 0 or i + 1 == n:
            print(f"  rendered {i+1}/{n} slides")
    doc.close()
    return n


# Match a section heading like `## Page 7 -- Some Title` or `## Slide 12 ...`.
SECTION_RE = re.compile(r"(?m)^## (?:Page|Slide) (\d+)(?: -- .*)?$")


def rewrite_markdown(md_path: Path, slug: str) -> tuple[int, int]:
    """In each section, replace cutout image refs with one slide-render ref.

    Returns (sections_rewritten, cutout_refs_removed).
    """
    text = md_path.read_text(encoding="utf-8")

    # Update frontmatter — add `slide_deck: true` if missing
    fm_match = re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL)
    if fm_match and "slide_deck:" not in fm_match.group(1):
        new_fm = fm_match.group(1).rstrip("\n") + "\nslide_deck: true\n"
        text = "---\n" + new_fm + "---\n" + text[fm_match.end() :]

    matches = list(SECTION_RE.finditer(text))
    if not matches:
        print("  no `## Page N` / `## Slide N` sections found — nothing to rewrite")
        return (0, 0)

    chunks: list[str] = [text[: matches[0].start()]]
    sections_rewritten = 0
    cutouts_removed = 0

    cutout_re = re.compile(
        rf"^!\[[^]]*\]\(assets/{re.escape(slug)}/p\d+-fig\d+\.[a-zA-Z]+\)\s*$",
        re.MULTILINE,
    )
    slide_ref_re = re.compile(
        rf"!\[[^]]*\]\(assets/{re.escape(slug)}/p\d+-slide\.[a-zA-Z]+\)"
    )

    for i, m in enumerate(matches):
        page_num = int(m.group(1))
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section = text[start:end]

        # Skip if section already references the slide render
        if slide_ref_re.search(section):
            chunks.append(section)
            continue

        # Find every cutout reference; count and strip them
        cutouts = cutout_re.findall(section)
        if not cutouts:
            chunks.append(section)
            continue

        cutouts_removed += len(cutouts)
        # Strip cutout lines
        section_no_cutouts = cutout_re.sub("", section)
        # Collapse 3+ blank lines down to 2
        section_no_cutouts = re.sub(r"\n{3,}", "\n\n", section_no_cutouts)

        # Insert the slide-render reference immediately before the first
        # speaker-notes blockquote, or before any `<!-- ... -->` marker, or
        # at the end of the section (before the trailing blank line).
        slide_ref = f"![p{page_num:03d}-slide.png](assets/{slug}/p{page_num:03d}-slide.png)"

        # Find a good insertion point: just before "> **Speaker Notes:**" or "<!--"
        insert_re = re.compile(r"^(> \*\*Speaker Notes:\*\*|<!--)", re.MULTILINE)
        ins_match = insert_re.search(section_no_cutouts)
        if ins_match:
            insert_pos = ins_match.start()
            new_section = (
                section_no_cutouts[:insert_pos].rstrip()
                + "\n\n"
                + slide_ref
                + "\n\n"
                + section_no_cutouts[insert_pos:]
            )
        else:
            # Append at the end (before trailing blank lines)
            stripped = section_no_cutouts.rstrip("\n")
            new_section = stripped + "\n\n" + slide_ref + "\n"

        chunks.append(new_section)
        sections_rewritten += 1

    new_text = "".join(chunks)
    # Final whitespace cleanup
    new_text = re.sub(r"\n{3,}", "\n\n", new_text)
    md_path.write_text(new_text, encoding="utf-8")
    return (sections_rewritten, cutouts_removed)


def delete_cutouts(slug: str) -> int:
    slug_assets = ASSETS_DIR / slug
    if not slug_assets.exists():
        return 0
    deleted = 0
    for f in slug_assets.glob("p*-fig*.png"):
        f.unlink()
        deleted += 1
    for f in slug_assets.glob("p*-fig*.jpg"):
        f.unlink()
        deleted += 1
    return deleted


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug", help="canonical slug (matches <RESEARCH_ROOT>/Prepared/<slug>.md)")
    ap.add_argument(
        "--source",
        required=True,
        help="path to source PDF or PPTX (must match the original extraction source)",
    )
    ap.add_argument("--scale", type=float, default=2.0, help="render scale multiplier (default 2.0)")
    ap.add_argument(
        "--no-delete-cutouts",
        action="store_true",
        help="keep the old pNNN-figXX.png files alongside the new pNNN-slide.png",
    )
    args = ap.parse_args()

    md_path = RESEARCH_DIR / f"{args.slug}.md"
    if not md_path.exists():
        sys.exit(f"markdown not found: {md_path}")
    if not os.path.exists(args.source):
        sys.exit(f"source not found: {args.source}")

    print(f"== upgrading {args.slug} ==")
    print(f"  source:   {args.source}")
    print(f"  markdown: {md_path.relative_to(PROJECT_ROOT)}")

    print(f"\n[1/3] rendering slides at {args.scale}x ...")
    n_pages = render_slides(args.source, args.slug, args.scale)
    print(f"      -> {n_pages} slides written to assets/{args.slug}/p*-slide.png")

    print(f"\n[2/3] rewriting markdown image references ...")
    sections, cutouts = rewrite_markdown(md_path, args.slug)
    print(f"      -> {sections} sections rewritten, {cutouts} cutout refs replaced")

    if not args.no_delete_cutouts:
        print(f"\n[3/3] deleting old cutout files ...")
        deleted = delete_cutouts(args.slug)
        print(f"      -> deleted {deleted} pNNN-figXX.* files")
    else:
        print(f"\n[3/3] skipping cutout deletion (--no-delete-cutouts)")

    print("\ndone.")


if __name__ == "__main__":
    main()
