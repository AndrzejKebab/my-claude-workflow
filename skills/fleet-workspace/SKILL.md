---
name: fleet-workspace
description: Use when a command or file write is refused by the workspace guard, or before writing any output, report, log or temporary file. Says where your files belong and which paths outside your work folders you may read.
---

# Fleet workspace

Every bot works only inside the work folders: `F:/Programowanie` and `F:/Unity`. A guard runs before every
`terminal`, `write_file`, `patch`, `read_file`, `search_files` and `vision_analyze` call and refuses:

- any write outside the work folders;
- any command or read that names another drive (`C:`, `D:`, `E:`), another part of `F:`, `/tmp`, or `~/`
  outside the read-only list below.

## Where your files go

Every output, report, log, probe result and temporary file goes in your scratch:

- Workers: `<your worktree>/.scratch/` (ignored by git);
- the other bots: `F:/Programowanie/KebabAI OS/Hermes/profiles/<you>/cache/scratch/`.

`$TMPDIR`, `$TMP` and `$TEMP` point into your scratch, so `tempfile` and tools that use them are already
right. Write `"$TMPDIR/x"` or a scratch path; never `/tmp/x` (a Windows program reads that as `F:\tmp\x`). A
`terminal` call with no `workdir` runs in your scratch, so a relative output lands there too.

## Read-only paths

`read-only.txt` next to this file lists the places outside the work folders you may read or run, never
write: the Unity editors and CLI, Unity and game logs and crash reports, installed programs. Anything else is
the owner's. If you need a path added, ask the owner through Manager; do not retry the refused path another way.

## The guard

`scripts/workspace_guard.py` is a Hermes `pre_tool_call` hook, set in each bot's `config.yaml`. Its refusals
are logged to `Hermes/fleet-watchdog/guard.jsonl` and counted in the daily digest. Tests:
`python -m unittest discover -s scripts/tests`.

Example run (a write outside the work folders):

```
$ echo '{"tool_name":"write_file","tool_input":{"path":"D:/x.txt"}}' | python scripts/workspace_guard.py \
      --root F:/Programowanie --root F:/Unity --scratch F:/Unity/s
{"action": "block", "message": "Refused by the workspace guard: `D:/x.txt` is outside your work folders ..."}
```
