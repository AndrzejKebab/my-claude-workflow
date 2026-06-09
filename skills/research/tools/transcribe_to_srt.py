#!/usr/bin/env python3
"""Generate an SRT transcript from a video using faster-whisper.

Usage:
    .venv/bin/python tools/transcribe_to_srt.py <video> <out.srt> [model_size] [--force]

`model_size` defaults to `large-v3` — the SOTA Whisper model. This is the
canonical transcript source for the /research video pipeline: recorded-talk
audio is always re-transcribed here rather than scraped from YouTube
auto-captions, which are lower quality and frequently mis-segment technical
vocabulary. `research_video.py` imports `transcribe()` from this module for
exactly that reason.

CUDA libraries are self-bootstrapped (see `_preload_cuda_libs`): the skill venv
carries torch's CUDA-13 nvidia stack, but ctranslate2 (faster-whisper's backend)
`dlopen`s `libcublas.so.12` by soname, so the CUDA-12 cublas wheel
(`nvidia-cublas-cu12`, pinned in `pyproject.toml`) is preloaded by absolute path
before the model is built. No `LD_LIBRARY_PATH` dance is required at the call
site, and the preload is import-safe (no process re-exec), so it works whether
this module is run as a script or imported. When CUDA is unavailable the model
falls back to CPU int8.

This file used to live as an inline `/tmp/transcribe_to_srt.py` blob recreated by
the /research skill on every run. Promoted to tools/ so future runs reuse this
single source of truth.

Non-destructive: refuses to overwrite an existing SRT unless `--force` is passed.
The temporary WAV is always cleaned up.
"""
import ctypes
import datetime
import glob
import os
import secrets
import subprocess
import sys
import sysconfig
import tempfile

# SOTA Whisper checkpoint. Override with the optional 3rd positional arg.
DEFAULT_MODEL = "large-v3"


def _preload_cuda_libs() -> bool:
    """Preload the CUDA-12 cublas stack ctranslate2 dlopens by soname.

    ctranslate2 4.7.x calls ``dlopen("libcublas.so.12")`` at encode time. glibc
    matches that against any object already loaded with a matching DT_SONAME, so
    loading the venv-bundled CUDA-12 cublas by absolute path here makes the later
    soname lookup resolve without touching LD_LIBRARY_PATH. Loaded RTLD_GLOBAL in
    dependency order (cublasLt before cublas). Best-effort: a missing lib just
    means the CPU fallback path takes over.

    Returns True if libcublas.so.12 was loaded.
    """
    site_packages = sysconfig.get_paths()["purelib"]
    # Dependency order: a lib's own NEEDED entries must already be resolvable.
    relpaths = [
        "nvidia/cuda_nvrtc/lib/libnvrtc.so.12",
        "nvidia/cublas/lib/libcublasLt.so.12",
        "nvidia/cublas/lib/libcublas.so.12",
        "nvidia/cudnn/lib/libcudnn.so.9",
    ]
    loaded_cublas = False
    for rel in relpaths:
        for path in glob.glob(os.path.join(site_packages, rel)):
            try:
                ctypes.CDLL(path, mode=ctypes.RTLD_GLOBAL)
                if rel.endswith("libcublas.so.12"):
                    loaded_cublas = True
            except OSError:
                pass  # tolerate; CPU fallback handles a broken CUDA stack
    return loaded_cublas


def _build_model(model_size: str):
    """Build a WhisperModel on CUDA when possible, else CPU int8."""
    from faster_whisper import WhisperModel

    if _preload_cuda_libs():
        try:
            return WhisperModel(model_size, device="cuda", compute_type="float16"), "cuda"
        except Exception as exc:  # noqa: BLE001 — any CUDA init failure → CPU
            print(f"  CUDA init failed ({exc}); falling back to CPU", file=sys.stderr)
    return WhisperModel(model_size, device="cpu", compute_type="int8"), "cpu"


def _fmt(s: float) -> str:
    h = int(s) // 3600
    m = (int(s) % 3600) // 60
    sec = int(s) % 60
    ms = int((s - int(s)) * 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def transcribe(video_path: str, srt_out: str, model_size: str = DEFAULT_MODEL,
               force: bool = False, language: str = "en") -> str:
    """Transcribe ``video_path`` to an SRT at ``srt_out`` and return the path written.

    Without ``force``, an existing ``srt_out`` is preserved and the transcript is
    written to a randomised ``.regen-<stamp>-<hex>.srt`` sidecar instead, so
    concurrent agents retranscribing the same video never clobber each other.
    """
    if os.path.exists(srt_out) and not force:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = secrets.token_hex(3)
        base, ext = os.path.splitext(srt_out)
        srt_out = f"{base}.regen-{stamp}-{suffix}{ext}"
        print(f"  SRT exists, writing to sidecar: {srt_out}", file=sys.stderr)
        print(f"  (pass force=True / --force to overwrite in place)", file=sys.stderr)

    wav = tempfile.mktemp(suffix=".wav")
    try:
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1", "-y", wav],
            capture_output=True, check=True,
        )

        model, device = _build_model(model_size)
        print(f"  Transcribing with faster-whisper {model_size} on {device}...")
        # vad_filter drops non-speech (applause, demo SFX, music) so large-v3
        # does not hallucinate looped text over silent gameplay footage.
        segments, _info = model.transcribe(
            wav, language=language, beam_size=5, vad_filter=True,
        )

        lines = []
        for i, seg in enumerate(segments, 1):
            lines += [str(i), f"{_fmt(seg.start)} --> {_fmt(seg.end)}", seg.text.strip(), ""]
        with open(srt_out, "w") as f:
            f.write("\n".join(lines))
    finally:
        if os.path.exists(wav):
            os.unlink(wav)
    return srt_out


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    video_path, srt_out = sys.argv[1], sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else DEFAULT_MODEL
    force = "--force" in sys.argv
    written = transcribe(video_path, srt_out, model_size=model_size, force=force)
    print(f"Wrote {written}")


if __name__ == "__main__":
    main()
