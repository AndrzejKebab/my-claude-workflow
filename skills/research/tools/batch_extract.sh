#!/usr/bin/env bash
#
# Pass-1 batch runner for /research: extract many PDFs sequentially, survive a
# contended GPU, and resume safely after a kill.
#
# Pass 1 is hard-serial (marker/surya own the GPU) and GPU-only by policy
# (marker_extract._require_marker_gpu). This runner exists because the naive
# loop fails in three ways that all look like success:
#
#   1. The policy gate samples free VRAM ONCE, before torch imports. A batch
#      passes it and then OOMs on a later paper when another process spikes.
#      Fix: poll for headroom well above the 3 GiB gate before each paper.
#   2. `extract_research.py` without --force writes a `<slug>.regen-*.md`
#      sidecar instead of erroring, so a re-run reads as success while the
#      canonical file is untouched. Fix: skip slugs already extracted.
#   3. A resume guard keyed on `<slug>.md` short-circuits EVERY later step for
#      that paper, including the source archive. Kill a run between a paper's
#      extraction and its `cp` and the resumed run skips the archive forever.
#      Fix: archive in its own idempotent pass, and verify at the end.
#
# NEVER "fix" a VRAM shortfall by setting CUDA_VISIBLE_DEVICES="". The policy
# rejects it and forbids the PyMuPDF fallback, by deliberate choice: a silent
# CPU downgrade reads downstream as "marker worked but produced poor output".
#
# Usage:
#   batch_extract.sh MANIFEST
#
# MANIFEST is a text file of `<pdf-path> <canonical-slug>` pairs, one per line;
# blank lines and `#` comments ignored. Run detached, since a large batch takes
# tens of minutes and a sub-agent that returns kills its own background jobs:
#
#   setsid nohup batch_extract.sh papers.txt > batch.log 2>&1 < /dev/null &
#
set -u

MANIFEST="${1:?usage: batch_extract.sh MANIFEST}"
SKILL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RESEARCH_ROOT="${RESEARCH_ROOT:-F:/Programowanie/my-claude-workflow/research-library}"
PREP="$RESEARCH_ROOT/Prepared"
ARC="$RESEARCH_ROOT"
VRAM_BAR="${VRAM_BAR:-6000}"   # MiB free required to start a paper; gate itself needs 3072
ATTEMPTS="${ATTEMPTS:-3}"

[ -r "$MANIFEST" ] || { echo "manifest not readable: $MANIFEST" >&2; exit 2; }
command -v uv >/dev/null || { echo "uv is required" >&2; exit 2; }

# The marker LLM tier reads CLAUDE_API_KEY; the session shell does not export it.
# Without this the run degrades silently to marker-without-LLM (HTTP 401 per processor).
if [ -r "$HOME/.envrc" ]; then set -a; . "$HOME/.envrc"; set +a; fi
[ -n "${CLAUDE_API_KEY:-}${ANTHROPIC_API_KEY:-}" ] || echo "WARNING: no CLAUDE_API_KEY — marker LLM cleanup will 401 and degrade silently" >&2
unset CUDA_VISIBLE_DEVICES

free_mib() { nvidia-smi --query-gpu=memory.free --format=csv,nounits,noheader 2>/dev/null | sort -n | head -1; }

wait_vram() {
  for _ in $(seq 1 60); do
    f=$(free_mib)
    [ -n "$f" ] || { echo "  nvidia-smi unavailable"; return 1; }
    [ "$f" -ge "$VRAM_BAR" ] && return 0
    echo "  waiting for VRAM: ${f} MiB free < ${VRAM_BAR} MiB"
    sleep 20
  done
  return 1
}

extract() {  # $1=pdf path  $2=slug
  if [ -s "$PREP/$2.md" ]; then echo "════ $2 ════ SKIP (already extracted)"; return 0; fi
  for a in $(seq 1 "$ATTEMPTS"); do
    echo "════ $2 ════ attempt $a $(date +%T)"
    wait_vram || { echo "RESULT $2: BLOCKED on VRAM"; return 1; }
    uv run --project "$SKILL" python "$SKILL/tools/extract_research.py" "$1" --slug="$2" 2>&1 | grep -vE '^\s*$|it/s\]|%\|' | tail -20
    if [ -s "$PREP/$2.md" ]; then
      uv run --project "$SKILL" python "$SKILL/tools/cleanup_research.py" --only="$2" 2>&1 | tail -3
      echo "RESULT $2: OK | lines: $(wc -l < "$PREP/$2.md") | pngs: $(find "$PREP/assets/$2" -name '*.png' 2>/dev/null | wc -l) | marker: $([ -f "$PREP/assets/$2/marker.md" ] && echo yes || echo NO-FALLBACK)"
      return 0
    fi
    [ "$a" -lt "$ATTEMPTS" ] && { echo "  attempt $a produced no markdown; backing off"; sleep 30; }
  done
  echo "RESULT $2: FAILED after $ATTEMPTS attempts"
  return 1
}

# Pass 1 — extract, strictly one at a time.
while read -r pdf slug; do
  case "${pdf:-}" in ''|'#'*) continue;; esac
  [ -n "${slug:-}" ] || { echo "manifest line missing slug: $pdf" >&2; continue; }
  extract "$pdf" "$slug"
done < "$MANIFEST"

# Pass 2 — archive sources. Separate and idempotent on purpose: folding this into
# the loop above is what lets a mid-run kill lose a paper's archive silently.
echo "════ ARCHIVE ════"
while read -r pdf slug; do
  case "${pdf:-}" in ''|'#'*) continue;; esac
  [ -f "$ARC/$slug.pdf" ] || { cp "$pdf" "$ARC/$slug.pdf" && echo "  archived $slug"; }
done < "$MANIFEST"

# Pass 3 — verify. An extraction that produced markdown but no archived source is
# a corpus entry whose `source:` will dangle once staging is cleaned up.
echo "════ VERIFY ════"
rc=0
while read -r pdf slug; do
  case "${pdf:-}" in ''|'#'*) continue;; esac
  [ -s "$PREP/$slug.md" ] || { echo "  MISSING markdown: $slug"; rc=1; }
  [ -f "$ARC/$slug.pdf" ]  || { echo "  MISSING archive:  $slug"; rc=1; }
  [ -f "$PREP/assets/$slug/marker.md" ] || echo "  WARNING no marker cache (degraded extraction?): $slug"
done < "$MANIFEST"
[ "$rc" -eq 0 ] && echo "  all entries have markdown + archived source"
echo "════ BATCH COMPLETE $(date +%T) ════"
exit "$rc"
