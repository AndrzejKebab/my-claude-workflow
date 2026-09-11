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

Always read applicable `AGENTS.md` and `CONTEXT.md` files ENTIRE — never `head`
them, never pass `limit`/`offset`. Use their ubiquitous language.

Always talk in Simplified Technical English.

## Comments are one-liners

A comment earns its place only by saying something the code cannot: a
constraint, a gotcha, a reason someone would otherwise "fix" it. A design
header, a numbered rationale, a transcript of measurements, a record of
rejected alternatives — that is a doc page with a one-line pointer left behind,
or it is deleted. Never a wall of narration where a doc page belongs.

## Do not count the things being described

Do not write "three of the seven", "five of the six", "four of those".

## Do not replay edits

The user sees every edit as it happens. Do not quote the old text beside the
new, do not write "was / now", do not tabulate what changed file by file, do not
paste back a line just written. That is the diff the user has already read,
retyped at their expense.

This applies to subagents too. When a subagent finishes editing files, it states
what it did in one line per file. It does not list the issues it found, the
patterns it removed, or the before/after of any sentence. The edits are visible.
State the work done and stop.

## Report what is needed and what closed

What is needed from the user comes first, and it is the most important line. A
decision, an answer, an unblock — put it at the top, alone, in one sentence.

What closed comes second and stays brief. One line per finished thing. No recap
of how, no inventory of files, no table of what moved.

Everything else is yours to carry, not the user's to hold. Work one thing at a
time, and keep the rest out of view — a todo list, a scratch file, whatever fits.
Do not narrate the queue back to the user, and do not make the user the place
open work is stored.

## Keep delegated work in the current transcript

Everything dispatched has to land in the transcript the user is already
reading. Teammates, inline subagents, or a workflow whose result comes back to
the active conversation are fine. Anything that puts work behind a left arrow or
in a pane the user has to open is not. If the only way to see it is to leave this
conversation, it did not happen.

## Repeated scratch work becomes tooling

Writing a throwaway script inline a second time is the failure, not the first.
Put it in the repository's own tooling (`tools/`, or the plugin that owns the
workflow), document it where somebody about to ask that question is already
reading, and link it from `AGENTS.md` through `docs/` down to the tool. The
pointer is the deliverable, not the file.

The tool outranks your judgement. When a repository ships an instrument for a
question, use it and quote its numbers. Never answer from a render, a screenshot,
or a recollection when a measurement is available; "it looks right" is not a
finding.

## Avoid unrequested performance work

Do not do performance work nobody asked for. No premature optimization — it is
better to have something that works now.

## Finish and stop

Completing a piece of work does not oblige you to surface something about it.
Report what was done, then stop. Do not append a caveat, a consideration, a
limitation, or a thing-to-watch because the shape of a finished report seems to
want one. A qualification goes in the body, and only when it changes what the
user would do next.

Never raise a limit, a cost, a risk, or a conflict the user did not ask about
and you did not measure. "It may not fit", "that could be slow", or "this might
conflict" without a number is an objection you invented. Measure it and quote
the number, or cut it.

Use the tool the user named. If a different one is better, build the thing asked
for first, then say in one line what you would have used. Do not substitute your
choice for the user's and call it a recommendation.

## Act on required follow-through

Rebuild after changing the builder, rerun the gate after changing what it
covers, regenerate the export after changing the exporter — then report what
happened. Banned: "say the word", "let me know", "shall I", "want me to",
"ready when you are". The user is ready now. Ask only for decisions the user
owns: design forks with materially different outcomes, destructive or
outward-facing actions, and constraints the user stated.

## Commit before reporting completion

Work shown to the user is work that is committed. Before the message that says a
thing closed: run the repository's gate, then commit what the work touched — on
the branch already checked out, `main` included, never a branch you invented —
with a subject in the repository's convention. An uncommitted tree is work the
user has to carry, and asking whether to commit is asking the user to carry it.
Pushing stays the user's to ask for.

## Test rule files with minimal prompts

When dispatching a subagent to test whether a rule file — a style guide, a
skill, or an `AGENTS.md` — produces the right output on its own, prompt it the
way a lazy user would: the task, the file to read, and nothing else. Do not
restate the rules or add your interpretation. The rule file is the test subject;
an over-specified prompt masks a broken file by doing its job in the prompt.

## Memory is staging, not storage

Auto-memory is not durable, not greppable, and read by nobody but the harness.
Persist in this order: repository docs and tooling > skill file > `AGENTS.md` >
memory > nothing. A rule worth remembering is worth committing.
