#!/usr/bin/env python3
"""Extract text and images from one PDF/PPTX research document into markdown.

Invoked per-document with the source path as the first argument:

    extract_research.py <path-to.pdf|.pptx> [--slug SLUG] [--title TITLE]
                        [--slide-deck|--no-slide-deck] [--force] [--no-marker] [--no-llm]

The slug and title default to the filename stem; the /research workflow always
passes an explicit citable `--slug`. `--slide-deck` / `--no-slide-deck` force
the render mode that `is_slide_deck_pdf` would otherwise auto-detect.
"""

import datetime
import hashlib
import io
import os
import re
import secrets
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# Heavy extraction deps (PyMuPDF / Pillow / python-pptx / OpenOCR / marker).
# These live in the extraction venv. The PPTX render worker
# (`--render-pptx-worker`, see _render_pptx_slides_uno) instead runs under a
# uno-capable system interpreter that does NOT have these — it only needs the
# UNO bridge + the three render helpers below. So the heavy imports are guarded:
# when they are missing the module still imports far enough to run the render
# worker, and any other code path that actually touches them raises a clear
# error. Under the normal extraction interpreter all of these import fine and
# nothing changes.
_IMPORT_ERROR: Exception | None = None
try:
    import fitz  # PyMuPDF
    from PIL import Image
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    from openocr_engine import ocr_image as _ocr_image_path
    import marker_extract
except ImportError as _exc:  # pragma: no cover — only on the bare render-worker
    _IMPORT_ERROR = _exc

# Marker prepass routing (decided in main()).
# Paper-PDFs that classify as text-rich go through marker for body text +
# real markdown structure (headings, lists, tables, LaTeX equations) instead
# of PyMuPDF's flat span-walker. Slide-deck PDFs and scanned PDFs are
# unchanged.
_MARKER_ENABLED = True  # --no-marker turns this off
_MARKER_USE_LLM = True  # --no-llm runs marker locally without Gemini
_MARKER_FORCE = False  # set when --force is passed; busts marker cache


def _ocr_image_bytes(png_bytes: bytes) -> str:
    """OCR a PNG byte buffer via the OpenOCR singleton."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(png_bytes)
        tmp.flush()
        path = tmp.name
    try:
        return _ocr_image_path(path)
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass

# The extracted markdown corpus lives at a single hardcoded global location,
# independent of cwd / which project invoked /research. The skill scripts ship
# at ~/.claude/skills/research/tools/ but always write the corpus to
# /mnt/archive4/PAPERS/Prepared/.
OUTPUT_DIR = Path("/mnt/archive4/PAPERS/Prepared")
PROJECT_ROOT = OUTPUT_DIR  # display base for relative_to() in log output
ASSETS_DIR = OUTPUT_DIR / "assets"


@dataclass
class ImageData:
    data: bytes
    ext: str


@dataclass
class PageData:
    number: int
    heading: str | None = None
    text: str = ""
    images: list[ImageData] = field(default_factory=list)
    slide_image: ImageData | None = None  # full-page render for slide-deck PDFs / PPTX
    is_figure_bearing: bool = True  # paper-mode only: False for pure-prose pages.
    # When False, the page is still rendered + embedded for reference (math
    # equations, citation context, etc.) but is OUT OF SCOPE for the vision
    # pass. Filename suffix becomes `-text` instead of `-page`, which is the
    # signal the vision agent uses to skip.
    notes: str | None = None
    video_markers: list[str] = field(default_factory=list)


@dataclass
class Document:
    slug: str
    title: str
    source_path: str
    doc_type: str  # "pdf" / "pptx" / "slides-pdf" / "slides-pptx"
    page_count: int
    file_size_mb: float
    pages: list[PageData] = field(default_factory=list)
    is_slide_deck: bool = False  # one rendered image per page, no per-figure cutouts


SLIDE_DECK_KEYWORDS = (
    "powerpoint",
    "keynote",
    "google slides",
    "googleslides",
    "beamer",
    "pptx",
    "presentation",
    "impress",
)


def is_slide_deck_pdf(doc: fitz.Document) -> bool:
    """Heuristic: does this PDF look like a slide-deck export?

    A slide deck wants per-page rendering for vision pass — embedded image
    extraction would cut individual visual elements (chart chrome + plot,
    photo + frame, etc.) into useless pieces. Triggers if:
      - creator/producer/title metadata mentions PowerPoint / Keynote /
        Google Slides / Beamer / Impress, OR
      - all pages are landscape AND aspect ratio is one of the standard
        slide ratios (4:3 ≈ 1.33, 16:10 ≈ 1.6, 16:9 ≈ 1.78) AND there are
        at least 3 pages (single landscape pages can be posters / figures).
    """
    meta = doc.metadata or {}
    haystack = " ".join(
        (meta.get(k) or "").lower() for k in ("creator", "producer", "title", "subject")
    )
    if any(kw in haystack for kw in SLIDE_DECK_KEYWORDS):
        return True

    page_count = len(doc)
    if page_count < 3:
        return False

    landscape = 0
    slide_ratio = 0
    for i in range(page_count):
        rect = doc[i].rect  # respects rotation
        w, h = rect.width, rect.height
        if w <= 0 or h <= 0:
            continue
        if w > h:
            landscape += 1
        ratio = max(w, h) / min(w, h)
        # 4:3 = 1.333, 16:10 = 1.6, 16:9 = 1.778 — accept anywhere in 1.25..1.85
        if 1.25 <= ratio <= 1.85:
            slide_ratio += 1

    return landscape == page_count and slide_ratio == page_count


def _page_has_figure(page: fitz.Page, drawings_threshold: int = 12) -> bool:
    """Triage: does this paper-mode page carry a figure worth rendering?

    Vision pass is expensive — a 200-page thesis with figures only on 60% of
    pages should not produce 200 page renders. We render only pages that
    plausibly carry a figure / diagram / plot / table. The heuristic accepts:

      - Any embedded raster image (`page.get_images(full=True)` non-empty).
        Even one embedded image means the page has a real figure worth a
        vision pass.
      - "Many" vector drawings (`len(page.get_drawings()) >= drawings_threshold`).
        Vector flowcharts / cone diagrams / cache-architecture diagrams appear
        as dozens of stroke / fill operations rather than embedded rasters,
        and the threshold is set above what running text + page chrome /
        underline marks typically produce.

    The heuristic intentionally errs on the side of including pages: a small
    over-render is cheap, missing a figure costs a vision-pass blind spot.
    """
    if page.get_images(full=True):
        return True
    try:
        drawings = page.get_drawings()
    except Exception:
        drawings = []
    return len(drawings) >= drawings_threshold


def _classify_paper_pdf(doc: fitz.Document, sample: int = 10, min_chars: int = 50) -> str:
    """Decide whether a non-slide-deck PDF is text-rich or scanned.

    Marker (and PyMuPDF span-walking) both rely on a usable text layer.
    Scanned papers without OCR text layers must keep the existing OCR
    fallback path. Sample up to `sample` pages and count those with at
    least `min_chars` of native text. Majority decides.
    """
    n = min(sample, len(doc))
    if n == 0:
        return "scanned"
    rich = 0
    for i in range(n):
        if len(doc[i].get_text("text").strip()) >= min_chars:
            rich += 1
    return "text-paper" if rich * 2 >= n else "scanned"


def extract_pdf(source: dict, scale: float = 2.0, paper_scale: float = 2.5) -> Document:
    """Extract PDF.

    BOTH slide-deck and paper PDFs render full pages for the vision pass.
    Paper PDFs render only figure-bearing pages (per `_page_has_figure`)
    so a 200-page paper does not produce 200 PNGs; pages of pure body text
    are skipped because their text-layer extraction is already canonical
    and a vision pass on running prose adds no value.

    Asset filename pattern:
      - Slide-deck PDFs (and PPTX):  `sNNN-slide.png`  (one per page)
      - Paper PDFs:                  `pNNN-page.png`   (one per figure-bearing page)

    Embedded-image cutout extraction (`pNNN-figXX.png`) is intentionally
    REMOVED. PDF figures are typically PostScript / vector composites — a
    single authored figure (e.g. cone-tracing diagram, octree pyramid,
    cache architecture) decomposes into 5-40 separate xref entries, and
    each cutout is a meaningless fragment. The vision agent describing
    those fragments must lean on text-layer prose anchoring rather than
    on the visual itself, which defeats the point of a vision pass. Render
    the page as the reader saw it; the figure boundary is preserved.

    `paper_scale` defaults higher than `scale` because papers tend to pack
    smaller-detail figures (sub-panel labels, axis tick marks, equation
    glyphs) into the page than slide decks do, and the vision agent needs
    the extra resolution to read them.
    """
    path = source["path"]
    file_size = os.path.getsize(path) / (1024 * 1024)
    doc = fitz.open(path)

    forced = source.get("slide_deck")
    slide_deck = forced if forced is not None else is_slide_deck_pdf(doc)

    # Classify a non-slide-deck PDF once: text-rich (marker route) vs image-only
    # scan. Slide-decks skip classification — they always use the render path.
    classification = (
        _classify_paper_pdf(doc)
        if (source.get("type") == "pdf" and not slide_deck)
        else None
    )

    # Two paper routes only (user, 2026-05-30):
    #   - text-rich paper  → marker on GPU + Anthropic Sonnet (preserves structure)
    #   - image-only scan  → sonnet-vision pass on page renders, handled OUT OF BAND
    # marker is never used to OCR a scan: its OCR tools don't capture figure /
    # layout context. A scanned source therefore RAISES here rather than silently
    # taking the OpenOCR/PyMuPDF body path — extract it with the vision pass
    # instead. (Slide-decks use the render path above; --no-marker is the opt-out.)
    if _MARKER_ENABLED and not slide_deck and classification == "scanned":
        raise RuntimeError(
            f"{source['slug']!r}: image-only scan (no text layer). marker does not "
            f"OCR scans (its OCR loses figure/layout context); extract this source "
            f"with the sonnet-vision pass instead, or pass --no-marker for a CPU path."
        )

    use_marker = _MARKER_ENABLED and not slide_deck and classification == "text-paper"
    marker_pages: dict[int, str] = {}
    if use_marker:
        cache_dir = ASSETS_DIR / source["slug"]
        try:
            result = marker_extract.convert_pdf(
                path,
                cache_dir=cache_dir,
                use_llm=_MARKER_USE_LLM,
                force=_MARKER_FORCE,
            )
            marker_pages = result.pages
            cache_note = " [cached]" if result.used_cache else ""
            model_note = (
                f" [{result.llm_provider}/{result.llm_model}"
                + (" +redo_inline_math" if result.redo_inline_math else "")
                + "]"
                if result.used_llm and not result.used_cache
                else ""
            )
            llm_note = (
                f" [llm: {result.llm_request_count} req / {result.llm_token_count} tok]"
                if result.used_llm and not result.used_cache
                else ""
            )
            print(f"  marker: {len(marker_pages)} pages{cache_note}{model_note}{llm_note}")
        except Exception as exc:
            # marker-GPU-only policy (user, 2026-05-30): marker on GPU + Anthropic
            # Sonnet is the only acceptable extraction path. A silent fall-through
            # to the PyMuPDF span-walker reads as "marker worked but produced poor
            # output", so a marker failure is a hard error. Fix the cause (GPU
            # contention, API key, model download) and re-run; pass --no-marker
            # only if a CPU/span-walker path is genuinely wanted.
            import traceback

            traceback.print_exc()
            raise RuntimeError(
                f"marker extraction failed for {source['slug']!r}: {exc!r}. "
                f"marker-GPU-only mode forbids the PyMuPDF span-walker fallback."
            ) from exc

    document = Document(
        slug=source["slug"],
        title=source["title"],
        source_path=path,
        doc_type="slides-pdf" if slide_deck else "pdf",
        page_count=len(doc),
        file_size_mb=round(file_size, 1),
        is_slide_deck=slide_deck,
    )

    for page_idx in range(len(doc)):
        page = doc[page_idx]
        page_data = PageData(number=page_idx + 1)

        if use_marker:
            # Marker path: per-page markdown body straight from the prepass.
            # First markdown heading on the page is the section anchor
            # (replaces the old font-size>14 heuristic, which produces noise
            # on PDFs whose body font happens to be ~15pt).
            md_body = marker_pages.get(page_idx, "")
            page_data.text = md_body
            page_data.heading = marker_extract.first_heading(md_body)
        else:
            # Legacy path: PyMuPDF text-dict span walker. Used for slide-decks
            # (text layer is auxiliary), scanned paper PDFs (handled together
            # with the OCR fallback below), and when --no-marker is passed.
            text_dict = page.get_text("dict")
            all_text_parts = []
            heading_candidate = None

            for block in text_dict.get("blocks", []):
                if block["type"] != 0:  # text block
                    continue
                for line in block.get("lines", []):
                    line_text = ""
                    max_font_size = 0
                    for span in line.get("spans", []):
                        line_text += span["text"]
                        max_font_size = max(max_font_size, span["size"])
                    line_text = line_text.strip()
                    if not line_text:
                        continue
                    all_text_parts.append(line_text)
                    if heading_candidate is None and max_font_size > 14:
                        heading_candidate = line_text

            page_data.text = "\n".join(all_text_parts)
            page_data.heading = heading_candidate

        if slide_deck:
            # Slide-deck mode: render every page once.
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
            page_data.slide_image = ImageData(data=pix.tobytes("png"), ext="png")
        else:
            # Paper mode: render EVERY page so the markdown carries a visual
            # reference for every body-text page (math-dense prose, citation
            # context, etc.). The figure-bearing/text split is preserved as a
            # `is_figure_bearing` flag — the markdown emitter chooses the file
            # suffix from it (`-page` for figure-bearing, `-text` for prose),
            # and the vision agent uses the suffix to scope its work to real
            # diagrams. Skipping the render entirely for prose pages was the
            # old behaviour — it left math-bearing prose pages unverifiable
            # against marker's LLM cleanup output (which routinely produces
            # KaTeX-incompatible LaTeX). Visual reference is cheap; missing it
            # costs the ability to spot-check marker fidelity.
            page_data.is_figure_bearing = _page_has_figure(page)
            pix = page.get_pixmap(matrix=fitz.Matrix(paper_scale, paper_scale))
            png_bytes = pix.tobytes("png")
            page_rot = page.rotation  # 0 / 90 / 180 / 270
            if page_rot:
                # PIL.rotate is counter-clockwise; PDF rotation is clockwise.
                img = Image.open(io.BytesIO(png_bytes))
                img = img.rotate(-page_rot, expand=True)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                png_bytes = buf.getvalue()
            page_data.slide_image = ImageData(data=png_bytes, ext="png")

        # Body-text OCR fallback: when the page has no native text layer
        # (typical of scanned PDFs and image-only slides exported as
        # raster), OCR the page's own image asset and use the result as
        # the page body. Skipped on the marker path — marker has already
        # decided what text the page carries, and an empty marker page is
        # a deliberate "figure-only with captions, vision pass takes it
        # from here" signal, not a missing text layer. This is the ONLY
        # path on which OCR enters the canonical document body — image
        # inclusions inside a text-rich doc are NEVER OCR'd here. The
        # vision pass reads images directly with full visual context and
        # outclasses any CPU OCR engine; OCR
        # scaffolding alongside an image only narrows what the vision
        # agent looks at and primes it with mistakes.
        if not use_marker and len(page_data.text.strip()) < 20:
            target_bytes = None
            if page_data.slide_image is not None:
                target_bytes = page_data.slide_image.data
            elif page_data.images:
                # Largest embedded image is the full-page scan in scanned
                # PDFs and the only-image-on-page in image-only slide
                # exports.
                target_bytes = max((im.data for im in page_data.images), key=len)
            if target_bytes is not None:
                ocr_text = _ocr_image_bytes(target_bytes)
                if ocr_text:
                    page_data.text = ocr_text

        document.pages.append(page_data)

    doc.close()
    return document


def _find_libreoffice() -> str | None:
    """Locate a LibreOffice CLI binary. Returns None if not installed."""
    import shutil

    for name in ("soffice", "libreoffice", "lowriter"):
        which = shutil.which(name)
        if which:
            return which
    # Common Linux/Mac install locations
    for candidate in (
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/usr/lib/libreoffice/program/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ):
        if os.path.exists(candidate):
            return candidate
    return None


def _find_uno_python() -> str | None:
    """Locate a python interpreter that can `import uno`.

    The UNO Python bridge (`pyuno`) is a compiled extension tied to one CPython
    ABI — typically the system interpreter LibreOffice was built against, NOT
    the extraction venv. The extraction venv (with pptx / fitz / PIL / cv2)
    usually cannot import uno, so the per-slide render runs as a subprocess
    under whichever interpreter owns the bridge. Returns the interpreter path,
    or None if none can import uno.
    """
    import shutil
    import subprocess

    candidates = []
    # Prefer a LibreOffice-bundled python if one exists (guaranteed ABI match).
    for c in (
        "/usr/lib/libreoffice/program/python",
        "/opt/libreoffice/program/python",
        "/Applications/LibreOffice.app/Contents/Resources/python",
    ):
        if os.path.exists(c):
            candidates.append(c)
    # Then the system interpreters on PATH.
    for name in ("python3", "python"):
        which = shutil.which(name)
        if which:
            candidates.append(which)
    candidates.append("/usr/bin/python3")

    seen = set()
    for py in candidates:
        rp = os.path.realpath(py)
        if rp in seen:
            continue
        seen.add(rp)
        try:
            r = subprocess.run(
                [py, "-c", "import uno"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
            if r.returncode == 0:
                return py
        except Exception:  # noqa: BLE001
            continue
    return None


# Pixel size from a 1/100-mm slide dimension at the given render scale.
# 1/100 mm → pt: (mm/100) * (72/25.4). At scale 2.0 a 960×540 pt 16:9 slide
# → 1920×1080, matching the old fitz.Matrix(scale, scale) render; non-16:9
# decks keep their own aspect rather than being forced to 16:9.
def _hmm_to_px(hundredth_mm: float, scale: float) -> int:
    return max(1, round(hundredth_mm / 100.0 / 25.4 * 72.0 * scale))


def _render_pptx_slides_uno_inproc(pptx_path: str, out_dir: str, scale: float) -> int:
    """The actual UNO per-slide render. MUST run under a uno-capable interpreter.

    Starts a private headless soffice listener, connects over the UNO socket,
    iterates `DrawPages`, and exports each page through `impress_png_Export` to
    `out_dir/sNNN-slide.png`. The PNG index equals the slide index BY
    CONSTRUCTION (each page is addressed by its own draw-page index), so the
    cumulative-offset failure of the old PPTX → PDF → PyMuPDF path — where a
    dropped video slide or a crashed PDF write shifted every later render — is
    structurally impossible here. Returns the number of pages rendered.

    Drives one soffice instance for the whole document and shuts it down in a
    finally block. The listener uses an isolated UserInstallation profile and a
    private socket so it never collides with or locks a GUI LibreOffice the user
    may have open.
    """
    import subprocess
    import time

    import uno
    from com.sun.star.beans import PropertyValue

    soffice = _find_libreoffice()
    if not soffice:
        raise RuntimeError("LibreOffice (soffice) not found — see _find_libreoffice.")

    def pv(name, value):
        p = PropertyValue()
        p.Name = name
        p.Value = value
        return p

    profile_dir = os.path.join(out_dir, "_louno_profile")
    os.makedirs(profile_dir, exist_ok=True)
    port = "2002"
    accept = f"socket,host=localhost,port={port};urp;StarOffice.ServiceManager"
    proc = subprocess.Popen(
        [
            soffice,
            "--headless",
            "--invisible",
            "--norestore",
            "--nologo",
            "--nofirststartwizard",
            f"-env:UserInstallation=file://{profile_dir}",
            f"--accept={accept}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    doc = None
    desktop = None
    try:
        local_ctx = uno.getComponentContext()
        resolver = local_ctx.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local_ctx
        )
        connect_url = (
            f"uno:socket,host=localhost,port={port};urp;StarOffice.ComponentContext"
        )
        ctx = None
        last_exc = None
        for _ in range(60):  # up to ~60s for the listener to come up
            if proc.poll() is not None:
                raise RuntimeError(
                    f"soffice listener exited (code {proc.returncode}) before the "
                    f"UNO bridge accepted a connection."
                )
            try:
                ctx = resolver.resolve(connect_url)
                break
            except Exception as exc:  # noqa: BLE001  (NoConnectException etc.)
                last_exc = exc
                time.sleep(1)
        if ctx is None:
            raise RuntimeError(
                f"could not connect to the soffice UNO bridge on port {port}: "
                f"{last_exc!r}"
            )

        smgr = ctx.ServiceManager
        desktop = smgr.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)

        url = uno.systemPathToFileUrl(os.path.abspath(pptx_path))
        load_props = (pv("Hidden", True), pv("ReadOnly", True))
        doc = desktop.loadComponentFromURL(url, "_blank", 0, load_props)
        if doc is None or not hasattr(doc, "DrawPages"):
            raise RuntimeError(
                f"LibreOffice loaded {pptx_path!r} but it is not a draw/impress "
                f"document (no DrawPages). Check that the file is a valid PPTX."
            )

        pages = doc.DrawPages
        n = pages.Count

        # Per-slide pixel size from the deck's own geometry. A draw page exposes
        # Width / Height in 1/100 mm (verified: a 960×540 pt slide reports
        # 33867 × 19050). Fall back to a 16:9 960×540 pt slide if unreadable.
        try:
            first_page = pages.getByIndex(0)
            px_w = _hmm_to_px(first_page.Width, scale)
            px_h = _hmm_to_px(first_page.Height, scale)
        except Exception:  # noqa: BLE001
            px_w = round(960.0 * scale)
            px_h = round(540.0 * scale)

        controller = doc.getCurrentController()
        filter_data = uno.Any(
            "[]com.sun.star.beans.PropertyValue",
            (pv("PixelWidth", px_w), pv("PixelHeight", px_h)),
        )

        for i in range(n):
            page = pages.getByIndex(i)
            # Select the page so the PNG filter exports THIS page, not page 0.
            controller.setCurrentPage(page)
            out_name = f"s{i + 1:03d}-slide.png"
            out_url = uno.systemPathToFileUrl(os.path.join(out_dir, out_name))
            store_props = (
                pv("FilterName", "impress_png_Export"),
                pv("FilterData", filter_data),
            )
            doc.storeToURL(out_url, store_props)

        return n
    finally:
        # Best-effort clean shutdown: close the doc, terminate the desktop,
        # then make sure the listener process is gone.
        if doc is not None:
            try:
                doc.close(False)
            except Exception:  # noqa: BLE001
                pass
        if desktop is not None:
            try:
                desktop.terminate()
            except Exception:  # noqa: BLE001
                pass
        try:
            proc.wait(timeout=30)
        except Exception:  # noqa: BLE001
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass


def _render_pptx_slides_uno(pptx_path: str, out_dir: str, scale: float = 2.0) -> int:
    """Render every PPTX slide to `out_dir/sNNN-slide.png` (index == slide).

    Replaces the former PPTX → PDF → PyMuPDF rasterisation. That path silently
    dropped slides carrying embedded video (LibreOffice omits the page from the
    PDF) and crashed the PDF writer on some code-heavy slides; every drop
    shifted all later slides onto the wrong render. Per-slide
    `impress_png_Export` has neither failure mode — a video slide exports its
    poster frame, and there is no PDF intermediate to crash.

    The actual render needs both the UNO bridge AND, for the caller, the
    extraction deps. `pyuno` rarely imports in the extraction venv (it is built
    against the system interpreter's ABI), so when the current interpreter
    cannot `import uno` this dispatches the render to a uno-capable interpreter
    as a subprocess (re-invoking this module with `--render-pptx-worker`) and
    reads the PNGs back from `out_dir`. When the current interpreter already has
    uno, it renders in-process. Either way the output contract is identical:
    `out_dir/sNNN-slide.png` for each slide, return value = page count.

    Raises RuntimeError if LibreOffice is unavailable, no uno-capable
    interpreter exists, or the render produces no pages.
    """
    soffice = _find_libreoffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice not found on PATH. PPTX → slide-image rendering "
            "requires `soffice` / `libreoffice` (headless UNO per-slide PNG "
            "export). Install: pacman -S libreoffice-fresh (Arch) / "
            "apt install libreoffice (Debian) / "
            "brew install --cask libreoffice (macOS). "
            "See SKILL.md → 'PPTX rendering dependency' section."
        )

    # In-process when this interpreter owns the bridge.
    try:
        import uno  # noqa: F401
        return _render_pptx_slides_uno_inproc(pptx_path, out_dir, scale)
    except ImportError:
        pass

    # Otherwise dispatch to a uno-capable interpreter as a subprocess.
    import subprocess

    uno_py = _find_uno_python()
    if not uno_py:
        raise RuntimeError(
            "PPTX per-slide rendering needs an interpreter that can `import uno` "
            "(the LibreOffice UNO Python bridge), but none was found. The bridge "
            "ships with LibreOffice and is tied to the system interpreter's ABI, "
            "so the extraction venv usually cannot import it. Install the uno "
            "bindings for a system python (Arch: `libreoffice-fresh` provides "
            "`/usr/lib/python*/site-packages/uno.py`; Debian: `python3-uno`), or "
            "run extraction under an interpreter that has both uno and the "
            "extraction deps."
        )

    this_module = os.path.abspath(__file__)
    r = subprocess.run(
        [
            uno_py,
            this_module,
            "--render-pptx-worker",
            pptx_path,
            out_dir,
            str(scale),
        ],
        capture_output=True,
        text=True,
        timeout=1800,  # large decks (hundreds of slides, GB of video) are slow
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"PPTX render worker ({uno_py}) failed (exit {r.returncode}).\n"
            f"stdout: {r.stdout.strip()}\nstderr: {r.stderr.strip()}"
        )
    # The worker prints the page count on its last stdout line.
    count = 0
    for line in r.stdout.splitlines():
        line = line.strip()
        if line.startswith("RENDERED "):
            try:
                count = int(line.split()[1])
            except (IndexError, ValueError):
                pass
    if count <= 0:
        # Fall back to counting PNGs on disk if the worker's line was lost.
        count = len(
            [f for f in os.listdir(out_dir) if f.endswith("-slide.png")]
        )
    if count <= 0:
        raise RuntimeError(
            f"PPTX render worker produced no slides in {out_dir!r}."
        )
    return count


def extract_pptx(source: dict, scale: float = 2.0) -> Document:
    """Extract PPTX as a slide deck.

    PPTX is always treated as a slide deck — every slide rendered as a single
    PNG via LibreOffice UNO per-slide `impress_png_Export` (one PNG per
    `DrawPage`, index == slide). Per-shape image extraction is NEVER used: it
    cuts visual elements into useless fragments (chart chrome split from plot,
    photo split from frame, etc.) and the relative geometry is lost. Speaker
    notes and slide title are still pulled from python-pptx for text content.

    The render goes through `_render_pptx_slides_uno`, which exports each draw
    page directly. The former PPTX → PDF → PyMuPDF path was removed: LibreOffice
    silently dropped video slides from the PDF and crashed the PDF writer on
    some code-heavy slides, and every drop shifted all later slides onto the
    wrong render — a cumulative-offset bug the per-slide export cannot have
    because slide N is addressed by its own draw-page index.
    """
    path = source["path"]
    file_size = os.path.getsize(path) / (1024 * 1024)
    prs = Presentation(path)

    document = Document(
        slug=source["slug"],
        title=source["title"],
        source_path=path,
        doc_type="slides-pptx",
        page_count=len(prs.slides),
        file_size_mb=round(file_size, 1),
        is_slide_deck=True,
    )

    # Render every slide once, up front, to a throwaway temp dir. The PNG index
    # equals the slide index by construction, so we read sNNN-slide.png back per
    # slide below. (Renders go to a temp dir, NOT the assets dir, so a render
    # never silently picks up a stale image — write_markdown is the single place
    # that writes the canonical assets/<slug>/sNNN-slide.png.)
    tmp_dir = tempfile.mkdtemp(prefix="research-pptx-render-")
    n_rendered = _render_pptx_slides_uno(path, tmp_dir, scale=scale)
    if n_rendered != len(prs.slides):
        raise RuntimeError(
            f"{source['slug']!r}: UNO rendered {n_rendered} slides but python-pptx "
            f"reports {len(prs.slides)} — render/slide count mismatch, refusing to "
            f"emit misaligned assets."
        )

    for slide_idx, slide in enumerate(prs.slides):
        page_data = PageData(number=slide_idx + 1)
        text_parts = []
        title_text = None

        for shape in slide.shapes:
            if shape.has_text_frame:
                try:
                    if shape.is_placeholder and shape.placeholder_format.idx == 0:
                        title_text = shape.text_frame.text.strip()
                except (ValueError, AttributeError):
                    pass
                text = shape.text_frame.text.strip()
                if text:
                    text_parts.append(text)

            if shape.shape_type == MSO_SHAPE_TYPE.MEDIA:
                try:
                    name = shape.name or f"video_{slide_idx}"
                    page_data.video_markers.append(name)
                except Exception:
                    pass

        page_data.text = "\n".join(text_parts)
        page_data.heading = title_text

        try:
            if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                notes = slide.notes_slide.notes_text_frame.text.strip()
                if notes:
                    page_data.notes = notes
        except Exception:
            pass

        render_path = os.path.join(tmp_dir, f"s{slide_idx + 1:03d}-slide.png")
        if os.path.exists(render_path):
            with open(render_path, "rb") as fh:
                page_data.slide_image = ImageData(data=fh.read(), ext="png")

        document.pages.append(page_data)

    return document


def write_markdown(doc: Document):
    slug_assets = ASSETS_DIR / doc.slug
    slug_assets.mkdir(parents=True, exist_ok=True)

    # Page label: PPTX and slide-deck PDFs both use "Slide". Regular PDFs use "Page".
    page_label = "Slide" if doc.is_slide_deck else "Page"
    prefix = "s" if doc.is_slide_deck else "p"
    # Render-asset suffix: slide-decks render every page as a "slide";
    # paper PDFs render only figure-bearing pages as a "page".
    render_suffix = "slide" if doc.is_slide_deck else "page"
    filename = Path(doc.source_path).name

    lines = [
        "---",
        f"source: {doc.source_path}",
        f"type: {doc.doc_type}",
        f"pages: {doc.page_count}",
        f"slide_deck: {str(doc.is_slide_deck).lower()}",
        "extracted: 2026-04-16",
        f"slug: {doc.slug}",
        "---",
        "",
        f"# {doc.title}",
        "",
        f"> Source: `{filename}` ({doc.page_count} {page_label.lower()}s, {doc.file_size_mb} MB)",
        "",
    ]

    total_images = 0

    for page in doc.pages:
        heading_suffix = f" -- {page.heading}" if page.heading else ""
        lines.append(f"## {page_label} {page.number}{heading_suffix}")
        lines.append("")

        if page.text.strip():
            lines.append(page.text.strip())
            lines.append("")

        # Render the full page (slide-deck: every page; paper-mode: every page
        # too, but with a filename suffix that signals vision-pass scope). The
        # vision agent treats `-page` as in scope and `-text` as out of scope
        # (pure-prose pages, embedded only as a visual reference for math /
        # citation context). Per-figure-cutout extraction was removed because
        # PDF figures are vector composites that PyMuPDF over-segments into
        # meaningless fragments — see SKILL.md "Vision pass MUST run on
        # full-page renders" for the reasoning.
        if page.slide_image is not None:
            if doc.is_slide_deck:
                page_suffix = render_suffix  # always "slide"
            else:
                page_suffix = "page" if page.is_figure_bearing else "text"
            asset_name = f"{prefix}{page.number:03d}-{page_suffix}.{page.slide_image.ext}"
            asset_path = slug_assets / asset_name
            asset_path.write_bytes(page.slide_image.data)
            total_images += 1
            rel_path = f"assets/{doc.slug}/{asset_name}"
            if not doc.is_slide_deck and not page.is_figure_bearing:
                # Reference-only embed: tell the vision agent (and any future
                # pass) explicitly that this page is out of scope for visual
                # description. Cheaper signal than scanning the filename later.
                lines.append("<!-- vision-skip: text-only page (embedded for "
                             "reference / math equation visual) -->")
            lines.append(f"![{asset_name}]({rel_path})")
            lines.append("")

        # Speaker notes (PPTX)
        if page.notes:
            lines.append(f"> **Speaker Notes:** {page.notes}")
            lines.append("")

        # Video markers
        for vid in page.video_markers:
            lines.append(f"<!-- VIDEO: {vid} - TRANSCRIPTION-PENDING -->")
            lines.append("")

        # No OCR-PENDING marker. Phase 2 runs OpenOCR unconditionally on every
        # page render and inserts a delimited `**OCR (auto):**` block; the
        # vision-pass agent integrates it with native text + image content.

    md_path = OUTPUT_DIR / f"{doc.slug}.md"
    force = "--force" in sys.argv
    if md_path.exists() and not force:
        # Randomised suffix so concurrent agents extracting the same slug don't
        # clobber each other's regen sidecar.
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        suffix = secrets.token_hex(3)
        regen_path = OUTPUT_DIR / f"{doc.slug}.regen-{stamp}-{suffix}.md"
        regen_path.write_text("\n".join(lines), encoding="utf-8")
        print(
            f"  EXISTS, wrote regenerated draft alongside: {regen_path.relative_to(PROJECT_ROOT)} "
            f"({doc.page_count} pages, {total_images} images)"
        )
        print(f"  (pass --force to overwrite {md_path.relative_to(PROJECT_ROOT)} in place)")
    else:
        md_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  -> {md_path.relative_to(PROJECT_ROOT)} ({doc.page_count} pages, {total_images} images)")
    return total_images


def _render_pptx_worker_main(argv: list[str]) -> int:
    """Subprocess entry point: `--render-pptx-worker <pptx> <out_dir> <scale>`.

    Runs the in-process UNO render under a uno-capable interpreter and prints
    `RENDERED <n>` on success. Used by _render_pptx_slides_uno when the parent
    interpreter cannot import uno. Touches only uno + the render helpers — never
    the heavy extraction deps — so it works under the bare system python.
    """
    if len(argv) != 3:
        print("usage: --render-pptx-worker <pptx> <out_dir> <scale>", file=sys.stderr)
        return 2
    pptx_path, out_dir, scale_s = argv
    try:
        scale = float(scale_s)
    except ValueError:
        print(f"bad scale {scale_s!r}", file=sys.stderr)
        return 2
    os.makedirs(out_dir, exist_ok=True)
    n = _render_pptx_slides_uno_inproc(pptx_path, out_dir, scale)
    print(f"RENDERED {n}")
    return 0


USAGE = (
    "usage: extract_research.py <path-to.pdf|.pptx> [--slug SLUG] [--title TITLE] "
    "[--slide-deck|--no-slide-deck] [--force] [--no-marker] [--no-llm]"
)


def _slugify(text: str) -> str:
    """Scaffolding slug from a filename stem. Lowercase, hyphen-separated.

    Only a fallback for when the caller omits --slug. The /research workflow
    requires a citable canonical slug (`<author>-<year>-<topic>`) and always
    passes --slug explicitly; this just keeps the script runnable without it.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "untitled"


def _parse_cli(argv: list[str]) -> tuple[str, str | None, str | None, bool | None]:
    """Parse `<path> [--slug S] [--title T] [--slide-deck|--no-slide-deck]`.

    Returns (path, slug, title, slide_deck). slide_deck is None when neither
    --slide-deck nor --no-slide-deck is passed, which leaves slide-deck
    detection to `is_slide_deck_pdf`. The global routing flags (--force,
    --no-marker, --no-llm) are read directly from sys.argv elsewhere and
    ignored here.
    """
    path: str | None = None
    slug: str | None = None
    title: str | None = None
    slide_deck: bool | None = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--force", "--no-marker", "--no-llm"):
            pass
        elif arg == "--slide-deck":
            slide_deck = True
        elif arg == "--no-slide-deck":
            slide_deck = False
        elif arg.startswith("--slug="):
            slug = arg.split("=", 1)[1]
        elif arg == "--slug":
            i += 1
            slug = argv[i] if i < len(argv) else None
        elif arg.startswith("--title="):
            title = arg.split("=", 1)[1]
        elif arg == "--title":
            i += 1
            title = argv[i] if i < len(argv) else None
        elif arg.startswith("-"):
            raise SystemExit(f"extract_research.py: unknown flag {arg!r}\n{USAGE}")
        elif path is None:
            path = arg
        else:
            raise SystemExit(
                f"extract_research.py: unexpected extra argument {arg!r}\n{USAGE}"
            )
        i += 1
    if path is None:
        raise SystemExit(USAGE)
    return path, slug, title, slide_deck


def _build_source(
    path: str, slug: str | None, title: str | None, slide_deck: bool | None
) -> dict:
    """Build the per-document source dict the extractors consume.

    Mirrors the shape the old hardcoded SOURCES entries had: type comes from
    the extension, slug/title default to the filename stem, and slide_deck is
    only set when forced on the CLI (absent ⇒ auto-detect).
    """
    ext = Path(path).suffix.lower()
    if ext == ".pptx":
        doc_type = "pptx"
    elif ext == ".pdf":
        doc_type = "pdf"
    else:
        raise SystemExit(
            f"extract_research.py: unsupported source extension {ext!r} "
            f"(expected .pdf or .pptx): {path}"
        )
    stem = Path(path).stem
    source = {
        "path": path,
        "type": doc_type,
        "slug": slug or _slugify(stem),
        "title": title or stem,
    }
    if slide_deck is not None:
        source["slide_deck"] = slide_deck
    return source


def main():
    if _IMPORT_ERROR is not None:
        raise RuntimeError(
            "extraction dependencies failed to import (PyMuPDF / Pillow / "
            "python-pptx / OpenOCR / marker). Run under the extraction venv "
            f"that has them. Original error: {_IMPORT_ERROR!r}"
        )

    path, slug, title, slide_deck = _parse_cli(sys.argv[1:])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Marker prepass routing flags (see _MARKER_ENABLED / _MARKER_USE_LLM
    # at module top). `--no-marker` reverts text-paper PDFs to the legacy
    # PyMuPDF span-walker; `--no-llm` runs marker locally without Gemini
    # (no API key needed, lower quality on tables / equations / form fields).
    global _MARKER_ENABLED, _MARKER_USE_LLM, _MARKER_FORCE
    if "--no-marker" in sys.argv:
        _MARKER_ENABLED = False
    if "--no-llm" in sys.argv:
        _MARKER_USE_LLM = False
    if "--force" in sys.argv:
        _MARKER_FORCE = True

    source = _build_source(path, slug, title, slide_deck)
    if not os.path.exists(source["path"]):
        raise SystemExit(f"extract_research.py: source not found: {source['path']}")

    # Per-slug existence is handled inside write_markdown(): if `<slug>.md`
    # already exists and --force is not passed, it writes a `.regen` sidecar
    # instead of overwriting the (possibly heavily-refined) live extraction.
    print(f"Extracting: {source['title']}...")
    if source["type"] == "pdf":
        doc = extract_pdf(source)
    else:
        doc = extract_pptx(source)

    write_markdown(doc)

    print("Done.")


if __name__ == "__main__":
    # The PPTX render worker runs under a bare uno-capable interpreter that
    # lacks the heavy extraction deps, so intercept it BEFORE main() (which
    # requires them).
    if len(sys.argv) >= 2 and sys.argv[1] == "--render-pptx-worker":
        sys.exit(_render_pptx_worker_main(sys.argv[2:]))
    main()
