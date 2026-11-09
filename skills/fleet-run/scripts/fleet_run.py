#!/usr/bin/env python3
"""Run a fleet tool so it cannot outlive its run, eat the box, or start programs in a loop.

    fleet_run.py [--deadline S] [--cap-gib N] [--tree-cap-gib N] [--storm-names a.exe,b.exe] [--tool NAME]
                 [--sweep-project PATH] [--data DIR] -- <command...>
    fleet_run.py stop (--all | --bot NAME | --pid N) [--data DIR]

The command and everything it starts run in one Windows Job Object that is killed whole when the run ends.
Every stop prints one fixed line, `[fleet_run] finished: ...` or `[fleet_run] stopped: <reason> ...`, and exits
with its own code: the command's own code when it finished, 124 deadline, 9 memory cap, 125 spawn storm,
143 stopped by owner. Each run is logged to <data>/runs.jsonl. Programs started: the given command.
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import psutil

EXIT = {'deadline': 124, 'memory cap': 9, 'spawn storm': 125, 'stopped by owner': 143}
STORM_NAMES = 'Unity.exe,Unity Hub.exe'  # the programs behind the Hub loop; builds start many other helpers


def default_data() -> Path:
    home = os.environ.get('HERMES_HOME')
    if home and Path(home).parent.name == 'profiles':
        return Path(home).parents[1] / 'fleet-watchdog'
    return Path(home or Path.home()) / 'fleet-watchdog'


def calling_bot() -> str:
    home = os.environ.get('HERMES_HOME') or ''
    return Path(home).name if Path(home).parent.name == 'profiles' else 'owner'


class Job:
    """A Windows Job Object that kills every process in it when closed or terminated."""

    def __init__(self):
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self.handle = self.kernel.CreateJobObjectW(None, None)

        class Basic(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', ctypes.c_int64), ('PerJobUserTimeLimit', ctypes.c_int64),
                        ('LimitFlags', wintypes.DWORD), ('MinimumWorkingSetSize', ctypes.c_size_t),
                        ('MaximumWorkingSetSize', ctypes.c_size_t), ('ActiveProcessLimit', wintypes.DWORD),
                        ('Affinity', ctypes.c_size_t), ('PriorityClass', wintypes.DWORD),
                        ('SchedulingClass', wintypes.DWORD)]

        class Io(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in ('a', 'b', 'c', 'd', 'e', 'f')]

        class Extended(ctypes.Structure):
            _fields_ = [('BasicLimitInformation', Basic), ('IoInfo', Io), ('ProcessMemoryLimit', ctypes.c_size_t),
                        ('JobMemoryLimit', ctypes.c_size_t), ('PeakProcessMemoryUsed', ctypes.c_size_t),
                        ('PeakJobMemoryUsed', ctypes.c_size_t)]

        limits = Extended()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # KILL_ON_JOB_CLOSE; no breakaway, so nothing escapes
        self.kernel.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits))

    def add(self, pid: int) -> None:
        process = self.kernel.OpenProcess(0x0001 | 0x0100, False, pid)  # TERMINATE | SET_QUOTA
        if process:
            self.kernel.AssignProcessToJobObject(self.handle, process)
            self.kernel.CloseHandle(process)

    def pids(self) -> list[int]:
        count = 4096

        class Listing(ctypes.Structure):
            _fields_ = [('Assigned', wintypes.DWORD), ('InList', wintypes.DWORD),
                        ('Ids', ctypes.c_size_t * count)]

        listing = Listing()
        if not self.kernel.QueryInformationJobObject(self.handle, 3, ctypes.byref(listing), ctypes.sizeof(listing),
                                                     None):
            return []
        return [int(listing.Ids[i]) for i in range(listing.InList)]

    def kill(self) -> None:
        self.kernel.TerminateJobObject(self.handle, 1)


def processes(job: Job | None, root: psutil.Process) -> list[psutil.Process]:
    if job is not None:
        found = []
        for pid in job.pids():
            try:
                found.append(psutil.Process(pid))
            except psutil.Error:
                pass
        return found
    try:
        return [root, *root.children(recursive=True)]
    except psutil.Error:
        return []


def sweep_project(project: str, started_after: float) -> list[int]:
    """Kill Unity processes on `project` started during this run: a killed shell does not always take its Editor."""
    killed = []
    for p in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            if (p.info['name'] or '').lower() != 'unity.exe' or p.info['create_time'] < started_after:
                continue
            if project.replace('\\', '/').lower() in ' '.join(p.info['cmdline'] or []).replace('\\', '/').lower():
                p.kill()
                killed.append(p.info['pid'])
        except psutil.Error:
            pass
    return killed


def stop_tree(job: Job | None, procs: list[psutil.Process]) -> None:
    if job is not None:
        job.kill()
    for proc in procs:
        try:
            proc.kill()
        except psutil.Error:
            pass
    psutil.wait_procs(procs, timeout=10)


def run(args, command: list[str]) -> int:
    data = Path(args.data) if args.data else default_data()
    (data / 'runs').mkdir(parents=True, exist_ok=True)
    record = data / 'runs' / f'{os.getpid()}.json'
    stop_file = record.with_suffix('.stop')
    bot, tool = calling_bot(), args.tool or Path(command[0]).name
    record.write_text(json.dumps({'pid': os.getpid(), 'bot': bot, 'tool': tool, 'started': time.time(),
                                  'command': ' '.join(command)[:300]}), encoding='utf-8')
    storm_names = {name.strip().lower() for name in args.storm_names.split(',') if name.strip()}
    started = time.time()
    job = Job() if os.name == 'nt' else None
    child = subprocess.Popen(command)
    if job is not None:
        job.add(child.pid)
    root = psutil.Process(child.pid)
    seen, starts = set(), []
    reason, detail, peak_tree, peak_box = '', '', 0.0, 0.0
    code = None
    try:
        # Bounded: --deadline ends the loop at the latest.
        while code is None:
            code = child.poll()
            if code is not None:
                break
            procs = processes(job, root)
            for proc in procs:
                if proc.pid not in seen:
                    seen.add(proc.pid)
                    try:
                        name = proc.name().lower()
                    except psutil.Error:
                        continue
                    if name in storm_names:
                        starts.append((time.time(), name))
            tree = sum(_rss(proc) for proc in procs) / 2**30
            box = psutil.virtual_memory().used / 2**30
            peak_tree, peak_box = max(peak_tree, tree), max(peak_box, box)
            recent = [name for at, name in starts if time.time() - at <= args.storm_window]
            storm = next((name for name in set(recent) if recent.count(name) > args.storm_count), '')
            if stop_file.exists():
                reason, detail = 'stopped by owner', 'fleet_run stop'
            elif time.time() - started > args.deadline:
                reason, detail = 'deadline', f'{args.deadline:.0f} s'
            elif tree > args.tree_cap_gib:
                reason, detail = 'memory cap', f'tree {tree:.1f} GiB > {args.tree_cap_gib:.1f}'
            elif box > args.cap_gib:
                reason, detail = 'memory cap', f'box {box:.1f} GiB > {args.cap_gib:.1f}'
            elif storm:
                reason, detail = 'spawn storm', f'{storm} started {recent.count(storm)} times in {args.storm_window:.0f} s'
            if reason:
                stop_tree(job, procs)
                code = EXIT[reason]
                break
            time.sleep(args.interval)
    finally:
        if job is not None and code is None:
            job.kill()
        duration = time.time() - started
        if reason:
            print(f'[fleet_run] stopped: {reason} ({detail}); exit {code}', flush=True)
        else:
            print(f'[fleet_run] finished: exit {code} in {duration:.0f} s', flush=True)
        print(f'[fleet_run] peak tree {peak_tree:.1f} GiB, peak box {peak_box:.1f} GiB', flush=True)
        if args.sweep_project:
            swept = sweep_project(args.sweep_project, started)
            print(f'[fleet_run] swept {len(swept)} orphan Unity process(es) on {args.sweep_project}', flush=True)
        if args.report_peak:
            Path(args.report_peak).write_text(json.dumps({'tree_gib': round(peak_tree, 1), 'box_gib': round(peak_box, 1),
                                                          'rule': detail or None, 'reason': reason or 'finished'}),
                                              encoding='utf-8')
        with open(data / 'runs.jsonl', 'a', encoding='utf-8') as handle:
            handle.write(json.dumps({'at': started, 'bot': bot, 'tool': tool, 'reason': reason or 'finished',
                                     'code': code, 'seconds': round(duration, 1), 'peak_tree_gib': round(peak_tree, 1)})
                         + '\n')
        for path in (record, stop_file):
            try:
                path.unlink()
            except OSError:
                pass
    return code if code is not None else 1


def _rss(proc: psutil.Process) -> int:
    try:
        return proc.memory_info().rss
    except psutil.Error:
        return 0


def stop(args) -> int:
    data = Path(args.data) if args.data else default_data()
    targets = []
    for path in sorted((data / 'runs').glob('*.json')):
        try:
            entry = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        if not psutil.pid_exists(entry.get('pid', -1)):
            path.unlink(missing_ok=True)  # a run that died without cleaning up
            continue
        if args.all or entry.get('bot') == args.bot or entry.get('pid') == args.pid:
            targets.append((path, entry))
    for path, entry in targets:
        path.with_suffix('.stop').write_text('stop', encoding='utf-8')
    print(f'stopping {len(targets)} run(s)' + ''.join(f'\n  {e["bot"]} {e["tool"]} (pid {e["pid"]})'
                                                      for _, e in targets))
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == 'stop':
        parser = argparse.ArgumentParser(prog='fleet_run.py stop', description='stop fleet_run runs')
        parser.add_argument('--data')
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true')
        group.add_argument('--bot')
        group.add_argument('--pid', type=int)
        return stop(parser.parse_args(sys.argv[2:]))
    parser = argparse.ArgumentParser(description=(__doc__ or '').splitlines()[0])
    parser.add_argument('--deadline', type=float, default=900.0, help='wall-clock seconds (default 900)')
    parser.add_argument('--cap-gib', type=float, default=34.0, help='whole box RAM (default 34)')
    parser.add_argument('--tree-cap-gib', type=float, default=12.0, help="the run's own processes (default 12)")
    parser.add_argument('--interval', type=float, default=1.0)
    parser.add_argument('--storm-names', default=STORM_NAMES, help=f'programs watched for a storm ({STORM_NAMES})')
    parser.add_argument('--storm-count', type=int, default=5)
    parser.add_argument('--storm-window', type=float, default=600.0)
    parser.add_argument('--sweep-project', help='after the run, kill Unity processes on this project it left')
    parser.add_argument('--report-peak', help='write the peaks and the stop reason to this JSON file')
    parser.add_argument('--tool', help='name logged for this run (default: the program)')
    parser.add_argument('--data', help='run registry and log folder (default: Hermes fleet-watchdog)')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command:
        parser.error('no command given: fleet_run.py [options] -- <command...>')
    return run(args, command)


if __name__ == '__main__':
    sys.exit(main())
