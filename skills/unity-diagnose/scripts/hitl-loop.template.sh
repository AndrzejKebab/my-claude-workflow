#!/usr/bin/env bash
# Human-in-the-loop reproduction loop — Unity flavor.
# Copy this file, edit the steps below, and run it.
# The agent runs the script; the user follows prompts in their terminal.
# Last resort: use only when the bug needs a human hand (device builds,
# feel-dependent bugs, editor interactions that can't be scripted).
#
# Usage:
#   bash hitl-loop.template.sh
#
# Two helpers:
#   step "<instruction>"          → show instruction, wait for Enter
#   capture VAR "<question>"      → show question, read response into VAR
#
# At the end, captured values are printed as KEY=VALUE for the agent to parse.
# Tip: point the user at the log they should watch —
#   Editor:  Editor.log  (Help > Open Editor Log / ~/Library/Logs/Unity or %LOCALAPPDATA%\Unity\Editor)
#   Player:  Player.log next to the build, or adb logcat -s Unity for Android.

set -euo pipefail

step() {
  printf '\n>>> %s\n' "$1"
  read -r -p "    [Enter when done] " _
}

capture() {
  local var="$1" question="$2" answer
  printf '\n>>> %s\n' "$question"
  read -r -p "    > " answer
  printf -v "$var" '%s' "$answer"
}

# --- edit below ---------------------------------------------------------

step "Open the project in Unity and load the scene Assets/_Prototypes/repro/Repro.unity."

step "Enter play mode and perform the trigger: place a blueprint, then save and reload within the same second."

capture REPRODUCED "Did the bug occur (wrong voxels / exception in Console)? (y/n)"

capture ERROR_MSG "Paste the first Console error line with [stack top] (or 'none'):"

capture FRAME_NOTE "If it was a perf hiccup: paste the worst frame ms from the Profiler (or 'n/a'):"

# --- edit above ---------------------------------------------------------

printf '\n--- Captured ---\n'
printf 'REPRODUCED=%s\n' "$REPRODUCED"
printf 'ERROR_MSG=%s\n' "$ERROR_MSG"
printf 'FRAME_NOTE=%s\n' "$FRAME_NOTE"
