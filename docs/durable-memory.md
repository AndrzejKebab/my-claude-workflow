# Durable project knowledge

Agent-generated memory is useful only when it is accurate, scoped, reviewable,
and stored with the project that owns it. Provider-specific cache directories
are not the source of truth.

## Storage policy

- Put project architecture, workflows, commands, file relationships, and
  decisions in `<project>/docs/agent-memory/` or the owning project's existing
  documentation.
- Put reusable Unity and development knowledge in
  `<workflow-root>/memory/shared/`, organized by technical domain.
- Keep personal preferences in user-level agent instructions.
- Do not copy unrelated project memories into this repository.
- Do not automatically restore old memory archives into active agent context.

Claude Code and Codex may maintain their own local task state or caches. Those
locations can change and may contain sensitive material. The installer should
install shared skills and configuration without treating either provider's
transcript or memory cache as version-controlled project data.

## Promoting knowledge into documentation

Before preserving a memory, check:

1. Is it still true in the current codebase?
2. Does it belong to this project or to a reusable workflow?
3. Can it be written without private paths, credentials, or unrelated names?
4. Is the evidence or verification method included?
5. Will a future maintainer know when the note has become stale?

Rewrite the result as a focused document or update an existing one. A reusable
procedure with a clear trigger belongs in `skills/` rather than memory. Prefer a
small number of maintained references over a large archive of agent summaries.

## Retrieval order

Query an existing Graphify graph first when the relevant project or shared
memory directory already contains one. Otherwise use FFF when available, then
built-in repository search. Building a new graph is an explicit operation, not
a prerequisite for an ordinary lookup.

The shared `memory` skill defines classification, note structure, and the
copy-only import helper. That helper never deletes provider cache files or
replaces them with links.

## Backup boundary

Back up repositories through the normal version-control and backup process.
Back up provider transcripts separately only when required, with appropriate
privacy controls; see [`transcript-backup.md`](transcript-backup.md).
