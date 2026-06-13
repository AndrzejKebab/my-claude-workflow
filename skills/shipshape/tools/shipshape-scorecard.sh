#!/usr/bin/env bash
# shipshape-scorecard: before/after metric battery between two revisions.
# Materializes each revision into a temp worktree, csharpier-normalizes both
# copies (so line-packing never counts as LOC reduction), then diffs the
# metrics, the tell battery, and the public API surface (grep-level: public
# type/member signature lines). Statement count moving opposite to LOC is
# called out as suspected golfing.
# Usage: shipshape-scorecard.sh <repo> <base-ref> <head-ref> [subdir]
set -euo pipefail

REPO="${1:?usage: shipshape-scorecard.sh <repo> <base-ref> <head-ref> [subdir]}"
BASE="${2:?base ref}"
HEAD_REF="${3:?head ref}"
SUBDIR="${4:-.}"
TOOLS="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="$(mktemp -d /tmp/shipshape-scorecard.XXXXXX)"
trap 'git -C "$REPO" worktree remove --force "$WORK/base" 2>/dev/null; git -C "$REPO" worktree remove --force "$WORK/head" 2>/dev/null; rm -rf "$WORK"' EXIT

git -C "$REPO" worktree add --detach "$WORK/base" "$BASE" >/dev/null
git -C "$REPO" worktree add --detach "$WORK/head" "$HEAD_REF" >/dev/null

# Normalize both revisions with the SAME csharpier config, else a base lacking
# a .csharpierrc reflows at a different print width than a config-bearing head
# and the LOC delta becomes a formatter artifact (observed: a phantom -3089).
# The head revision's config is authoritative; copy it over the base.
for cfg in .csharpierrc .csharpierrc.yaml .csharpierrc.json .editorconfig; do
    [ -f "$WORK/head/$cfg" ] && cp "$WORK/head/$cfg" "$WORK/base/$cfg"
done

normalize() {
    if command -v csharpier >/dev/null 2>&1; then
        (cd "$1" && csharpier format . >/dev/null 2>&1) || echo "warn: csharpier failed in $1" >&2
    else
        echo "warn: csharpier not on PATH — counting unnormalized sources" >&2
    fi
}
normalize "$WORK/base/$SUBDIR"
normalize "$WORK/head/$SUBDIR"

api_surface() {
    rg --no-heading --no-line-number -g '*.cs' -g '!Samples~' -g '!*Tests*' \
        -e '^\s*(\[[^\]]*\]\s*)*public\s+(static\s+|sealed\s+|abstract\s+|partial\s+|readonly\s+|unsafe\s+)*(class|struct|interface|enum|delegate|event|const)?\s*[^={]+' "$1" 2>/dev/null \
        | sed 's/^[^:]*://' | sed 's/^\s*//;s/\s*$//' | sort | uniq
}

python3 "$TOOLS/shipshape-metrics.py" "$WORK/base/$SUBDIR" --json "$WORK/base.json" >"$WORK/base-metrics.md"
python3 "$TOOLS/shipshape-metrics.py" "$WORK/head/$SUBDIR" --json "$WORK/head.json" >"$WORK/head-metrics.md"
bash "$TOOLS/shipshape-tells.sh" "$WORK/base/$SUBDIR" --count-only >"$WORK/base-tells.md"
bash "$TOOLS/shipshape-tells.sh" "$WORK/head/$SUBDIR" --count-only >"$WORK/head-tells.md"
api_surface "$WORK/base/$SUBDIR" >"$WORK/base-api.txt"
api_surface "$WORK/head/$SUBDIR" >"$WORK/head-api.txt"

echo "# shipshape scorecard — $REPO ($BASE -> $HEAD_REF, scope: $SUBDIR)"
echo
echo "## Soft battery (csharpier-normalized)"
python3 - "$WORK/base.json" "$WORK/head.json" <<'PY'
import json, sys
b, h = (json.load(open(p)) for p in sys.argv[1:3])
rows = [
    ("code LOC", b["totals"]["code"], h["totals"]["code"]),
    ("statements", b["totals"]["statements"], h["totals"]["statements"]),
    ("// comments", b["totals"]["comment"], h["totals"]["comment"]),
    ("/// xmldoc", b["totals"]["xmldoc"], h["totals"]["xmldoc"]),
    ("comment density %", b["density_pct"], h["density_pct"]),
    ("method p50", b["p50"], h["p50"]),
    ("method p95", b["p95"], h["p95"]),
    ("method max", b["max"], h["max"]),
    ("narration hits", b["narration_hits"], h["narration_hits"]),
    ("trailing // markers", b["totals"]["trailing_markers"], h["totals"]["trailing_markers"]),
]
print("| metric | base | head | delta |")
print("|---|---|---|---|")
for name, bv, hv in rows:
    print(f"| {name} | {bv} | {hv} | {round(hv - bv, 2):+} |")
dl, ds = h["totals"]["code"] - b["totals"]["code"], h["totals"]["statements"] - b["totals"]["statements"]
if dl < 0 and ds > 0:
    print("\n**WARNING: LOC down but statements up — suspected line-packing/golfing.**")
# The band rule is about in-body // narration, not /// xmldoc (public-API docs
# count toward the healthy side per STYLE). Band-check inline density only.
inline = h["totals"]["comment"] / max(1, h["totals"]["comment"] + h["totals"]["code"]) * 100
band = 5 <= inline <= 20
print(f"\ninline // density (band rule): {inline:.1f}% — {'inside' if band else 'OUTSIDE'} 5-20% band")
print(f"total comment density (incl. /// xmldoc, FYI): {h['density_pct']}%")
PY
echo
echo "## Tell battery (hit counts, base -> head)"
python3 - "$WORK/base-tells.md" "$WORK/head-tells.md" <<'PY'
import re, sys
def counts(p):
    out = {}
    for line in open(p):
        m = re.match(r"## (T\d+ .*): (\d+)$", line.strip())
        if m:
            out[m.group(1)] = int(m.group(2))
    return out
b, h = counts(sys.argv[1]), counts(sys.argv[2])
print("| tell | base | head | delta |")
print("|---|---|---|---|")
for k in b:
    print(f"| {k} | {b[k]} | {h.get(k, 0)} | {h.get(k, 0) - b[k]:+} |")
new = [k for k in b if h.get(k, 0) > b[k]]
if new:
    print(f"\n**WARNING: new tell hits in: {', '.join(new)}**")
PY
echo
echo "## Public API surface"
if diff -q "$WORK/base-api.txt" "$WORK/head-api.txt" >/dev/null; then
    echo "unchanged ($(wc -l <"$WORK/head-api.txt") public signature lines)"
else
    echo '```diff'
    diff -u "$WORK/base-api.txt" "$WORK/head-api.txt" | head -80
    echo '```'
    echo "**API surface differs — every line above must be declared intentional.**"
fi
echo
echo "## Moved-line ratio (refactor honesty)"
git -C "$REPO" diff --color-moved=zebra --stat "$BASE..$HEAD_REF" -- "$SUBDIR" | tail -3
