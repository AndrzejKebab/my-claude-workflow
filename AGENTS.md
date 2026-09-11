# Shared Agent Instructions

These rules apply across projects. Repository-level `AGENTS.md` files add or
override project facts and constraints.

## Scope

- Implement only what the user requested and what is strictly required.
- Do not invent features, roadmap items, abstractions, or product decisions.
- Ask before making a material architecture or product choice with meaningfully
  different outcomes.
- Preserve unrelated work in the working tree.
- Treat suggestions as suggestions, not authorization to implement them.

## Navigation and evidence

For codebase and durable-memory questions, query an existing Graphify graph
first. Read the identified source before making implementation decisions. If no
graph exists or it lacks the needed detail, use FFF when available, then `rg`,
file search, and direct reads. Do not build a graph for an ordinary lookup unless
`/graphify` was requested.

When sources disagree, prefer current source and configuration, then observed
verification, current-state records, architecture documentation and decisions,
and finally roadmaps. Resolve contradictions instead of copying them forward.

## Knowledge and documentation

Use `docs/durable-memory.md` for knowledge placement, source-of-truth
precedence, sequential `DXXX` decisions, recurring known problems,
documentation consistency, and end-of-task knowledge updates.

Use `docs/code-comments.md` for comment discipline. Prefer clear code; preserve
only non-obvious constraints, ownership, ordering, compatibility requirements,
or measured invariants in comments.

Do not create memory, decisions, documentation, or roadmap entries for trivial
work. Project-specific knowledge stays with the project; reusable Unity and
development knowledge belongs in the shared workflow repository.

## Verification and completion

Use `docs/testing.md` for verification scope and precise status language. Do not
claim that work is working, fixed, tested, or complete without an observable
result.

Before finishing meaningful work:

1. Determine exactly what changed and what remains outside scope.
2. Verify the smallest relevant behavior, then expand when boundaries require it.
3. Update only affected state, notes, decisions, documentation, and existing
   roadmap items.
4. Check consistency across code, configuration, and project knowledge.
5. Confirm unrelated files were not included.
6. Commit only completed task files when the active workflow requires a commit.
