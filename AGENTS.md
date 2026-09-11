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

FFF is an optional Rust file-search MCP server with frecency-ranked fuzzy
matching and Git-aware filtering. When it is available, use:

- `fffind` for fuzzy filename search;
- `ffgrep` for literal, regular-expression, or fuzzy content search;
- `fff-multi-grep` for multiple content searches in one call.

Use FFF after an existing Graphify graph and before built-in file search when it
fits the question. Built-in tools remain appropriate when FFF is unavailable or
a direct `rg` query is simpler. Install or update FFF only after reviewing its
current upstream instructions; do not execute a downloaded installer merely
because this guide mentions the tool.

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

## Instruction loading and language

Read applicable `AGENTS.md` and `CONTEXT.md` files in full. Do not truncate them
with partial reads. Use the project's established vocabulary and communicate in
Simplified Technical English.

## Comments are one-liners

A comment earns its place only by saying something the code cannot: a
constraint, a gotcha, or a reason someone would otherwise remove necessary
behavior. Design headers, numbered rationales, measurement transcripts, and
rejected alternatives belong in documentation with at most a short pointer in
code. Never leave a wall of narration where a document belongs.

## Do not count the things being described

Do not write phrases such as "three of the seven", "five of the six", or "four
of those".

## Do not replay edits

The user can see edits as they happen. Do not quote old and new text, produce
before-and-after tables, or paste back lines just written. State completed work
briefly. Subagents follow the same rule.

## Report what is needed and what closed

When user input is required, put the exact decision, answer, or unblock first in
one sentence. Then report completed work briefly. Keep internal queues and
scratch planning out of the user-facing report, and work on one thing at a time.

## Keep delegated work in the current transcript

Use teammates or inline subagents whose results return to the active
conversation. Do not place work in a separate task or hidden pane that the user
must open to discover the result.

## Repeated scratch work becomes tooling

If the same throwaway script would be written a second time, turn it into a
maintained tool in the owning repository or plugin. Document it where future
users will look and link from project instructions through documentation to the
tool.

When a repository provides an instrument for a question, use it and report its
measurements. Do not substitute a screenshot, visual impression, or recollection
when direct measurement is available.

## Avoid unrequested performance work

Do not perform speculative optimization. Make the requested behavior work first
unless performance work was requested or measurements establish the need.

## Finish and stop

Report completed work without adding a ritual caveat, limitation, risk, or
thing-to-watch. Include a qualification only when it changes what the user
should do next. Measure limits, costs, risks, and conflicts before raising them.

Use the tool the user named. If another tool would be preferable, complete the
requested approach first and mention the alternative briefly instead of silently
substituting it.

## Act on required follow-through

Rebuild after changing a builder, rerun a gate after changing what it covers,
and regenerate an artifact after changing its generator. Do not offer an obvious
next step that is already part of completing the task. Ask only for decisions
the user owns, including material design forks, destructive or outward-facing
actions, and stated constraints.

## Commit before reporting completion

Run the repository's relevant gate and commit the completed task files on the
current branch before reporting that work is closed. Do not create a branch
unless requested, and do not push unless requested.

## Test rule files with minimal prompts

When testing whether an instruction file or skill works on its own, give the
test agent only the task and the file to read. Do not restate or interpret the
rules in the test prompt, because that masks missing guidance in the file under
test.

## Memory is staging, not storage

Persist durable knowledge in this order: repository documentation and tooling,
then a reusable skill, then `AGENTS.md`, then provider memory, then nowhere. A
rule worth remembering is worth committing.
