#!/usr/bin/env python3
"""shipshape-metrics: self-contained C# metrics for the shipshape battery.

Emits, for a directory tree of .cs files: line classification (code / //
comment / /// xml-doc / blank), statement count, method-length distribution
(p50/p95/max + top offenders), max nesting depth offenders, and a
narration-comment classifier (comments whose tokens overlap the next code
line). No project files, no network, stdlib only. Method and nesting numbers
come from a brace-scan heuristic (strings are stripped, preprocessor lines
ignored) — treat them as ±a few lines, good for distributions and diffs, not
for citation.

Usage: shipshape-metrics.py <dir> [<dir>...] [--json FILE] [--exclude NAME]...
"""

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

DEFAULT_EXCLUDES = {"Samples~", "Documentation~", "Library", "obj", "bin", ".git", "Temp"}

MODIFIERS = (
    "public|private|protected|internal|static|sealed|override|virtual|"
    "abstract|async|unsafe|extern|new|partial|readonly|ref"
)
METHOD_RE = re.compile(
    r"^\s*(?:\[[^\]]*\]\s*)*(?:(?:" + MODIFIERS + r")\s+)+"
    r"[\w<>\[\],\.\?\s]+?\s+(\w+)\s*(?:<[^>()]*>)?\s*\("
)
CONTROL_KEYWORDS = {"if", "for", "foreach", "while", "switch", "using", "lock", "catch", "return"}
NARRATION_VERB_RE = re.compile(
    r"^\s*//\s(?:Get|Set|Check|Create|Initialize|Calculate|Compute|Update|"
    r"Return|Call|Loop|Iterate|Now|First|Then|Finally|Add|Remove|Step \d)\b"
)
STRING_RE = re.compile(r'\$?@?"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\'')
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def split_camel(token):
    return [p.lower() for p in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", token) if len(p) > 2]


def classify_file(path):
    """Return per-file stats dict."""
    try:
        lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    except OSError as e:
        print(f"warn: unreadable {path}: {e}", file=sys.stderr)
        return None

    stats = {
        "code": 0, "comment": 0, "xmldoc": 0, "blank": 0,
        "statements": 0, "methods": [], "narration": [], "trailing_markers": 0,
    }
    in_block = False
    pending_comments = []  # (lineno, text) of contiguous // comments awaiting next code line
    method_stack = []  # (name, start_line, start_depth, max_rel_depth)
    depth = 0

    for i, raw in enumerate(lines, 1):
        line = raw.strip()
        if in_block:
            stats["comment"] += 1
            if "*/" in line:
                in_block = False
            continue
        if not line:
            stats["blank"] += 1
            continue
        if line.startswith("///"):
            stats["xmldoc"] += 1
            continue
        if line.startswith("//"):
            stats["comment"] += 1
            pending_comments.append((i, line))
            continue
        if line.startswith("/*"):
            stats["comment"] += 1
            if "*/" not in line:
                in_block = True
            continue
        if line.startswith("#"):
            continue

        # code line (possibly with trailing comment)
        stats["code"] += 1
        nostr = STRING_RE.sub('""', raw)
        comment_idx = nostr.find("//")
        code_part = nostr if comment_idx < 0 else nostr[:comment_idx]
        if comment_idx >= 0 and nostr[comment_idx:].strip() == "//":
            stats["trailing_markers"] += 1
        stats["statements"] += code_part.count(";")

        # narration check against pending comment block
        if pending_comments:
            code_tokens = set()
            for ident in IDENT_RE.findall(code_part):
                code_tokens.update(split_camel(ident))
                if len(ident) > 2:
                    code_tokens.add(ident.lower())
            for lineno, ctext in pending_comments:
                words = [w.lower() for w in IDENT_RE.findall(ctext) if len(w) > 2]
                if len(words) >= 2:
                    overlap = sum(1 for w in words if w in code_tokens)
                    verb_hit = bool(NARRATION_VERB_RE.match(ctext))
                    if overlap / len(words) >= 0.5 or (verb_hit and overlap / len(words) >= 0.3):
                        stats["narration"].append((lineno, ctext[:100]))
            pending_comments = []

        # method detection (before brace tracking so the signature line counts).
        # Expression-bodied members never enter the stack — counting them to the
        # class-closing brace was a phantom-offender bug (846-"line" 2-line helpers).
        m = METHOD_RE.match(code_part)
        if m and m.group(1) not in CONTROL_KEYWORDS and "=>" not in code_part:
            if "{" in code_part or not code_part.rstrip().endswith(";"):
                method_stack.append({"name": m.group(1), "start": i, "depth0": depth, "maxrel": 0})

        for ch in code_part:
            if ch == "{":
                depth += 1
                for ms in method_stack:
                    ms["maxrel"] = max(ms["maxrel"], depth - ms["depth0"])
            elif ch == "}":
                depth = max(0, depth - 1)
                if method_stack and depth == method_stack[-1]["depth0"]:
                    ms = method_stack.pop()
                    length = i - ms["start"] + 1
                    if length >= 2:
                        stats["methods"].append(
                            {"name": ms["name"], "line": ms["start"], "len": length,
                             "nest": max(0, ms["maxrel"] - 1)}
                        )
    return stats


def percentile(values, p):
    if not values:
        return 0
    values = sorted(values)
    k = max(0, min(len(values) - 1, round(p / 100 * len(values)) - 1))
    return values[k]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--exclude", action="append", default=[])
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()
    excludes = DEFAULT_EXCLUDES | set(args.exclude)

    files = {}
    for d in args.dirs:
        root = Path(d)
        for p in sorted(root.rglob("*.cs")):
            if any(part in excludes for part in p.parts):
                continue
            st = classify_file(p)
            if st:
                files[str(p)] = st

    tot = {k: sum(f[k] for f in files.values()) for k in ("code", "comment", "xmldoc", "blank", "statements", "trailing_markers")}
    all_methods = [dict(m, file=fp) for fp, f in files.items() for m in f["methods"]]
    lengths = [m["len"] for m in all_methods]
    narrations = [(fp, ln, tx) for fp, f in files.items() for ln, tx in f["narration"]]
    commenty = tot["comment"] + tot["xmldoc"]
    density = commenty / max(1, commenty + tot["code"]) * 100

    print(f"# shipshape metrics — {', '.join(args.dirs)}\n")
    print(f"| files | code | // comment | /// xmldoc | blank | density % | statements | trailing `//` |")
    print(f"|---|---|---|---|---|---|---|---|")
    print(f"| {len(files)} | {tot['code']} | {tot['comment']} | {tot['xmldoc']} | {tot['blank']} | {density:.1f} | {tot['statements']} | {tot['trailing_markers']} |\n")
    print(f"methods: {len(all_methods)}  p50: {percentile(lengths,50)}  p95: {percentile(lengths,95)}  max: {max(lengths) if lengths else 0}\n")
    print("## Longest methods")
    for m in sorted(all_methods, key=lambda m: -m["len"])[: args.top]:
        print(f"- {m['len']:5d}  {m['file']}:{m['line']}  {m['name']}  (nest {m['nest']})")
    deep = [m for m in all_methods if m["nest"] > 4]
    print(f"\n## Nesting depth > 4: {len(deep)}")
    for m in sorted(deep, key=lambda m: -m["nest"])[: args.top]:
        print(f"- nest {m['nest']}  {m['file']}:{m['line']}  {m['name']}")
    print(f"\n## Narration-comment candidates: {len(narrations)}")
    for fp, ln, tx in narrations[: args.top * 2]:
        print(f"- {fp}:{ln}  {tx}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps({
            "totals": tot, "density_pct": round(density, 2), "files": len(files),
            "methods": len(all_methods), "p50": percentile(lengths, 50),
            "p95": percentile(lengths, 95), "max": max(lengths) if lengths else 0,
            "narration_hits": len(narrations),
            "longest": sorted(all_methods, key=lambda m: -m["len"])[:25],
        }, indent=1))


if __name__ == "__main__":
    main()
