#!/usr/bin/env python3
"""Align video transcript (SRT) to slide-deck PDF pages for dual-source merging.

This module provides utilities to map per-slide transcript text to PDF slide
indices for dual-source /research runs where one source is a PDF (slides) and
another is a YouTube video (transcript).

Two alignment strategies are supported:

1. perceptual_hash (pHash) — preferred when the video frame reader works (h264
   or non-AV1 video). Computes pHash on each PDF slide render and each video
   scene-capture frame, then matches nearest neighbour by Hamming distance.

2. time_proportional — fallback when frame decoding fails (e.g., AV1 codec
   with no hardware support, opencv-python-headless build without AV1 decoders).
   Divides the total duration evenly across the slide count, then assigns SRT
   cues to slides by their timestamp. This is approximate (±1-3 slides near
   slide transitions) but gives usable per-slide speaker notes.

CLI usage (run directly):
    # Time-proportional fallback
    python align_video_to_slides.py time-prop \
        --srt /path/to/<slug>.en.srt \
        --slides 63 \
        --duration 3647 \
        --out /tmp/slide_transcript_map.json

    # pHash alignment (h264 video + per-slide renders)
    python align_video_to_slides.py phash \
        --srt /path/to/<slug>.en.srt \
        --slides-dir /mnt/archive4/PAPERS/Prepared/assets/<slug>/ \
        --scenes-tsv /tmp/scenes_<slug>-video.tsv \
        --frames-dir /mnt/archive4/PAPERS/Prepared/assets/<slug>-video/ \
        --out /tmp/slide_transcript_map.json

Output JSON (both modes):
    {
        "1": "speaker text for slide 1...",
        "2": "speaker text for slide 2...",
        ...
        "63": "(no aligned transcript)"
    }

The alignment_mode key is also written:
    "alignment_mode": "time_proportional" | "phash"
    "alignment_note": "human-readable caveat"
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# SRT parsing
# ---------------------------------------------------------------------------

def parse_srt_timestamps(srt_path: str) -> list[tuple[float, float, str]]:
    """Parse an SRT file into a list of (start_sec, end_sec, text) triples.

    Handles both standard SRT and auto-caption SRT (where the same text
    appears in consecutive cues — deduplicated at the window level).
    """
    content = Path(srt_path).read_text(encoding="utf-8", errors="replace")
    # Split into blocks on double newline
    blocks = [b.strip() for b in re.split(r"\n\s*\n", content) if b.strip()]

    entries = []
    for block in blocks:
        lines = block.splitlines()
        # Find the timestamp line (contains " --> ")
        ts_line = None
        ts_idx = None
        for i, line in enumerate(lines):
            if " --> " in line:
                ts_line = line
                ts_idx = i
                break
        if ts_line is None:
            continue
        start, end = _parse_ts_pair(ts_line)
        if start is None:
            continue
        text_lines = [l.strip() for l in lines[ts_idx + 1:] if l.strip()]
        text = " ".join(text_lines)
        if text:
            entries.append((start, end, text))
    return entries


def _parse_ts_pair(ts_line: str) -> tuple[float | None, float | None]:
    """Parse '00:01:23,456 --> 00:01:25,789' → (83.456, 85.789)."""
    m = re.match(
        r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)",
        ts_line.strip(),
    )
    if not m:
        return None, None
    h0, m0, s0, ms0, h1, m1, s1, ms1 = [int(x) for x in m.groups()]
    start = h0 * 3600 + m0 * 60 + s0 + ms0 / 1000
    end = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
    return start, end


# ---------------------------------------------------------------------------
# Deduplication helper for auto-caption SRTs
# ---------------------------------------------------------------------------

def _deduplicate_adjacent(
    entries: list[tuple[float, float, str]]
) -> list[tuple[float, float, str]]:
    """Remove consecutive duplicate text cues (YouTube auto-caption artifact)."""
    if not entries:
        return []
    result = [entries[0]]
    for entry in entries[1:]:
        if entry[2] != result[-1][2]:
            result.append(entry)
    return result


# ---------------------------------------------------------------------------
# Strategy 1: time-proportional alignment
# ---------------------------------------------------------------------------

def time_proportional_alignment(
    srt_entries: list[tuple[float, float, str]],
    num_slides: int,
    total_duration_s: float,
) -> dict[int, str]:
    """Assign SRT cues to slides by evenly dividing total_duration_s.

    Each slide gets a time window of (total_duration_s / num_slides) seconds.
    SRT cues whose midpoint falls in that window are collected for that slide.

    Returns dict slide_idx (1-based) → concatenated speaker text.
    """
    window = total_duration_s / num_slides
    entries = _deduplicate_adjacent(srt_entries)

    slide_texts: dict[int, list[str]] = {i: [] for i in range(1, num_slides + 1)}
    for start, end, text in entries:
        mid = (start + end) / 2
        slide_idx = min(num_slides, int(mid / window) + 1)
        slide_texts[slide_idx].append(text)

    # Collapse to single string per slide, trimming internal duplicates
    result = {}
    for idx in range(1, num_slides + 1):
        combined = " ".join(slide_texts[idx])
        # SRT auto-captions often repeat phrases across adjacent cues
        # (the cue text is a rolling window); simple phrase dedup:
        combined = _trim_rolling_duplicates(combined)
        result[idx] = combined if combined else "(no aligned transcript)"
    return result


def _trim_rolling_duplicates(text: str) -> str:
    """Remove obvious phrase-level repetitions from rolling-window auto-captions.

    Auto-caption SRTs emit a 10-word window that shifts by ~2 words per cue.
    Naive concatenation produces e.g.:
      "hello world foo hello world foo bar" → "hello world foo bar"
    """
    if len(text) < 20:
        return text
    # Build result word-by-word, skip a word if the last N words already
    # contain this word sequence.
    words = text.split()
    result_words: list[str] = []
    look_back = 8  # avoid 8-word repetitions
    for i, word in enumerate(words):
        # Check if this word starts a sequence that already exists in recent output
        if len(result_words) >= look_back:
            tail = result_words[-look_back:]
            # Find first occurrence of `word` in tail
            for j, w in enumerate(tail):
                if w == word:
                    # Check if the next few words also match
                    remaining = words[i + 1 : i + 1 + (look_back - j - 1)]
                    tail_remaining = tail[j + 1 : j + 1 + len(remaining)]
                    if remaining == tail_remaining and len(remaining) >= 3:
                        break  # skip this word (it's a repetition)
            else:
                result_words.append(word)
        else:
            result_words.append(word)
    return " ".join(result_words)


# ---------------------------------------------------------------------------
# Strategy 2: pHash alignment (requires imagehash + frame images)
# ---------------------------------------------------------------------------

def phash_alignment(
    srt_entries: list[tuple[float, float, str]],
    slides_dir: str,
    scenes_tsv: str,
    frames_dir: str,
    hamming_threshold: int = 20,
) -> dict[int, str]:
    """Match video scene captures to PDF slide renders by perceptual hash.

    slides_dir: directory containing sNNN-slide.png renders from the PDF.
    scenes_tsv: /tmp/scenes_<slug>.tsv written by redetect_scenes.py.
    frames_dir: assets/<slug>-video/ containing scene-NNN-NNNN.jpg captures.
    hamming_threshold: max Hamming distance for a match (0-64 scale).

    Returns dict slide_idx (1-based) → concatenated speaker text.
    Slides with no scene match get "(no aligned transcript)".
    """
    try:
        import imagehash
        from PIL import Image
    except ImportError:
        raise RuntimeError(
            "imagehash / Pillow not installed. Run: "
            "~/.claude/skills/research/.venv/bin/pip install imagehash Pillow"
        )

    # Load PDF slide hashes
    slides_path = Path(slides_dir)
    slide_hashes: dict[int, object] = {}
    for png in sorted(slides_path.glob("s???-slide.png")):
        m = re.match(r"s(\d+)-slide\.png", png.name)
        if m:
            idx = int(m.group(1))
            img = Image.open(png).convert("RGB")
            slide_hashes[idx] = imagehash.phash(img)

    if not slide_hashes:
        raise RuntimeError(f"No sNNN-slide.png found in {slides_dir}")

    # Load scene timestamps from TSV.
    # redetect_scenes.py writes 3-column TSV: start\tend\t/full/path/to/frame.jpg
    # research_video.py writes 3-column TSV in the same format.
    # We accept both and resolve the frame path as an absolute path if given,
    # or as a relative name under frames_dir if it is a bare filename.
    scenes: list[tuple[float, float, str]] = []  # (start, end, frame_path_or_name)
    tsv_path = Path(scenes_tsv)
    if tsv_path.exists():
        for line in tsv_path.read_text().splitlines():
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 3:
                scenes.append((float(parts[0]), float(parts[1]), parts[2].strip()))

    if not scenes:
        raise RuntimeError(f"No scenes found in TSV: {scenes_tsv}")

    # Compute pHash for each scene capture
    frames_path = Path(frames_dir)
    scene_to_slide: dict[int, int | None] = {}
    for scene_idx, (t_start, t_end, frame_fn) in enumerate(scenes):
        # frame_fn may be an absolute path (from redetect_scenes.py) or a bare
        # filename relative to frames_dir (from research_video.py).
        raw = Path(frame_fn)
        frame_path = raw if raw.is_absolute() else frames_path / frame_fn
        if not frame_path.exists():
            scene_to_slide[scene_idx] = None
            continue
        scene_hash = imagehash.phash(Image.open(frame_path).convert("RGB"))
        best_slide = None
        best_dist = hamming_threshold + 1
        for slide_idx, slide_hash in slide_hashes.items():
            dist = scene_hash - slide_hash
            if dist < best_dist:
                best_dist = dist
                best_slide = slide_idx
        scene_to_slide[scene_idx] = best_slide if best_dist <= hamming_threshold else None

    # Map SRT cues to slides via scene→slide mapping
    num_slides = max(slide_hashes.keys())
    entries = _deduplicate_adjacent(srt_entries)
    slide_texts: dict[int, list[str]] = {i: [] for i in range(1, num_slides + 1)}

    for start, end, text in entries:
        mid = (start + end) / 2
        # Find which scene this cue falls in
        matched_slide = None
        for scene_idx, (t_start, t_end, _) in enumerate(scenes):
            if t_start <= mid < t_end:
                matched_slide = scene_to_slide[scene_idx]
                break
        if matched_slide is not None:
            slide_texts[matched_slide].append(text)

    result = {}
    for idx in range(1, num_slides + 1):
        combined = " ".join(slide_texts[idx])
        combined = _trim_rolling_duplicates(combined)
        result[idx] = combined if combined else "(no aligned transcript)"
    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)

    tp = sub.add_parser("time-prop", help="Time-proportional alignment (fallback)")
    tp.add_argument("--srt", required=True)
    tp.add_argument("--slides", type=int, required=True, help="Number of slides")
    tp.add_argument("--duration", type=float, required=True, help="Video duration in seconds")
    tp.add_argument("--out", required=True)

    ph = sub.add_parser("phash", help="pHash alignment (preferred, needs imagehash)")
    ph.add_argument("--srt", required=True)
    ph.add_argument("--slides-dir", required=True)
    ph.add_argument("--scenes-tsv", required=True)
    ph.add_argument("--frames-dir", required=True)
    ph.add_argument("--hamming-threshold", type=int, default=20)
    ph.add_argument("--out", required=True)

    args = parser.parse_args()

    srt_entries = parse_srt_timestamps(args.srt)
    print(f"Loaded {len(srt_entries)} SRT cues", file=sys.stderr)

    if args.mode == "time-prop":
        mapping = time_proportional_alignment(srt_entries, args.slides, args.duration)
        mode = "time_proportional"
        note = (
            f"Time-proportional alignment: {args.duration:.0f}s / {args.slides} slides = "
            f"{args.duration / args.slides:.1f}s per slide. "
            "May be off by ±1-3 slides near transitions."
        )
    else:
        mapping = phash_alignment(
            srt_entries,
            args.slides_dir,
            args.scenes_tsv,
            args.frames_dir,
            args.hamming_threshold,
        )
        mode = "phash"
        note = f"pHash alignment (Hamming threshold={args.hamming_threshold})."

    output = {"alignment_mode": mode, "alignment_note": note}
    output.update({str(k): v for k, v in mapping.items()})

    Path(args.out).write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"Wrote {args.out} ({len(mapping)} slide entries)", file=sys.stderr)


if __name__ == "__main__":
    main()
