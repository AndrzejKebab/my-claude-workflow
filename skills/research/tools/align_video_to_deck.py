#!/usr/bin/env python3
"""Align a recorded talk to its own slide deck by matching video frames to deck renders.

Given a talk recording and the `sNNN-slide.png` renders produced by `extract_research.py`
for the same deck, this decides which deck slide is on screen at each sampled timestamp,
then emits per-slide start times and per-slide transcript windows.

Why this exists: a recorded conference talk and its published deck are two extractions of
one source. Scene detection alone gives "something changed at t=..." but cannot say *which*
slide that is, so the two artefacts stay separate documents. Matching against the deck
renders is an analytical oracle -- the answer is checkable, not guessed.

The metric is a chrome-cropped edge-gradient normalized cross-correlation:

  * Chrome-cropped, because conference templates put an identical banner/footer on every
    slide. Identical content correlates identically against every candidate, which inflates
    the whole score column and buries the discriminating signal.
  * Edge-gradient, because raw luminance is dominated by the slide's background. A deck of
    black-text-on-white slides is very nearly invisible to a brightness-based comparison --
    measured on this corpus, true-slide and wrong-slide scores fell within 0.01 of each
    other (blind). On gradients the same pairs separate ~3-4x.

Measured separation on `clavet-2016-motion-matching` (two hand-verified anchors):

  frame t=600s  -> true slide 20: 0.756, runner-up 0.230  (3.3x)
  frame t=2400s -> true slide 61: 0.822, runner-up 0.194  (4.2x)

Slide 20 matched correctly even though the deck render carries a PowerPoint animation build
(an image) that had not yet appeared in the projected frame -- i.e. the metric tolerates
partial-content divergence, which is the common case for animated decks.

The edge-gradient signal alone drifts by a slide or two through the demo-heavy back half of a
talk, where the screen is mostly embedded video and neighbouring "white label over gameplay"
slides look alike (measured: t=2900s and t=3500s both landed +2 slides early). Adding an OCR
token signal (`--pdf`, TF-IDF over the slide's own text against OCR of the pane) pins those
down -- both drift cases corrected to the hand-verified truth (slide 72 and slide 88). Enable
it whenever the deck carries a text layer.

Sabotage control (`--control shuffle`, the criterion for "could this have failed"): permuting
the deck must collapse the alignment, because a talk's true slide sequence is non-decreasing
in time and a permuted deck cannot be traversed monotonically through the good matches.
Measured on `clavet-2016-motion-matching`, edge+text, 1019 samples:

  true deck order : median matched score 1.290, monotone-path/argmax agreement 79.8%
  permuted deck   : median matched score 0.131, agreement 14.9%

A ~10x collapse in the DP path score is the demonstrated sensitivity; run the control before
trusting any new alignment.

Per-frame scores are then run through a monotonic DP alignment. A talk advances through its
deck in order, so the slide index must be non-decreasing in time; that constraint carries
the frames that match nothing (embedded video playing full-screen, cuts to the speaker) and
suppresses isolated mismatches that a per-frame argmax would accept.

Usage:
    align_video_to_deck.py VIDEO --slug SLUG [--interval 2.0] [--rect x,y,w,h]
    align_video_to_deck.py VIDEO --slug SLUG --srt PATH --emit-windows OUT.md

Verify an alignment before trusting it with `--control shuffle`, which re-runs the match
against a permuted deck. Scores must collapse; if they do not, the metric is not reading
slide identity and nothing downstream is trustworthy.
"""

from __future__ import annotations

import argparse
import glob
import math
import os
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass

import cv2
import numpy as np

PREPARED = "/mnt/archive4/PAPERS/Prepared"

FEAT_W, FEAT_H = 384, 216
CROP_TOP, CROP_BOTTOM = 0.11, 0.94
CROP_LEFT, CROP_RIGHT = 0.02, 0.98


def features(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape
    inner = gray[
        int(CROP_TOP * h) : int(CROP_BOTTOM * h),
        int(CROP_LEFT * w) : int(CROP_RIGHT * w),
    ]
    if inner.size == 0:
        return np.zeros(FEAT_W * FEAT_H, dtype=np.float32)
    small = cv2.resize(inner, (FEAT_W, FEAT_H)).astype(np.float32)
    small = cv2.GaussianBlur(small, (3, 3), 0)
    gx = cv2.Sobel(small, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(small, cv2.CV_32F, 0, 1, ksize=3)
    edge = np.sqrt(gx * gx + gy * gy)
    edge -= edge.mean()
    return (edge / (edge.std() + 1e-6)).ravel()


def load_deck(assets_dir: str) -> tuple[list[str], np.ndarray]:
    paths = sorted(glob.glob(os.path.join(assets_dir, "s*-slide.png")))
    if not paths:
        raise SystemExit(f"no sNNN-slide.png renders in {assets_dir}")
    mat = np.stack(
        [features(cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY)) for p in paths]
    )
    return paths, mat


TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


def tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def deck_text(pdf_path: str, n_slides: int) -> list[set[str]]:
    import fitz

    doc = fitz.open(pdf_path)
    out = [tokenize(doc[i].get_text()) for i in range(min(n_slides, doc.page_count))]
    while len(out) < n_slides:
        out.append(set())
    doc.close()
    return out


def build_idf(slide_tokens: list[set[str]]) -> dict[str, float]:
    df = Counter()
    for toks in slide_tokens:
        df.update(toks)
    n = len(slide_tokens)
    return {t: math.log(n / (1.0 + c)) + 1e-3 for t, c in df.items()}


def text_vectors(
    slide_tokens: list[set[str]], idf: dict[str, float]
) -> list[dict[str, float]]:
    vecs = []
    for toks in slide_tokens:
        v = {t: idf.get(t, 0.0) for t in toks}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({t: x / norm for t, x in v.items()})
    return vecs


def text_scores(
    frame_tokens: set[str], vecs: list[dict[str, float]], idf: dict[str, float]
) -> np.ndarray:
    q = {t: idf.get(t, 0.0) for t in frame_tokens if t in idf}
    norm = math.sqrt(sum(x * x for x in q.values()))
    if norm == 0.0:
        return np.zeros(len(vecs), dtype=np.float32)
    q = {t: x / norm for t, x in q.items()}
    out = np.zeros(len(vecs), dtype=np.float32)
    for i, v in enumerate(vecs):
        if len(q) < len(v):
            out[i] = sum(x * v.get(t, 0.0) for t, x in q.items())
        else:
            out[i] = sum(x * q.get(t, 0.0) for t, x in v.items())
    return out


@dataclass
class Rect:
    x: int
    y: int
    w: int
    h: int

    def crop(self, frame: np.ndarray) -> np.ndarray:
        return frame[self.y : self.y + self.h, self.x : self.x + self.w]

    def __str__(self) -> str:
        return f"{self.x},{self.y},{self.w},{self.h}"


def detect_rect(cap, deck_paths: list[str], probes: int = 12) -> Rect:
    """Find the slide pane by multi-scale template matching a few deck renders."""
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    picks = np.linspace(0.1, 0.9, probes)
    templates = []
    step = max(1, len(deck_paths) // 8)
    for p in deck_paths[::step][:8]:
        templates.append(cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2GRAY))

    votes: dict[tuple[int, int, int, int], float] = {}
    for frac in picks:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(total * frac))
        ok, frame = cap.read()
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        best = None
        for tmpl in templates:
            for width in range(int(gray.shape[1] * 0.5), int(gray.shape[1] * 1.01), 25):
                height = int(round(width * tmpl.shape[0] / tmpl.shape[1]))
                if height >= gray.shape[0] or width >= gray.shape[1]:
                    continue
                resized = cv2.resize(tmpl, (width, height))
                res = cv2.matchTemplate(gray, resized, cv2.TM_CCOEFF_NORMED)
                _, mx, _, loc = cv2.minMaxLoc(res)
                if best is None or mx > best[0]:
                    best = (mx, loc[0], loc[1], width, height)
        if best and best[0] > 0.5:
            key = (
                int(round(best[1] / 5) * 5),
                int(round(best[2] / 5) * 5),
                int(round(best[3] / 5) * 5),
                int(round(best[4] / 5) * 5),
            )
            votes[key] = votes.get(key, 0.0) + best[0]

    if not votes:
        raise SystemExit("could not detect the slide pane; pass --rect x,y,w,h explicitly")
    x, y, w, h = max(votes.items(), key=lambda kv: kv[1])[0]
    del fps
    return Rect(x, y, w, h)


def score_matrix(
    video: str,
    deck: np.ndarray,
    rect: Rect,
    interval: float,
    vecs: list[dict[str, float]] | None = None,
    idf: dict[str, float] | None = None,
    text_weight: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total / fps
    times = np.arange(0.0, duration, interval)
    scores = np.zeros((len(deck), len(times)), dtype=np.float32)
    denom = float(FEAT_W * FEAT_H)

    wanted = [int(t * fps) for t in times]
    pos = 0
    for i, target in enumerate(wanted):
        while pos < target:
            if not cap.grab():
                break
            pos += 1
        ok, frame = cap.retrieve()
        pos += 1
        if not ok:
            continue
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        pane = features(rect.crop(gray))
        full = features(gray)
        scores[:, i] = np.maximum(deck @ pane, deck @ full) / denom
        if vecs is not None and idf is not None:
            from openocr_engine import ocr_numpy

            text = ocr_numpy(rect.crop(frame))
            if text:
                scores[:, i] += text_weight * text_scores(tokenize(text), vecs, idf)
        if i % 100 == 0:
            print(f"  scored {i}/{len(times)} frames", file=sys.stderr, flush=True)
    cap.release()
    return times, scores


def monotonic_align(scores: np.ndarray, jump_penalty: float = 0.02) -> np.ndarray:
    """Best non-decreasing slide path through the score matrix."""
    n_slides, n_times = scores.shape
    dp = scores[:, 0].astype(np.float64).copy()
    back = np.zeros((n_times, n_slides), dtype=np.int32)
    for t in range(1, n_times):
        run_max = -np.inf
        run_arg = 0
        prev_best = np.empty(n_slides)
        prev_arg = np.empty(n_slides, dtype=np.int32)
        for k in range(n_slides):
            if dp[k] > run_max:
                run_max = dp[k]
                run_arg = k
            prev_best[k] = run_max - (jump_penalty if run_arg != k else 0.0)
            prev_arg[k] = run_arg
        dp = prev_best + scores[:, t]
        back[t] = prev_arg
    path = np.zeros(n_times, dtype=np.int32)
    path[-1] = int(np.argmax(dp))
    for t in range(n_times - 1, 0, -1):
        path[t - 1] = back[t][path[t]]
    return path


def parse_srt(path: str) -> list[tuple[float, float, str]]:
    def to_sec(stamp: str) -> float:
        h, m, rest = stamp.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0

    cues = []
    blocks = re.split(r"\n\s*\n", open(path, encoding="utf-8").read().strip())
    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        stamp = next((ln for ln in lines if "-->" in ln), None)
        if not stamp:
            continue
        start, end = [s.strip() for s in stamp.split("-->")]
        text = " ".join(lines[lines.index(stamp) + 1 :]).strip()
        if text:
            cues.append((to_sec(start), to_sec(end), text))
    return cues


def starts_from_tsv(path: str) -> dict[int, float]:
    starts: dict[int, float] = {}
    with open(path, encoding="utf-8") as fh:
        next(fh)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            t = float(parts[0])
            slide = int(parts[1])
            starts.setdefault(slide, t)
    return starts


def emit_windows(starts: dict[int, float], srt: str, out: str) -> None:
    cues = parse_srt(srt)
    bounds = sorted(starts.items())
    with open(out, "w", encoding="utf-8") as fh:
        for idx, (slide, start) in enumerate(bounds):
            end = bounds[idx + 1][1] if idx + 1 < len(bounds) else 1e9
            text = " ".join(
                c[2] for c in cues if c[0] >= start - 0.01 and c[0] < end - 0.01
            )
            fh.write(f"## [{int(start) // 60}:{int(start) % 60:02d}] slide {slide}\n")
            fh.write(text.strip() + "\n\n")
    print(f"wrote {out} ({len(bounds)} slide windows)", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--assets-dir", default=None)
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--rect", default=None, help="x,y,w,h of the slide pane")
    ap.add_argument("--jump-penalty", type=float, default=0.02)
    ap.add_argument(
        "--pdf",
        default=None,
        help="deck PDF; enables OCR token matching as a second signal",
    )
    ap.add_argument("--text-weight", type=float, default=1.0)
    ap.add_argument("--out", default=None, help="TSV of time -> slide")
    ap.add_argument("--srt", default=None)
    ap.add_argument("--emit-windows", default=None, help="write per-slide transcript md")
    ap.add_argument(
        "--from-tsv",
        default=None,
        help="emit windows from an existing alignment TSV; skips all scoring",
    )
    ap.add_argument(
        "--control",
        choices=["shuffle"],
        default=None,
        help="sabotage check: permute the deck; scores must collapse",
    )
    args = ap.parse_args()

    assets = args.assets_dir or os.path.join(PREPARED, "assets", args.slug)

    if args.from_tsv:
        if not (args.srt and args.emit_windows):
            raise SystemExit("--from-tsv needs --srt and --emit-windows")
        starts = starts_from_tsv(args.from_tsv)
        emit_windows(starts, args.srt, args.emit_windows)
        return 0

    deck_paths, deck = load_deck(assets)
    print(f"deck: {len(deck_paths)} renders from {assets}", file=sys.stderr)

    if args.control == "shuffle":
        order = list(range(len(deck)))
        random.Random(1234).shuffle(order)
        deck = deck[order]
        print("CONTROL: deck permuted", file=sys.stderr)

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise SystemExit(f"cannot open {args.video}")
    if args.rect:
        x, y, w, h = (int(v) for v in args.rect.split(","))
        rect = Rect(x, y, w, h)
    else:
        rect = detect_rect(cap, deck_paths)
    cap.release()
    print(f"slide pane rect: {rect}", file=sys.stderr)

    vecs = idf = None
    if args.pdf:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        toks = deck_text(args.pdf, len(deck_paths))
        if args.control == "shuffle":
            toks = [toks[i] for i in order]
        idf = build_idf(toks)
        vecs = text_vectors(toks, idf)
        nonempty = sum(1 for t in toks if t)
        print(
            f"text signal: {nonempty}/{len(toks)} slides carry a text layer",
            file=sys.stderr,
        )

    times, scores = score_matrix(
        args.video, deck, rect, args.interval, vecs, idf, args.text_weight
    )
    path = monotonic_align(scores, args.jump_penalty)
    matched = scores[path, np.arange(len(times))]
    raw = scores.argmax(axis=0)
    raw_score = scores.max(axis=0)

    print(
        f"aligned {len(times)} samples -> slides "
        f"{path.min() + 1}..{path.max() + 1}; "
        f"median matched score {np.median(matched):.3f}, "
        f"median per-frame best {np.median(raw_score):.3f}, "
        f"argmax agrees with path on {100.0 * (raw == path).mean():.1f}% of samples",
        file=sys.stderr,
    )

    out = args.out or os.path.join(assets, f"{args.slug}-alignment.tsv")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("time_s\tslide\tmatched_score\targmax_slide\targmax_score\n")
        for i, t in enumerate(times):
            fh.write(
                f"{t:.2f}\t{path[i] + 1}\t{matched[i]:.4f}\t"
                f"{raw[i] + 1}\t{raw_score[i]:.4f}\n"
            )
    print(f"wrote {out}", file=sys.stderr)

    starts: dict[int, float] = {}
    for i, t in enumerate(times):
        starts.setdefault(int(path[i]) + 1, float(t))
    print(f"{len(starts)} of {len(deck_paths)} slides seen on screen", file=sys.stderr)

    if args.emit_windows:
        if not args.srt:
            raise SystemExit("--emit-windows needs --srt")
        emit_windows(starts, args.srt, args.emit_windows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
