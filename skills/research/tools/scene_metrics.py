"""Frame-difference metrics for slide/scene detection.

Shared by `research_video.py` (which builds the final markdown) and
`redetect_scenes.py` (the aggressive re-detection helper) so the two cannot
drift apart.

Why more than one metric exists
-------------------------------

The original detector compared a 2D **hue-saturation** histogram with the
Bhattacharyya distance. That metric discards luminance by construction, so a
deck of black-text-on-white slides is very nearly invisible to it: two entirely
different text slides differ only in where the black pixels sit, which is a
luminance-only change.

Measured on the I3D 2026 Hoffman keynote (720p24, white slides with a small
live speaker picture-in-picture in the corner), sampling pairs 5-10 s apart
within one slide as the noise floor and pairs spanning a known slide change as
the signal:

    pair                        HS-bhat    lumaMAD    edgeMAD
    SAME slide (2150 / 2155)     0.0633     0.0016     0.0056
    SAME slide (2150 / 2160)     0.0575     0.0014     0.0056
    SAME slide (1900 / 1910)     0.0566     0.0015     0.0041
    DIFF slide (2150 / 2200)     0.0676     0.0682     0.0818
    DIFF slide (1850 / 1950)     0.0535     0.0467     0.0690
    DIFF slide (1790 / 1850)     0.3478     0.1439     0.1411
    DIFF slide (2050 / 2150)     0.2924     0.1592     0.1116

For the two text-only slide changes the HS-histogram score (0.0535, 0.0676)
falls *inside* the same-slide band (0.0566-0.0633) — signal is below noise, so
no threshold can separate them and lowering `--threshold` only adds false
positives elsewhere. `luma` separates the same two pairs by roughly 30x
(0.0467 vs a 0.0016 floor) and still fires strongly on the colourful pairs, so
it dominates the histogram on both slide classes rather than trading one for
the other.

The speaker picture-in-picture is live video and is already moving within every
same-slide sample above, so its motion is part of the quoted noise floor.

`luma` is therefore the default. `hsv` is kept for footage where luminance
changes constantly but content does not — handheld camera work, stage lighting,
gameplay capture — and for reproducing pre-2026-07 extractions. `edge` is a
middle option that keys on text/line structure and ignores flat-field
brightness shifts (projector auto-exposure, fades).

Default thresholds sit in the measured gap, not at a round number: `luma`
0.010 is ~6x the observed same-slide floor and ~4.5x below the weakest real
transition.
"""

from __future__ import annotations

import cv2
import numpy as np

METRICS = ("luma", "hsv", "edge")

DEFAULT_THRESHOLDS = {
    "luma": 0.010,
    "hsv": 0.35,
    "edge": 0.020,
}

_LUMA_SIZE = (160, 90)
_EDGE_SIZE = (320, 180)


def default_threshold(metric: str) -> float:
    try:
        return DEFAULT_THRESHOLDS[metric]
    except KeyError:
        raise ValueError(
            f"unknown scene metric {metric!r}; expected one of {', '.join(METRICS)}"
        ) from None


def signature(frame, metric: str = "luma"):
    """Reduce a BGR frame to a comparable signature for `distance`."""
    if metric == "hsv":
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [48, 48], [0, 180, 0, 256])
        cv2.normalize(hist, hist)
        return hist

    if metric == "luma":
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return cv2.resize(gray, _LUMA_SIZE).astype(np.float32) / 255.0

    if metric == "edge":
        gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), _EDGE_SIZE)
        return (cv2.Canny(gray, 60, 160) > 0).astype(np.float32)

    raise ValueError(
        f"unknown scene metric {metric!r}; expected one of {', '.join(METRICS)}"
    )


def distance(prev, cur, metric: str = "luma") -> float:
    """Difference between two signatures; larger means more likely a cut."""
    if metric == "hsv":
        return float(cv2.compareHist(prev, cur, cv2.HISTCMP_BHATTACHARYYA))
    return float(np.abs(prev - cur).mean())
