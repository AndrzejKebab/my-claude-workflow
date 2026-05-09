"""Singleton wrapper around openocr-python for the research pipeline.

The OpenOCR engine has a non-trivial init cost (model load + first-run ONNX
download). Phase-2 OCR processes many pages per run, so all callers share a
single lazily-initialised instance instead of paying the cost per page.

Public API:

    ocr_image(path)   -> str   # OCR a file path, return concatenated text
    ocr_numpy(img)    -> str   # OCR an in-memory cv2/numpy image (BGR)
    ocr_available()   -> bool  # True if openocr is importable

The engine runs in mobile/ONNX mode by default (auto-downloads ~36 MB of
models to ~/.cache/openocr/ on first use). Override via env vars:

    OPENOCR_MODE=server          # higher-accuracy torch backend
    OPENOCR_BACKEND=torch        # implies torch + torchvision installed
    OPENOCR_DROP_SCORE=0.5       # confidence cutoff
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache

import cv2


def ocr_available() -> bool:
    try:
        import openocr  # noqa: F401
        return True
    except ImportError:
        return False


@lru_cache(maxsize=1)
def _get_engine():
    from openocr import OpenOCR

    mode = os.environ.get("OPENOCR_MODE", "mobile")
    backend = os.environ.get("OPENOCR_BACKEND", "onnx")
    drop_score = float(os.environ.get("OPENOCR_DROP_SCORE", "0.5"))
    return OpenOCR(task="ocr", mode=mode, backend=backend, drop_score=drop_score)


def _sort_key(entry):
    pts = entry.get("points") or [[0, 0]]
    ys = [p[1] for p in pts]
    xs = [p[0] for p in pts]
    return (min(ys), min(xs))


def ocr_numpy(img) -> str:
    """OCR a BGR numpy image, return text lines joined by newlines."""
    if img is None:
        return ""
    try:
        engine = _get_engine()
        results, _ = engine(img_numpy=img)
    except Exception as e:
        print(f"  [openocr] error: {e}", file=sys.stderr)
        return ""
    if not results:
        return ""
    # results is list-of-list when img_numpy is passed (one outer entry per image)
    entries = []
    for res in results:
        if not res:
            continue
        entries.extend(res)
    entries.sort(key=_sort_key)
    return "\n".join(
        (e.get("transcription") or "").strip()
        for e in entries
        if (e.get("transcription") or "").strip()
    )


def ocr_image(image_path: str) -> str:
    """OCR an image file, return text lines joined by newlines."""
    img = cv2.imread(image_path)
    if img is None:
        return ""
    return ocr_numpy(img)
