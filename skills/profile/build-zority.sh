#!/usr/bin/env bash
# Build a Development player for a zori_test_bed project via Unity batchmode.
# No live editor required — no unity-cli, no IPC, no delayCall.
#
# Usage: build-zority.sh <project>
#   project: one of zority_6_0 | zority_6_3 | zority_6_4
#            or an absolute path to the project directory.
#
# Promoted from the ad-hoc /tmp/build-zority-6-4.sh written during the
# fog-detail-perf Step 9 profile dispatch (2026-05-18). See:
#   docs/orchestrate/fog-detail-perf/06-profile-skill-update.md
#
# Entry point: Zori.TestBed.Editor.ProfileBuild.BuildDevelopmentLinux
# That static method must:
#   - read scenes from EditorBuildSettings,
#   - call BuildPipeline.BuildPlayer with StandaloneLinux64 +
#     BuildOptions.Development (+ ConnectToHost for profiler capture),
#   - on failure throw or call EditorApplication.Exit(1).
#
# -----------------------------------------------------------------------
# CRITICAL: NEVER pass -nographics to Unity batchmode in this testbed.
# CLAUDE.md §"Agentic mechanism: batchmode-first, no live editor" forbids it.
# -nographics caps RenderTexture resolution at 4096 and breaks GPU resource
# allocation during asset import and IL post-process.  The symptom is
# "RenderTexture.Create failed" during Library bake — the build then silently
# produces an unusable player.  Omit -nographics on ALL batchmode invocations:
# compile checks, tests, and player builds alike.
# -----------------------------------------------------------------------

set -uo pipefail
trap '' PIPE

TESTBED_ROOT=/mnt/archive4/UNITY/Projects/zori_test_bed

if [[ -z "${1:-}" ]]; then
  echo "Usage: build-zority.sh <zority_6_0|zority_6_3|zority_6_4|/abs/path>" >&2
  exit 1
fi

PROJECT="$1"
if [[ ! -d "$PROJECT" ]]; then
  PROJECT="$TESTBED_ROOT/$PROJECT"
fi
[[ -d "$PROJECT" ]] || { echo "ERROR: Project not found: $PROJECT" >&2; exit 1; }

LOG=/tmp/profile-build-$(basename "$PROJECT").log

echo "=== Development Build (batchmode) — $(basename "$PROJECT") ==="
echo "    Log: $LOG"

rm -f "$PROJECT/Temp/UnityLockfile"

# Lower FD soft limit to work around Mono NamedPipeServerStream FD-assertion
# (Unity 6000.4.x + corefx-bugfix asserts when accepted-socket FD exceeds
# cached _SC_OPEN_MAX). 8192 is plenty for asset import + IL post-process.
ulimit -n 8192

# DO NOT add -nographics — see header comment above.
unity "$PROJECT" \
  -batchmode -quit \
  -executeMethod Zori.TestBed.Editor.ProfileBuild.BuildDevelopmentLinux \
  -logFile - \
  > "$LOG" 2>&1
exit_code=$?

errs=$(grep -c 'error CS' "$LOG" || true)
echo "unity exit: $exit_code   error CS: $errs   log: $LOG"

if [[ $exit_code -ne 0 || $errs -gt 0 ]]; then
  echo "ERROR: build failed" >&2
  tail -30 "$LOG" >&2
  exit 1
fi

echo "=== Build Complete ==="
