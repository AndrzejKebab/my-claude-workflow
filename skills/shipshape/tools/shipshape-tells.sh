#!/usr/bin/env bash
# shipshape-tells: the mechanical LLM-tell battery over a C# tree.
# Reports per-category hit counts and locations; a hit is a flag for judgment,
# not an auto-fail (>=3 categories firing on one file is the strong signal).
# Usage: shipshape-tells.sh <dir> [--count-only]
set -euo pipefail

DIR="${1:?usage: shipshape-tells.sh <dir> [--count-only]}"
COUNT_ONLY="${2:-}"
RG=(rg --no-heading --line-number -g '*.cs' -g '!Samples~' -g '!Documentation~')

run_cat() {
    local id="$1" name="$2"; shift 2
    local out
    out="$("${RG[@]}" "$@" "$DIR" 2>/dev/null || true)"
    local n=0
    if [[ -n "$out" ]]; then
        n="$(wc -l <<<"$out")"
    fi
    echo "## T$id $name: $n"
    if [[ "$COUNT_ONLY" != "--count-only" && -n "$out" ]]; then
        head -20 <<<"$out" | sed 's/^/  /'
        if [[ "$n" -gt 20 ]]; then
            echo "  ... ($((n - 20)) more)"
        fi
    fi
}

echo "# shipshape tell battery — $DIR"
run_cat 1 "narration-verb comments" \
    -e '^\s*// (Get|Set|Check|Create|Initialize|Calculate|Compute|Update|Return|Call|Loop|Iterate|Now|First|Then|Finally|Add|Remove|Step [0-9])\b'
run_cat 2 "tautological xml docs" \
    -e '/// <summary>\s*(Gets or sets|Gets|Sets|Returns) the [a-z]+\s*\.?\s*</summary>'
run_cat 3 "marketing vocabulary in comments" \
    -e "//.*\b(robust|comprehensive|seamless|gracefully|effortless|powerful|elegant)\b" \
    -e "//.*(ensures? that|important to note|for clarity)"
run_cat 4 "emoji / glyphs in source" -e '[✅❌🚀⚠🎉✨🔥💡✓✗]'
run_cat 5 "blanket catch(Exception)" -e 'catch \(Exception\b' -e 'catch \(System\.Exception\b'
run_cat 6 "compatibility ghosts" -e '//.*(for (backward[s]? )?compat|kept for compat|legacy support)'
run_cat 7 "weak-noun new types" -e 'class \w+(Helper|Manager|Utils?|Handler|Processor|Wrapper)\b'
run_cat 8 "change-history comments" \
    -e '//.*( removed —| removed -|was deleted|deleted in |the old (code|path|form)|used to (be|do)|no longer)' \
    -e '//.*(Step [0-9]+ (of|in) |orchestration|session)'
run_cat 9 "redundant else-after-return" -U -e 'return [^;]*;\s*\n\s*\}\s*\n\s*else\b'
run_cat 10 "bare trailing // markers" -e ';\s*//\s*$'
# T11: references that resolve only against a non-shipping design/process artifact
# (chunk/phase labels, design-decision tags, design-section pointers). High-precision
# patterns — they do NOT match the legitimate upstream `REF/<file>:<line>` citations,
# nor a package abbreviation that merely contains "C<n>" (e.g. CC2D).
run_cat 11 "non-shipping design-doc references" \
    -e '\b(design (D[0-9]|§[0-9]|section [0-9])|chunk C[0-9]|motion-drive D[0-9])\b' \
    -e '\bC[0-9]-? ?contract\b' \
    -e '///?.*\([CD][0-9]\)' \
    -e '//.*\b[CD][0-9][ab]?\b (core|solve|chain|gate|seam|verdict|resolution|deliverable)'
