# my-claude-workflow

Personal Claude Code skills, sub-agents, and workflow automation.

## Installation

```bash
./install.sh
```

This symlinks `skills/` and `agents/` into `~/.claude/`. Edit the canonicals
here in the repo — re-run `install.sh` to refresh the symlinks. Launcher scripts
in `bin/` are made executable; add `bin/` to your `PATH` to use them.

## Skills

### Git & worktree workflow

| Skill | Description |
|-------|-------------|
| `commit` | Commit all changes, including untracked files |
| `worktree` | Create or switch to a git worktree for isolated feature/fix work |
| `rebase` | Rebase the current worktree branch onto latest main |
| `merge` | Merge the current worktree branch into main, clean up the worktree |

### Orchestration

| Skill | Description |
|-------|-------------|
| `delegate` | Multi-agent orchestration — scope work, audit for reuse, dispatch every step to sub-agents |
| `refactor` | Three-phase refactoring orchestrator: explore smells → design → apply |
| `research` | Extract research content from YouTube talks, PDFs, or PPTX into structured markdown |
| `handoff` | Write a continuation-link handoff prompt for a future session |
| `diagnose-first` | Debugging methodology that forces observation before action |

### Code quality

| Skill | Description |
|-------|-------------|
| `deadcode` | Find and delete dead code — zero callers means zero reasons to exist |
| `dry` | Scan crates for SOLID/DRY/KISS violations, rank the worst, fix them |
| `sniff` | Find and fix code smells — anonymous tuples, magic numbers, deep nesting, weak types |
| `tdd` | RED/GREEN TDD — write a failing test first, then fix |
| `review-agent` | Launch a sub-agent to review the current branch diff against master |
| `review-plan` | Audit a plan file for completeness before exiting plan mode |
| `sanitize` | Audit tracked files for leaked references to external proprietary code |

### Docs & context

| Skill | Description |
|-------|-------------|
| `docs` | Edit documentation only — no source code |
| `refine-docs` | Interactive document refinement, file by file, with Q&A |
| `claude-status` | Show active Claude sessions across all projects |
| `enforce` | Pre-load CLAUDE.md constraints into session context |
| `prune` | Prune context and memories — strip redundancy, preserve sharp rules |

### Project utilities

| Skill | Description |
|-------|-------------|
| `reset-repos` | Preserve in-progress work and reset all p7 repos to latest master |
| `profile` | Build, run, and analyze Unity profiler data with call-stack attribution |
| `domain-availability` | Generate domain name ideas and check availability across TLDs |
| `rustrover` | Open RustRover in the current worktree |
| `rider` | Open Rider in the current worktree |
| `webstorm` | Open WebStorm in the current worktree |

## Agents

Sub-agent definitions dispatched by the orchestrator skills. Installed alongside
skills so `delegate`, `refactor`, and `research` can fan work out to fresh
context windows.

| Agent | Used by | Role |
|-------|---------|------|
| `delegate-auditor` | `delegate` | Audits the codebase for existing functionality before any design |
| `delegate-architect` | `delegate` | Designs the implementation and persists it to the group file |
| `delegate-consolidated` | `delegate` | Runs compounded phases in one continuous 1M-context run |
| `delegate-reviewer` | `delegate` | Fresh-eyes verification against success criteria |
| `refactor-explorer` | `refactor` | Phase 1 — surfaces concrete code smells and architectural problems |
| `refactor-architect` | `refactor` | Phase 2 — designs the target-state structure |
| `refactor-implementer` | `refactor` | Phase 3 — applies the migration as real code edits |
| `research-extractor` | `research` | Pass 1 — runs the extraction pipeline and marks problem areas |
| `research-vision` | `research` | Vision pass — describes slide/figure images inline |
| `research-refiner` | `research` | Pass 3 — resolves FIXME marks and cleans up the document |

## Directory Structure

```
my-claude-workflow/
├── README.md
├── install.sh                # symlinks skills/ + agents/ into ~/.claude/
├── skills/                   # one directory per skill, each with a SKILL.md
│   ├── claude-status/         #   SKILL.md + claude-status.sh
│   ├── commit/
│   ├── deadcode/
│   ├── delegate/
│   ├── diagnose-first/
│   ├── docs/
│   ├── domain-availability/
│   ├── dry/
│   ├── enforce/               #   SKILL.md + enforce.sh
│   ├── handoff/
│   ├── merge/
│   ├── profile/               #   SKILL.md + build-zority.sh
│   ├── prune/
│   ├── rebase/
│   ├── refactor/
│   ├── refine-docs/
│   ├── research/              #   SKILL.md + tools/ (Python extraction pipeline)
│   ├── reset-repos/
│   ├── review-agent/
│   ├── review-plan/
│   ├── rider/
│   ├── rustrover/
│   ├── sanitize/
│   ├── sniff/
│   ├── tdd/
│   ├── webstorm/
│   └── worktree/
├── agents/                   # sub-agent definitions for the orchestrator skills
│   ├── delegate-*.md
│   ├── refactor-*.md
│   └── research-*.md
└── bin/                      # launcher scripts (add to PATH)
    ├── killunity
    ├── unity
    ├── unity-launch
    └── unity-recompile
```
