---
name: skill-check
description: Use before promoting a script from your scratch into a toolbox skill, and when asked whether a tool is ready. Checks --help, the index entry, loops that can run forever, the recorded example run, declared program starts and GUI programs.
---

# Skill check

```
python F:/Programowanie/my-claude-workflow/skills/skill-check/scripts/skill_check.py <tool-or-skill-folder>... [--quiet]
```

A tool may be promoted from a worktree's `.scratch/` into a skill only when this prints `0 with findings`
(design.md #38-41). Per tool:

- **help**: `--help` exits 0 with a usage text (`.py`, `.sh`, `.ps1`; a library with no `__main__` is skipped);
- **index**: the tool is named in its skill's `SKILL.md` (or `--index <file>`);
- **example**: the `SKILL.md` has an "Example run" block with the tool's command and its real output;
- **loop**: `fleet-lint`'s `loop_guard.py` finds no loop that can run forever;
- **spawns**: a tool that starts programs lists them (`spawns:` or `Programs started:` in its header);
- **gui**: it starts no GUI program (notepad, Explorer, Unity Hub, VS Code).

A draft that duplicates an existing tool is not promoted: add a flag to the existing one instead.
spawns: the checked tool, with `--help`. Tests: `python -m unittest discover -s scripts/tests`.

Example run:

```
$ python skill_check.py skills/fleet-seat
skill_check: 1 tool(s), 0 with findings
```
