---
name: memory
description: Retrieve, classify, or save durable development knowledge across projects. Use when recalling prior solutions or when the user asks to remember a verified Unity, engineering, or project-specific fact.
---

# Durable development memory

Keep memory in reviewed, searchable Markdown rather than relying on provider caches. Separate reusable knowledge from facts owned by one project.

## Retrieve before investigating

For a codebase or development question, use this order:

1. If the relevant project or shared-memory directory already contains `graphify-out/graph.json`, query that graph first.
2. If FFF tools are available, use them for fast file and content search.
3. Fall back to repository search tools such as `rg` and normal file reads.

Do not build or install Graphify merely because no graph exists. A new graph requires an explicit `/graphify` request; updating an existing graph after an approved memory write is allowed.

Search both tiers when the question may combine general technique with local implementation:

- Shared memory: `<workflow-root>/memory/shared/`.
- Project memory: `<project-root>/docs/agent-memory/`.

Treat memory as a lead, not proof. Verify code-specific claims against the current project and note version constraints for Unity, packages, render pipelines, or external tools.

## Classify before saving

Save to shared memory when the knowledge applies across projects, such as a verified UI Toolkit failure mode, an ECS scheduling rule, a Burst constraint, or a reusable debugging technique.

Save to project memory when it names project files, systems, scenes, architecture, configuration, or decisions. For example, how `MainMenu.cs` interacts with a specific bootstrap system belongs to that project.

Turn a repeatable procedure with a clear trigger into a skill instead of a memory note. Keep temporary hypotheses in investigation notes until they are verified.

## Write useful notes

A durable note should include only applicable fields:

```markdown
# Title

- Scope: shared or project
- Verified: YYYY-MM-DD
- Applies to: Unity/package/tool versions

## Problem

Observable symptom and relevant context.

## Resolution

The verified explanation or solution.

## Evidence

Commands, documentation, tests, or code locations that established it.

## Revalidate when

Conditions that could make the note stale.
```

Remove credentials, private transcript text, machine-specific temporary paths, and unrelated project names. Update an existing note when it covers the same concept instead of creating duplicates.

## Copy an existing verified note

The adjacent `scripts/store_memory.py` helper copies one Markdown note into the selected tier. It never deletes or modifies the source and refuses to overwrite different destination content.

```powershell
python scripts/store_memory.py shared note.md --workflow-root <workflow-root> --category unity/ui-toolkit
python scripts/store_memory.py project note.md --project-root <project-root> --category architecture
```

Use `--dry-run` to preview. Category paths must be relative and cannot contain `..`.

After saving, verify the destination and commit it in the repository that owns it. If that memory directory already has a Graphify graph, update the existing graph; do not create a new graph implicitly.
