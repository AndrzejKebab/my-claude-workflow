# Claude, Codex, and Hermes Unity workflow

A shared collection of agent skills, specialist definitions, documentation, and command-line helpers. The repository is maintained for a Windows-based Unity workflow, with emphasis on ECS, jobs, Burst, rendering, profiling, and voxel-game development. Portable skills remain usable on other platforms where their dependencies are available.

The files in this repository are canonical. Change them here, commit the change, and rerun the installer when you want to refresh the active Claude, Codex, and Hermes copies.

## Install

On Windows, run the installer from Git Bash:

```bash
cd /f/Programowanie/my-claude-workflow
./install.sh
```

It asks what to do, then which agents to touch:

```text
What do you want to do?
  1) Install   create or refresh the selected tools
  2) Update    refresh only what this workflow already installed

install — select the tools:
  [x] 1) Claude   /c/Users/you/.claude           installed
  [x] 2) Codex    /c/Users/you/.codex            detected
  [x] 3) Hermes   /f/.../Hermes                  installed
Select targets (1,3 — or "all" / "none") [1,2,3]:
```

An agent is offered when its configuration directory holds its own config file
or its command is on `PATH`, and the detected ones are preselected. `Update`
preselects only what this workflow already installed, and skips a selected agent
that carries no managed manifest because there is nothing of this workflow's to
refresh there yet.

Unattended runs answer both questions with flags:

```bash
./install.sh --action install --targets claude,codex,hermes --yes
./install.sh --action update  --targets all --tools none --yes
```

The installer requires Bash, Git utilities, and `python3`. Set `CODEX_HOME` or
`HERMES_HOME` before running it only when those tools use a non-default
configuration directory.

### Linux cloud container

For a Linux Claude cloud environment, run the bootstrap. It installs only and
never touches a project directory:

```bash
./setup-claude-cloud.sh
```

It clones or fast-forward-updates this workflow under `$HOME/my-claude-workflow`
and then runs the installer unattended for Claude. The workflow checkout
defaults to the `kebab-unity` branch; override it with `WORKFLOW_BRANCH` only
when intentionally testing another branch.

### What the installer manages

- Every repository skill is copied into both `~/.claude/skills/` and `${CODEX_HOME:-~/.codex}/skills/`.
- Skills previously installed by this repository are replaced on later runs, so repository updates take effect.
- An unrelated user skill with the same name is moved to a timestamped backup before the repository version is installed.
- Unrelated skills with other names remain untouched.
- Backups live under each tool's `backups/my-claude-workflow/` directory, outside skill discovery. The newest five install backup sets are retained by default; set `WORKFLOW_BACKUP_RETENTION` to a non-negative integer to change that limit.
- Claude specialist agents and the selected root instruction documents are installed as managed copies under `~/.claude/`.
- Claude hooks are merged into `~/.claude/settings.json` without replacing unrelated settings. Codex does not use those Claude hook entries.
- Hermes receives the same skills under `${HERMES_HOME:-~/.hermes}/skills/`, and the shared rules as the skill `my-claude-workflow`. Hermes reads project rules from the working directory and ignores a home-level `AGENTS.md`, so the rules ship as a loadable skill rather than a dumped instruction file.
- The tools this workflow depends on are installed once per machine and registered with each selected agent. See [Tools](#tools).
- Files under `bin/` are made executable but are not added to `PATH` automatically.

The installer keeps manifests in the Claude, Codex, and Hermes configuration roots to distinguish repository-managed copies from user-owned content. Legacy backups accidentally placed inside skill discovery are moved to the external backup area.

## Tools

`install.sh` installs the tools this workflow depends on, once per machine, then
registers each with the agents selected in the same run. Control them with
`--tools graphify,fff,semantica`, `--tools all`, or `--no-tools`.

| Tool | What it provides | Registration |
| --- | --- | --- |
| `graphify` | Codebase knowledge graph, queried with `graphify query`/`path`/`explain`. | `graphify install --platform <agent>`, which it supports for claude, codex, and hermes. |
| `fff` | Rust file-search MCP server with frecency-ranked fuzzy matching. | Registered as the MCP server `fff` with `claude mcp add`, `codex mcp add`, or `hermes mcp add`. |
| `semantica` | Context and decision graph over the markdown corpus. | Executable only. Its MCP server needs a project graph path, so registration stays per project. |

`graphify` is installed with `uv tool install --upgrade graphifyy` when `uv` is
present and `python3 -m pip install --user --upgrade graphifyy` otherwise, with
a 300-second timeout and three attempts. `fff` is installed from its upstream
`install-mcp.sh`. `semantica` requires Python below 3.14, so it is installed
into its own virtual environment (`SEMANTICA_VENV`, default
`${HOME}/.local/share/semantica/venv`) and the `bin`/`Scripts` layout is
detected rather than assumed, which is what lets the same installer work on a
Linux container and on Windows.

A tool that fails to install is reported at the end of the run and does not undo
the rest of the install.

`graphify` resolves the Hermes home itself, and on Windows it has been observed
writing its skill to the Hermes install root rather than to `HERMES_HOME`. The
installer warns when `HERMES_HOME` is not the default so the placement can be
checked. `graphify` is also deliberately excluded from the managed skill copies
for Hermes: it owns that directory and refreshes it itself.

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

The repository contains ten focused agent definitions:

- `refactor-explorer`, `refactor-architect`, and `refactor-implementer` support the three-phase refactoring workflow.
- `research-extractor`, `research-vision`, and `research-refiner` support extraction, visual reconstruction, and final cleanup of research material.
- `logic-design-reviewer`, `performance-reviewer`, `readability-docs-reviewer`, and `simplicity-reviewer` provide evidence-gated Unity voxel/ECS review lenses.

The reviewer contract and scope boundaries are documented in
[`agents/README.md`](agents/README.md).

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
├── agents/              # refactor, research, and Unity review agents
├── bin/                 # Unity, Claude, audit, and maintenance helpers
├── docs/                # workflow and Unity technical documentation
├── memory/shared/       # reusable, reviewed Unity/development knowledge
├── share/systemd/       # optional Linux transcript-backup timer template
├── skills/              # canonical shared skill directories
├── CLAUDE.md            # Claude instruction entry point
├── DOCTRINE.list        # optional extra documents injected by cc-doctrine
├── install.sh           # managed installer for Claude, Codex, and Hermes
├── setup-claude-cloud.sh # install-only bootstrap for a Linux Claude container
└── research-library/    # generated local corpus; ignored by Git
```

Binding root documents are assembled into the global `AGENTS.md` installed for
Claude and Codex. The separate files remain the maintainable source modules;
Codex does not follow Claude-style Markdown imports. `HARNESS.md` is included
with an explicit Claude Code-only condition.

## Safety notes

- Review `git status` before running repository-maintenance workflows.
- `install.sh` may replace only content recorded as repository-managed; collisions with unrecognized user content are backed up first.
- Worktree removal, process termination, history rewriting, remote synchronization, and pushing remain explicit operations.
- Treat raw agent transcripts and research archives as sensitive local data.
