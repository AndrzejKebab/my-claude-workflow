#!/usr/bin/env python3
"""Fold speaker-only sections of a video extraction into the slide they narrate.

`research_video.py --all-slides` deliberately promotes every detected scene to
its own `## Slide N` section. That is the right default for a slides-end-to-end
talk — the brightness/edge classifier it bypasses drops dark-themed slides — but
it also promotes every cut to the podium camera. The result is a document where
one slide's narration is split across the slide section and the several podium
sections that follow it, each carrying a redundant photograph of the speaker.

This pass restores the skill's slide-centric contract ("speaker scenes never
open a section — their narration folds into the current slide's transcript")
without giving up `--all-slides`' guarantee that no slide is ever dropped.

Identifying podium shots
------------------------

Brightness alone is not safe. On the I3D 2026 Hoffman keynote the podium frames
sit at mean-luma 12-25 with a bright-pixel fraction of exactly 0.000 — but so do
two genuine content slides (a green wireframe head on black, and a Valve Source
Editor screenshot), and folding those away would silently destroy content.

What actually separates them is *self-similarity*: podium shots come from a
locked-off camera, so they are near-identical to each other, while every slide
differs from every other slide. So the largest cluster of mutually-similar
frames is the speaker shot. Measured on that keynote, cluster members sat within
0.0393 of the cluster medoid while the nearest non-member was 0.0515 away — the
0.045 default threshold sits in that gap. The two dark content slides scored
0.094 and 0.307 and were correctly kept.

The cluster must also be *large* to be believable (`--min-cluster`, default 8%
of sections): a talk with no podium cuts must fold nothing rather than
collapsing whatever handful of frames happen to resemble each other.

Transcript handling
-------------------

A folded section's transcript is appended to the nearest preceding kept section,
or — for podium shots that open the document, before any slide has appeared — to
the nearest following one, so no narration is ever lost. Sections are renumbered
sequentially afterwards. Folded frames become unreferenced and are deleted
unless `--keep-frames` is passed.

Usage:
    tools/fold_speaker_sections.py --only=<slug> [--dry-run] [--threshold 0.045]
                                   [--min-cluster 0.08] [--keep-frames]

Dry-run prints the fold plan and touches nothing. Run it first.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from research_paths import PREPARED_DIR

import cv2
import numpy as np

PREPARED = PREPARED_DIR
ASSETS_ROOT = PREPARED / "assets"

SECTION_RE = re.compile(r'^## (?:Slide \d+(?: -- .*)?|\[[\d:]+\].*)$', re.M)
FRAME_RE = re.compile(r'!\[[^\]]*\]\(assets/[^/]+/([^)]+)\)')


def split_sections(text: str):
    """Return (preamble, [(header, body), ...])."""
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        return text, []
    preamble = text[: matches[0].start()]
    out = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out.append((m.group(0), text[m.end(): end]))
    return preamble, out


def frame_signature(path: Path):
    img = cv2.imread(str(path))
    if img is None:
        return None
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.resize(gray, (160, 90)).astype(np.float32) / 255.0


def largest_similar_cluster(sigs: dict, threshold: float):
    """Medoid-style: the frame whose neighbourhood within `threshold` is biggest."""
    names = [n for n, s in sigs.items() if s is not None]
    if not names:
        return set(), None
    best_name, best_members = None, set()
    for a in names:
        members = {b for b in names
                   if float(np.abs(sigs[a] - sigs[b]).mean()) < threshold}
        if len(members) > len(best_members):
            best_name, best_members = a, members
    return best_members, best_name


def extract_transcript(body: str) -> str:
    return "\n".join(l for l in body.splitlines() if l.startswith("> ")).strip()


def strip_transcript(body: str) -> str:
    return "\n".join(l for l in body.splitlines() if not l.startswith("> "))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", required=True, help="slug to process")
    ap.add_argument("--threshold", type=float, default=0.045)
    ap.add_argument("--min-cluster", type=float, default=0.08,
                    help="cluster must cover at least this fraction of sections")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-frames", action="store_true")
    args = ap.parse_args()

    md = PREPARED / f"{args.only}.md"
    if not md.exists():
        raise SystemExit(f"FATAL: {md} not found")
    assets = ASSETS_ROOT / args.only

    text = md.read_text(encoding="utf-8")
    preamble, sections = split_sections(text)
    if not sections:
        raise SystemExit("FATAL: no '## Slide N' sections found")

    frame_of, sigs = {}, {}
    for idx, (header, body) in enumerate(sections):
        m = FRAME_RE.search(body)
        if not m:
            continue
        frame_of[idx] = m.group(1)
        sigs[m.group(1)] = frame_signature(assets / m.group(1))

    cluster, medoid = largest_similar_cluster(sigs, args.threshold)
    frac = len(cluster) / max(1, len(sections))
    print(f"sections: {len(sections)}   framed: {len(frame_of)}")
    print(f"largest similar cluster: {len(cluster)} frames "
          f"({frac:.1%} of sections), medoid {medoid}")

    if frac < args.min_cluster:
        print(f"cluster below --min-cluster {args.min_cluster:.0%}; "
              f"nothing to fold (this talk has no locked-off speaker camera)")
        return 0

    fold = {i for i, f in frame_of.items() if f in cluster}
    keep = [i for i in range(len(sections)) if i not in fold]
    if not keep:
        raise SystemExit("FATAL: every section classified as speaker; aborting")

    print(f"folding {len(fold)} speaker sections into {len(keep)} slide sections")
    for i in sorted(fold):
        print(f"  fold  {sections[i][0][:70]}")

    if args.dry_run:
        print("\n(dry run — nothing written)")
        return 0

    carried = {i: [] for i in keep}
    for i in sorted(fold):
        target = max((k for k in keep if k < i), default=None)
        if target is None:
            target = min(k for k in keep if k > i)
        t = extract_transcript(sections[i][1])
        if t:
            carried[target].append(t)

    out, n = [preamble.rstrip("\n"), ""], 0
    for i in keep:
        header, body = sections[i]
        n += 1
        title = header.split(" -- ", 1)[1] if " -- " in header else ""
        out.append(f"## Slide {n} -- {title}" if title else f"## Slide {n}")

        own = extract_transcript(body)
        merged = "\n".join(x for x in ([own] + carried[i]) if x)
        rest = strip_transcript(body).rstrip("\n")
        out.append(rest)
        if merged:
            out.append("")
            out.append(merged)
        out.append("")

    md.write_text("\n".join(out).rstrip("\n") + "\n", encoding="utf-8")
    print(f"wrote {md} ({n} sections)")

    if not args.keep_frames:
        removed = 0
        for i in sorted(fold):
            f = frame_of.get(i)
            if f and (assets / f).exists():
                (assets / f).unlink()
                removed += 1
        print(f"removed {removed} unreferenced speaker frames")
    return 0


if __name__ == "__main__":
    sys.exit(main())
