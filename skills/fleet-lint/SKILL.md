---
name: fleet-lint
description: Use before adding or changing a tool, and when a tool might loop forever. Finds loops that cannot end (while true, unbounded shell polling).
---

# Fleet lint

```
python F:/Programowanie/my-claude-workflow/skills/fleet-lint/scripts/loop_guard.py <file-or-dir>... [--list-rules]
```

`scripts/loop_guard.py` fails (exit 1) on loops that can run forever: `while true` / `while :` / `until false` in
shell, `while True` in Python, `while (true)` / `for (;;)` in C# and PowerShell, and a shell `while`/`until`
whose condition has nothing that ends it. A loop bounded another way carries a `loop-bound: <reason>` comment.
The old `bot-tools/lint/loop_guard.py` is a shim to this. spawns: none.

Example run:

```
$ python loop_guard.py skills/fleet-run
loop_guard: 0 finding(s)
```
