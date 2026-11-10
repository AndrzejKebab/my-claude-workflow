#!/usr/bin/env bash
# Run a Unity player under cdb so a native crash leaves a readable stack.
#
# Windows Error Reporting LocalDumps needs an elevated registry write, which a bot
# session does not have; attaching cdb needs nothing but the WinDbg package.
#
#   crash_capture.sh <player.exe> [args...]
#
# Writes <player>-crash-<timestamp>.log next to the exe (dumped with .logopen) and
# keeps the console output too. `-g` ignores the initial break, `-G` ignores the
# final one, so the player runs normally until it faults.

set -u
# spawns: cdbX64.exe, the given player
case "${1:-}" in -h|--help) sed -n '2,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac

CDB="${CDB:-$LOCALAPPDATA/Microsoft/WindowsApps/cdbX64.exe}"
if [ ! -x "$CDB" ]; then
    echo "cdb not found at $CDB — pass CDB=<path to cdbX64.exe>" >&2
    exit 2
fi

if [ "$#" -lt 1 ]; then
    echo "usage: crash_capture.sh <player.exe> [args...]" >&2
    exit 2
fi

EXE="$1"; shift
DIR="$(dirname "$EXE")"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$DIR/$(basename "${EXE%.exe}")-crash-$STAMP.log"

echo "running $EXE under cdb"
echo "stack log: $LOG"

"$CDB" -o -g -G \
    -c ".logopen \"$LOG\"; sxe -c \"kb; !analyze -v; q\" av; g" \
    "$EXE" "$@" 2>&1 | tee "$LOG.console"

echo
echo "if a crash happened, the stack is in: $LOG"
