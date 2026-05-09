#!/usr/bin/env python3
"""Group SRT entries into per-slide transcript windows.

Given a YouTube SRT (rolling auto-captions, often with overlapping/duplicate
text) and a sorted list of slide-start timestamps, write one cleaned paragraph
per slide window `[start_i, start_{i+1})` to an output file.

Usage:
    tools/srt_to_windows.py <captions.srt> <slide_starts.txt> [--out windows.txt]

`slide_starts.txt`: one integer-second timestamp per line, ascending.
Output format per window:
    ## [MM:SS] (Ns)
    <one-paragraph deduplicated transcript text>
"""
import argparse
import re
import sys
from pathlib import Path


def parse_srt(p: Path):
    """Yield (start_sec, text) for each entry, deduplicating identical lines."""
    blocks = re.split(r"\n\n+", p.read_text().strip())
    seen = set()
    out = []
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+)[,\.](\d+) --> ", lines[1])
        if not m:
            continue
        h, mn, s, ms = map(int, m.groups())
        start = h * 3600 + mn * 60 + s + ms / 1000
        text = " ".join(lines[2:]).strip()
        if not text or text in ("[Applause]", "[Music]"):
            continue
        if text in seen:
            continue
        seen.add(text)
        out.append((start, text))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("srt", type=Path)
    ap.add_argument("slide_starts", type=Path)
    ap.add_argument("--out", type=Path, default=Path("/tmp/windowed_transcript.txt"))
    args = ap.parse_args()

    if not args.srt.exists():
        raise SystemExit(f"FATAL: SRT not found: {args.srt}")
    if not args.slide_starts.exists():
        raise SystemExit(f"FATAL: slide_starts not found: {args.slide_starts}")

    entries = parse_srt(args.srt)
    starts = sorted(int(line.strip()) for line in args.slide_starts.read_text().splitlines() if line.strip())
    starts.append(10**9)  # sentinel

    with args.out.open("w") as f:
        for i in range(len(starts) - 1):
            lo, hi = starts[i], starts[i + 1]
            text = " ".join(t for ts, t in entries if lo <= ts < hi).strip()
            mm, ss = divmod(lo, 60)
            f.write(f"## [{mm:02d}:{ss:02d}] ({lo}s)\n{text}\n\n")

    print(f"Wrote {len(starts) - 1} windows to {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
