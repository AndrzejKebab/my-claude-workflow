#!/usr/bin/env python3
"""Phase 2: PPTX video transcription.

Phase 2 used to run OCR on every referenced image asset, but that role
moved into phase 1 as a body-text fallback (image-only PDFs / slides /
scanned reproductions where there is no native text layer to extract).
Image inclusions inside otherwise-text-rich docs are NEVER OCR'd here —
the vision pass reads them with full visual context and outclasses any
CPU OCR engine; OCR scaffolding alongside an image only narrows what
the vision agent looks at and primes it with mistakes.

What's left for phase 2: extract videos embedded in PPTX decks and
transcribe them with faster-whisper.

Invoked per-document with the source path as the first argument:

    extract_research_phase2.py <path-to.pptx> [--slug SLUG]

The slug defaults to the filename stem and must match the one phase 1 used;
the /research workflow passes the same explicit --slug to both. A non-PPTX
path is a no-op (only PPTX decks carry embedded video).
"""

import os
import re
import sys
import subprocess
import tempfile
import zipfile
from lxml import etree
from pathlib import Path

# The extracted markdown corpus lives at a single hardcoded global location,
# independent of cwd / which project invoked /research.
OUTPUT_DIR = Path("/mnt/archive4/PAPERS/Prepared")
PROJECT_ROOT = OUTPUT_DIR  # display base for relative_to() in log output
ASSETS_DIR = OUTPUT_DIR / "assets"


def extract_pptx_videos(pptx_path: str, slug: str) -> dict[str, Path]:
    """Extract all video files from PPTX, return {media_name: output_path}."""
    slug_assets = ASSETS_DIR / slug
    slug_assets.mkdir(parents=True, exist_ok=True)

    extracted = {}
    zf = zipfile.ZipFile(pptx_path)
    for name in zf.namelist():
        if not name.startswith("ppt/media/media"):
            continue
        basename = name.split("/")[-1]
        out_path = slug_assets / basename
        with open(out_path, "wb") as f:
            f.write(zf.read(name))
        extracted[basename] = out_path
    zf.close()
    return extracted


def get_slide_video_map(pptx_path: str) -> dict[int, list[str]]:
    """Map slide numbers to their embedded video filenames."""
    zf = zipfile.ZipFile(pptx_path)
    slide_videos = {}
    for name in sorted(zf.namelist()):
        if not (name.startswith("ppt/slides/_rels/") and name.endswith(".rels")):
            continue
        content = zf.read(name)
        root = etree.fromstring(content)
        videos = []
        for rel in root:
            target = rel.get("Target", "")
            if "media/media" in target:
                videos.append(target.split("/")[-1])
        if videos:
            # slide1.xml.rels -> slide number 1
            slide_name = name.replace("ppt/slides/_rels/", "").replace(".xml.rels", "")
            slide_num = int(re.search(r"(\d+)", slide_name).group(1))
            # Deduplicate
            slide_videos[slide_num] = list(dict.fromkeys(videos))
    zf.close()
    return slide_videos


def has_audio(video_path: str) -> bool:
    """Check if a video file has an audio track."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0", video_path],
            capture_output=True, text=True, timeout=10,
        )
        return "audio" in result.stdout
    except Exception:
        return False


def get_duration(video_path: str) -> float:
    """Get video duration in seconds."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "csv=p=0", video_path],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def extract_audio(video_path: str, audio_path: str) -> bool:
    """Extract audio from video to WAV for whisper."""
    try:
        subprocess.run(
            ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1", "-y", audio_path],
            capture_output=True, timeout=60,
        )
        return os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000
    except Exception:
        return False


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using faster-whisper."""
    try:
        model = transcribe_audio._model
        segments, info = model.transcribe(audio_path, language="en", beam_size=5)
        text = " ".join(seg.text.strip() for seg in segments)
        return text.strip()
    except Exception as e:
        print(f"    Whisper error: {e}")
        return ""


def load_whisper_model():
    """Load faster-whisper model once."""
    try:
        from faster_whisper import WhisperModel
        print("Loading faster-whisper model (base)...")
        model = WhisperModel("base", device="cpu", compute_type="int8")
        transcribe_audio._model = model
        return True
    except ImportError:
        print("WARNING: faster-whisper not installed, skipping video transcription")
        return False
    except Exception as e:
        print(f"WARNING: whisper load failed: {e}")
        return False


def process_video(pptx_path: str, slug: str):
    """Extract videos from one PPTX, transcribe audio, update `<slug>.md`."""
    print("\n=== Phase 2b: Video Extraction & Transcription ===\n")

    md_file = OUTPUT_DIR / f"{slug}.md"
    if not md_file.exists():
        print(f"SKIP: {md_file} does not exist — run phase 1 first.")
        return 0, 0

    content = md_file.read_text(encoding="utf-8")
    if "VIDEO:" not in content:
        print(f"No VIDEO markers in {slug}.md — nothing to transcribe.")
        return 0, 0

    print(f"Processing videos: {slug}...")

    whisper_available = load_whisper_model()
    video_count = 0
    transcript_count = 0

    # Extract all videos from PPTX
    video_files = extract_pptx_videos(pptx_path, slug)
    print(f"  Extracted {len(video_files)} video files")

    # Get slide-to-video mapping
    slide_map = get_slide_video_map(pptx_path)

    # Build a lookup: video_name -> list of slide numbers
    video_to_slides = {}
    for slide_num, vids in slide_map.items():
        for vid in vids:
            video_to_slides.setdefault(vid, []).append(slide_num)

    # Transcribe each unique video
    transcripts = {}
    for vid_name, vid_path in sorted(video_files.items()):
        vid_path_str = str(vid_path)
        duration = get_duration(vid_path_str)
        has_aud = has_audio(vid_path_str)

        print(f"  {vid_name}: {duration:.1f}s, audio={'yes' if has_aud else 'no'}")

        if has_aud and whisper_available:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                wav_path = tmp.name
            if extract_audio(vid_path_str, wav_path):
                text = transcribe_audio(wav_path)
                if text:
                    transcripts[vid_name] = text
                    transcript_count += 1
                    print(f"    Transcribed: {len(text)} chars")
                os.unlink(wav_path)
            else:
                if os.path.exists(wav_path):
                    os.unlink(wav_path)

    # Update markdown: replace VIDEO markers with video links + transcripts
    lines = content.split("\n")
    new_lines = []
    # Find the slide number context for each VIDEO marker
    current_slide = None
    seen_videos_on_slide = {}

    for line in lines:
        m = re.match(r"## Slide (\d+)", line)
        if m:
            current_slide = int(m.group(1))
            seen_videos_on_slide[current_slide] = 0

        video_match = re.search(r"<!-- VIDEO: (.+?) - TRANSCRIPTION-PENDING -->", line)
        if not video_match:
            new_lines.append(line)
            continue

        shape_name = video_match.group(1)
        video_count += 1

        # Find which video file this corresponds to
        vid_filename = None
        if current_slide and current_slide in slide_map:
            slide_vids = slide_map[current_slide]
            idx = seen_videos_on_slide.get(current_slide, 0)
            if idx < len(slide_vids):
                vid_filename = slide_vids[idx]
                seen_videos_on_slide[current_slide] = idx + 1

        if vid_filename and vid_filename in video_files:
            rel_path = f"assets/{slug}/{vid_filename}"
            duration = get_duration(str(video_files[vid_filename]))
            new_lines.append(f"**Video:** [{vid_filename}]({rel_path}) ({duration:.1f}s)")
            new_lines.append("")

            if vid_filename in transcripts:
                new_lines.append(f"> **Transcript:** {transcripts[vid_filename]}")
                new_lines.append("")
            elif not has_audio(str(video_files[vid_filename])):
                new_lines.append(f"> *Silent video (no audio track)*")
                new_lines.append("")
        else:
            # Can't resolve video file — keep a simpler marker
            new_lines.append(f"**Video:** {shape_name} *(embedded, not resolved)*")
            new_lines.append("")

    md_file.write_text("\n".join(new_lines), encoding="utf-8")

    print(f"\nVideos: {video_count} markers processed, {transcript_count} transcribed")
    return video_count, transcript_count


def report_pending_markers(slug: str):
    """Print the count of unresolved phase-2 markers in `<slug>.md`."""
    md_file = OUTPUT_DIR / f"{slug}.md"
    video_remaining = md_file.read_text(encoding="utf-8").count("TRANSCRIPTION-PENDING") if md_file.exists() else 0
    print(f"  Phase 2 marker counts: TRANSCRIPTION-PENDING={video_remaining}")


def _slugify(text: str) -> str:
    """Scaffolding slug from a filename stem (fallback when --slug is omitted).

    Must match extract_research.py's _slugify so phase 1 and phase 2 agree on
    the `<slug>.md` filename when neither call passes --slug. The /research
    workflow always passes an explicit citable --slug to both.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "untitled"


USAGE = "usage: extract_research_phase2.py <path-to.pptx> [--slug SLUG]"


def main():
    path: str | None = None
    slug: str | None = None
    i = 0
    argv = sys.argv[1:]
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--slug="):
            slug = arg.split("=", 1)[1]
        elif arg == "--slug":
            i += 1
            slug = argv[i] if i < len(argv) else None
        elif arg.startswith("-"):
            raise SystemExit(f"extract_research_phase2.py: unknown flag {arg!r}\n{USAGE}")
        elif path is None:
            path = arg
        else:
            raise SystemExit(
                f"extract_research_phase2.py: unexpected extra argument {arg!r}\n{USAGE}"
            )
        i += 1
    if path is None:
        raise SystemExit(USAGE)

    # Phase 2 only handles videos embedded in PPTX decks. A PDF source has none,
    # so it is a no-op rather than an error.
    if Path(path).suffix.lower() != ".pptx":
        print(f"phase 2 handles PPTX video extraction only; {path} is not a .pptx — nothing to do.")
        print("\nPhase 2 complete.")
        return

    if slug is None:
        slug = _slugify(Path(path).stem)

    process_video(path, slug)
    report_pending_markers(slug)
    print("\nPhase 2 complete.")


if __name__ == "__main__":
    main()
