---
name: refactor
description: Orchestrate a structural code refactor through separate exploration, architecture, and implementation phases with user approval between phases. Use for an explicit /refactor request or a structural cleanup that benefits from investigation before edits.
---

# Refactor orchestrator

Run a three-phase refactor: explore the current design, propose a target architecture, then implement the user-approved migration. Keep the phases separate so observations, design choices, and code changes remain auditable.

Use the dedicated `refactor-explorer`, `refactor-architect`, and `refactor-implementer` roles when available. If the host supports only general subagents, give each phase to a fresh agent with the same ownership and deliverable boundaries.

## Activation boundary

Use this workflow when the user explicitly invokes `/refactor`, asks for structural refactoring, or requests a smell-find → redesign → implement process. Do not trigger it merely because ordinary feature work exposes a small cleanup. Use a direct edit for a narrow, behavior-preserving change that does not need architectural investigation.

If the target scope is missing, ask for it. Otherwise make reasonable assumptions and ask only questions whose answers materially affect scope, compatibility, or verification.

## Invariants

- The user approves the findings selected for architecture and the architecture selected for implementation.
- The target scope established at the start applies to all phases. Expanding it requires explicit user approval.
- Each specialist owns its phase artifact and writes it to disk before returning.
- Briefs are self-contained even when the host can inherit conversation history.
- The architect designs only for approved findings. The implementer follows only approved migration steps.
- Existing user changes are preserved. A checkpoint commit never bundles unrelated work without the user's authorization.
- Failed verification stops implementation at the affected step unless the fix is clearly within the approved design.

## Shared artifacts

Choose a short kebab-case slug and create:

```text
docs/orchestrate/refactor-<slug>/
├── README.md
├── 01-context.md
├── 02-exploration.md
├── 03-architecture.md
└── 04-refactoring.md
```

`README.md` contains the goal and a checklist for exploration, architecture, and implementation. `01-context.md` is the canonical brief and records:

- the user's goal, quoting exact wording only where it affects the design;
- exact target paths or globs;
- project instructions and architectural references;
- compatibility requirements and forbidden changes;
- verification commands and manual checks;
- relevant dirty-worktree state.

If an attached image is load-bearing, use its available local path when one is provided. Otherwise ask the user to attach it again if an agent must inspect it. Always describe the important visual facts in `01-context.md`; never rely on phrases such as “the image above.” Do not assume a Claude or Codex cache location.

## Phase 1: exploration

Dispatch `refactor-explorer` with ownership of `02-exploration.md`. Its brief must include:

1. the complete goal and exact scope;
2. a required first action to read `01-context.md` fully;
3. permission to inspect code only within the stated scope and necessary callers or tests;
4. a required final action to write findings to `02-exploration.md`;
5. the expected result: a prioritized table followed by expanded evidence for the most important findings.

Each finding should state severity, exact location, observed structure, why it creates a concrete cost or risk, and a suggested direction without prescribing the full design. Require verified file and symbol references rather than inferred ones.

After the explorer returns, confirm that `02-exploration.md` was written and mark exploration complete in `README.md`. Summarize the findings and ask the user which findings should proceed to architecture. Do not dispatch the architect until the user confirms.

## Phase 2: architecture

Dispatch `refactor-architect` with ownership of `03-architecture.md`. Its brief must include:

1. the complete goal and approved finding numbers;
2. a required first action to read `01-context.md` and `02-exploration.md` fully;
3. the compatibility and forbidden-change constraints;
4. a required final action to write the design to `03-architecture.md`.

The design should contain:

- target modules, types, responsibilities, and dependency direction;
- what stays, changes, moves, and is removed;
- an ordered migration with independently verifiable steps;
- expected behavior and API compatibility;
- risks, rollback points, and verification gates.

After the architect returns, confirm that `03-architecture.md` was written and mark architecture complete. Summarize user-visible effects and risks, then ask whether to implement all or a selected subset of steps. Do not begin implementation without confirmation.

Before implementation, inspect the working tree. If a checkpoint would protect existing work, propose it explicitly. Create the checkpoint directly or through a commit-capable agent only after the user authorizes committing the files in scope. Never push unless requested.

## Phase 3: implementation

Dispatch `refactor-implementer` with ownership of the approved code scope and `04-refactoring.md`. Remind it that other work may exist in the repository and must not be reverted. Its brief must include:

1. the complete goal and approved migration steps;
2. a required first action to read all three prior artifacts fully;
3. exact owned files or modules and explicit forbidden areas;
4. verification gates to run after each meaningful step;
5. a required final action to write the execution log to `04-refactoring.md`.

For each step, the log records files changed, behavior preserved or intentionally changed, verification performed, and failures or deviations. If a required change falls outside the architecture, stop and return to the architecture phase rather than improvising.

After the implementer returns, verify the artifact and the actual diff, mark implementation complete only when the approved steps and gates are complete, and report the resulting state. Offer a final commit only if it has not already been authorized.

## Specialist brief template

```markdown
# Goal
<self-contained goal>

# Scope and ownership
<exact paths, allowed dependencies, and forbidden areas>

# Required reading
1. docs/orchestrate/refactor-<slug>/01-context.md
2. <prior phase artifacts>

# Task
<one phase only>

# Constraints and verification
<user decisions, compatibility requirements, and exact gates>

# Deliverable
Write <phase artifact> before returning. Final chat text is status only.
```

## Completion

The workflow is complete when the approved implementation steps pass their required gates and all three phase artifacts are present. Leave the orchestration directory intact as the decision and execution record unless the user asks to remove it.
