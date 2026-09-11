---
name: prune
description: Review and compact Claude/Codex instructions and staged agent memory while preserving user mandates and consulting before relocation or deletion.
---

# Configuration and memory pruning

Reduce context cost and move durable knowledge into the tracked file that owns it. This workflow may edit or delete configuration and memory only after the user reviews the proposed relocations and deletions.

## Discover the active layers

Inspect only files that exist and apply to the current setup:

- repository-level `AGENTS.md` and `CLAUDE.md` files;
- installed global Claude or Codex instruction files;
- relevant tracked workflow skills and documentation;
- Claude project memory or another explicitly identified agent-memory store;
- project documentation that already owns the subject.

Distinguish installed managed copies from their tracked source. Edit the tracked source in `F:\Programowanie\my-claude-workflow` when this workflow owns it, then use the installer; do not independently edit both copies.

## Classify content

- **KEEP AND COMPACT** — a current user mandate, non-obvious constraint, verified environment fact, or sharp recurring gotcha in its correct tracked layer.
- **RELOCATE TO SKILL** — reusable task methodology that should load only when that skill is invoked.
- **RELOCATE TO PROJECT DOCS** — durable architecture, Unity/ECS knowledge, project decisions, or operational instructions owned by one repository.
- **RELOCATE TO GLOBAL INSTRUCTIONS** — a concise user preference that genuinely applies to nearly every task.
- **DELETE** — stale session state, duplicated content, obsolete paths/APIs, generic advice, or claims that cannot be supported and have no durable value.

Machine-local memory is staging, not the final home. Promote verified, reusable content into tracked skills or documentation; delete transient residue after its useful content has moved. Do not turn unverified session observations into canon.

## Consultation boundary

Before relocating or deleting anything, present:

- source file and concise content description;
- proposed destination or deletion;
- why the current layer is wrong;
- conflicts with existing instructions;
- anything whose meaning or ownership is uncertain.

Wait for the user's decision. Straight compaction within a confirmed file may proceed only when it preserves every mandate and changes no meaning.

## Compact conservatively

Remove duplication, filler, obsolete examples, and implementation facts already obvious from current code. Prefer one precise rule over repeated explanations. Preserve the reason when it is necessary to prevent recurrence, but remove personal history and author-specific paths from reusable guidance.

Do not weaken safety, verification, Git, platform, or project constraints merely to reduce tokens. Do not compact invoked skill documentation simply because it is long; skill content is on-demand and should be reduced only when inaccurate, redundant, or outside its purpose.

## Verify and report

Diff every changed file, check references to removed material, and validate changed skills. Measure before/after tokens with `ttok` when available; otherwise report word and line counts as an explicit approximation.

Report reductions separately for always-loaded instructions and on-demand material. List relocations and deletions with one-line reasons, and confirm that tracked canonical files—not only installed copies—contain the result.
