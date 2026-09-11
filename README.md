# Claude and Codex Unity workflow

A shared collection of agent skills, specialist definitions, documentation, and command-line helpers. The repository is maintained for a Windows-based Unity workflow, with emphasis on ECS, jobs, Burst, rendering, profiling, and voxel-game development. Portable skills remain usable on other platforms where their dependencies are available.

The files in this repository are canonical. Change them here, commit the change, and rerun the installer when you want to refresh the active Claude and Codex copies.

## Install

On Windows, run the installer from Git Bash:

```bash
cd /f/Programowanie/my-claude-workflow
./install.sh
```

The installer requires Bash, Git utilities, and `python3`. Set `CODEX_HOME` before running it only when Codex uses a non-default configuration directory.

### What the installer manages

- Every repository skill is copied into both `~/.claude/skills/` and `${CODEX_HOME:-~/.codex}/skills/`.
- Skills previously installed by this repository are replaced on later runs, so repository updates take effect.
- An unrelated user skill with the same name is moved to a timestamped backup before the repository version is installed.
- Unrelated skills with other names remain untouched.
- Backups live under each tool's `backups/my-claude-workflow/` directory, outside skill discovery. The newest five install backup sets are retained by default; set `WORKFLOW_BACKUP_RETENTION` to a non-negative integer to change that limit.
- Claude specialist agents and the selected root instruction documents are installed as managed copies under `~/.claude/`.
- Claude hooks are merged into `~/.claude/settings.json` without replacing unrelated settings. Codex does not use those Claude hook entries.
- Files under `bin/` are made executable but are not added to `PATH` automatically.

The installer keeps manifests in the Claude and Codex configuration roots to distinguish repository-managed copies from user-owned content. Legacy backups accidentally placed inside skill discovery are moved to the external backup area.

## Skills

The `skills/` directory currently contains:

### Unity and game development

`initialize-ai-navigation`, `localization`, `new-unity-project`, `optimize-audio`, `optimize-text-mesh-pro`, `profile`, `shader-graph-create-custom-node`, `sprite-editor`, `ui`, `ui-imgui`, `ui-ugui`, `ui-uitk`, `unity-cli`, `unity-diagnose`, `unity-grill`, `unity-grill-with-docs`, `unity-mcp-skill`, `unity-package-management`, `unity-prototype`, `unity-refactor`, `urp-postprocessing`, and `validate-urp-render-graph-renderer-feature`.

### Git and delivery

`cdiff`, `github-code-review`, `github-pr-workflow`, `merge`, `rebase`, `reset-repos`, `review-agent`, `review-plan`, and `worktree`.

Manual Git worktrees default to the ignored `.worktrees/` directory. The workflow detects the intended local base instead of assuming every repository uses `main`, and it never pushes unless explicitly requested.

### Code quality and reusable knowledge

`deadcode`, `docs`, `dry`, `humanizer`, `memory`, `prune`, `recipe-spec`, `refactor`, `refine`, `refine-docs`, `sanitize`, `sniff`, `tdd`, `write-a-skill`, and `research`.

### Utilities

`claude-status`, `domain-availability`, `enforce`, `find-skills`, `graphify`, `rider`, `rustrover`, and `webstorm`.

Some utilities are necessarily product- or application-specific. Their presence does not make the shared Unity and engineering skills Claude-only.

Graphify and FFF setup, maintenance, and search precedence are documented in [Codebase navigation](docs/codebase-navigation.md).

## Specialist agents

The repository contains six focused agent definitions:

- `refactor-explorer`, `refactor-architect`, and `refactor-implementer` support the three-phase refactoring workflow.
- `research-extractor`, `research-vision`, and `research-refiner` support extraction, visual reconstruction, and final cleanup of research material.

Claude receives these definitions under `~/.claude/agents/`. Codex can use the shared skill instructions with its native collaboration roles where available.

## Unity command-line helpers

Add `F:\Programowanie\my-claude-workflow\bin` to the Git Bash `PATH` to use the helper commands. Keep the official Unity CLI location on `PATH` as well.

| Command | Purpose |
| --- | --- |
| `unity-editor <project>` | Reads `ProjectVersion.txt`, resolves the matching installed editor, and safely launches that project. |
| `unity-cli-recompile <project>` | Requests recompilation through a connected editor and shows status plus recent compiler errors. |
| `unity-ps [filter]` | Lists running Unity project-editor processes without worker-process noise. |
| `killunity <filter> [--force]` | Previews matching editors; termination requires the explicit `--force` flag. |

On this Windows setup, editor discovery uses the official Unity CLI first and falls back to `F:\Unity Editors`. Override it with `UNITY_CLI_BIN` or `UNITY_EDITOR_ROOT`. The bare `unity` helper is retained as a compatibility alias, but it may collide with the official `unity.exe`; use `unity-editor` when the intended command must be unambiguous.

## Claude-specific helpers

The installer currently wires these hooks only into Claude Code:

| Command | Event | Purpose |
| --- | --- | --- |
| `cc-nospin` | `PreToolUse(Bash)` | Rejects repeated or no-op shell spin loops. |
| `cc-doctrine` | `SessionStart` | Loads the paths explicitly listed in `DOCTRINE.list`. |
| `cc-no-hedge` | `Stop` | Applies deterministic response-style checks. |
| `cc-whole-file-reads` | `PreToolUse(Read\|Bash)` | Protects instruction files from partial reads. |
| `cc-comment-wall` | `PostToolUse(Write\|Edit)` | Detects oversized narration comments. |

Additional `cc-*` scripts remain available for manual inspection, status experiments, rule auditing, and optional transcript backup. See `docs/` before enabling them. `cc-transcript-backup` requires explicit source and rclone-remote configuration; it has no default cloud destination.

The `claude`, `claudeh`, `claude-draft`, and `claude-editor` launchers are intentionally Claude-specific. Shared skills do not depend on them.

## Research storage

The research workflow uses:

```text
F:\Programowanie\my-claude-workflow\research-library
```

The directory is ignored by Git because generated research corpora can be large and may contain archived source material. Override the location with `RESEARCH_ROOT` when needed. The research skill documents its Python and external-tool requirements.

## Repository layout

```text
my-claude-workflow/
├── agents/              # refactor and research specialist definitions
├── bin/                 # Unity, Claude, audit, and maintenance helpers
├── docs/                # workflow and Unity technical documentation
├── memory/shared/       # reusable, reviewed Unity/development knowledge
├── share/systemd/       # optional Linux transcript-backup timer template
├── skills/              # canonical shared skill directories
├── CLAUDE.md            # Claude instruction entry point
├── DOCTRINE.list        # optional extra documents injected by cc-doctrine
├── install.sh           # managed Claude and Codex installer
└── research-library/    # generated local corpus; ignored by Git
```

Root documents such as `HARNESS.md`, `VERIFY.md`, `MODEL.md`, `PROSE.md`, and `NONDUAL.md` are retained as reusable guidance. They are not automatically injected by `DOCTRINE.list`; add a path there only when it should consume context every session.

## Safety notes

- Review `git status` before running repository-maintenance workflows.
- `install.sh` may replace only content recorded as repository-managed; collisions with unrecognized user content are backed up first.
- Worktree removal, process termination, history rewriting, remote synchronization, and pushing remain explicit operations.
- Treat raw agent transcripts and research archives as sensitive local data.
