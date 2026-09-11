#!/usr/bin/env python3
"""Validate LaTeX and Mermaid syntax in research markdown.

Walks `<RESEARCH_ROOT>/Prepared/<slug>.md` (or all `*.md` if no `--only`), extracts every
LaTeX block (inline `$...$`, display `$$...$$`) and every Mermaid fenced code
block, and dispatches each block to the Node validator (`validate_md.mjs`).

LaTeX is checked via KaTeX (`renderToString` with `throwOnError: true`).
Mermaid is checked via `mermaid.parse()` (jsdom-backed); when the mermaid
library can't load in Node, blocks are reported as warnings rather than errors.

Per-doc report is written to:
  <RESEARCH_ROOT>/Prepared/assets/<slug>/findings-pass2.5-validate.md

Optional `--html` also writes a self-contained preview HTML (KaTeX server-side,
mermaid client-side via CDN) at the same location, named `<slug>.preview.html`.

Exit status:
  0 — all blocks parsed cleanly
  1 — at least one block had a parse error
  2 — tool error (Node missing, deps not installed, malformed args)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from research_paths import PREPARED_DIR

SKILL_ROOT = Path(__file__).resolve().parent.parent
NODE_VALIDATE = SKILL_ROOT / "tools" / "validate_md.mjs"
NODE_RENDER = SKILL_ROOT / "tools" / "render_md_html.mjs"
NODE_MODULES = SKILL_ROOT / "node_modules"


@dataclass
class Block:
    kind: str  # "inline" | "display" | "mermaid"
    content: str
    start_line: int  # 1-indexed line of the opening delimiter
    end_line: int
    file: str


def extract_blocks(md_path: Path) -> list[Block]:
    """Walk the markdown line-by-line, extracting LaTeX and Mermaid blocks.

    Skips fenced code blocks (except ```mermaid). Handles multi-line $$...$$
    and multi-line ``` fences correctly.
    """
    text = md_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    blocks: list[Block] = []

    in_code = False         # inside ``` fence (not mermaid)
    in_mermaid = False      # inside ```mermaid fence
    in_display = False      # inside multi-line $$...$$
    code_marker = ""        # exact opening fence ("```", "~~~", or longer)

    mermaid_buf: list[str] = []
    mermaid_start = 0

    display_buf: list[str] = []
    display_start = 0

    for i, line in enumerate(lines):
        line_no = i + 1

        # --- multi-line $$ display block ---
        if in_display:
            idx = line.find("$$")
            if idx >= 0:
                display_buf.append(line[:idx])
                content = "\n".join(display_buf).strip()
                blocks.append(Block(
                    kind="display",
                    content=content,
                    start_line=display_start,
                    end_line=line_no,
                    file=str(md_path),
                ))
                in_display = False
                display_buf = []
            else:
                display_buf.append(line)
            continue

        # --- ```mermaid block ---
        if in_mermaid:
            stripped = line.strip()
            if stripped == code_marker or (stripped.startswith(code_marker)
                                           and set(stripped) == set(code_marker[0])):
                blocks.append(Block(
                    kind="mermaid",
                    content="\n".join(mermaid_buf),
                    start_line=mermaid_start,
                    end_line=line_no,
                    file=str(md_path),
                ))
                in_mermaid = False
                mermaid_buf = []
                code_marker = ""
            else:
                mermaid_buf.append(line)
            continue

        # --- generic ``` code fence (skip math extraction inside) ---
        if in_code:
            stripped = line.strip()
            if stripped == code_marker or (stripped.startswith(code_marker)
                                           and set(stripped) == set(code_marker[0])):
                in_code = False
                code_marker = ""
            continue

        # --- detect fence opening ---
        m = re.match(r"^\s*(`{3,}|~{3,})\s*([^\s`~]*)", line)
        if m:
            marker, lang = m.group(1), m.group(2).lower()
            if lang == "mermaid":
                in_mermaid = True
                code_marker = marker
                mermaid_buf = []
                mermaid_start = line_no
            else:
                in_code = True
                code_marker = marker
            continue

        # --- $$ on this line (single-line or start of multi-line) ---
        col = 0
        consumed_to = -1
        while True:
            idx = line.find("$$", col)
            if idx < 0:
                break
            close = line.find("$$", idx + 2)
            if close >= 0:
                content = line[idx + 2:close].strip()
                if content:
                    blocks.append(Block(
                        kind="display",
                        content=content,
                        start_line=line_no,
                        end_line=line_no,
                        file=str(md_path),
                    ))
                consumed_to = close + 2
                col = close + 2
            else:
                in_display = True
                display_start = line_no
                display_buf = [line[idx + 2:]]
                consumed_to = len(line)
                break

        # --- inline $...$ (single-line, single dollars) ---
        if not in_display:
            # Mask off any single-line $$...$$ regions we already captured so
            # their dollar pairs don't get mistaken for a long $...$ inline.
            scan = re.sub(r"\$\$.*?\$\$", lambda m: " " * len(m.group(0)), line)
            for mi in re.finditer(r"(?<![\$\\])\$([^\$\n]+?)\$(?!\$)", scan):
                content = mi.group(1)
                if not content.strip():
                    continue
                # Filter likely false positives: "$5", "$200/month", etc.
                if re.fullmatch(r"\s*\d[\d,.\s/%a-zA-Z-]*", content):
                    continue
                # Require at least one LaTeX-ish character to be confident.
                if not re.search(r"[\\^_{}=<>+\-*/]", content):
                    continue
                blocks.append(Block(
                    kind="inline",
                    content=content.strip(),
                    start_line=line_no,
                    end_line=line_no,
                    file=str(md_path),
                ))

    # Unterminated $$ block — flag but extract what we have so the user sees it
    if in_display:
        blocks.append(Block(
            kind="display",
            content="\n".join(display_buf).strip(),
            start_line=display_start,
            end_line=len(lines),
            file=str(md_path),
        ))

    return blocks


def validate_blocks(blocks: list[Block]) -> list[dict]:
    if not blocks:
        return []
    if not shutil.which("node"):
        print("[validate] `node` not on PATH — install Node.js (>=20)", file=sys.stderr)
        sys.exit(2)
    if not NODE_VALIDATE.exists():
        print(f"[validate] Node helper missing: {NODE_VALIDATE}", file=sys.stderr)
        sys.exit(2)
    if not NODE_MODULES.exists():
        print(f"[validate] Node modules not installed at {NODE_MODULES}", file=sys.stderr)
        print(f"[validate] Run: cd {SKILL_ROOT} && npm install", file=sys.stderr)
        sys.exit(2)

    payload = json.dumps([asdict(b) for b in blocks])
    proc = subprocess.run(
        ["node", str(NODE_VALIDATE)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=str(SKILL_ROOT),
    )
    if proc.returncode != 0:
        print(f"[validate] Node helper failed (exit {proc.returncode}):", file=sys.stderr)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        sys.exit(2)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        print(f"[validate] Failed to parse Node output: {e}", file=sys.stderr)
        print(proc.stdout[:2000], file=sys.stderr)
        sys.exit(2)


def render_html(md_path: Path, html_path: Path) -> None:
    if not NODE_RENDER.exists():
        print(f"[validate] Renderer missing: {NODE_RENDER}", file=sys.stderr)
        return
    html_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["node", str(NODE_RENDER), str(md_path), str(html_path)],
        capture_output=True,
        text=True,
        cwd=str(SKILL_ROOT),
    )
    if proc.returncode != 0:
        print(f"[validate] Renderer failed: {proc.stderr.strip()}", file=sys.stderr)
    elif proc.stderr.strip():
        print(f"[validate] {proc.stderr.strip()}", file=sys.stderr)


def write_sidecar(report_path: Path, results: list[dict], slug: str,
                  html_path: Path | None) -> None:
    errors = [r for r in results if r.get("ok") is False]
    warnings = [r for r in results if r.get("ok") is None]
    ok_count = sum(1 for r in results if r.get("ok") is True)

    by_kind = {"display": 0, "inline": 0, "mermaid": 0}
    for r in results:
        by_kind[r["kind"]] = by_kind.get(r["kind"], 0) + 1

    lines = [
        f"# Pass 2.5 validation — {slug}",
        "",
        f"- Blocks scanned: **{len(results)}** "
        f"(display LaTeX: {by_kind['display']}, inline LaTeX: {by_kind['inline']}, "
        f"mermaid: {by_kind['mermaid']})",
        f"- OK: **{ok_count}**",
        f"- Errors: **{len(errors)}**",
        f"- Warnings (validator unavailable): **{len(warnings)}**",
    ]
    if html_path is not None:
        lines.append(f"- Preview HTML: `{html_path}` (open in browser)")
    lines.append("")

    if errors:
        lines += ["## Errors", ""]
        for r in errors:
            loc = f"{Path(r['file']).name}:{r['start_line']}"
            if r["start_line"] != r["end_line"]:
                loc += f"-{r['end_line']}"
            lines.append(f"### {loc} — `{r['kind']}`")
            lines.append("")
            preview = r["content"]
            if len(preview) > 600:
                preview = preview[:600] + " …"
            fence = "```" if "```" not in preview else "~~~"
            lines += [fence, preview, fence, ""]
            lines.append(f"**Error:** {r['error'].strip()}")
            lines.append("")

    if warnings:
        lines += ["## Warnings (validator unavailable)", ""]
        for r in warnings:
            loc = f"{Path(r['file']).name}:{r['start_line']}"
            lines.append(f"- {loc} `{r['kind']}` — {r['error'].strip()}")
        lines.append("")

    if not errors and not warnings:
        lines.append("All LaTeX and Mermaid blocks parsed cleanly. ✓")
        lines.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines))


def process_one(md_path: Path, research_dir: Path, want_html: bool,
                want_sidecar: bool) -> tuple[int, int, int]:
    """Returns (ok, errors, warnings)."""
    slug = md_path.stem
    print(f"[validate] {slug}", file=sys.stderr)
    blocks = extract_blocks(md_path)
    results = validate_blocks(blocks)
    errors = [r for r in results if r.get("ok") is False]
    warnings = [r for r in results if r.get("ok") is None]
    ok = sum(1 for r in results if r.get("ok") is True)

    print(f"  blocks={len(results)} ok={ok} errors={len(errors)} warn={len(warnings)}",
          file=sys.stderr)
    for r in errors:
        first = (r.get("error") or "").splitlines()[0] if r.get("error") else "?"
        preview = r["content"].replace("\n", " ")[:80]
        print(f"  ERROR {Path(r['file']).name}:{r['start_line']} {r['kind']}: {first}",
              file=sys.stderr)
        print(f"        {preview!r}", file=sys.stderr)

    html_path: Path | None = None
    if want_html:
        html_path = research_dir / "assets" / slug / f"{slug}.preview.html"
        render_html(md_path, html_path)

    if want_sidecar:
        sidecar = research_dir / "assets" / slug / "findings-pass2.5-validate.md"
        write_sidecar(sidecar, results, slug, html_path)

    return ok, len(errors), len(warnings)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", help="Slug to validate (matches <RESEARCH_ROOT>/Prepared/<slug>.md). "
                                   "Repeat with comma for multiple slugs.")
    ap.add_argument("--research-dir", default=str(PREPARED_DIR),
                    help=f"Directory containing research markdown (default: {PREPARED_DIR})")
    ap.add_argument("--html", action="store_true",
                    help="Also emit a preview HTML at assets/<slug>/<slug>.preview.html")
    ap.add_argument("--no-sidecar", action="store_true",
                    help="Skip writing findings-pass2.5-validate.md sidecar")
    args = ap.parse_args()

    research_dir = Path(args.research_dir).resolve()
    if not research_dir.is_dir():
        print(f"[validate] Not a directory: {research_dir}", file=sys.stderr)
        return 2

    if args.only:
        slugs = [s.strip() for s in args.only.split(",") if s.strip()]
        targets = [research_dir / f"{s}.md" for s in slugs]
        missing = [t for t in targets if not t.exists()]
        if missing:
            for t in missing:
                print(f"[validate] No such file: {t}", file=sys.stderr)
            return 2
    else:
        targets = sorted(p for p in research_dir.glob("*.md")
                         if not p.name.startswith("index"))

    total_errors = 0
    total_warnings = 0
    for md_path in targets:
        _ok, errs, warns = process_one(
            md_path, research_dir,
            want_html=args.html,
            want_sidecar=not args.no_sidecar,
        )
        total_errors += errs
        total_warnings += warns

    print("", file=sys.stderr)
    if total_errors:
        print(f"[validate] FAIL: {total_errors} parse error(s) "
              f"({total_warnings} warning(s)) across {len(targets)} file(s)",
              file=sys.stderr)
        return 1
    if total_warnings:
        print(f"[validate] OK with warnings: {total_warnings} block(s) skipped "
              f"across {len(targets)} file(s)", file=sys.stderr)
    else:
        print(f"[validate] OK: {len(targets)} file(s) clean", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
