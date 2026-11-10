#!/usr/bin/env python3
"""Check an approvals.deny glob list against commands that must be blocked and commands that must pass.

Uses Hermes's own matcher (tools.approval_floors._match_user_deny_rule) with HERMES_HOME pointed at a
profile, so the answer is what the agent's terminal will actually do - not a reimplementation.

Usage (run with the hermes-agent venv python, from hermes-agent/):
  deny_check.py --profile <profile-dir> [--cases <file>]
  deny_check.py --guard --cases <file>    # which commands the dangerous-command guard flags (refused in headless turns)
Cases file: one command per line, prefixed `BLOCK ` or `ALLOW `. Default cases cover the owner's rule:
agents never open, close or relaunch an Editor (nor start Hub); the Unity CLI itself stays allowed. Exit 0 when every case behaves, 1 otherwise.
"""
import argparse
import os
import sys

DEFAULT_CASES = r'''
BLOCK "F:/Unity Editors/7000.0.0a12/Editor/Unity.exe" -batchmode -projectPath x -quit
BLOCK cd x && "F:/Unity Editors/7000.0.0a12/Editor/Unity.exe" -projectPath y
BLOCK nohup "F:/Unity Editors/7000.0.0a12/Editor/Unity.exe" -projectPath y &
BLOCK "$UNITY_EDITOR" -projectPath y
BLOCK powershell -Command "Start-Process 'F:/Unity Editors/7000.0.0a12/Editor/Unity.exe'"
BLOCK unity open F:/Unity/Projects/VoxelGame-worker-1
BLOCK "$UNITY" open "$WORKTREE"
BLOCK "$LOCALAPPDATA/Unity/bin/unity.exe" close F:/Unity/Projects/VoxelGame-worker-1
BLOCK unity command editor.quit --project-path x
BLOCK start "" "C:/Program Files/Unity Hub/Unity Hub.exe"
BLOCK python tools/unity/agent_worktree.py compile worker-1
BLOCK python tools/unity/agent_worktree.py test worker-1 --platform EditMode
BLOCK python tools/build_player.py --profile x
BLOCK bash tools/host_save_and_probe.sh --save x
BLOCK ./tools/mirror_lag_sample.sh 60
BLOCK bash bot-tools/unity/editor_slot_build.sh --method X
BLOCK bash bot-tools/unity/join_verify.sh
BLOCK bash -x tools/host_save_and_probe.sh
ALLOW unity status
ALLOW "$LOCALAPPDATA/Unity/bin/unity.exe" status
ALLOW "$UNITY" command script eval_file --project-path x a.cs
ALLOW unity command script eval_file --project-path x a.cs
ALLOW unity command editor.playmode start --project-path x
ALLOW unity cmd --runtime-path Builds/Benchmark/Client eval --code "return true;"
ALLOW bash tools/run_stress_flight.sh
ALLOW bash bot-tools/perf/latency-pass.sh
ALLOW git status
ALLOW gh pr view 392
ALLOW python bot-tools/unity/unity_procs.py ps
ALLOW python tools/unity/agent_worktree.py list
ALLOW grep -c "error CS" Logs/Editor.log
ALLOW grep -n Unity.exe tools/host_save_and_probe.sh
ALLOW python bot-tools/lint/loop_guard.py tools/mirror_lag_sample.sh
ALLOW git diff tools/host_save_and_probe.sh
ALLOW sed -n 1,40p tools/mirror_lag_sample.sh
ALLOW bash -n tools/host_save_and_probe.sh
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--profile')
    parser.add_argument('--cases')
    parser.add_argument('--guard', action='store_true',
                        help='check the dangerous-command guard instead of approvals.deny (BLOCK = flagged)')
    args = parser.parse_args()
    if not args.guard and not args.profile:
        parser.error('--profile is required unless --guard')

    if args.profile:
        os.environ['HERMES_HOME'] = args.profile
    sys.path.insert(0, os.getcwd())
    if args.guard:
        from tools.approval_detection import detect_dangerous_command, detect_hardline_command

        def check(command):
            hard = detect_hardline_command(command)
            if hard and hard[0]:
                return f'hardline: {hard[1]}'
            return detect_dangerous_command(command)[1]
    else:
        from tools.approval_floors import _match_user_deny_rule as check

    text = open(args.cases, encoding='utf-8').read() if args.cases else DEFAULT_CASES
    bad = 0
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw:
            continue
        want, command = raw.split(' ', 1)
        hit = check(command)
        got = 'BLOCK' if hit else 'ALLOW'
        ok = got == want
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} want {want} got {got} {('[' + hit + ']') if hit else ''} | {command[:90]}")
    print(f'deny_check: {bad} wrong')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
