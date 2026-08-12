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

import scene_metrics
from openocr_engine import ocr_numpy as _ocr_numpy_engine

# The extracted markdown corpus lives at a single hardcoded global location,
# independent of cwd / which project invoked /research.
OUTPUT_DIR = Path("/mnt/archive4/PAPERS/Prepared")
PROJECT_ROOT = OUTPUT_DIR  # display base for relative_to() in log output
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

    # Download video (720p max for speed). The transcript is produced by the
    # SOTA STT pass in main() (faster-whisper), never scraped from YouTube
    # auto-captions — see transcribe_to_srt.transcribe().
    if not video_path.exists():
        print(f"  Downloading video...")
        dl_cmd = [
            "yt-dlp",
            # Prefer H.264 (avc1): OpenCV's FFmpeg backend cannot decode YouTube's
            # default AV1/VP9 (it yields all-black frames, collapsing scene
            # detection). Fall back to any mp4, then best — _ensure_cv2_decodable
            # transcodes whatever lands if it still isn't H.264.
            "-f", ("bestvideo[height<=720][ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/"
                   "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"),
            "--merge-output-format", "mp4",
            "-o", str(video_path),
            url,
        ]
        subprocess.run(dl_cmd, capture_output=True, timeout=600)

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


def _ensure_cv2_decodable(video_path: Path) -> Path:
    """Return a path to a video OpenCV can decode, transcoding to H.264 if needed.

    OpenCV's FFmpeg backend cannot decode AV1 (and frequently VP9): it silently
    yields all-black frames, which collapses scene detection to a single scene —
    a failure that looks like "the detector found nothing" rather than a codec
    error. YouTube serves AV1/VP9 by default, so probe the video codec and, when
    it is not H.264, transcode to a scratch `<stem>-h264.mp4` beside the source.
    The original (the canonical archive copy) is never modified. ffmpeg/whisper
    handle AV1 audio fine, so only the cv2 image path needs this.
    """
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(video_path)],
            capture_output=True, text=True, timeout=30,
        )
        codec = probe.stdout.strip().lower()
    except Exception:
        codec = ""  # probe failed; let cv2 try the original
    if codec in ("", "h264"):
        return video_path
    h264_path = video_path.with_name(video_path.stem + "-h264.mp4")
    if not h264_path.exists():
        print(f"  Transcoding {codec} -> h264 for scene detection (cv2 cannot decode {codec})...")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(video_path), "-c:v", "libx264",
             "-preset", "veryfast", "-crf", "23", "-an", str(h264_path)],
            capture_output=True, check=True,
        )
    return h264_path


def detect_scenes(video_path: Path, sample_interval: float = 1.0,
                  threshold: float | None = None,
                  metric: str = "luma") -> list[tuple[float, float]]:
    """Detect scene transitions by frame difference.

    `metric` selects the difference measure — see tools/scene_metrics.py for
    why `luma` is the default and when `hsv` / `edge` are the right choice.
    A `threshold` of None takes that metric's calibrated default.

    Returns list of (start_time, end_time) for each scene.
    """
    if threshold is None:
        threshold = scene_metrics.default_threshold(metric)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps

    frame_interval = int(fps * sample_interval)
    prev_sig = None
    transitions = [0.0]  # always start at 0

    print(f"  Scanning {duration:.0f}s video at {sample_interval}s intervals "
          f"(metric={metric}, threshold={threshold})...")

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
                time_sec = frame_idx / fps
                # Don't add transitions too close together (< 2s)
                if time_sec - transitions[-1] > 2.0:
                    transitions.append(time_sec)

        prev_sig = sig
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

    # Bright projected-slide signal (light-themed decks fill the slide area with
    # bright pixels). Kept as the primary cue for backward compatibility.
    slide_region = gray[:, int(w * 0.35):]
    bright_ratio = np.mean(slide_region > 160)

    overall_brightness = np.mean(gray)

    # Brightness-independent slide signal. A content slide carries dense, sharp
    # text/vector edges regardless of theme; a dark-themed slide has low
    # brightness but retains that edge structure, where a genuine dark
    # speaker/transition shot does not. Measure edge density on the left 65% of
    # the frame -- the slide area in the typical screen-capture composite layout
    # (large slide + small speaker webcam PiP in the top-right corner). Without
    # this cue, dark-themed decks score as "speaker" and their frames are dropped
    # from the markdown entirely. For recordings that are slides end-to-end, use
    # the --all-slides override, which is exact rather than heuristic.
    left_edges = cv2.Canny(gray[:, : int(w * 0.65)], 50, 150)
    edge_density = np.mean(left_edges > 0)

    # Slide: bright projected region OR structured (text/diagram) content.
    if bright_ratio > 0.25 or edge_density > 0.03:
        return "slide"

    # Speaker: dark and featureless (stage lighting, no slide structure).
    if overall_brightness < 80:
        return "speaker"

    # Demo: everything else (game footage, varied brightness).
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


def process_video(video_path: Path, info: VideoInfo, srt_path: Path,
                  scene_threshold: float | None = None, merge: bool = True,
                  all_slides: bool = False, scene_metric: str = "luma") -> str:
    """Full pipeline: detect scenes, classify, OCR, transcribe, emit markdown.

    `merge=False` skips the consecutive-scene merge pass. The merge heuristic
    ("always merge same-type speaker/demo runs, plus any scene <3s") suits a
    talking-head talk but over-collapses a slide/gameplay-dense deck — e.g. it
    merges a 31-min talk's 190 redetected scenes down to ~6. For those, run with
    --no-merge (typically alongside a tighter --threshold) to keep one section
    per detected slide.
    """
    slug = info.slug
    slug_assets = ASSETS_DIR / slug
    slug_assets.mkdir(parents=True, exist_ok=True)

    # All cv2 reads below (detect_scenes, classify_scene, extract_frame) need an
    # H.264-decodable source — transcode once here if the download was AV1/VP9.
    video_path = _ensure_cv2_decodable(video_path)

    # Parse captions
    captions = parse_srt(srt_path)
    print(f"  Loaded {len(captions)} caption entries")

    # Detect scene transitions
    scene_intervals = detect_scenes(video_path, threshold=scene_threshold,
                                    metric=scene_metric)

    # Classify and process each scene
    scenes = []
    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)

    for i, (start, end) in enumerate(scene_intervals):
        # --all-slides: the recording is slides end-to-end (screen-capture
        # composite). Skip the brightness/edge heuristic, which can drop
        # dark-themed slides, and treat every detected scene as a slide so its
        # frame is OCR'd and embedded.
        scene_type = "slide" if all_slides else classify_scene(video_path, start, end)

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

    # Merge similar consecutive scenes (skip for slide/demo-dense talks)
    if merge:
        scenes = merge_similar_scenes(scenes, video_path)
        print(f"  {len(scenes)} scenes after merging")
    else:
        print(f"  {len(scenes)} scenes (merge disabled)")

    # Generate markdown
    md_lines = [
        "---",
        "type: Conference Talk",
        f"title: {info.title}",
        "medium: youtube",
        f"source: {info.url}",
        f"duration: {format_timestamp(info.duration)}",
        f"extracted: {datetime.date.today().isoformat()}",
        f"slug: {slug}",
        "---",
        "",
        f"# {info.title}",
        "",
        f"> Source: [{info.title}]({info.url}) ({format_timestamp(info.duration)})",
        "",
    ]

    # Slide-centric emit: only a *visual* scene (slide or demo) opens a section.
    # Speaker scenes never emit a header -- their narration is folded into the
    # current section's transcript, which is buffered and flushed when the next
    # visual scene (or the end) arrives. Without this, the non---all-slides path
    # emits a bare "## [MM:SS]" header per speaker micro-scene and splits one
    # continuous sentence across many of them, so an animation-revealed slide
    # becomes dozens of empty timestamp headers with shredded transcript. See the
    # "Slide-centric emit" rule in SKILL.md.
    slide_num = 0
    transcript_buf = []

    def flush_transcript():
        text = " ".join(t.strip() for t in transcript_buf if t.strip())
        transcript_buf.clear()
        if text:
            md_lines.append(f"> {text}")
            md_lines.append("")

    for scene in scenes:
        ts = format_timestamp(scene.start_time)
        dur = scene.end_time - scene.start_time

        if scene.scene_type == "slide":
            flush_transcript()
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

            # NB: scene.ocr_text is deliberately NOT dumped into the body. OpenOCR
            # reads top-to-bottom with no column awareness, so a multi-column slide
            # comes out interleaved row-by-row into mangled, sense-losing text. The
            # vision pass produces the layout-aware slide description; OCR stays
            # internal-only (heading hint above + merge_similar_scenes). See the
            # "OCR is internal-only" rule in SKILL.md.

            md_lines.append(f"![{Path(scene.frame_path).name}]({scene.frame_path})")
            md_lines.append("")

        elif scene.scene_type == "demo":
            flush_transcript()
            md_lines.append(f"## Demo [{ts}]")
            md_lines.append(f"*({dur:.0f}s)*")
            md_lines.append("")
            md_lines.append(f"![{Path(scene.frame_path).name}]({scene.frame_path})")
            md_lines.append("")

        # speaker scenes open no section -- fall through and fold the narration
        # into the current section's transcript buffer.
        if scene.transcript:
            transcript_buf.append(scene.transcript)

    flush_transcript()

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
        print("Usage: research_video.py <url-or-local-path> [--title='...'] [--slug='...'] "
              "[--metric=luma|hsv|edge] [--threshold=...] [--no-merge] [--all-slides] "
              "[--bundle=Prepared|Articles] [--language=xx|auto] [--task=transcribe|translate]")
        sys.exit(1)

    url = sys.argv[1]
    # Which OKF bundle the document belongs to. Prepared is the primary-source
    # corpus (papers, conference talks); Articles is everything secondary —
    # blog posts, tutorials, community write-ups. The distinction is editorial,
    # not technical, so it is the caller's to make and there is no default worth
    # guessing: staying on Prepared preserves every existing invocation.
    global OUTPUT_DIR, PROJECT_ROOT, ASSETS_DIR
    bundle = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--bundle=")), "Prepared")
    if bundle not in ("Prepared", "Articles"):
        print(f"Unknown --bundle={bundle!r}; expected Prepared or Articles")
        sys.exit(1)
    OUTPUT_DIR = OUTPUT_DIR.parent / bundle
    PROJECT_ROOT = OUTPUT_DIR
    ASSETS_DIR = OUTPUT_DIR / "assets"
    extra_title = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--title=")), None)
    extra_slug = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--slug=")), None)
    metric_arg = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--metric=")), None)
    scene_metric = metric_arg or "luma"
    if scene_metric not in scene_metrics.METRICS:
        print(f"Unknown --metric={scene_metric!r}; expected one of "
              f"{', '.join(scene_metrics.METRICS)}")
        sys.exit(1)
    threshold_arg = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--threshold=")), None)
    scene_threshold = float(threshold_arg) if threshold_arg else None
    merge = "--no-merge" not in sys.argv[2:]
    all_slides = "--all-slides" in sys.argv[2:]
    # What is spoken, and what we want out. Forcing the default English decoder
    # onto non-English audio does not degrade gracefully — it invents fluent
    # English that was never said — so a non-English source MUST pass this.
    # task=translate is Whisper's speech-to-English mode and is the only route to
    # an English transcript when the upload carries no dubbed audio track.
    lang_arg = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--language=")), "en")
    language = None if lang_arg == "auto" else lang_arg
    task = next((a.split("=", 1)[1] for a in sys.argv[2:] if a.startswith("--task=")), "transcribe")
    if task not in ("transcribe", "translate"):
        print(f"Unknown --task={task!r}; expected transcribe or translate")
        sys.exit(1)
    # The SRT is named for the language it CONTAINS, not the one that was spoken:
    # a translate run over Russian audio writes English, and calling it .ru.srt
    # would mislabel it for every later pass and for the archive.
    srt_lang = "en" if task == "translate" else (lang_arg if lang_arg != "auto" else "auto")
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
        srt_candidate = video_path.parent / f"{video_path.stem}.{srt_lang}.srt"
        srt_path = srt_candidate if srt_candidate.exists() else work_dir / f"{slug}.{srt_lang}.srt"
        print(f"Local file: {video_path} ({format_timestamp(duration)})")
    else:
        print(f"Downloading: {url}")
        video_path, info = download_video(url, work_dir)
        if extra_title:
            info.title = extra_title
        if extra_slug:
            info.slug = extra_slug
        srt_path = work_dir / f"{info.slug}.{srt_lang}.srt"

    # Transcript source is always SOTA STT (faster-whisper), never YouTube
    # auto-captions. A pre-existing SRT next to a local video is reused as-is
    # (presumed an earlier STT run); otherwise we transcribe the audio now.
    if not srt_path.exists():
        from transcribe_to_srt import transcribe
        print("  Transcribing audio with faster-whisper (SOTA STT)...")
        transcribe(str(video_path), str(srt_path), language=language, task=task)

    print(f"Processing: {info.title} ({format_timestamp(info.duration)})")
    md_path = process_video(video_path, info, srt_path, scene_threshold=scene_threshold,
                            merge=merge, all_slides=all_slides, scene_metric=scene_metric)

    print(f"\nDone: {md_path}")


if __name__ == "__main__":
    main()
