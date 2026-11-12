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

## A build's provenance file and its executable live in different directories

A game's build wrapper that accepts `--output` may still write `build-info.json` to its **own** default
(`<project>/Builds/Benchmark/Client/build-info.json`) while the player lands in the directory you named. Two
consequences, both of which have produced false evidence:

- the provenance gate reads the file at the **default** path, never at the output directory — looking only beside
the exe reports "no build-info" and tempts you to hand the run over on trust;
- the stale file from an earlier build stays in that default directory, so **check `branchSha` against the head you
  meant to build and the file's mtime against the exe's**, not the folder's existence. An exe at `01:56` with
  `branchSha` naming the previous commit is the normal shape of a build you did not actually make.

Quote the pair in the report — `build-info.json` `branchSha = <sha>` with its mtime, and the exe path with its
time — and treat a mismatch as no build at all.

## A compile count is only fresh if the log was new

A compile tool that reads a fixed path (`Logs/batch-compile.log`, `Logs/batch-compile.jsonl`) will happily report
the previous run's numbers: the command returns, the counts look identical to the last attempt, and a cache fix
that actually worked reads as a failure that did not. Delete those logs before starting the run, then quote the
log's own mtime beside the counts. `unity-test-failures.py --stale` is the same guard for results XML — refuse
any file older than the run that was supposed to write it.

**Two counts, never one.** A run can be `exit code 0` with zero `error CS` and still print dozens of console
errors: the wrapper reports `console: N error(s)`, typically job-reflection noise
(`Failed to create job reflection data`, `MethodAccessException … CreateJobReflectionData()`). Report it as
"exit 0, `error CS` count 0, N console errors of the <class> kind"; calling that "0 errors" or "clean console" is a
false claim that a later reader will trust. When the wrapper's own counts disagree with a plain grep of the log,
the wrapper is describing console entries and the grep is describing compiler diagnostics — say which one you
quoted.

## A binary pinned by git-lfs is only real once the object is pushed

A plugin `.dll`/`.so` stored through git-lfs looks pinned in the diff while its **content object may never have
left your machine**: `git lfs ls-files` marks it absent, the working file falls back to whatever the clone
already had, and a test whose subject is the binary's contents (a node/type count, a version string) fails on
every clone except yours.

- After committing a binary, run `git lfs push origin <branch>` explicitly, then verify from a **fresh clone**
  (`--depth 1 --branch <branch>` with LFS enabled) that the file's size and a byte-string count are right.
- Treat a binary-content test as an LFS liveness check, not just a behaviour check: when it fails on a clean
  clone and passes on yours, look at `git lfs ls-files` before touching the code.

## A hung Editor outlives the shell kill

`Stop-Process -Id <pid>` and `taskkill /F /PID <pid>` can return without killing a wedged batch Editor: the
process stays alive, keeps `Temp/UnityLockfile`, and every later batchmode run exits 1 moments after
`[Licensing::IpcConnector] Successfully connected` — before any test or compile output.

- Confirm the state by **pid read-back** (`unity_procs.py ps`, `Get-Process -Id <pid>`), never by the kill
  command's exit status. A command that reports success while the process survives is the normal shape here.
- The route that works is `unity_procs.py kill --worktree <name> --batch-only --yes`, scoped to your worktree.
- Never delete `Temp/UnityLockfile` while its holder is alive: a stale lock is a symptom, and deleting it
  under a running holder is how two Editors end up on one project. A lock that stays `Device or resource busy`
  with no process of yours listed means the holder is someone else's — ask, do not clear.
- A refusal that lands **after** licensing connects and **before** tests is the lock/seat path, not a licence
  denial. Say which of the two it is when reporting; conflating them sends the coordinator to the wrong problem.

## A gitignored leftover is invisible to merges

`Assets/` is mostly gitignored in some projects (`/Assets/*` with explicit re-includes), so a package folder, a
generated settings file or a stray tool left behind by an older setup survives every merge, never shows in
`git status`, and is absent from the main clone that everyone measures against. When a worktree compiles and the
main clone does not — or the reverse — list the same directory in both and run `git check-ignore -v <path>`
before reading any code. Recipe and ordering for a cold worktree: `references/worktree-cold-compile.md`.

## Deleting under `Packages/` needs a link check first

Some worktrees carry `Packages/` entries that are junctions into folders outside the repository; a recursive
delete follows the link and empties the target. Before any `rm -rf` under `Packages/`, check the attributes —
`os.lstat` plus `FILE_ATTRIBUTE_REPARSE_POINT` — and treat a reparse point as "report it, do not delete".
`clear_caches.py` refuses links for the same reason: prefer it, or delete explicit paths, never a wildcard.
A plain directory still is not free to remove — say which folder, who asked, and why the count needs it.

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
