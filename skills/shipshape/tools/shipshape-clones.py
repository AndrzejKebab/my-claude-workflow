#!/usr/bin/env python3
"""shipshape-clones: discover candidate near-duplicate families for the E pass.

This tool only *nominates*. It runs jscpd (a token-based Type-1/2/3 clone
detector that works across C#, Rust, TypeScript, and more), groups jscpd's
pairwise duplicate fragments into connected *families*, and ranks them by
drift-risk (instance count x representative size). Whether a family is a
genuine commonality worth one shared block, or a false commonality of
different concepts that merely resemble each other today, is a judgment the
surveyor makes with the six-test discriminator and the adversary refutes — it
is NOT decided here. Mechanical similarity is necessary, never sufficient.

jscpd is fetched via `npx -y jscpd` (the one networked tool in the kit, by
existing design); if node is unavailable the tool says so and exits cleanly.

Usage: shipshape-clones.py <dir>... [--min-tokens N] [--min-lines N]
                                     [--formats csharp,rust,typescript]
                                     [--top N] [--json OUT]
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# jscpd format name -> the file globs it should scan for that language.
FORMAT_GLOBS = {
    "csharp": ["**/*.cs"],
    "rust": ["**/*.rs"],
    "typescript": ["**/*.ts", "**/*.tsx"],
    "javascript": ["**/*.js", "**/*.jsx"],
    "python": ["**/*.py"],
    "cpp": ["**/*.cpp", "**/*.cc", "**/*.h", "**/*.hpp"],
}

IGNORE = "**/Samples~/**,**/Documentation~/**,**/obj/**,**/bin/**,**/Library/**,**/.git/**,**/Temp/**,**/node_modules/**"


def _line(end_or_start):
    """jscpd has shifted the shape of firstFile.start across versions: an int
    line, or a {line, column} loc. Accept either."""
    if isinstance(end_or_start, dict):
        return end_or_start.get("line", 0)
    return end_or_start or 0


class _UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def run_jscpd(dirs, fmts, min_tokens, min_lines, out_dir):
    globs = []
    for f in fmts:
        globs += FORMAT_GLOBS.get(f, [])
    cmd = [
        "npx", "-y", "jscpd",
        "--silent", "--reporters", "json", "--output", str(out_dir),
        "--min-tokens", str(min_tokens), "--min-lines", str(min_lines),
        "--format", ",".join(fmts), "--ignore", IGNORE, "--absolute",
        *dirs,
    ]
    try:
        subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=900)
    except FileNotFoundError:
        print("# shipshape-clones: `npx` not found — node is required for jscpd.")
        print("# Install node, or run the E-pass discovery manually with another")
        print("# clone detector (PMD CPD, Simian, NiCad) and feed families to the surveyor.")
        sys.exit(0)
    except subprocess.TimeoutExpired:
        print("# shipshape-clones: jscpd timed out (900s) — narrow <dir> or raise --min-tokens.")
        sys.exit(0)
    report = out_dir / "jscpd-report.json"
    if not report.exists():
        print("# shipshape-clones: jscpd produced no report (no clones above threshold, or it errored).")
        sys.exit(0)
    return json.loads(report.read_text())


def build_families(duplicates):
    uf = _UnionFind()
    meta = {}  # key -> (file, start, end)
    pair_size = {}  # key -> max representative (lines, tokens) seen
    for d in duplicates:
        a, b = d.get("firstFile", {}), d.get("secondFile", {})
        ka = (a.get("name", "?"), _line(a.get("start")))
        kb = (b.get("name", "?"), _line(b.get("start")))
        meta[ka] = (a.get("name", "?"), _line(a.get("start")), _line(a.get("end")))
        meta[kb] = (b.get("name", "?"), _line(b.get("start")), _line(b.get("end")))
        lines, tokens = d.get("lines", 0), d.get("tokens", 0)
        for k in (ka, kb):
            pl, pt = pair_size.get(k, (0, 0))
            pair_size[k] = (max(pl, lines), max(pt, tokens))
        uf.union(ka, kb)

    fams = {}
    for k in meta:
        fams.setdefault(uf.find(k), []).append(k)

    out = []
    for members in fams.values():
        spans = sorted({meta[k] for k in members})
        rep_lines = max(pair_size.get(k, (0, 0))[0] for k in members)
        rep_tokens = max(pair_size.get(k, (0, 0))[1] for k in members)
        out.append({
            "instances": len(spans),
            "lines": rep_lines,
            "tokens": rep_tokens,
            "score": len(spans) * rep_lines,
            "spans": [{"file": f, "start": s, "end": e} for (f, s, e) in spans],
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--min-tokens", type=int, default=50,
                    help="jscpd min clone size in tokens (lower = more Type-3 near-clones, noisier)")
    ap.add_argument("--min-lines", type=int, default=5)
    ap.add_argument("--formats", default="csharp",
                    help="comma list: csharp,rust,typescript,javascript,python,cpp")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args()

    if not shutil.which("npx"):
        print("# shipshape-clones: `npx` not on PATH — node is required for jscpd. See module docstring.")
        sys.exit(0)

    fmts = [f.strip() for f in args.formats.split(",") if f.strip()]
    with tempfile.TemporaryDirectory() as td:
        report = run_jscpd(args.dirs, fmts, args.min_tokens, args.min_lines, Path(td))
    families = build_families(report.get("duplicates", []))

    print(f"# shipshape-clones: {len(families)} candidate clone families "
          f"(min-tokens {args.min_tokens}, formats {','.join(fmts)})")
    print("# CANDIDATES ONLY — each family is mechanical similarity, not an extraction verdict.")
    print("# Adjudicate every family against the six-test discriminator (SKILL.md, the E pass):")
    print("#   1 rule of three or proven drift   2 one reason to change   3 differences are data not control flow")
    print("#   4 nameable as one operation       5 call sites read better 6 no boundary it should not cross")
    print("# Default to LEAVE DUPLICATED on a tie. Record rejected families with rationale in the journal.\n")
    if not families:
        print("(no families above threshold)")
        return
    for i, fam in enumerate(families[:args.top], 1):
        print(f"## family {i}: {fam['instances']} instances, ~{fam['lines']} lines / "
              f"{fam['tokens']} tokens each (drift-score {fam['score']})")
        for s in fam["spans"]:
            print(f"   - {s['file']}:{s['start']}-{s['end']}")
        print()
    if len(families) > args.top:
        print(f"# ... {len(families) - args.top} more families below the top {args.top} (raise --top to see).")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(families, indent=1))


if __name__ == "__main__":
    main()
