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

When a project already has an established knowledge layout, use it rather than
creating a competing tree. A useful division is:

- `.project-state/` for current, verified implementation state by project area;
- `.memory/notes/` for focused investigations and recurring known problems;
- `.memory/decisions/` for architectural and design decisions;
- `Docs/` or `docs/` for project-facing architecture and workflows;
- `ROADMAP.md` for explicitly planned future work.

These names are a convention, not a migration requirement. The owning
project's existing documented locations take precedence.

## Sources of truth

When project knowledge disagrees, resolve the contradiction rather than copying
it forward. Use this default priority:

1. Current source code and project configuration.
2. Observed build, test, Editor, or runtime results.
3. Current-state records.
4. Architecture documentation and decision records.
5. Roadmaps and other future intent.

A roadmap item does not prove that a feature exists. A memory note does not
prove that current code still behaves as recorded.

## Decisions and known problems

When the project uses numbered decision records, name them
`DXXX-<topic>.md`, choose the next unused three-digit number, and never renumber
existing decisions. If a decision is replaced, record which earlier decision it
supersedes instead of rewriting history. Routine implementation details do not
need decision records.

Record a failure or limitation only after it has been verified and only when it
is likely to affect future work. Put it in the affected current-state record or
a focused note. Do not preserve transient errors or unverified hypotheses as
durable knowledge, and do not create roadmap work unless future work is
actually planned.

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

## Keeping documentation consistent

When implementation changes documented behavior, architecture, ownership, data
flow, APIs, or constraints, update the canonical documentation in the same
task. Describe verified implementation rather than planned behavior. Correct a
stale fact where it is owned instead of duplicating a newer version elsewhere,
and leave unrelated documentation alone.

At the end of meaningful implementation work:

1. Determine what actually changed and what was verified.
2. Update only the affected current-state records.
3. Preserve reusable investigation findings in focused notes.
4. Record a decision only when architecture or design changed.
5. Update affected project documentation.
6. Update existing roadmap items only when the work changed them; add new work
   only when the user requested planning.
7. Check consistency across code, configuration, state, memory, decisions,
   documentation, and roadmap.

Do not create memory or documentation entries for trivial edits.

## Retrieval order

Query an existing Graphify graph first when the relevant project or shared
memory directory already contains one. Otherwise use FFF when available, then
built-in repository search. Building a new graph is an explicit operation, not
a prerequisite for an ordinary lookup.

The shared `memory` skill defines classification, note structure, and the
copy-only import helper. That helper never deletes provider cache files or
replaces them with links.

## Related documentation

- [Code comments](code-comments.md)
- [Game-development verification](testing.md)

## Backup boundary

Back up repositories through the normal version-control and backup process.
Back up provider transcripts separately only when required, with appropriate
privacy controls; see [`transcript-backup.md`](transcript-backup.md).
