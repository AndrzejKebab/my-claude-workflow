# Which rules does Claude actually obey?

A rule in `CLAUDE.md` is a hypothesis, not a mechanism. The file is injected as
context, so every line competes with the harness system prompt, the active skill
text, the tool descriptions and the conversation itself. Some rules win that
competition and some never do — and until it is measured, which is which is a
guess.

`bin/cc-rule-audit` measures it against the transcript archive.

```
cc-rule-audit                 # last 14 days
cc-rule-audit --days 30
cc-rule-audit --project p7    # only transcript dirs matching a substring
```

## Baseline, measured 2026-08-13 over 637 sessions / 14 days

| Rule | Compliance | Disposition |
|------|-----------|-------------|
| prefer fff over built-in `Glob`/`Grep` | fff 147, Glob/Grep 0 | Moot — the built-ins are gone from this harness. The `@FFF.md` import was dropped from `CLAUDE.md`; the MCP tool descriptions carry themselves. |
| read `AGENTS.md`/`CONTEXT.md` entire | full 90, partial 74 → **45.1%** | `cc-whole-file-reads` denies the partial call. |
| act; do not offer the next step | **322** hedges, 18.6 per 1000 blocks | `cc-no-hedge` refuses the stop. |
| never count the things you write about | **93** hits, 5.4 per 1000 blocks | `cc-no-hedge` refuses the stop. |
| `/i-have-adhd` | 9 of 637 sessions → **98.6% miss** | `cc-doctrine` loads the skill body instead — see below. |

## The two failure shapes

**A slash command in `CLAUDE.md` is not an invocation.** `CLAUDE.md` arrives as
context, so the model reads the literal string `/i-have-adhd` and may or may not
decide to call the `Skill` tool. Measured, it decides to 1.4% of the time. Any
rule expressed as "invoke X" in `CLAUDE.md` has this shape and scores near zero.
The fix is to load the body, not to reword the pointer.

**A rule that is never loaded is not ignored; it is absent.** `~/.claude/` holds
`CLAUDE_B`, `CLAUDE_C`, `HARNESS`, `NONDUAL`, `PROSE`, `VERIFY`, `RTK`,
`negative-space-expanded` and `FFF`, and `CLAUDE.md` imported exactly one of
them — `@FFF.md`, the moot one. Before adding any of the rest to
`DOCTRINE.list`, establish that it is live: **`CLAUDE_B.md`, `CLAUDE_C.md` and
`CLAUDE_D.md` are rejected variants of `CLAUDE.md`** — drafts that were tried and
did not work. They are unloaded on purpose and must stay that way. Loading a
graveyard is worse than loading nothing, because a rejected rule that reaches a
session outranks a live one that does not.

## The escalation ladder

Rank a rule by what happens when the model is mid-task and the rule is
inconvenient:

1. **Prose in `CLAUDE.md`** — advisory. Fine for taste and voice, where an
   occasional miss costs nothing.
2. **A skill file** — loaded on invocation, so it is fresh and verbose exactly
   when it applies. This beats memory: the `/research` model pin regressed to
   Opus after a compaction because the skill's own text argued for Opus while
   the contradicting fact sat in a memory file. The fix was to correct the skill
   text, not to restate the memory.
3. **A hook** — deterministic. The harness executes it; the model does not get a
   vote.

A rule that scores badly and matters is a rule at the wrong rung. Move it down.

## The hooks this repo wires, and why each is a hook

### `cc-doctrine` — SessionStart

Injects the files listed in `DOCTRINE.list` — currently `VOICE.md` and the
`i-have-adhd` skill body, 1847 tokens. Two reasons it is a hook rather than an
`@import` in `CLAUDE.md`:

- **It fires again after a compaction.** `SessionStart` carries a `source`
  field and `compact` is one of its values. An import is injected once; this
  comes back when the summary replaces the conversation. That is the exact
  moment rules go missing.
- **It arrives without the disclaimer.** Injected context is framed as "may or
  may not be relevant"; hook output is not.

`DOCTRINE.list` is paid on every session and after every compaction, so keep it
short and re-measure with `cc-rule-audit` before adding to it. Token costs are
recorded in the manifest's own header.

### `cc-no-hedge` — Stop

Blocks a turn whose last message hedges ("want me to", "say the word") or counts
("three of them"). Both rules are about the last thing written, which is exactly
what a Stop hook can see. Three properties it holds:

- **Never latch.** `stop_hook_active` is set when the harness is already
  re-running after a block; blocking then would loop forever, so that case exits
  clean.
- **Do not block quoted text.** The rules name their own banned phrases, so any
  turn discussing them contains them. Fenced code, inline code, blockquotes,
  table rows and double-quoted spans are data and are stripped before matching —
  the same reasoning that makes `no-latching-waits.sh` strip quoted spans.
- **Fail open.** A Stop hook that dies on a malformed transcript would end every
  turn with an error.

### `cc-whole-file-reads` — PreToolUse (Read, Bash)

Denies `Read` with `limit`/`offset` on `AGENTS.md`/`CONTEXT.md`, and `head`/
`tail` on them through Bash. The rule was never ambiguous and never forgotten —
a partial read is simply cheaper in the moment, and prose does not price that.
Denying the call does. Same shape as the `unity-cli editor refresh` deny already
in `settings.json`: the harness refuses, and the refusal carries the alternative.

### `cc-comment-wall` — PostToolUse (Write, Edit)

Enforces `VOICE.md` "Dose" — *"Comments are one-liners. A longer one earns its
place only by saying something the code cannot"* — and "Cut", which sends
self-narration to the commit message or nowhere. Blocks on 4+ contiguous `//` or
`#` narration lines and names the line numbers.

Doc comments (`///`, `/** */`, docstrings) pass; so do licence headers, SPDX
lines and preprocessor directives. File type comes from the extension, or from
the shebang when there is none — `bin/` scripts carry no suffix.

The same rule is stated more forcefully in `CLAUDE_D.md` ("write a documentation
page"), but that file is a rejected variant and is not the anchor. `VOICE.md` is
binding and live, so the hook quotes `VOICE.md`.

Note what it found on arrival: the pre-existing `bin/` scripts in this repo carry
headers of 9, 12, 17, 20, 22, 27 and 31 lines. The hook fires only on files
Claude writes, so those are not blocked retroactively — but the next edit to one
will ask for the relocation. That backlog is the measure of how long the rule
went unenforced.

## Prior art, checked before building

- [`karanb192/claude-code-hooks`](https://github.com/karanb192/claude-code-hooks)
  (MIT) ships a `dead-rules-audit` plugin that tallies rule compliance and
  renders a scorecard. It is live-session and edit-scoped
  (SessionStart/PostToolUse/SessionEnd), so it scores forward from install;
  `cc-rule-audit` is retrospective over the existing transcript archive, which
  is what made a 637-session baseline possible. Complementary.
  `/plugin marketplace add karanb192/claude-code-hooks`
- [`albertnahas/claude-core-values`](https://github.com/albertnahas/claude-core-values)
  (MIT) does SessionStart injection plus post-compaction re-injection plus a
  per-prompt motto, configured from `~/.claude/core-values.yml`. Same mechanism
  as `cc-doctrine`, as an installable plugin. `cc-doctrine` was kept because the
  doctrine files are already version-controlled here and the persistence order
  in `CLAUDE.md` puts the repo above a plugin — but core-values is the drop-in
  if this repo ever stops being the home.
- No off-the-shelf Stop hook blocks on output phrasing, and none denies partial
  reads of a named file. Those two are bespoke.

## Adding a rule to the audit

Text rules are data: append a `(label, compiled regex)` pair to `TEXT_RULES` in
`bin/cc-rule-audit`. Tool-shaped rules go in `tool_use()`, which sees every
`tool_use` block with its input.
