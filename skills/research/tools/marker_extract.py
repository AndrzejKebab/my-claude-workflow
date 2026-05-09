"""Marker prepass for paper-PDFs.

Runs `marker-pdf` (datalab-to/marker) on a paper PDF and returns per-page
markdown. Replaces the old PyMuPDF span-walker for the prose body of paper-mode
PDFs — gives real markdown structure (headings, lists, tables, LaTeX equations)
instead of flat span concatenation.

Routing (decided in `extract_research.py`):
  - slide-deck PDF  → not used (full-page render path is canonical)
  - text-rich paper → THIS module
  - scanned PDF     → not used (OpenOCR fallback path is canonical)

Image handling: marker's auto image-description processor is dropped from the
pipeline because the /research vision pass already produces vision blocks with
project-specific taxonomy (`**Diagram (LLM vision pass):**`, …). Image FILES
are also not extracted to disk — the vision pass reads PyMuPDF page renders.

Caching: marker calls cost real Gemini money. The result is cached at
`<cache_dir>/marker.md` keyed by PDF mtime + use_llm flag (in cache header).
`force=True` bypasses.

API key: `GoogleGeminiService` reads `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) via
the google-genai SDK env-var fallback.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

# Default processor list = marker's defaults MINUS the auto image-description
# processor. The vision pass generates image blocks with stricter taxonomy.
_DEFAULT_PROCESSORS = (
    "marker.processors.order.OrderProcessor",
    "marker.processors.block_relabel.BlockRelabelProcessor",
    "marker.processors.line_merge.LineMergeProcessor",
    "marker.processors.blockquote.BlockquoteProcessor",
    "marker.processors.code.CodeProcessor",
    "marker.processors.document_toc.DocumentTOCProcessor",
    "marker.processors.equation.EquationProcessor",
    "marker.processors.footnote.FootnoteProcessor",
    "marker.processors.ignoretext.IgnoreTextProcessor",
    "marker.processors.line_numbers.LineNumbersProcessor",
    "marker.processors.list.ListProcessor",
    "marker.processors.page_header.PageHeaderProcessor",
    "marker.processors.sectionheader.SectionHeaderProcessor",
    "marker.processors.table.TableProcessor",
    "marker.processors.llm.llm_table.LLMTableProcessor",
    "marker.processors.llm.llm_table_merge.LLMTableMergeProcessor",
    "marker.processors.llm.llm_form.LLMFormProcessor",
    "marker.processors.text.TextProcessor",
    "marker.processors.llm.llm_complex.LLMComplexRegionProcessor",
    # "marker.processors.llm.llm_image_description.LLMImageDescriptionProcessor",
    "marker.processors.llm.llm_equation.LLMEquationProcessor",
    "marker.processors.llm.llm_handwriting.LLMHandwritingProcessor",
    "marker.processors.llm.llm_mathblock.LLMMathBlockProcessor",
    "marker.processors.llm.llm_sectionheader.LLMSectionHeaderProcessor",
    "marker.processors.llm.llm_page_correction.LLMPageCorrectionProcessor",
    "marker.processors.reference.ReferenceProcessor",
    "marker.processors.blank_page.BlankPageProcessor",
    "marker.processors.debug.DebugProcessor",
)

# Page boundary marker emitted by marker when paginate_output=True.
# Format: "{N}" on its own line, then 48 dashes on the next line, with a
# blank line surrounding the pair.
_PAGE_BOUNDARY_RE = re.compile(r"^\{(\d+)\}-{40,}\s*$", re.MULTILINE)


@dataclass
class MarkerResult:
    pages: dict[int, str]  # 0-indexed page number -> markdown body
    llm_request_count: int
    llm_token_count: int
    used_llm: bool
    used_cache: bool


def _split_paginated_markdown(text: str) -> dict[int, str]:
    """Split marker's paginate_output=True markdown into a {page_index: body} dict.

    The boundary `{N}<48-dashes>` appears at the START of each page's content
    (including page 0). Content before the first boundary is discarded as
    pre-document chrome.
    """
    matches = list(_PAGE_BOUNDARY_RE.finditer(text))
    if not matches:
        # No boundaries found — single-page or paginate_output disabled.
        return {0: text.strip()}

    pages: dict[int, str] = {}
    for i, m in enumerate(matches):
        page_idx = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        pages[page_idx] = text[start:end].strip()
    return pages


def _llm_stats(metadata: dict | None) -> tuple[int, int]:
    """Pull total LLM request and token counts from marker metadata."""
    if not metadata:
        return (0, 0)
    requests = 0
    tokens = 0
    for stat in metadata.get("page_stats", []) or []:
        if not isinstance(stat, dict):
            continue
        bm = stat.get("block_metadata") or {}
        requests += int(bm.get("llm_request_count", 0) or 0)
        tokens += int(bm.get("llm_tokens_used", 0) or 0)
    return (requests, tokens)


def _cache_paths(cache_dir: Path) -> tuple[Path, Path]:
    return (cache_dir / "marker.md", cache_dir / "marker-meta.json")


def _read_cache(cache_dir: Path, pdf_path: Path, use_llm: bool) -> MarkerResult | None:
    md_path, meta_path = _cache_paths(cache_dir)
    if not md_path.exists() or not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text())
    except json.JSONDecodeError:
        return None
    if meta.get("pdf_mtime_ns") != pdf_path.stat().st_mtime_ns:
        return None
    if meta.get("use_llm") != use_llm:
        return None
    text = md_path.read_text()
    return MarkerResult(
        pages=_split_paginated_markdown(text),
        llm_request_count=int(meta.get("llm_request_count", 0)),
        llm_token_count=int(meta.get("llm_token_count", 0)),
        used_llm=use_llm,
        used_cache=True,
    )


def _write_cache(
    cache_dir: Path,
    pdf_path: Path,
    use_llm: bool,
    markdown: str,
    llm_requests: int,
    llm_tokens: int,
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    md_path, meta_path = _cache_paths(cache_dir)
    md_path.write_text(markdown)
    meta_path.write_text(
        json.dumps(
            {
                "pdf_mtime_ns": pdf_path.stat().st_mtime_ns,
                "use_llm": use_llm,
                "llm_request_count": llm_requests,
                "llm_token_count": llm_tokens,
            },
            indent=2,
        )
    )


def convert_pdf(
    pdf_path: str | os.PathLike,
    *,
    cache_dir: str | os.PathLike,
    use_llm: bool = True,
    force: bool = False,
) -> MarkerResult:
    """Run marker on a paper PDF and return per-page markdown.

    `cache_dir` is the per-document assets directory (e.g.
    `docs/research/assets/<slug>/`). The marker output is stored at
    `<cache_dir>/marker.md` + `<cache_dir>/marker-meta.json` and reused
    on subsequent runs unless the PDF's mtime changed or the use_llm
    flag flipped or `force=True`.

    `use_llm=True` requires a Gemini API key in the environment as
    `GOOGLE_API_KEY` (or `GEMINI_API_KEY`); the call will raise if neither
    is set. `use_llm=False` runs marker locally (surya OCR + layout) with
    no network calls — quality is still better than PyMuPDF span-walking
    on most modern PDFs.
    """
    pdf_path = Path(pdf_path)
    cache_dir = Path(cache_dir)

    if not force:
        cached = _read_cache(cache_dir, pdf_path, use_llm)
        if cached is not None:
            return cached

    if use_llm and not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
        raise RuntimeError(
            "marker --use_llm requires GOOGLE_API_KEY (or GEMINI_API_KEY) in the "
            "environment. Set it in the project .envrc or pass use_llm=False."
        )

    # Imports deferred — marker pulls torch + surya weights on import, which is
    # a multi-second cost we should not pay when the cache hits.
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser
    from marker.output import text_from_rendered

    config: dict = {
        "output_format": "markdown",
        "paginate_output": True,
        "disable_image_extraction": True,
    }
    if use_llm:
        config["use_llm"] = True
        config["llm_service"] = "marker.services.gemini.GoogleGeminiService"

    parser = ConfigParser(config)
    converter_kwargs: dict = {
        "config": parser.generate_config_dict(),
        "artifact_dict": create_model_dict(),
        "processor_list": list(_DEFAULT_PROCESSORS),
        "renderer": parser.get_renderer(),
    }
    if use_llm:
        converter_kwargs["llm_service"] = parser.get_llm_service()

    converter = PdfConverter(**converter_kwargs)
    rendered = converter(str(pdf_path))
    text, _, _ = text_from_rendered(rendered)
    requests, tokens = _llm_stats(rendered.metadata)

    _write_cache(cache_dir, pdf_path, use_llm, text, requests, tokens)

    return MarkerResult(
        pages=_split_paginated_markdown(text),
        llm_request_count=requests,
        llm_token_count=tokens,
        used_llm=use_llm,
        used_cache=False,
    )


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)


def first_heading(markdown: str) -> str | None:
    """Return the first markdown heading text in `markdown`, or None.

    Used by extract_research.py to populate `PageData.heading` from
    marker's structured output instead of the old font-size>14 heuristic.
    """
    m = _HEADING_RE.search(markdown)
    return m.group(2).strip() if m else None
