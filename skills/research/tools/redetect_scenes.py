#!/usr/bin/env python3
"""Aggressive scene redetection for slide-heavy talk videos.

This helper re-runs scene detection with a finer interval and a chosen metric,
writes one representative frame per scene under the asset directory, and prints
a TSV of `(start, end, path)`.

Reach for it when `research_video.py`'s own detection still under-segments —
typically a deck whose consecutive slides share a template and differ only in
body text. Note that since the `luma` metric became the default, plain
under-detection is much rarer; the histogram metric it replaced was blind to
black-text-on-white changes by construction (see tools/scene_metrics.py for the
measured comparison), and lowering `--threshold` could never fix that.

Usage:
    tools/redetect_scenes.py <video.mp4> <slug> \\
        [--metric luma|hsv|edge] [--threshold ...] [--interval 1.0] \\
        [--min-gap 1.5] [--width 1280]

`--threshold` defaults to the chosen metric's calibrated value rather than a
single number, because the metrics are on different scales.

Output:
    /mnt/archive4/PAPERS/Prepared/assets/<slug>/scene-NNN-SSSS.jpg   (one per detected scene)
    /tmp/scenes_<slug>.tsv                                          (TSV of detected scenes)

Non-destructive: appends to an existing asset dir; never deletes other files.
Stale scene-* files from a prior run with different parameters can be cleared
manually with `find /mnt/archive4/PAPERS/Prepared/assets/<slug> -name 'scene-*.jpg' -delete`
before invoking this — the script intentionally does NOT do this for you.
"""
import argparse
import subprocess
import sys
from pathlib import Path

import cv2

import scene_metrics

# The extracted markdown corpus lives at a single hardcoded global location,
# independent of cwd / which project invoked /research.
ASSETS_ROOT = Path("/mnt/archive4/PAPERS/Prepared/assets")


def ensure_cv2_decodable(video: Path) -> Path:
    """Return a video OpenCV can decode, transcoding to H.264 if needed.

    cv2's FFmpeg backend yields all-black frames for AV1 (and often VP9), so the
    histogram diff sees no change and detection collapses to a single scene —
    the exact under-detection this tool exists to fix. Probe the codec and
    transcode to a scratch `<stem>-h264.mp4` when it is not H.264. Detection runs
    on the copy; ffmpeg frame extraction still uses the original (best quality,
    and ffmpeg decodes AV1 fine). Kept inline rather than imported from
    research_video.py, whose module import would load the OpenOCR engine.
    """
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(video)],
            capture_output=True, text=True, timeout=30,
        )
        codec = probe.stdout.strip().lower()
    except Exception:
        codec = ""
    if codec in ("", "h264"):
        return video
    h264 = video.with_name(video.stem + "-h264.mp4")
    if not h264.exists():
        print(f"Transcoding {codec} -> h264 for cv2 detection...", file=sys.stderr)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-an", str(h264)],
            check=True,
        )
    return h264


def detect_scenes(video: Path, threshold: float, interval: float, min_gap: float,
                  metric: str = "luma"):
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps else 0
    if not duration:
        cap.release()
        raise SystemExit(f"FATAL: ffprobe failed on {video}")

    frame_interval = max(1, int(fps * interval))
    transitions = [0.0]
    prev_sig = None

    print(
        f"Scanning {duration:.0f}s @ {interval}s intervals, "
        f"metric {metric}, threshold {threshold}",
        file=sys.stderr,
    )

    frame_idx = 0
    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        sig = scene_metrics.signature(frame, metric)

        if prev_sig is not None:
            diff = scene_metrics.distance(prev_sig, sig, metric)
            if diff > threshold:
                t = frame_idx / fps
                if t - transitions[-1] > min_gap:
                    transitions.append(t)

        prev_sig = sig
        frame_idx += frame_interval

    cap.release()
    transitions.append(duration)
    return [(transitions[i], transitions[i + 1]) for i in range(len(transitions) - 1)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("slug")
    ap.add_argument("--metric", choices=scene_metrics.METRICS, default="luma",
                    help="frame-difference measure (see tools/scene_metrics.py)")
    ap.add_argument("--threshold", type=float, default=None,
                    help="override the chosen metric's calibrated default")
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--min-gap", type=float, default=1.5)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--offset", type=float, default=1.5,
                    help="seconds after scene start to grab the representative frame")
    args = ap.parse_args()

    if not args.video.exists():
        raise SystemExit(f"FATAL: video not found: {args.video}")

    out_dir = ASSETS_ROOT / args.slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Detect on an H.264-decodable copy (cv2 can't read AV1/VP9); extract frames
    # below from the original for best quality.
    cv_video = ensure_cv2_decodable(args.video)
    threshold = (args.threshold if args.threshold is not None
                 else scene_metrics.default_threshold(args.metric))
    scenes = detect_scenes(cv_video, threshold, args.interval, args.min_gap,
                           metric=args.metric)
    print(f"Found {len(scenes)} scenes", file=sys.stderr)

    tsv_path = Path(f"/tmp/scenes_{args.slug}.tsv")
    with tsv_path.open("w") as tsv:
        for i, (start, end) in enumerate(scenes):
            pick = min(start + args.offset, (start + end) / 2)
            out = out_dir / f"scene-{i:03d}-{int(start):04d}.jpg"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error",
                    "-ss", f"{pick:.2f}", "-i", str(args.video),
                    "-frames:v", "1",
                    "-vf", f"scale={args.width}:-1",
                    "-q:v", "3", str(out),
                ],
                check=True,
            )
            tsv.write(f"{start:.2f}\t{end:.2f}\t{out}\n")
            print(f"{i:3d}\t{start:7.2f}\t{end:7.2f}\t{out.name}")

    print(f"\nWrote {tsv_path} with {len(scenes)} scenes", file=sys.stderr)


if __name__ == "__main__":
    main()
