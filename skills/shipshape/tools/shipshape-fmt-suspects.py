#!/usr/bin/env python3
"""shipshape-fmt-suspects: find code whose readability csharpier degraded.

csharpier wraps purely by print width, with no model of the *logical* grouping
inside an expression. It therefore mangles a broad class of constructs in two
opposite directions:

  - flattened: a structured literal or a boolean gate left on one wide line
    because it happened to fit, its row/clause structure invisible;
  - shredded: a fluent/LINQ chain or a long condition broken at every `.` or
    operator, one fragment per line, so logical stages no longer group.

The repair in both directions is the trailing-`//` idiom — a line ending in
`//` keeps its break through every later csharpier pass — applied at the
logical boundary: one matrix row per line, the operands of one precedence
level together, one pipeline stage per line, the two arms of a ternary aligned.

This tool only *locates and categorizes* candidates; it never rewrites. Which
fragments form a logical group is a judgment the F-pass agent makes against the
csharpier diff, and the regroup is then verified token-identical. The
categories differ in confidence: STRUCTURED-LITERAL is precise; the LOGIC,
CHAIN, and WIDE categories are heuristic nets that include false positives the
agent filters. Stdlib only, no project files.

Usage: shipshape-fmt-suspects.py <dir> [--json FILE] [--width N]
"""

import argparse
import json
import re
import sys
from pathlib import Path

EXCLUDES = {"Samples~", "Documentation~", "Library", "obj", "bin", ".git", "Temp"}

MATRIX_CTORS = {
    "float2x2": 2, "float3x3": 3, "float4x4": 4,
    "float2x3": 3, "float3x2": 2, "float3x4": 4, "float4x3": 3,
    "double2x2": 2, "double3x3": 3, "double4x4": 4,
}
CTOR_RE = re.compile(r"\b(?:math\.)?(" + "|".join(MATRIX_CTORS) + r")\s*\(")
NUMERIC_ARG = re.compile(r"^-?[\w.]+f?$")
STRING_RE = re.compile(r'\$?@?"(?:[^"\\]|\\.)*"')
LINE_COMMENT_RE = re.compile(r"//.*$")


def strip_noise(line):
    return LINE_COMMENT_RE.sub("", STRING_RE.sub('""', line))


def scan_matrix(path, lines):
    hits = []
    for i, line in enumerate(lines, 1):
        for m in CTOR_RE.finditer(line):
            ctor = m.group(1)
            rows = MATRIX_CTORS[ctor]
            depth, buf, j, ln, done = 0, [], m.end() - 1, i, False
            while ln <= len(lines) and not done:
                cur = lines[ln - 1]
                k = j if ln == i else 0
                while k < len(cur):
                    c = cur[k]
                    if c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                        if depth == 0:
                            done = True
                            break
                    buf.append(c)
                    k += 1
                if not done:
                    ln += 1
            args = [a.strip() for a in "".join(buf).lstrip("(").split(",") if a.strip()]
            if len(args) >= rows * 2 and all(NUMERIC_ARG.match(a) for a in args):
                span = ln - i + 1
                grouped = span in (rows, rows + 2)
                marked = any(lines[i - 1 + r].rstrip().endswith("//")
                             for r in range(min(span, rows)) if i - 1 + r < len(lines))
                if not (grouped and marked):
                    hits.append((path, i, ln, "STRUCTURED-LITERAL",
                                 f"{ctor} {len(args)} args on {'1 line' if span==1 else f'{span} lines'} — regroup to {rows} rows + //"))
    return hits


def scan_logic_and_width(path, lines, width):
    hits = []
    for i, line in enumerate(lines, 1):
        code = strip_noise(line)
        stripped = code.strip()
        if not stripped or stripped.startswith("//"):
            continue
        ands, ors = code.count("&&"), code.count("||")
        ternaries = len(re.findall(r"\?(?![.?:])", code))  # rough ternary '?' count
        # LOGIC: a boolean gate mixing precedence levels, or a multi-clause gate,
        # or a multi-arm ternary, all kept on one physical line.
        if (ands and ors) or (ands + ors) >= 3 or ternaries >= 2:
            if len(line) > 60:
                kind = "mixed &&/||" if (ands and ors) else (f"{ands+ors} bool ops" if ands+ors >= 3 else f"{ternaries} ternaries")
                hits.append((path, i, i, "LOGIC",
                             f"one-line gate ({kind}, {len(line)} cols) — break per precedence level + //"))
                continue
        # WIDE: any non-comment line over the width budget that carries operators
        # csharpier could not break cleanly.
        if len(line) > width and re.search(r"[+\-*/%<>=&|?]", code):
            hits.append((path, i, i, "WIDE",
                         f"{len(line)} cols > {width} with operators — candidate for a //-preserved break"))
    return hits


def scan_chains(path, lines):
    hits = []
    run_start = None
    count = 0
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("."):
            if run_start is None:
                run_start = i
            count += 1
        else:
            if count >= 4:
                hits.append((path, run_start, i - 1, "CHAIN",
                             f"{count} consecutive .calls one-per-line — group pipeline stages with //"))
            run_start, count = None, 0
    if count >= 4:
        hits.append((path, run_start, len(lines), "CHAIN",
                     f"{count} consecutive .calls one-per-line — group pipeline stages with //"))
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--width", type=int, default=115, help="WIDE threshold (cols)")
    args = ap.parse_args()

    hits = []
    for d in args.dirs:
        for p in sorted(Path(d).rglob("*.cs")):
            if any(part in EXCLUDES for part in p.parts):
                continue
            try:
                lines = p.read_text(encoding="utf-8-sig", errors="replace").splitlines()
            except OSError:
                continue
            sp = str(p)
            hits += scan_matrix(sp, lines)
            hits += scan_logic_and_width(sp, lines, args.width)
            hits += scan_chains(sp, lines)

    by_cat = {}
    for h in hits:
        by_cat.setdefault(h[3], []).append(h)
    order = ["STRUCTURED-LITERAL", "LOGIC", "CHAIN", "WIDE"]
    conf = {"STRUCTURED-LITERAL": "precise", "LOGIC": "heuristic", "CHAIN": "heuristic", "WIDE": "noisy net"}

    print(f"# csharpier readability-damage candidates: {len(hits)}")
    print("# STRUCTURED-LITERAL is precise; LOGIC/CHAIN/WIDE are nets — the F-pass agent")
    print("# judges each against the csharpier diff and regroups only where it reads worse.\n")
    for cat in order:
        rows = by_cat.get(cat, [])
        if not rows:
            continue
        print(f"## {cat} ({len(rows)}, {conf[cat]})")
        for path, a, b, _, desc in rows:
            loc = f"{path}:{a}" if a == b else f"{path}:{a}-{b}"
            print(f"- {loc}  {desc}")
        print()
    if not hits:
        print("(none)")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(
            [{"file": h[0], "line": h[1], "endline": h[2], "category": h[3], "desc": h[4]} for h in hits],
            indent=1))


if __name__ == "__main__":
    main()
