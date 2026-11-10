---
name: fleet-unity
description: Use for Unity processes, memory, builds, test results, caches and .meta checks on the shared box - before blaming or killing a process, after a test run, when a build stalls, when a .cs file may lack its .meta. Moved from bot-tools/unity and bot-tools/git.
---

# Fleet Unity

All under `F:/Programowanie/my-claude-workflow/skills/fleet-unity/scripts/`. The old `bot-tools/` paths are shims.
Run builds and players through `fleet-run`, and hold the seat (`fleet-seat`) for player builds, player runs and Play.

| Tool | What it does |
|---|---|
| `unity_procs.py` | Memory and Unity/player processes: `mem [--samples N --every S]` (peak and the five largest), `ps` (pid, worktree, command line: use it before blaming or killing anything), `list`, `players`, `busy` (CPU ~0 while a compile should work means stalled), `kill --worktree … [--batch-only] --yes` (never the owner's main clone without `--allow-main`), `hub` (lists Hub, never kills it). spawns: none. |
| `unity-test-failures.py` | Reads a results XML: failing cases with stacks, `--totals`, `--namespace` to separate your assembly from package suites, `--stale MINUTES` refuses an old result (exit 2). spawns: none. |
| `repeat_runs.py` | Runs a suite N times as evidence for an intermittent fix: deletes the results XML before each run, marks a run with no fresh results "does not count", prints `--watch` tests per run, `--stop-on-extra`. spawns: the test runner, `unity_procs.py`. |
| `editor_slot_build.sh` | One Editor, one build method, no Editor left behind: refuses while any `Unity.exe` is up, classifies the failure (C#, content, profile, lock, licence = exit 4, never retried), retries a plain pass before a reimport, kills only Editors on that project. Needs the seat (exit 75 without). The Editor is the one the project's `ProjectVersion.txt` names unless `--unity`. A game wrapper that starts Unity itself (VoxelGame's `build_player.py`) is refused because it skips the seat: pass its `-executeMethod` as `--method` (`VoxelGame.Benchmark.Editor.BenchmarkBuildScript.Run`). spawns: Unity.exe. |
| `crash_capture.sh` | Runs a player under `cdb` and on a native crash writes `kb` + `!analyze -v` to `<player>-crash-<stamp>.log` beside the exe. spawns: cdbX64.exe, the player. |
| `clear_caches.py` | Clears `Library/Bee`, `Library/ScriptAssemblies`, `Library/BuildPlayerData` after an Editor upgrade; refuses links, never touches `Library` wholesale or `Packages/`. `--dry-run`. spawns: none. |
| `empty_worktree_scratch.py` | Empties a worktree's `.scratch/`; refuses a folder that is not a git worktree. `--dry-run`. spawns: none. |
| `kill_players.ps1` | Kills players started from ONE executable path, by full-path comparison: `-Exe <path>`. spawns: none. |
| `kill_editors.ps1` | `-Project <your worktree>`: kills Editors whose `-projectPath` is that worktree only; never the owner's main clone. spawns: none. |
| `clone_flip_watch.py` | `--repo <clone> --out <log>`: on every branch change of the clone, logs a process snapshot, so whoever moved the checkout is named. spawns: git. |
| `meta_integrity.py` | Every `.cs` under `Assets/` has a committed `.meta` and no `.meta` is orphaned: `--ref` (default `origin/main`) or `--staged`. Exit 1 on findings. spawns: git. |

Example run (real output, 2026-11-09):

```
$ python unity_procs.py mem
ram used/total GiB 21.8 47.9 avail 26.1
commit approx GiB 22.4 of 96.1
$ python meta_integrity.py --ref origin/main          # in the game repo
origin/main: 866 .cs under Assets, 0 without a .meta, 0 orphan .meta
$ python unity-test-failures.py --help
usage: unity-test-failures.py [-h] [--totals] [--namespace NAMESPACE] [--no-traces] [--stale STALE]
$ python repeat_runs.py --help
usage: repeat_runs.py [-h] --project PROJECT --task TASK [--runs RUNS] [--platform PLATFORM] ...
$ python clear_caches.py --help
usage: clear_caches.py [-h] --project PROJECT [--dry-run]
$ python empty_worktree_scratch.py --help
usage: empty_worktree_scratch.py [-h] [--dry-run] worktree
$ python clone_flip_watch.py --help
usage: clone_flip_watch.py [-h] --repo REPO --out OUT [--minutes MINUTES]
$ bash editor_slot_build.sh --help
Run ONE Unity Editor build method under the fleet's single-Editor rule, and leave no Editor behind.
$ bash crash_capture.sh --help
Run a Unity player under cdb so a native crash leaves a readable stack.
$ powershell -File kill_players.ps1 -Exe "F:/Unity/Projects/NoSuchGame/Builds/Client/Game.exe"
killed 0 from F:\Unity\Projects\NoSuchGame\Builds\Client\Game.exe
$ powershell -File kill_editors.ps1 -Project "F:/Unity/Projects/NoSuchGame-worker-9"
killed 0 for F:\Unity\Projects\NoSuchGame-worker-9 (left 0 other Editors alone)
```
