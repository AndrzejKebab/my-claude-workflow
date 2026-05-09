#!/usr/bin/env python3
"""Subsample long scenes from `redetect_scenes.py` output to catch slide changes
the histogram threshold missed (e.g. consecutive slides that share a template).

Usage:
    tools/subsample_long_scenes.py <video.mp4> <slug> \\
        [--scenes-tsv /tmp/scenes_<slug>.tsv] \\
        [--interval 20.0] [--min-len 40.0] [--width 1280]

Reads a TSV of `(start, end, scene_path)` rows and, for every scene longer than
`--min-len`, writes additional sample frames every `--interval` seconds into
the same asset directory under names `sub-NNN-MM-SSSS.jpg`.

Non-destructive: only writes new files; never deletes.
"""
import argparse
import os
import subprocess
from pathlib import Path

# Resolve from invocation cwd, not script location (skill-shipped scripts).
PROJECT_ROOT = Path(os.environ.get("RESEARCH_PROJECT_ROOT", os.getcwd())).resolve()
ASSETS_ROOT = PROJECT_ROOT / "docs" / "research" / "assets"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("slug")
    ap.add_argument("--scenes-tsv", type=Path, default=None)
    ap.add_argument("--interval", type=float, default=20.0)
    ap.add_argument("--min-len", type=float, default=40.0)
    ap.add_argument("--width", type=int, default=1280)
    args = ap.parse_args()

    if not args.video.exists():
        raise SystemExit(f"FATAL: video not found: {args.video}")

    tsv_path = args.scenes_tsv or Path(f"/tmp/scenes_{args.slug}.tsv")
    if not tsv_path.exists():
        raise SystemExit(f"FATAL: scenes TSV not found: {tsv_path} "
                         f"(run redetect_scenes.py first)")

    out_dir = ASSETS_ROOT / args.slug
    out_dir.mkdir(parents=True, exist_ok=True)

    scenes = []
    for line in tsv_path.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            scenes.append((float(parts[0]), float(parts[1]), parts[2]))

    new_subs = []
    for i, (start, end, _) in enumerate(scenes):
        if end - start <= args.min_len:
            continue
        t = start + args.interval
        sub_idx = 1
        while t < end - 5.0:
            out = out_dir / f"sub-{i:03d}-{sub_idx:02d}-{int(t):04d}.jpg"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-ss", f"{t:.2f}", "-i", str(args.video),
                    "-frames:v", "1",
                    "-vf", f"scale={args.width}:-1",
                    "-q:v", "3", str(out),
                ],
                check=True,
            )
            new_subs.append((t, str(out)))
            t += args.interval
            sub_idx += 1

    print(f"Wrote {len(new_subs)} sub-samples")
    subs_tsv = Path(f"/tmp/subs_{args.slug}.tsv")
    with subs_tsv.open("w") as f:
        for t, p in new_subs:
            f.write(f"{t:.2f}\t{p}\n")
    print(f"Wrote {subs_tsv}")


if __name__ == "__main__":
    main()
