#!/usr/bin/env python
"""Run a Unity EditMode/PlayMode suite N times and record each run as its own evidence.

Programs started: the game repo's test runner, unity_procs.py.

An intermittent fix is not proven by one green run, and the failure mode of naive repetition is
worse than not running: a killed or crashed run leaves the PREVIOUS run's results XML in place, so
five runs can look like five passes when three never happened. This deletes the results file before
every run, records the run's own start time (UTC) and the results file's write time, and treats a
run with no fresh results file as "does not count".

Usage:
    python repeat_runs.py --project F:/Unity/Projects/VoxelGame-worker-5 --task worker-5 --runs 5
    python repeat_runs.py --project ... --task worker-5 --runs 3 --filter SectorIOSchedulerTests
    python repeat_runs.py --project ... --task worker-5 --runs 5 --watch IdleSectorsCloseTheirHandleAndTheNumberOpenIsCapped

Options
    --runs N        how many times to run the suite (default 5)
    --filter F      pass a test filter, e.g. "SectorIOSchedulerTests|SavedChunkReloadTests"
    --watch NAME    a test that must pass in every run; repeatable. Printed per run.
    --summary PATH  where to write the run log (default <project>/Logs/repeat-runs.txt)
    --log-dir PATH  where the per-run console logs go (default <project>/Logs)
    --platform P    EditMode (default) or PlayMode
    --stop-on-extra stop when a run fails on anything the first run did not fail on

Exit codes
    0  every run produced fresh results; 1  at least one run produced none.
"""

import argparse
import os
import re
import subprocess
import sys
import time

TARGET_RE = r'<test-case\b[^>]*fullname="([^"]+)"[^>]*result="Failed"'


def failing_cases(results_path):
    text = open(results_path, encoding="utf-8", errors="replace").read()
    return [match.group(1) for match in re.finditer(TARGET_RE, text)]


def verdict(results_path, name):
    text = open(results_path, encoding="utf-8", errors="replace").read()
    match = re.search(r'<test-case\b[^>]*fullname="[^"]*' + re.escape(name) + r'"[^>]*?result="(\w+)"',
                      text)
    return match.group(1) if match else "absent"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project", required=True, help="Unity project root of the worktree")
    parser.add_argument("--task", required=True, help="worktree task name, e.g. worker-5")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--platform", default="EditMode")
    parser.add_argument("--filter", default=None)
    parser.add_argument("--watch", action="append", default=[])
    parser.add_argument("--summary", default=None)
    parser.add_argument("--log-dir", default=None)
    parser.add_argument("--stop-on-extra", action="store_true")
    args = parser.parse_args()

    logs = args.log_dir or os.path.join(args.project, "Logs")
    summary_path = args.summary or os.path.join(logs, "repeat-runs.txt")
    results_path = os.path.join(logs, f"{args.platform}-results.xml")

    os.makedirs(logs, exist_ok=True)

    # Kill stray batch Editors from earlier attempts before the first run. A previous invocation that
    # was killed leaves its Unity child alive; two of them contend for the project lock and batchmode
    # then sits at ~0 CPU, which looks exactly like a slow suite.
    procs_tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unity_procs.py")
    if os.path.exists(procs_tool):
        subprocess.run([sys.executable, procs_tool, "kill", "--worktree", args.task,
                        "--batch-only", "--yes"], capture_output=True)

    lock_file = os.path.join(args.project, "Temp", "UnityLockfile")
    if os.path.exists(lock_file):
        os.remove(lock_file)

    first_failures = None
    clean_runs = 0

    with open(summary_path, "a", encoding="utf-8") as summary:
        for run in range(1, args.runs + 1):
            if os.path.exists(results_path):
                os.remove(results_path)

            started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            begin = time.time()

            command = [sys.executable, os.path.join(args.project, "tools/unity/agent_worktree.py"),
                       "test", args.task, "--platform", args.platform]
            if args.filter:
                command += ["--filter", args.filter]

            log_path = os.path.join(logs, f"repeat-{run}.txt")
            with open(log_path, "w", encoding="utf-8") as out:
                completed = subprocess.run(command, cwd=args.project, stdout=out, stderr=subprocess.STDOUT)

            elapsed = int(time.time() - begin)

            if not os.path.exists(results_path):
                summary.write(f"run {run}: NO RESULTS (exit {completed.returncode}, {elapsed} s) - "
                              f"does not count\n")
                summary.flush()
                continue

            written = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.path.getmtime(results_path)))
            text = open(results_path, encoding="utf-8", errors="replace").read()
            totals = re.search(r'total="(\d+)" passed="(\d+)" failed="(\d+)"', text)
            failures = failing_cases(results_path)

            line = (f"run {run}: started {started} written {written} {elapsed} s "
                    f"exit {completed.returncode} "
                    f"total={totals.group(1)} passed={totals.group(2)} failed={totals.group(3)}")
            for name in args.watch:
                line += f" | {name}={verdict(results_path, name)}"
            summary.write(line + "\n    failures: " + ", ".join(failures) + "\n")
            summary.flush()

            clean_runs += 1

            if first_failures is None:
                first_failures = set(failures)
            elif args.stop_on_extra:
                extra = set(failures) - first_failures
                if extra:
                    summary.write(f"stopping: run {run} failed on {sorted(extra)}, which the first run did not\n")
                    summary.flush()
                    break

    print(f"{clean_runs} run(s) with fresh results, log at {summary_path}")
    return 0 if clean_runs == args.runs else 1


if __name__ == "__main__":
    raise SystemExit(main())
