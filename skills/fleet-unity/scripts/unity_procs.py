#!/usr/bin/env python3
"""Inspect and clean up Unity/player processes and memory on the VoxelGame box.

Why this exists: `tasklist //FI` is rejected by the agent shells (MSYS path conversion is off)
and returns nothing, so an "is anything running?" check silently reports zero. This reads
process data directly and matches Unity editors to their worktree by command line, which is
the only reliable ownership test on a box shared by several lanes.

Commands
    mem                      physical memory and commit, in GiB
    list                     Unity editors, import workers, players, and who owns them
    players                  only VoxelGame players/servers, with exe path and start time
    busy --worktree <dir>    sample CPU per editor; ~0 means stalled, not thinking
    kill --worktree <dir>    kill every process whose command line or exe holds <dir>
    kill --pid <pid> ...     kill specific pids, after printing what they are

Examples
    python unity_procs.py mem
    python unity_procs.py list --worktree VoxelGame-worker-4
    python unity_procs.py busy --worktree VoxelGame-worker-4
    python unity_procs.py kill --worktree VoxelGame-worker-4 --batch-only --yes

Exit codes
    0  fine; 1  nothing matched or a refusal; 2  bad arguments.

Notes
    A batchmode editor started with `-projectPath VoxelGame-worker-<N>` carries the RELATIVE
    name, so a search for the absolute path misses it. Match on the folder name.
"""

import argparse
import datetime
import re
import sys
import time

try:
    import psutil
except ImportError:
    sys.exit("psutil is required: pip install psutil")

EDITOR = "unity.exe"
PLAYER = ("voxelgame.exe", "voxelgameserver.exe", "voxelgame_server.exe")


def fmt_time(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%H:%M")


def owner_of(cmdline, exe):
    text = " ".join(cmdline or []) + " " + (exe or "")
    m = re.search(r"VoxelGame-worker-(\d+)", text)
    if m:
        return "w" + m.group(1)
    if re.search(r"Projects[\\/]VoxelGame(\W|$)", text):
        return "main"
    return "?"


def iter_unity():
    for p in psutil.process_iter(["name", "cmdline", "exe", "create_time", "memory_info"]):
        name = (p.info["name"] or "").lower()
        if name == EDITOR or name in PLAYER:
            # The Unity CLI's own broker (unity.exe --internal-auth-broker-serve) shares the
            # exe name and holds no licence; counting it made a free seat look taken.
            text = " ".join(p.info["cmdline"] or [])
            if "--internal-" in text:
                continue
            yield p


def cmd_mem(args):
    """One sample, or a bounded series that reports the PEAK.

    A single reading cannot answer "did we run out of memory": the spike that
    matters is the one between two commands. `mem --samples 60 --every 2`
    covers two minutes and prints the peak, so a run can carry its own memory
    evidence instead of a later argument about what was running.
    """
    samples = getattr(args, "samples", 0) or 0
    every = getattr(args, "every", 5) or 5
    peak = {"used": 0.0, "commit": 0.0, "time": ""}

    def sample(record):
        vm = psutil.virtual_memory()
        sm = psutil.swap_memory()
        used = vm.used / 2**30
        commit = (vm.used + sm.used) / 2**30
        if record and used > peak["used"]:
            peak.update(used=used, commit=commit, time=datetime.datetime.now().strftime("%H:%M:%S"))
        print("ram used/total GiB %.1f %.1f avail %.1f" % (used, vm.total / 2**30, vm.available / 2**30))
        print("commit approx GiB %.1f of %.1f" % (commit, (vm.total + sm.total) / 2**30))

    sample(False)
    if samples:
        for i in range(samples):  # bounded: --samples decides the count
            time.sleep(every)
            vm = psutil.virtual_memory()
            used = vm.used / 2**30
            commit = (vm.used + psutil.swap_memory().used) / 2**30
            if used > peak["used"]:
                peak.update(used=used, commit=commit, time=datetime.datetime.now().strftime("%H:%M:%S"))
            print("%s  sample %d/%d  used %.1f  commit %.1f  avail %.1f" % (
                datetime.datetime.now().strftime("%H:%M:%S"), i + 1, samples, used, commit, vm.available / 2**30))
        print("peak used %.1f GiB, commit %.1f GiB at %s" % (peak["used"], peak["commit"], peak["time"]))
        top = sorted(iter_unity(), key=lambda p: p.info["memory_info"].rss, reverse=True)[:5]
        for p in top:
            print("  %-14s %6d %5.2f GiB %s" % (p.info["name"], p.pid,
                                                p.info["memory_info"].rss / 2**30, owner_of(p.info["cmdline"], p.info["exe"])))
    return 0


def cmd_list(args):
    rows = []
    for p in iter_unity():
        exe = (p.info["exe"] or "").lower()
        who = owner_of(p.info["cmdline"], p.info["exe"])
        if args.worktree and args.worktree.lower() not in exe and args.worktree.lower() not in " ".join(p.info["cmdline"] or []).lower():
            continue
        rows.append(("%-8s %-14s %6d %5s %5.2f %s" % (
            who, p.info["name"], p.pid, fmt_time(p.info["create_time"]),
            p.info["memory_info"].rss / 2**30, (p.info["exe"] or "")[-60:])))
    for row in sorted(rows):
        print(row)
    if not rows:
        print("no Unity or player processes matched")
        return 1
    return 0


def cmd_players(args):
    rows = []
    for p in iter_unity():
        if (p.info["name"] or "").lower() not in PLAYER:
            continue
        exe = p.info["exe"] or ""
        if args.worktree and args.worktree.lower() not in exe.lower():
            continue
        rows.append("%-8s %6d %5s %s" % (owner_of(p.info["cmdline"], exe), p.pid,
                                         fmt_time(p.info["create_time"]), exe))
    for row in sorted(rows):
        print(row)
    if not rows:
        print("no players matched")
        return 1
    return 0


def cmd_busy(args):
    editors = []
    needle = (args.worktree or "").lower()
    for p in iter_unity():
        if (p.info["name"] or "").lower() != EDITOR:
            continue
        text = (" ".join(p.info["cmdline"] or []) + " " + (p.info["exe"] or "")).lower()
        if needle and needle not in text:
            continue
        editors.append((p, "-batchmode" in text))
    if not editors:
        print("no Unity editor matched")
        return 1

    def tree_cpu(p):
        # A batch build idles the Editor process while bee_backend, dotnet and the
        # import workers do the work, so counting only Unity.exe reports 0 CPU/s on
        # a build that is running perfectly well.
        total = 0.0
        for q in [p] + p.children(recursive=True):
            try:
                t = q.cpu_times()
                total += t.user + t.system
            except psutil.Error:
                pass
        return total

    before = {p.pid: tree_cpu(p) for p, _ in editors}
    time.sleep(args.seconds)
    print("%-12s %6s %8s %8s %7s" % ("mode", "pid", "cpu/s", "tree", "threads"))
    for p, batch in editors:
        try:
            spent = tree_cpu(p) - before[p.pid]
        except psutil.Error:
            print("%-12s %6d gone while sampling" % ("batch" if batch else "interactive", p.pid))
            continue
        rate = spent / args.seconds
        age_min = (time.time() - p.create_time()) / 60.0
        stalled = rate < 0.2
        if stalled and age_min < 30:
            verdict = " (idle under %d min: a batch build can idle here, wait before calling it stuck)" % int(age_min)
        elif stalled:
            verdict = " (stalled: ~0 CPU across the whole tree after %d min)" % int(age_min)
        else:
            verdict = ""
        print("%-12s %6d %8.2f %8.2f %7d%s" % (
            "batch" if batch else "interactive", p.pid, rate, rate, p.num_threads(), verdict))
    return 0


MAIN_CLONE_MARKERS = ("projects/voxelgame ", "projects/voxelgame\\", "projects\\voxelgame ",
                      "projects\\voxelgame\\", "projects/voxelgame\"", "projects\\voxelgame\"")


def is_main_clone(text):
    """True when a process belongs to the owner's/Reviewer's main clone rather than a worktree."""
    t = (text or "").lower().replace("\\\\", "\\")
    if "voxelgame-worker-" in t or "voxelgame-manager" in t:
        return False
    return "projects/voxelgame" in t or "projects\\voxelgame" in t


def _describe(p):
    try:
        return ((" ".join(p.cmdline()) if p.cmdline() else "") + " " + (p.exe() or ""))
    except psutil.Error:
        return ""


def cmd_ps(args):
    """Every Unity process with its full command line and which worktree it belongs to."""
    rows = 0
    needle = (args.worktree or "").lower()
    for p in psutil.process_iter(["pid", "name", "cmdline", "exe"]):
        name = (p.info["name"] or "").lower()
        if name not in (EDITOR, "voxelgame.exe"):
            continue
        text = " ".join(p.info["cmdline"] or [])
        if needle and needle not in text.lower():
            continue
        where = "main" if is_main_clone(text) else (owner_of(p.info["cmdline"], p.info["exe"]) or "?")
        print("%-6s %6d %-8s %s" % (name[:6], p.pid, where, text[:160].replace("\\", "/")))
        rows += 1
    if not rows:
        print("no unity or player")
        return 1
    return 0


def cmd_kill(args):
    targets = []
    if args.pid:
        for pid in args.pid:
            try:
                targets.append(psutil.Process(pid))
            except psutil.NoSuchProcess:
                print("gone", pid)
    if args.worktree:
        needle = args.worktree.lower()
        for p in iter_unity():
            text = ((" ".join(p.info["cmdline"] or []) + " " + (p.info["exe"] or "")).lower())
            if needle in text:
                if args.batch_only and "-batchmode" not in text:
                    continue
                targets.append(p)
    if args.worktree:
        # --worktree is path scoped: drop anything the needle does not actually hold,
        # including pids that came in through --pid.
        needle = args.worktree.lower()
        for p in list(targets):
            if needle not in _describe(p).lower():
                try:
                    print("dropping", p.pid, "--worktree does not match its command line")
                except psutil.Error:
                    pass
                targets.remove(p)
    if not targets:
        print("nothing matched")
        return 1

    # The main clone belongs to the owner and the Reviewer. --pid used to bypass every
    # ownership check, which is how an Editor the owner had loaded got killed.
    blocked = []
    if not args.allow_main:
        for p in list(targets):
            text = _describe(p)
            if is_main_clone(text) and not (args.worktree and args.worktree.lower() in text.lower()):
                blocked.append((p.pid, text))
                targets.remove(p)
    for pid, text in blocked:
        print("refusing %d: main clone (owner/Reviewer). Pass --allow-main only if they asked."
              % pid)
        print("    ", text[:140])
    if not targets:
        return 1

    for p in targets:
        try:
            print("would kill" if not args.yes else "killing", p.pid, p.name(),
                  ((p.exe() if p.pid else "") or "")[-70:])
        except psutil.Error:
            continue
    if not args.yes:
        print("refusing without --yes")
        return 1

    for p in targets:
        try:
            for child in p.children(recursive=True):
                child.kill()
            p.kill()
            p.wait(timeout=10)
        except psutil.NoSuchProcess:
            pass
        except psutil.TimeoutExpired:
            p.kill()
    print("killed", len(targets))
    return 0


def cmd_hub(args):
    """List Unity Hub processes and say who started each. Never kills.

    Measured from Hub's own log (`%APPDATA%/UnityHub/logs/info-log.json`, `Process arguments:`):
    every Unity CLI call (`unity status`, `unity command script eval_file ...`, `unity cmd ... eval`)
    starts a silent Hub when none is running. Killing Hub after a call therefore guarantees the next
    call starts another one - that kill-then-call cycle was the Hub loop. Hub is the owner's; leave it
    running. The fix is to stop calling the CLI, not to kill Hub.
    """
    found = 0
    for p in psutil.process_iter(["pid", "name", "cmdline", "ppid", "create_time"]):
        try:
            name = (p.info["name"] or "").lower()
            line = " ".join(p.info["cmdline"] or []).lower()

            if name.startswith("unity hub") or (name == "unity.exe" and "resources" in line and "serve" in line):
                parent = psutil.Process(p.info["ppid"]).name() if p.info["ppid"] else "-"
                started = time.strftime("%H:%M:%S", time.localtime(p.info["create_time"]))
                print(f"{p.info['pid']} {p.info['name']} started {started} parent {parent}")
                found += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not found:
        print("no Unity Hub processes")

    if getattr(args, "yes", False):
        print("refused: `hub --yes` no longer kills. Hub belongs to the owner, and killing it makes the next "
              "CLI call start another one.", file=sys.stderr)
        return 2

    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    mem = sub.add_parser("mem", help="memory now, or a bounded series reporting the peak")
    mem.add_argument("--samples", type=int, default=0, help="how many extra samples to take (0 = one reading)")
    mem.add_argument("--every", type=int, default=5, help="seconds between samples")
    mem.set_defaults(func=cmd_mem)

    p = sub.add_parser("ps", help="pid, worktree and full command line for every Unity/player process")
    p.add_argument("--worktree", help="only processes whose command line holds this text")
    p.set_defaults(func=cmd_ps)

    p = sub.add_parser("list")
    p.add_argument("--worktree", help="only processes whose exe or command line holds this text")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("players")
    p.add_argument("--worktree")
    p.set_defaults(func=cmd_players)

    p = sub.add_parser("busy")
    p.add_argument("--worktree", help="only editors whose exe or command line holds this text")
    p.add_argument("--seconds", type=float, default=5.0, help="sampling window (default 5)")
    p.set_defaults(func=cmd_busy)

    p = sub.add_parser("kill")
    p.add_argument("--worktree")
    p.add_argument("--pid", type=int, action="append")
    p.add_argument("--batch-only", action="store_true",
                   help="only -batchmode editors, so an interactive Editor somebody is driving survives")
    p.add_argument("--yes", action="store_true", help="actually kill; without it, list only")
    p.add_argument("--allow-main", action="store_true", dest="allow_main",
                   help="permit killing processes under the owner's main clone; only with their word")
    p.set_defaults(func=cmd_kill)

    p = sub.add_parser("hub", help="list Unity Hub processes and their parent; never kills")
    p.add_argument("--yes", action="store_true", help="actually kill; without it, list only")
    p.set_defaults(func=cmd_hub)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
