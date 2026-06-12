#!/usr/bin/env python3
"""shipshape-asmdef-graph: assembly-level dependency graph from .asmdef JSON.

Resolves GUID references via .asmdef.meta files found under the same roots,
prints an adjacency list plus a mermaid block, and flags cycles among the
scanned assemblies. Stdlib only.

Usage: shipshape-asmdef-graph.py <dir> [<dir>...]
"""

import json
import re
import sys
from pathlib import Path

EXCLUDES = {"Library", "obj", "bin", ".git", "Temp"}


def main():
    roots = [Path(d) for d in sys.argv[1:]] or [Path(".")]
    guid_to_name, asm = {}, {}
    for root in roots:
        for p in root.rglob("*.asmdef"):
            if any(part in EXCLUDES for part in p.parts):
                continue
            data = json.loads(p.read_text(encoding="utf-8-sig"))
            name = data.get("name", p.stem)
            asm[name] = {"path": str(p), "refs": data.get("references", [])}
            meta = Path(str(p) + ".meta")
            if meta.exists():
                m = re.search(r"guid:\s*([0-9a-f]{32})", meta.read_text())
                if m:
                    guid_to_name[m.group(1)] = name

    edges = {}
    for name, info in asm.items():
        resolved = []
        for r in info["refs"]:
            if r.startswith("GUID:"):
                resolved.append(guid_to_name.get(r[5:], r))
            else:
                resolved.append(r)
        edges[name] = resolved

    print("# asmdef graph")
    for name in sorted(edges):
        local = [r for r in edges[name] if r in asm]
        ext = [r for r in edges[name] if r not in asm]
        print(f"- **{name}** ({asm[name]['path']})")
        for r in local:
            print(f"  -> {r}")
        if ext:
            print(f"  external: {', '.join(sorted(ext))}")

    print("\n```mermaid\ngraph TD")
    for name in sorted(edges):
        for r in edges[name]:
            if r in asm:
                print(f'  {name.replace(".", "_")} --> {r.replace(".", "_")}')
    print("```")

    # cycle detection among scanned assemblies
    WHITE, GRAY, BLACK = 0, 1, 2
    color, cycles = {n: WHITE for n in asm}, []

    def dfs(n, stack):
        color[n] = GRAY
        for r in edges.get(n, []):
            if r not in asm:
                continue
            if color[r] == GRAY:
                cycles.append(stack[stack.index(r):] + [r] if r in stack else [n, r])
            elif color[r] == WHITE:
                dfs(r, stack + [r])
        color[n] = BLACK

    for n in asm:
        if color[n] == WHITE:
            dfs(n, [n])
    print(f"\ncycles: {len(cycles)}")
    for c in cycles:
        print("  " + " -> ".join(c))


if __name__ == "__main__":
    main()
