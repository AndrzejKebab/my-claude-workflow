#!/usr/bin/env python3
"""Generate an SRT transcript from a video using faster-whisper on CUDA.

Usage:
    LD_LIBRARY_PATH=/usr/local/lib/ollama/cuda_v12:$LD_LIBRARY_PATH \\
        tools/.venv/bin/python3 tools/transcribe_to_srt.py \\
        <video> <out.srt> [model_size]

`model_size` defaults to `medium`. Pick the smallest model that captures the
talk's vocabulary cleanly — `medium` is the established corpus default.

This file used to live as an inline `/tmp/transcribe_to_srt.py` blob recreated
by the /research skill on every HLS run. Promoted to tools/ so future runs reuse
this single source of truth.

Non-destructive: refuses to overwrite an existing SRT unless `--force` is passed
as the 4th positional arg. The temporary WAV is always cleaned up.
"""
import datetime
import os
import secrets
import subprocess
import sys
import tempfile


def main():
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    video_path, srt_out = sys.argv[1], sys.argv[2]
    model_size = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "medium"
    force = "--force" in sys.argv

    if os.path.exists(srt_out) and not force:
        # Write to a randomised sidecar so concurrent agents don't clobber each
        # other when retranscribing the same video.
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = secrets.token_hex(3)
        base, ext = os.path.splitext(srt_out)
        sidecar = f"{base}.regen-{stamp}-{suffix}{ext}"
        print(f"EXISTS, writing regenerated SRT to sidecar: {sidecar}", file=sys.stderr)
        print(f"(pass --force to overwrite {srt_out} in place)", file=sys.stderr)
        srt_out = sidecar

    wav = tempfile.mktemp(suffix=".wav")
    try:
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1", "-y", wav],
            capture_output=True, check=True,
        )

        from faster_whisper import WhisperModel
        model = WhisperModel(model_size, device="cuda", compute_type="float16")
        segments, _info = model.transcribe(wav, language="en", beam_size=5)

        def fmt(s):
            h = int(s) // 3600
            m = (int(s) % 3600) // 60
            sec = int(s) % 60
            ms = int((s - int(s)) * 1000)
            return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

        lines = []
        for i, seg in enumerate(segments, 1):
            lines += [str(i), f"{fmt(seg.start)} --> {fmt(seg.end)}", seg.text.strip(), ""]
        with open(srt_out, "w") as f:
            f.write("\n".join(lines))
    finally:
        if os.path.exists(wav):
            os.unlink(wav)


if __name__ == "__main__":
    main()
