---
name: fleet-run
description: Use for every build, player run, test run or long tool run, and when a run printed a `[fleet_run] stopped:` line. Runs the command so it cannot outlive the run, fill the box's memory, or start Unity in a loop; replaces mem_guard.
---

# Fleet run

```
python F:/Programowanie/my-claude-workflow/skills/fleet-run/scripts/fleet_run.py \
    [--deadline 900] [--tree-cap-gib 12] [--cap-gib 34] [--sweep-project <project>] -- <command...>
```

The command and everything it starts run in one Windows Job Object; when the run ends, for any reason, the
whole tree goes with it. Every run ends with one line, which you quote instead of guessing what happened:

| Line | Exit | Meaning |
|---|---|---|
| `[fleet_run] finished: exit N in S s` | N | the command ended on its own |
| `[fleet_run] stopped: deadline (S s)` | 124 | it ran past `--deadline`; not a bug in your code |
| `[fleet_run] stopped: memory cap (...)` | 9 | its processes or the whole box went over the cap |
| `[fleet_run] stopped: spawn storm (...)` | 125 | it started `Unity.exe` or `Unity Hub.exe` more than 5 times in 10 min |
| `[fleet_run] stopped: stopped by owner (...)` | 143 | the owner or the Unity seat stopped it |

A stop is the reason the run ended, not a failure to report as a bug: say which line you got and what you
change (a longer deadline, a smaller run, waiting for the seat).

`fleet_run.py stop --all | --bot <name> | --pid <n>` stops registered runs only, never a process matched by name.
Runs are logged to `Hermes/fleet-watchdog/runs.jsonl` (tool, bot, reason, exit, seconds, peak memory).
`--sweep-project` also kills Unity processes on that project started during the run (a killed shell does not
always take its Editor). The old `bot-tools/unity/mem_guard.py` is a shim to this; its `--timeout` is `--deadline`.

spawns: the given command. Tests: `python -m unittest discover -s scripts/tests`.

Example run:

```
$ python fleet_run.py --deadline 5 -- python -c "print('hello from the child')"
hello from the child
[fleet_run] finished: exit 0 in 1 s
[fleet_run] peak tree 0.0 GiB, peak box 21.6 GiB
```
