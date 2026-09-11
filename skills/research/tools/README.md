# Research skill — Python pipeline

Canonical Python scripts for the `/research` skill. Self-contained: ships its own `pyproject.toml` and uv-managed environment under the installed skill directory.

## Scripts

| Script | Purpose |
|---|---|
| `extract_research.py` | One PDF/PPTX → text + images. Invoked `extract_research.py <source-path> [--slug SLUG] [--title TITLE] [--slide-deck\|--no-slide-deck] [--force] [--no-marker] [--no-llm]` — the source path is the argument, no hardcoded source list. Auto-detects slide-deck vs paper; PPTX rendered via LibreOffice UNO per-slide PNG. **OCR fallback** built in: when a page has no native text layer (scanned PDFs, image-only slide exports), the page's image asset is OCR'd via `openocr_engine` and the result becomes the page body. |
| `extract_research_phase2.py` | Extract videos embedded in one PPTX deck and transcribe them with faster-whisper. Invoked `extract_research_phase2.py <source-path> [--slug SLUG]`; a non-PPTX path is a no-op. (No per-image OCR — that was removed; the vision pass owns image description, and body-text OCR fallback moved into phase 1.) |
| `openocr_engine.py` | Singleton wrapper around `openocr-python` (mobile/ONNX). Shared by phase 1 (body-text fallback) and `research_video.py` (per-frame OCR for recorded talks). |
| `cleanup_research.py` | Strip footer/watermark lines, remove duplicate slide-title duplicates, scrub garbage OCR. |
| `research_video.py` | YouTube / local video → scene detection + OCR + transcript alignment. |
| `redetect_scenes.py` | Aggressive scene re-detection for slide-heavy talks (low Bhattacharyya threshold). |
| `subsample_long_scenes.py` | Add intra-scene frames inside long held shots. |
| `srt_to_windows.py` | Group SRT into per-slide transcript windows from a `slide_starts.txt`. |
| `transcribe_to_srt.py` | faster-whisper SRT generation for non-YouTube videos. |
| `upgrade_to_slide_renders.py` | Migrate an already-extracted slide-deck research entry from per-figure cutouts to per-page rendered slide images. |
| `validate_research.py` | **Pass 2.5 validator.** Extracts every LaTeX (`$…$`, `$$…$$`) and Mermaid block from `$RESEARCH_ROOT/Prepared/<slug>.md` and dispatches them to `validate_md.mjs`. Writes `assets/<slug>/findings-pass2.5-validate.md`; exits 1 on any parse error. `--html` adds a self-contained preview. See SKILL.md "Pass 2.5: Validate" for the full contract. |
| `update_topics.py` | **Pass 3.6 topic maintainer.** Regenerates the OKF `<bundle>/topics/<tag>.md` index pages from document frontmatter `tags`. `--only=<slug>` rebuilds the slug's bundle, `--bundle=<Prepared\|Articles>` one bundle, `--all` (default) both; `--check` dry-runs, `--prune` removes pages whose tag dropped below two members. Idempotent; owns only the member table (between `<!-- members:start -->` / `<!-- members:end -->`) and `topics/index.md`, preserving each page's intro. Per-bundle `flock` + atomic `os.replace` make concurrent invocations safe. |
| `validate_md.mjs` | Node helper for `validate_research.py`. Validates LaTeX via `katex.renderToString({throwOnError:true})` and Mermaid via `mermaid.parse()` (jsdom-backed). |
| `render_md_html.mjs` | Node helper for `validate_research.py --html`. markdown-it + KaTeX server-side + mermaid client-side via CDN → self-contained HTML preview. |

## Per-doc helpers

Per-document one-off helpers (e.g. `split_<slug>_notes.py` for a specific deck's PowerPoint Notes-Pages text-layer split) live in the **project's** `tools/` directory, NOT here. The skill ships only the generic, reusable pipeline.

## Setup

The skill is a uv project. Resolve `<research-skill-dir>` from the active Claude or Codex installation.

```bash
cd "<research-skill-dir>"
uv sync                              # Python: creates .venv (~30 s cold)
npm install --no-audit --no-fund     # Node: installs Pass 2.5 validators (~10 s cold)
```

On Windows, install LibreOffice, yt-dlp, and ffmpeg with your package manager and verify they are on `PATH`. Linux and macOS examples:

```bash
# Arch
sudo pacman -S libreoffice-fresh yt-dlp ffmpeg

# Debian / Ubuntu
sudo apt install libreoffice yt-dlp ffmpeg

# macOS
brew install --cask libreoffice
brew install yt-dlp ffmpeg
```

LibreOffice is needed for PPTX → PNG rendering (see SKILL.md "PPTX rendering dependency"). yt-dlp + ffmpeg are needed for the video pipeline. OCR is provided by [OpenOCR](https://github.com/Topdu/OpenOCR) (`openocr-python`, pinned in `pyproject.toml`) — no system OCR engine is needed. Detection and recognition ONNX models auto-download to the current user's cache on first use.

## Invocation

The extraction scripts take the source path as the first argument. Use `uv run` so the same command works across supported operating systems:

```bash
uv run --project "<research-skill-dir>" python "<research-skill-dir>/tools/extract_research.py" <source-path> --slug=<slug>
```

Or via `uv run` (auto-syncs if `pyproject.toml` changed):

```bash
uv run --project "<research-skill-dir>" python "<research-skill-dir>/tools/extract_research.py" <source-path> --slug=<slug>
```

The explicit-path form is faster (skips uv sync check); the `uv run` form is safer if you suspect dependencies drifted.

## Why a skill-local venv

Projects vary wildly in their Python requirements — some have no venv, some have version-conflicting installs (numpy pinned for ML, opencv with GUI flavour, torch versions, …). The research pipeline pins specific versions of PyMuPDF, opencv-python-headless, faster-whisper that should not be subject to "whatever the project happens to have". Decoupling means /research is reliable across every project that invokes it.

## Updating dependencies

```bash
cd "<research-skill-dir>"
# edit pyproject.toml → bump version constraints
uv sync                       # re-resolves and installs
```

`uv lock` produces a `uv.lock` file alongside `pyproject.toml` if you want fully-reproducible installs across machines. Commit the lockfile when added.

## Legacy project copies

Projects that adopted /research before the skill became self-contained may have their own copies of these scripts in `<project>/tools/*.py` running against `<project>/tools/.venv/`. Those continue to work but are **legacy**: no further updates land there. Migration: drop the per-project copies and let the agents call the skill's canonical versions.
