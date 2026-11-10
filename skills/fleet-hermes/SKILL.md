---
name: fleet-hermes
description: Use to prove what a bot's approvals.deny list blocks, or which commands Hermes's dangerous-command guard flags in headless turns, before relying on a command. Moved from bot-tools/hermes.
---

# Fleet Hermes

Run from `hermes-agent/` with its venv python (it imports Hermes's own matcher):

```
venv/Scripts/python.exe F:/Programowanie/my-claude-workflow/skills/fleet-hermes/scripts/deny_check.py --profile <profile-dir> [--cases file]
venv/Scripts/python.exe .../deny_check.py --guard --cases <file>     # the headless guard instead of approvals.deny
```

`scripts/deny_check.py` checks each `ALLOW`/`BLOCK` case line against the real matcher; exit 1 if any case
misbehaves. Case files live with their skills (`fleet-github/*-cases.txt`). The old
`bot-tools/hermes/deny_check.py` is a shim. spawns: none.

Example run:

```
$ venv/Scripts/python.exe deny_check.py --guard --cases skills/fleet-github/advisor-guard-cases.txt
ok   want ALLOW got ALLOW  | python F:/Programowanie/my-claude-workflow/skills/fleet-supervision/scripts/supervision.py
deny_check: 0 wrong
```
