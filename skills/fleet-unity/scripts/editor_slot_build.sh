#!/usr/bin/env bash
# Run ONE Unity Editor build method under the fleet's single-Editor rule, and leave no Editor behind.
# spawns: Unity.exe (the Editor, in batch mode), seat.py
#
# Why this exists: the owner's rule is one Unity Editor instance at a time, fleet-wide, and a script
# that opens one must close it on every exit path. The three ways an unattended build leaves an Editor
# alive are all handled here: the method throws, Unity exits without running -quit cleanly, or the
# build fails deep in a package callback (Entities content archives, for one) after the process has
# already lost its way.
#
# It also encodes the retry order that avoids wasting the slot: BUILD ONCE, and only if the failure was
# the content pipeline rather than C# does it retry - a second plain pass first (that clears a stale
# content-cache after a branch switch more often than not), and only then a reimport pass. Which one it
# took is printed, so the next run does not have to rediscover it.
#
#   editor_slot_build.sh --project <worktree> --method <Type.Method> [--log <path>]
#                        [--unity <Unity.exe>] [--no-retry] [--reimport-timeout MIN]
#
# A LICENCE failure is not retried. The cause is a SINGLE-SEAT Unity licence: a second Editor or build
# makes the first one's entitlement query return "0 entitlements" and it dies, taking the running build
# with it. Retrying therefore does not help - it either competes with whoever holds the seat or produces
# the same log again - so this exits 4 and names the seat, and the lane waits for a handover instead.
#
# Exit codes: 0 built, 1 failed after the permitted attempts, 2 usage/environment, 3 C# errors present,
# 4 licence/seat (not retryable - wait for the seat to be handed over).

set -u
# A player build needs the caller's Unity seat lease (skills/fleet-seat); 75 = try again once you hold it.
case "${1:-}" in -h|--help) ;; *) python "F:/Programowanie/my-claude-workflow/skills/fleet-seat/scripts/seat.py" check || exit 75 ;; esac

PROJECT=""
METHOD=""
LOG=""
UNITY="F:/Unity Editors/7000.0.0a12/Editor/Unity.exe"
RETRY=1
REIMPORT_TIMEOUT=25

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
  exit "${1:-2}"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --project) PROJECT="$2"; shift 2 ;;
    --method)  METHOD="$2";  shift 2 ;;
    --log)     LOG="$2";     shift 2 ;;
    --unity)   UNITY="$2";   shift 2 ;;
    --no-retry) RETRY=0;     shift ;;
    --reimport-timeout) REIMPORT_TIMEOUT="$2"; shift 2 ;;
    -h|--help) usage 0 ;;
    *) echo "unknown argument: $1" >&2; usage ;;
  esac
done

[ -n "$PROJECT" ] && [ -n "$METHOD" ] || usage
[ -x "$UNITY" ] || { echo "no Unity at $UNITY" >&2; exit 2; }
[ -d "$PROJECT" ] || { echo "no project at $PROJECT" >&2; exit 2; }
[ -n "$LOG" ] || LOG="$PROJECT/Logs/editor_slot_build.log"

mkdir -p "$(dirname "$LOG")"

# One Editor at a time, fleet-wide: refuse to start if another is already up. The owner did not allow
# silence about this, so say whose it might be rather than just the count.
#
# The Unity CLI's own auth broker is also called unity.exe (`--internal-auth-broker-serve`) and holds no
# licence; counting it made every run refuse at the gate with a single invisible process to blame.
# Hub ships its own CLI at `Unity Hub/resources/unity.exe` (`serve`) and that one holds no licence
# either - it is what Hub keeps alive once anything has used the CLI. Neither is an Editor.
busy() {
  powershell -NoProfile -Command \
    "(Get-CimInstance Win32_Process -Filter \"Name='Unity.exe'\" | Where-Object { \$_.CommandLine -notmatch '--internal-auth-broker-serve|--internal-|Unity Hub\\resources\\unity\.exe' } | Measure-Object).Count" 2>/dev/null | tr -d '\r'
}

before=$(busy)
if [ "${before:-0}" != "0" ]; then
  echo "REFUSING: $before Unity.exe already running. Single-seat Unity licence: one Editor or build at a time, fleet-wide - ask Manager for the seat." >&2
  exit 2
fi

# Kill any Editor that belongs to THIS project and is still alive after the run. Scoped to the project
# path so another worker's Editor is never touched.
reap() {
  powershell -NoProfile -Command \
    "Get-CimInstance Win32_Process -Filter \"Name='Unity.exe'\" | Where-Object { \$_.CommandLine -like '*$PROJECT*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force }" 2>/dev/null
  sleep 2
  powershell -NoProfile -Command \
    "(Get-CimInstance Win32_Process -Filter \"Name='Unity.exe'\" | Where-Object { \$_.CommandLine -like '*$PROJECT*' } | Measure-Object).Count" 2>/dev/null | tr -d '\r'
}

trap 'reap >/dev/null' EXIT INT TERM

run_build() { # $1 = label, $2 = extra editor arg ("" or "-reimportScripts" style)
  rm -f "$LOG"
  # shellcheck disable=SC2086
  "$UNITY" -quit -batchmode -nographics -projectPath "$PROJECT" \
           -executeMethod "$METHOD" -logFile "$LOG" $2 >/dev/null 2>&1
  local rc=$?
  echo "$1: exit $rc"
  return $rc
}

classify() { # prints the gate a failed log died at, empty when the log looks like a success
  if [ ! -f "$LOG" ]; then echo "no log written"; return; fi
  # A licence line is logged at Editor STARTUP even on a build that goes on to succeed, so presence of
  # the text is not a failure on its own. A build that finished is a build that finished: only look for
  # a gate when this log does not say so.
  if grep -qa "Build Finished, Result: Success" "$LOG"; then echo ""; return; fi
  if grep -qa "error CS" "$LOG"; then echo "csharp"; return; fi
  if grep -qa "BuildContentArchives failed" "$LOG"; then echo "content-archives"; return; fi
  if grep -qa "Failed to read the specified build profile" "$LOG"; then echo "missing-profile"; return; fi
  if grep -qa "another Unity instance\|already open" "$LOG"; then echo "editor-lock"; return; fi
  if grep -qa "0 free entitlements\|Access token is unavailable\|Found 0 entitlement groups" "$LOG"; then echo "licence"; return; fi
  echo ""
}

run_build "attempt 1" ""
rc=$?
gate=$(classify)
echo "gate: ${gate:-none}"

if [ $rc -eq 0 ] && [ -z "$gate" ]; then
  reap
  echo "result: built (exit 0), surviving editors: $(reap)"
  exit 0
fi

if [ "$gate" = "csharp" ]; then
  grep -a "error CS" "$LOG" | sort -u | head -8 >&2
  reap >/dev/null
  echo "result: failed on C# (exit 3), surviving editors: $(reap)" >&2
  exit 3
fi

# Not retryable: a signed-out Hub produces the same log every time, and Manager's rule is to stop and
# report it rather than retry into it.
if [ "$gate" = "licence" ]; then
  grep -a "0 free entitlements\|Access token is unavailable" "$LOG" | tail -2 >&2
  reap >/dev/null
  echo "result: LICENCE failure, not retried (exit 4) - re-sign the Hub, then rerun. surviving editors: $(reap)" >&2
  exit 4
fi

if [ "$RETRY" = "0" ]; then
  reap >/dev/null
  echo "result: failed at gate '${gate:-unknown}' with retry disabled, surviving editors: $(reap)" >&2
  exit 1
fi

# Retry ONCE with a plain pass before spending the slot on a reimport: a stale content cache after a
# branch switch clears on the second try often enough that Manager asked for this order explicitly.
run_build "attempt 2 (plain retry)" ""
rc=$?
gate=$(classify)

if [ $rc -eq 0 ] && [ -z "$gate" ]; then
  echo "result: built on attempt 2 (plain retry cleared it), surviving editors: $(reap)"
  exit 0
fi

if [ "$gate" = "csharp" ]; then
  grep -a "error CS" "$LOG" | sort -u | head -8 >&2
  reap >/dev/null
  echo "result: failed on C# (exit 3), surviving editors: $(reap)" >&2
  exit 3
fi

if [ "$gate" = "licence" ]; then
  grep -a "0 free entitlements\|Access token is unavailable" "$LOG" | tail -2 >&2
  reap >/dev/null
  echo "result: LICENCE failure on attempt 2, not retried (exit 4) - re-sign the Hub. surviving editors: $(reap)" >&2
  exit 4
fi

echo "attempt 2 failed at gate '${gate:-unknown}'; doing the reimport pass"

# Reimport pass: open the project long enough to rebuild the Library, then build again.
timeout "$((REIMPORT_TIMEOUT * 60))" "$UNITY" -quit -batchmode -nographics -projectPath "$PROJECT" \
        -logFile "$PROJECT/Logs/editor_slot_reimport.log" >/dev/null 2>&1
echo "reimport: exit $?"
reap >/dev/null

run_build "attempt 3 (after reimport)" ""
rc=$?
gate=$(classify)
survivors=$(reap)

if [ $rc -eq 0 ] && [ -z "$gate" ]; then
  echo "result: built on attempt 3 (after reimport), surviving editors: $survivors"
  exit 0
fi

echo "result: failed at gate '${gate:-unknown}' after retry and reimport, surviving editors: $survivors" >&2
exit 1
