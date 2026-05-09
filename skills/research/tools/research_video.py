#!/usr/bin/env python3
"""Extract presentation slides from YouTube/video recordings.

Scene detection pipeline:
1. Sample frames at 1fps
2. Compute histogram difference between consecutive frames
3. Detect scene transitions (large histogram changes)
4. Classify each scene: slide, speaker-only, demo/video
5. OCR slide frames, align with transcript timestamps
6. Output structured markdown
"""

import datetime
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from openocr_engine import ocr_numpy as _ocr_numpy_engine

# Resolve from invocation cwd, not script location (skill-shipped scripts).
PROJECT_ROOT = Path(os.environ.get("RESEARCH_PROJECT_ROOT", os.getcwd())).resolve()
OUTPUT_DIR = PROJECT_ROOT / "docs" / "research"
ASSETS_DIR = OUTPUT_DIR / "assets"


@dataclass
class Scene:
    start_time: float       # seconds
    end_time: float         # seconds
    scene_type: str         # "slide", "speaker", "demo"
    frame_path: str = ""    # path to representative frame
    ocr_text: str = ""      # OCR result for slides
    transcript: str = ""    # speech during this scene


@dataclass
class VideoInfo:
    title: str
    duration: float
    video_id: str
    url: str
    slug: str


def download_video(url: str, output_dir: Path) -> tuple[Path, VideoInfo]:
    """Download video and metadata via yt-dlp."""
    # Get metadata first
    meta_cmd = [
        "yt-dlp", "--print", "%(title)s\n%(duration)s\n%(id)s",
        "--no-download", url,
    ]
    result = subprocess.run(meta_cmd, capture_output=True, text=True, timeout=30)
    lines = [l for l in result.stdout.strip().split("\n") if l and not l.startswith("WARNING")]
    # Filter out error lines
    clean_lines = []
    for l in lines:
        if not any(x in l for x in ["Error", "WARNING", "EJS", "deno", "eval", "input ="]):
            clean_lines.append(l)
    title = clean_lines[0] if clean_lines else "Unknown"
    duration = float(clean_lines[1]) if len(clean_lines) > 1 else 0
    video_id = clean_lines[2] if len(clean_lines) > 2 else "unknown"

    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60]

    video_path = output_dir / f"{slug}.mp4"
    srt_path = output_dir / f"{slug}.en.srt"

    # Download video (720p max for speed)
    if not video_path.exists():
        print(f"  Downloading video...")
        dl_cmd = [
            "yt-dlp",
            "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
            "--merge-output-format", "mp4",
            "-o", str(video_path),
            url,
        ]
        subprocess.run(dl_cmd, capture_output=True, timeout=600)

    # Download auto-captions
    if not srt_path.exists():
        print(f"  Downloading captions...")
        sub_cmd = [
            "yt-dlp", "--write-auto-sub", "--sub-lang", "en",
            "--sub-format", "srt", "--skip-download",
            "-o", str(output_dir / slug),
            url,
        ]
        subprocess.run(sub_cmd, capture_output=True, timeout=60)

    info = VideoInfo(
        title=title, duration=duration, video_id=video_id,
        url=url, slug=slug,
    )
    return video_path, info


def parse_srt(srt_path: Path) -> list[tuple[float, float, str]]:
    """Parse SRT file into list of (start_sec, end_sec, text)."""
    if not srt_path.exists():
        return []
    content = srt_path.read_text(encoding="utf-8", errors="replace")
    entries = []
    blocks = re.split(r'\n\n+', content.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        time_match = re.match(
            r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})',
            lines[1],
        )
        if not time_match:
            continue
        g = time_match.groups()
        start = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
        end = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000
        text = ' '.join(lines[2:]).strip()
        # Skip music/sound markers
        if text.startswith('[') and text.endswith(']'):
            continue
        entries.append((start, end, text))
    return entries


def detect_scenes(video_path: Path, sample_interval: float = 1.0,
                  threshold: float = 0.35) -> list[tuple[float, float]]:
    """Detect scene transitions by histogram difference.

    Returns list of (start_time, end_time) for each scene.
    """
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    frame_interval = int(fps * sample_interval)
    prev_hist = None
    transitions = [0.0]  # always start at 0

    print(f"  Scanning {duration:.0f}s video at {sample_interval}s intervals...")

    frame_idx = 0
    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to HSV and compute histogram
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [32, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist)

        if prev_hist is not None:
            diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_BHATTACHARYYA)
            if diff > threshold:
                time_sec = frame_idx / fps
                # Don't add transitions too close together (< 2s)
                if time_sec - transitions[-1] > 2.0:
                    transitions.append(time_sec)

        prev_hist = hist
        frame_idx += frame_interval

    transitions.append(duration)
    cap.release()

    # Build scene intervals
    scenes = []
    for i in range(len(transitions) - 1):
        scenes.append((transitions[i], transitions[i + 1]))

    print(f"  Found {len(scenes)} scenes")
    return scenes


def extract_frame(video_path: Path, time_sec: float, output_path: Path):
    """Extract a single frame at given timestamp."""
    subprocess.run(
        ["ffmpeg", "-ss", str(time_sec), "-i", str(video_path),
         "-frames:v", "1", "-q:v", "2", "-y", str(output_path)],
        capture_output=True, timeout=10,
    )


def classify_frame(frame: np.ndarray) -> str:
    """Classify a frame as 'slide', 'speaker', or 'demo'.

    Heuristic: slides have a large bright rectangular region (the projected slide).
    Speaker-only frames are mostly dark (stage lighting).
    Demo frames are full-screen game footage (varied colors, no bright rectangle).
    """
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Check the right 60% of the frame (where slides typically appear)
    slide_region = gray[:, int(w * 0.35):]
    bright_ratio = np.mean(slide_region > 160) # fraction of bright pixels

    # Check overall brightness
    overall_brightness = np.mean(gray)

    # Slide: right portion has significant bright area (projected slide)
    if bright_ratio > 0.25:
        return "slide"

    # Speaker: overall dark, stage lighting
    if overall_brightness < 80:
        return "speaker"

    # Demo: everything else (game footage, varied brightness)
    return "demo"


def classify_scene(video_path: Path, start: float, end: float) -> str:
    """Classify a scene by sampling multiple frames and voting."""
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Sample up to 3 frames from the scene
    scene_dur = end - start
    sample_times = [
        start + scene_dur * 0.25,
        start + scene_dur * 0.5,
        start + scene_dur * 0.75,
    ]

    votes = {"slide": 0, "speaker": 0, "demo": 0}
    for t in sample_times:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
        ret, frame = cap.read()
        if ret:
            classification = classify_frame(frame)
            votes[classification] += 1

    cap.release()
    return max(votes, key=votes.get)


def find_slide_region(frame: np.ndarray) -> tuple[int, int, int, int] | None:
    """Detect the projected slide rectangle in a presentation frame.

    Returns (x, y, w, h) of the slide region, or None if not found.
    Uses the bright rectangular region that is the projected slide.
    """
    h, w = frame.shape[:2]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Threshold to find bright regions (slide background)
    _, binary = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Find largest rectangular contour in right half of frame
    best = None
    best_area = 0
    min_x = int(w * 0.25)  # slide must be in right 75%
    min_area = h * w * 0.08  # at least 8% of frame

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area = cw * ch
        if x + cw / 2 > min_x and area > min_area and area > best_area:
            # Check aspect ratio is reasonable (wider than tall)
            if 0.3 < ch / cw < 1.5:
                best = (x, y, cw, ch)
                best_area = area

    return best


def ocr_frame(frame_path: str) -> str:
    """OCR a frame image, auto-detecting the slide region."""
    try:
        img = cv2.imread(frame_path)
        if img is None:
            return ""
        h, w = img.shape[:2]

        # Try to detect the slide region
        region = find_slide_region(img)
        if region:
            rx, ry, rw, rh = region
            # Add small padding
            pad = 5
            rx = max(0, rx - pad)
            ry = max(0, ry - pad)
            rw = min(w - rx, rw + 2 * pad)
            rh = min(h - ry, rh + 2 * pad)
            slide_crop = img[ry:ry + rh, rx:rx + rw]
        else:
            # Fallback: crop right 60%
            slide_crop = img[:, int(w * 0.35):]

        # OpenOCR handles its own text-region detection — no thresholding /
        # masking needed (the heavy preprocessing the tesseract path required
        # was specifically to mask photographic backgrounds).
        text = _ocr_numpy_engine(slide_crop)

        # Light garbage filter — OpenOCR is much cleaner than tesseract,
        # but very-low-content frames (speaker thumbnails, dividers) still
        # produce a couple of stray words.
        clean_lines = []
        for line in text.split('\n'):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            words = re.findall(r'[a-zA-Z]{3,}', line)
            if not words:
                continue
            clean_lines.append(line)

        text = '\n'.join(clean_lines)
        if len(re.sub(r'[^a-zA-Z]', '', text)) < 10:
            return ""
        return text
    except Exception:
        return ""


def get_transcript_for_range(captions: list, start: float, end: float) -> str:
    """Get transcript text overlapping a time range, deduplicating auto-caption overlaps."""
    texts = []
    for cap_start, cap_end, text in captions:
        # Only include captions that START within our range
        # (prevents the heavy duplication from overlapping auto-captions)
        if cap_start >= start and cap_start < end:
            clean = text.strip()
            if clean:
                texts.append(clean)

    # Join and clean up repeated fragments
    result = ' '.join(texts)
    # Remove duplicate consecutive words (common in auto-captions)
    words = result.split()
    deduped = []
    for w in words:
        if not deduped or w.lower() != deduped[-1].lower():
            deduped.append(w)
    return ' '.join(deduped)


def merge_similar_scenes(scenes: list[Scene], video_path: Path) -> list[Scene]:
    """Merge consecutive scenes of the same type if the slide content hasn't changed."""
    if not scenes:
        return scenes

    merged = [scenes[0]]
    for scene in scenes[1:]:
        prev = merged[-1]

        should_merge = False

        if scene.scene_type == prev.scene_type:
            if scene.scene_type == "slide":
                # For slides, merge if OCR text is similar (same slide, animation step)
                if scene.ocr_text and prev.ocr_text:
                    words_a = set(prev.ocr_text.lower().split())
                    words_b = set(scene.ocr_text.lower().split())
                    if words_a and words_b:
                        overlap = len(words_a & words_b) / max(len(words_a), len(words_b))
                        if overlap > 0.4:
                            should_merge = True
                elif not scene.ocr_text and not prev.ocr_text:
                    # Both have no text — likely same visual
                    should_merge = True
            else:
                # Speaker/demo: always merge consecutive same-type
                should_merge = True

        # Also merge very short scenes (< 3s) into previous regardless of type
        if scene.end_time - scene.start_time < 3:
            should_merge = True

        if should_merge:
            prev.end_time = scene.end_time
            prev.transcript = (prev.transcript + ' ' + scene.transcript).strip()
            # Keep the longer OCR text
            if len(scene.ocr_text) > len(prev.ocr_text):
                prev.ocr_text = scene.ocr_text
                prev.frame_path = scene.frame_path
        else:
            merged.append(scene)

    return merged


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def process_video(video_path: Path, info: VideoInfo, srt_path: Path) -> str:
    """Full pipeline: detect scenes, classify, OCR, transcribe, emit markdown."""
    slug = info.slug
    slug_assets = ASSETS_DIR / slug
    slug_assets.mkdir(parents=True, exist_ok=True)

    # Parse captions
    captions = parse_srt(srt_path)
    print(f"  Loaded {len(captions)} caption entries")

    # Detect scene transitions
    scene_intervals = detect_scenes(video_path)

    # Classify and process each scene
    scenes = []
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)

    for i, (start, end) in enumerate(scene_intervals):
        scene_type = classify_scene(video_path, start, end)

        scene = Scene(
            start_time=start,
            end_time=end,
            scene_type=scene_type,
        )

        # Extract representative frame (middle of scene)
        mid_time = (start + end) / 2
        frame_name = f"frame-{i:04d}-{format_timestamp(start).replace(':', '')}.jpg"
        frame_path = slug_assets / frame_name
        extract_frame(video_path, mid_time, frame_path)
        scene.frame_path = f"assets/{slug}/{frame_name}"

        # OCR for slide frames
        if scene_type == "slide":
            scene.ocr_text = ocr_frame(str(frame_path))

        # Get transcript for this time range
        scene.transcript = get_transcript_for_range(captions, start, end)

        scenes.append(scene)

        if (i + 1) % 20 == 0:
            print(f"  Processed {i + 1}/{len(scene_intervals)} scenes...")

    cap.release()

    # Merge similar consecutive scenes
    scenes = merge_similar_scenes(scenes, video_path)
    print(f"  {len(scenes)} scenes after merging")

    # Generate markdown
    md_lines = [
        "---",
        f"source: {info.url}",
        "type: youtube",
        f"duration: {format_timestamp(info.duration)}",
        f"extracted: 2026-04-16",
        f"slug: {slug}",
        "---",
        "",
        f"# {info.title}",
        "",
        f"> Source: [{info.title}]({info.url}) ({format_timestamp(info.duration)})",
        "",
    ]

    slide_num = 0
    for scene in scenes:
        ts = format_timestamp(scene.start_time)
        dur = scene.end_time - scene.start_time

        if scene.scene_type == "slide":
            slide_num += 1
            # Try to extract a title from OCR text (first line that looks like a heading)
            heading = ""
            if scene.ocr_text:
                first_lines = scene.ocr_text.split('\n')
                for fl in first_lines:
                    fl = fl.strip()
                    if len(fl) > 3 and len(fl) < 80:
                        heading = f" -- {fl}"
                        break

            md_lines.append(f"## Slide {slide_num}{heading}")
            md_lines.append(f"*[{ts}] ({dur:.0f}s)*")
            md_lines.append("")

            if scene.ocr_text:
                md_lines.append(scene.ocr_text)
                md_lines.append("")

            md_lines.append(f"![{Path(scene.frame_path).name}]({scene.frame_path})")
            md_lines.append("")

        elif scene.scene_type == "demo":
            md_lines.append(f"## Demo [{ts}]")
            md_lines.append(f"*({dur:.0f}s)*")
            md_lines.append("")
            md_lines.append(f"![{Path(scene.frame_path).name}]({scene.frame_path})")
            md_lines.append("")

        else:  # speaker
            # Skip very short speaker-only segments
            if dur < 3:
                continue
            md_lines.append(f"## [{ts}]")
            md_lines.append("")

        if scene.transcript:
            md_lines.append(f"> {scene.transcript}")
            md_lines.append("")

    # Write markdown (refuse to overwrite an existing extraction unless --force).
    # Sidecar uses a randomised suffix so concurrent agents extracting the same
    # slug don't clobber each other's regen draft.
    md_path = OUTPUT_DIR / f"{slug}.md"
    force = "--force" in sys.argv
    if md_path.exists() and not force:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = secrets.token_hex(3)
        backup_path = OUTPUT_DIR / f"{slug}.regen-{stamp}-{suffix}.md"
        backup_path.write_text('\n'.join(md_lines), encoding="utf-8")
        print(f"  EXISTS, wrote regenerated draft alongside: {backup_path.relative_to(PROJECT_ROOT)}")
        print(f"  (pass --force to overwrite {md_path.relative_to(PROJECT_ROOT)} in place)")
        md_path = backup_path
    else:
        md_path.write_text('\n'.join(md_lines), encoding="utf-8")
        print(f"  -> {md_path.relative_to(PROJECT_ROOT)}")

    return str(md_path)


def main():
    if len(sys.argv) < 2:
        print("Usage: research_video.py <url-or-local-path> [--title='...'] [--slug='...']")
        sys.exit(1)

    url = sys.argv[1]
    extra_title = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--title=")), None)
    extra_slug = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--slug=")), None)
    work_dir = Path(tempfile.mkdtemp(prefix="research-"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    local_extensions = (".mp4", ".mkv", ".webm", ".mov", ".avi")
    if any(url.lower().endswith(ext) for ext in local_extensions) and os.path.exists(url):
        video_path = Path(url)
        import subprocess as _sp
        probe = _sp.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", url],
            capture_output=True, text=True,
        )
        import json as _json
        duration = float(_json.loads(probe.stdout).get("format", {}).get("duration", 0))
        title = extra_title or video_path.stem.replace("-", " ").replace("_", " ").title()
        slug = extra_slug or re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60]
        info = VideoInfo(title=title, duration=duration, video_id=slug, url=url, slug=slug)
        # Look for SRT next to the video file first, then fall back to work_dir
        srt_candidate = video_path.parent / f"{video_path.stem}.en.srt"
        srt_path = srt_candidate if srt_candidate.exists() else work_dir / f"{slug}.en.srt"
        print(f"Local file: {video_path} ({format_timestamp(duration)})")
    else:
        print(f"Downloading: {url}")
        video_path, info = download_video(url, work_dir)
        if extra_title:
            info.title = extra_title
        if extra_slug:
            info.slug = extra_slug
        srt_path = work_dir / f"{info.slug}.en.srt"

    print(f"Processing: {info.title} ({format_timestamp(info.duration)})")
    md_path = process_video(video_path, info, srt_path)

    print(f"\nDone: {md_path}")


if __name__ == "__main__":
    main()
