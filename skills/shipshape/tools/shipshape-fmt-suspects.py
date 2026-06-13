#!/usr/bin/env python3
"""shipshape-fmt-suspects: find structured literals csharpier flattened.

csharpier has no notion of the *logical* grouping inside a multi-argument
literal: a 4x4 matrix constructor is printed either as one long line or as
sixteen one-argument lines, both of which hide the row structure a reader
needs. The repair is the trailing-`//` idiom (a line ending in `//` keeps its
break through every future csharpier pass), applied at logical-group
boundaries — four floats per row for a float4x4, the components per vector,
RGBA per color.

This tool only *locates* candidates for an agent (or a human) to regroup; it
never rewrites — the regrouping is a semantic judgment (which arguments form a
row) that must be verified token-identical afterward. Output is file:line
ranges with the detected kind. Stdlib only, no project files.

Usage: shipshape-fmt-suspects.py <dir> [--json FILE]
"""

import argparse
import json
import re
import sys
from pathlib import Path

EXCLUDES = {"Samples~", "Documentation~", "Library", "obj", "bin", ".git", "Temp"}

# Constructors whose argument count has a canonical row grouping.
MATRIX_CTORS = {
    "float2x2": 2, "float3x3": 3, "float4x4": 4,
    "float2x3": 3, "float3x2": 2, "float3x4": 4, "float4x3": 3,
    "double2x2": 2, "double3x3": 3, "double4x4": 4,
}
CTOR_RE = re.compile(r"\b(?:math\.)?(" + "|".join(MATRIX_CTORS) + r")\s*\(")
# A flattened literal: the call and a long run of comma-separated simple args.
LONG_SINGLE_LINE = re.compile(r".{100,}")
NUMERIC_ARG = re.compile(r"^-?[\w.]+f?$")


def scan_file(path):
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return []
    lines = text.splitlines()
    hits = []

    for i, line in enumerate(lines, 1):
        for m in CTOR_RE.finditer(line):
            ctor = m.group(1)
            rows = MATRIX_CTORS[ctor]
            # gather the argument span: from the '(' to the matching ')'
            depth = 0
            start = m.end() - 1
            buf, j, ln = [], start, i
            done = False
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
            arg_text = "".join(buf).lstrip("(")
            args = [a.strip() for a in arg_text.split(",") if a.strip()]
            span = ln - i + 1
            # candidate if it is the wrong shape: one line (flat) or one-arg-per-line,
            # but NOT already grouped into `rows` lines, and the args are simple scalars.
            if len(args) >= rows * 2 and all(NUMERIC_ARG.match(a) for a in args):
                already_grouped = span == rows or span == rows + 2  # rows, or rows+open/close
                ends_marked = any(lines[i - 1 + r].rstrip().endswith("//") for r in range(min(span, rows)) if i - 1 + r < len(lines))
                if not (already_grouped and ends_marked):
                    shape = "one-line" if span == 1 else f"{span}-line"
                    hits.append({
                        "file": str(path), "line": i, "endline": ln,
                        "kind": ctor, "args": len(args), "rows": rows,
                        "shape": shape,
                    })
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    hits = []
    for d in args.dirs:
        for p in sorted(Path(d).rglob("*.cs")):
            if any(part in EXCLUDES for part in p.parts):
                continue
            hits.extend(scan_file(p))

    print(f"# csharpier-flattened structured-literal suspects: {len(hits)}\n")
    for h in hits:
        print(f"- {h['file']}:{h['line']}-{h['endline']}  {h['kind']} "
              f"({h['args']} args, currently {h['shape']}; regroup to {h['rows']} rows + trailing //)")
    if not hits:
        print("(none — no matrix/structured literal is mis-grouped)")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(hits, indent=1))


if __name__ == "__main__":
    main()
