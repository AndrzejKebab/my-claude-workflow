#!/usr/bin/env python3
"""Measure whether a scene metric can see this video's slide changes at all.

A detector that under-segments has two very different diseases, and they need
opposite treatment:

* **Mistuned** — the metric separates same-slide from different-slide pairs, but
  the threshold sits on the wrong side of the gap. Fix by moving `--threshold`.
* **Blind** — different-slide scores fall *inside* the same-slide noise band.
  No threshold exists that works, and lowering it only manufactures false
  positives elsewhere. Fix by changing `--metric`.

They look identical from the outside (multi-minute sections that refuse to
split), so guessing wastes whole re-extraction cycles. This probe tells them
apart in about a minute.

Give it timestamps you have already eyeballed: `--same` pairs that you know sit
within one slide, `--diff` pairs that you know straddle a slide change. It
scores every pair under every metric and reports the separation.

Usage:
    tools/probe_scene_metrics.py <video> \\
        --same 2150,2155 --same 2150,2160 --same 1900,1910 \\
        --diff 2150,2200 --diff 1850,1950 --diff 1790,1850

Read the verdict line per metric:

    luma   SAME max 0.0016  DIFF min 0.0467  -> SEPARATES (29.2x, suggest 0.0100)
    hsv    SAME max 0.0633  DIFF min 0.0535  -> BLIND (diff falls inside same band)

`SEPARATES` reports the ratio and a suggested threshold placed in the measured
gap (geometric mean of the two bounds). `BLIND` means stop tuning and switch
metric. Pick same-pairs a few seconds apart so that whatever moves during a
slide — a speaker picture-in-picture, a video loop, camera noise — is inside the
measured noise floor rather than ignored by it.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

import scene_metrics


def pair(arg: str):
    try:
        a, b = arg.split(",")
        return float(a), float(b)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"expected two comma-separated seconds, got {arg!r}") from None


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("--same", type=pair, action="append", default=[],
                    help="t1,t2 known to be within ONE slide (repeatable)")
    ap.add_argument("--diff", type=pair, action="append", default=[],
                    help="t1,t2 known to STRADDLE a slide change (repeatable)")
    ap.add_argument("--metric", action="append", default=None,
                    choices=scene_metrics.METRICS)
    args = ap.parse_args()

    if not args.same or not args.diff:
        raise SystemExit("FATAL: need at least one --same and one --diff pair")
    if not args.video.exists():
        raise SystemExit(f"FATAL: video not found: {args.video}")

    metrics = args.metric or list(scene_metrics.METRICS)
    cap = cv2.VideoCapture(str(args.video))
    if not cap.isOpened():
        raise SystemExit(f"FATAL: cannot open {args.video} "
                         f"(cv2 cannot decode AV1/VP9 — transcode to H.264 first)")

    def grab(t):
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok:
            raise SystemExit(f"FATAL: could not read a frame at {t}s")
        return frame

    wanted = sorted({t for p in args.same + args.diff for t in p})
    frames = {t: grab(t) for t in wanted}
    cap.release()

    print(f"{'pair':28} " + " ".join(f"{m:>9}" for m in metrics))
    scores = {m: {"same": [], "diff": []} for m in metrics}
    for kind, pairs in (("SAME", args.same), ("DIFF", args.diff)):
        for t1, t2 in pairs:
            row = []
            for m in metrics:
                d = scene_metrics.distance(
                    scene_metrics.signature(frames[t1], m),
                    scene_metrics.signature(frames[t2], m), m)
                scores[m][kind.lower()].append(d)
                row.append(f"{d:9.4f}")
            print(f"{kind} ({t1:g} vs {t2:g})".ljust(28) + " ".join(row))

    print()
    blind = []
    for m in metrics:
        smax, dmin = max(scores[m]["same"]), min(scores[m]["diff"])
        if dmin > smax:
            suggested = (smax * dmin) ** 0.5
            print(f"{m:6} SAME max {smax:.4f}  DIFF min {dmin:.4f}  "
                  f"-> SEPARATES ({dmin / max(smax, 1e-9):.1f}x, "
                  f"suggest {suggested:.4f})")
        else:
            blind.append(m)
            print(f"{m:6} SAME max {smax:.4f}  DIFF min {dmin:.4f}  "
                  f"-> BLIND (diff falls inside same band)")

    return 1 if len(blind) == len(metrics) else 0


if __name__ == "__main__":
    sys.exit(main())
