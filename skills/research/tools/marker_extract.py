"""Marker prepass for paper-PDFs.

Runs `marker-pdf` (datalab-to/marker) on a paper PDF and returns per-page
markdown. Replaces the old PyMuPDF span-walker for the prose body of paper-mode
PDFs — gives real markdown structure (headings, lists, tables, LaTeX equations)
instead of flat span concatenation.

Routing (decided in `extract_research.py`):
  - slide-deck PDF  → not used (full-page render path is canonical)
  - text-rich paper → THIS module
  - scanned PDF     → raises (marker-GPU-only policy; no OpenOCR fallback)

GPU is hard-required: `_require_marker_gpu()` raises if CUDA is unavailable or
free VRAM is below threshold, instead of silently forcing CPU inference. A
marker failure in `extract_research.py` likewise raises rather than falling
through to the PyMuPDF span-walker (user policy, 2026-05-30): marker on GPU +
Anthropic Sonnet is the only acceptable extraction path, so any degradation is
a loud error, not a silent quality regression.

Image handling: marker's auto image-description processor is dropped from the
pipeline because the /research vision pass already produces vision blocks with
project-specific taxonomy (`**Diagram (LLM vision pass):**`, …). Image FILES
are also not extracted to disk — the vision pass reads PyMuPDF page renders.

LLM backend: `marker.services.claude.ClaudeService` with model
`claude-sonnet-4-6`. We migrated off `gemini-2.0-flash` after observing
recurring KaTeX-incompatible LaTeX output from Flash (misplaced `&` inside
`\\begin{split}`, undefined macros like `\\ddy`, dropped exponents on
`(1 + cos²a)`). Sonnet 4.6 is strong on structured visual reasoning and math
transcription at meaningfully higher accuracy than Flash, while running
~5× cheaper per token than Opus 4.7. Marker invokes the LLM many times per
document (one per equation / table merge / complex region / page correction),
so cost-per-call matters; Sonnet 4.6 is the cost-quality sweet spot. Override
with `claude_model_name=` if you need Opus on a math-heavy primary source.

`redo_inline_math` is enabled by default. Marker's docs:
"If you want the absolute highest quality inline math conversion, use this
along with --use_llm." Inline math is exactly the surface where Flash failed
(misplaced `&`, undefined macros), so this is the correct default for our
workload — the cost is one extra LLM call per inline-math block, which on a
typical paper is small and the quality improvement is large.

API key: prefers `CLAUDE_API_KEY` (project convention, in `.envrc`), falls
back to `ANTHROPIC_API_KEY` (Anthropic SDK default). Errors clearly if neither
is set.

Caching: marker calls cost real Anthropic money. The result is cached at
`<cache_dir>/marker.md` keyed by PDF mtime + use_llm + provider + model + the
redo_inline_math flag (all in `marker-meta.json`). Any change invalidates the
cache. `force=True` bypasses.
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


DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-6"
DEFAULT_LLM_PROVIDER = "claude"  # "claude" | "gemini"
DEFAULT_REDO_INLINE_MATH = True


@dataclass
class MarkerResult:
    pages: dict[int, str]  # 0-indexed page number -> markdown body
    llm_request_count: int
    llm_token_count: int
    used_llm: bool
    used_cache: bool
    llm_provider: str | None = None
    llm_model: str | None = None
    redo_inline_math: bool = False


def _resolve_claude_api_key() -> str | None:
    """Read CLAUDE_API_KEY first (project convention), then ANTHROPIC_API_KEY."""
    return os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")


def _split_paginated_markdown(text: str) -> dict[int, str]:
    """Split marker's paginate_output=True markdown into a {page_index: body} dict.

    The boundary `{N}<48-dashes>` appears at the START of each page's content.
    marker's pagination is NOT one-boundary-per-page: it can emit the SAME page
    index more than once (one PDF page rendered as several layout blocks, each
    prefixed with the same `{N}` separator). An earlier version keyed the dict by
    page index and so the last `{N}` segment overwrote the earlier ones, silently
    dropping body text — exactly the kind of invisible truncation this corpus must
    not have. So segments sharing a page index are CONCATENATED in document order,
    and any content before the first boundary is preserved (folded into page 0)
    rather than discarded.
    """
    matches = list(_PAGE_BOUNDARY_RE.finditer(text))
    if not matches:
        # No boundaries found — single-page or paginate_output disabled.
        return {0: text.strip()}

    preamble = text[: matches[0].start()].strip()
    segments: dict[int, list[str]] = {}
    for i, m in enumerate(matches):
        page_idx = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        seg = text[start:end].strip()
        if seg:
            segments.setdefault(page_idx, []).append(seg)

    pages = {idx: "\n\n".join(segs) for idx, segs in segments.items()}
    if preamble:
        pages[0] = (preamble + "\n\n" + pages.get(0, "")).strip()
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


def _read_cache(
    cache_dir: Path,
    pdf_path: Path,
    use_llm: bool,
    llm_provider: str | None,
    llm_model: str | None,
    redo_inline_math: bool,
) -> MarkerResult | None:
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
    # When the LLM was used, the provider, model and redo_inline_math flag
    # all change the output. Any drift invalidates the cache so we don't
    # silently serve Flash-corrupted output after migrating to Claude.
    if use_llm:
        if meta.get("llm_provider") != llm_provider:
            return None
        if meta.get("llm_model") != llm_model:
            return None
        if bool(meta.get("redo_inline_math", False)) != redo_inline_math:
            return None
    text = md_path.read_text()
    return MarkerResult(
        pages=_split_paginated_markdown(text),
        llm_request_count=int(meta.get("llm_request_count", 0)),
        llm_token_count=int(meta.get("llm_token_count", 0)),
        used_llm=use_llm,
        used_cache=True,
        llm_provider=meta.get("llm_provider"),
        llm_model=meta.get("llm_model"),
        redo_inline_math=bool(meta.get("redo_inline_math", False)),
    )


def _write_cache(
    cache_dir: Path,
    pdf_path: Path,
    use_llm: bool,
    markdown: str,
    llm_requests: int,
    llm_tokens: int,
    llm_provider: str | None,
    llm_model: str | None,
    redo_inline_math: bool,
) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    md_path, meta_path = _cache_paths(cache_dir)
    md_path.write_text(markdown)
    meta_path.write_text(
        json.dumps(
            {
                "pdf_mtime_ns": pdf_path.stat().st_mtime_ns,
                "use_llm": use_llm,
                "llm_provider": llm_provider if use_llm else None,
                "llm_model": llm_model if use_llm else None,
                "redo_inline_math": redo_inline_math if use_llm else False,
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
    llm_provider: str = DEFAULT_LLM_PROVIDER,
    claude_model_name: str = DEFAULT_CLAUDE_MODEL,
    redo_inline_math: bool = DEFAULT_REDO_INLINE_MATH,
) -> MarkerResult:
    """Run marker on a paper PDF and return per-page markdown.

    `cache_dir` is the per-document assets directory (e.g.
    `<RESEARCH_ROOT>/Prepared/assets/<slug>/`). The marker output is stored at
    `<cache_dir>/marker.md` + `<cache_dir>/marker-meta.json` and reused on
    subsequent runs unless the PDF's mtime changed, the use_llm flag flipped,
    the LLM provider/model changed, the redo_inline_math flag flipped, or
    `force=True`.

    `use_llm=True` defaults to Anthropic Claude (`claude-sonnet-4-6`). The API
    key is read from `CLAUDE_API_KEY` (project convention) or
    `ANTHROPIC_API_KEY` (Anthropic SDK default). `use_llm=False` runs marker
    locally (surya OCR + layout) with no network calls — quality is still
    better than PyMuPDF span-walking on most modern PDFs but loses table
    merge / equation / form / section-header repair.

    `llm_provider="gemini"` falls back to the legacy `GoogleGeminiService`
    backend (model controlled by marker's own `gemini_model_name` field, key
    from `GOOGLE_API_KEY`/`GEMINI_API_KEY`). Use this only for compatibility
    with older cached outputs — Flash is a known source of broken LaTeX
    (misplaced `&`, undefined macros) and should not be the default for new
    extractions.

    `redo_inline_math=True` (the default) enables marker's
    `LLMEquationProcessor` / `LLMMathBlockProcessor` for inline math, which
    is the surface that previously produced KaTeX-incompatible output.
    """
    pdf_path = Path(pdf_path)
    cache_dir = Path(cache_dir)

    llm_provider = (llm_provider or DEFAULT_LLM_PROVIDER).lower()
    if llm_provider not in ("claude", "gemini"):
        raise ValueError(
            f"Unknown llm_provider {llm_provider!r}; expected 'claude' or 'gemini'."
        )

    # Per-provider model name (only one is meaningful at a time; keep the
    # cache key precise so swapping providers invalidates correctly).
    llm_model: str | None = None
    if use_llm:
        if llm_provider == "claude":
            llm_model = claude_model_name
        else:
            # marker.services.gemini.GoogleGeminiService default model
            llm_model = "gemini-2.0-flash"

    if not force:
        cached = _read_cache(
            cache_dir, pdf_path, use_llm,
            llm_provider=llm_provider if use_llm else None,
            llm_model=llm_model,
            redo_inline_math=redo_inline_math if use_llm else False,
        )
        if cached is not None:
            return cached

    # API key resolution per provider — fail clearly before any expensive work.
    claude_api_key: str | None = None
    if use_llm:
        if llm_provider == "claude":
            claude_api_key = _resolve_claude_api_key()
            if not claude_api_key:
                raise RuntimeError(
                    "marker --use_llm with provider=claude requires CLAUDE_API_KEY "
                    "(preferred, project .envrc convention) or ANTHROPIC_API_KEY "
                    "(Anthropic SDK fallback) in the environment. "
                    "Set one or pass use_llm=False."
                )
        else:
            if not (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")):
                raise RuntimeError(
                    "marker --use_llm with provider=gemini requires GOOGLE_API_KEY "
                    "(or GEMINI_API_KEY) in the environment. Set it in the project "
                    ".envrc or pass use_llm=False."
                )

    # The Anthropic SDK reads ANTHROPIC_BASE_URL and ANTHROPIC_AUTH_TOKEN from
    # the environment. On this workstation those env vars point to DeepSeek's
    # API (for Claude Code's model routing), which would cause every marker LLM
    # call to route to DeepSeek with an Anthropic-format key → 401. Save and
    # clear them so the SDK defaults to api.anthropic.com, then restore after.
    _saved_base_url = os.environ.pop("ANTHROPIC_BASE_URL", None)
    _saved_auth_token = os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)
    try:
        result = _convert_pdf_impl(
            pdf_path, cache_dir, use_llm, force,
            llm_provider, llm_model, redo_inline_math,
            claude_api_key,
        )
    finally:
        if _saved_base_url is not None:
            os.environ["ANTHROPIC_BASE_URL"] = _saved_base_url
        if _saved_auth_token is not None:
            os.environ["ANTHROPIC_AUTH_TOKEN"] = _saved_auth_token
    return result


def _convert_pdf_impl(
    pdf_path: Path,
    cache_dir: Path,
    use_llm: bool,
    force: bool,
    llm_provider: str,
    llm_model: str | None,
    redo_inline_math: bool,
    claude_api_key: str | None,
) -> MarkerResult:
    # marker-GPU-only policy (user, 2026-05-30): require a CUDA GPU with enough
    # free VRAM before any extraction. The check must happen BEFORE torch is
    # imported, since CUDA_VISIBLE_DEVICES is read once at torch module init.
    # Rather than silently forcing CPU inference when the GPU is contested (which
    # degrades quality invisibly), this raises — marker on GPU is the only
    # acceptable path, and ~15 GiB VRAM is expected to be free.
    _require_marker_gpu()

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
        config["redo_inline_math"] = redo_inline_math
        if llm_provider == "claude":
            config["llm_service"] = "marker.services.claude.ClaudeService"
            config["claude_model_name"] = llm_model
            config["claude_api_key"] = claude_api_key
            # Bump the per-call ceiling. Marker's default 8192 is plenty for
            # an equation/table cleanup, but a `redo_inline_math` pass on a
            # math-dense paragraph can push close to it. 16384 buys headroom
            # without changing per-call cost meaningfully (usage, not ceiling,
            # is billed).
            config["max_claude_tokens"] = 16384
        else:
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

    _write_cache(
        cache_dir, pdf_path, use_llm, text, requests, tokens,
        llm_provider=llm_provider if use_llm else None,
        llm_model=llm_model,
        redo_inline_math=redo_inline_math if use_llm else False,
    )

    return MarkerResult(
        pages=_split_paginated_markdown(text),
        llm_request_count=requests,
        llm_token_count=tokens,
        used_llm=use_llm,
        used_cache=False,
        llm_provider=llm_provider if use_llm else None,
        llm_model=llm_model,
        redo_inline_math=redo_inline_math if use_llm else False,
    )


def _require_marker_gpu(min_free_mib: int = 3072) -> None:
    """Require a CUDA GPU with enough free VRAM, else raise — never force CPU.

    marker-GPU-only policy (user, 2026-05-30): marker on GPU + Anthropic Sonnet
    is the ONLY acceptable extraction path for this corpus. The previous behaviour
    silently set CUDA_VISIBLE_DEVICES='' (CPU inference) when the GPU looked
    contested, which reads downstream as "marker worked but produced poor output".
    Making it a loud failure is correct: ~15 GiB VRAM is expected to be free, so a
    shortfall means something is wrong that the operator should see and fix.

    A caller-set CUDA_VISIBLE_DEVICES is honoured only if it is non-empty (lets
    the operator pin a specific GPU index); an explicitly-empty value (CPU) is
    rejected because it contradicts the policy.

    `min_free_mib` covers surya's layout (~600 MB) + recognition (~600 MB) models
    plus headroom for batched activations.
    """
    cvd = os.environ.get("CUDA_VISIBLE_DEVICES")
    if cvd is not None and cvd.strip() == "":
        raise RuntimeError(
            "CUDA_VISIBLE_DEVICES is empty (CPU inference). marker-GPU-only mode "
            "forbids CPU extraction; unset it or pin a GPU index."
        )
    try:
        import subprocess
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.free", "--format=csv,nounits,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        raise RuntimeError(
            f"nvidia-smi unavailable ({e!r}); cannot confirm a CUDA GPU. "
            "marker-GPU-only mode requires a working GPU."
        )
    if out.returncode != 0:
        raise RuntimeError(
            f"nvidia-smi failed (rc={out.returncode}): {out.stderr.strip()}. "
            "marker-GPU-only mode requires a working GPU."
        )
    try:
        free_mib = min(
            int(line) for line in out.stdout.strip().splitlines() if line.strip()
        )
    except ValueError as e:
        raise RuntimeError(f"could not parse nvidia-smi free-VRAM output: {e!r}")
    if free_mib < min_free_mib:
        raise RuntimeError(
            f"only {free_mib} MiB VRAM free (< {min_free_mib} MiB required). "
            f"marker-GPU-only mode refuses to run; free the GPU and retry."
        )
    print(f"  marker: GPU OK ({free_mib} MiB free)")


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)


def first_heading(markdown: str) -> str | None:
    """Return the first markdown heading text in `markdown`, or None.

    Used by extract_research.py to populate `PageData.heading` from
    marker's structured output instead of the old font-size>14 heuristic.
    """
    m = _HEADING_RE.search(markdown)
    return m.group(2).strip() if m else None
