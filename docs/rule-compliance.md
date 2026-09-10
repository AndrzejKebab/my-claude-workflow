# Making agent rules effective

A rule written in an instruction file is guidance, not a guarantee. It competes
with system instructions, tool descriptions, loaded skills, conversation state,
and the immediate task. Use the lightest mechanism that provides the reliability
the rule actually needs.

## Enforcement ladder

1. **Documentation** — background knowledge and rationale.
2. **Agent instructions** — always-relevant behavior and project constraints.
3. **Skills** — detailed workflows loaded only when their trigger applies.
4. **Automation or hooks** — deterministic checks around tool actions.
5. **Tests and CI gates** — executable acceptance criteria for repository state.

Move a repeatedly missed, important rule toward executable enforcement. Do not
make global instructions longer simply because one situational workflow needs
more detail.

## Claude and Codex compatibility

- Put shared repository facts in `AGENTS.md` or linked project documentation.
- Keep `CLAUDE.md` for Claude-specific behavior or as a concise pointer to the
  same shared documentation.
- Install reusable workflows as skills for both providers where supported.
- Treat Claude hooks as Claude integrations; do not assume Codex executes them.
- Prefer repository tests and scripts when the rule must hold regardless of the
  agent used.

A literal slash-command name in prose does not necessarily invoke a skill. Use
the provider's actual skill mechanism, and keep essential constraints in the
loaded skill body rather than in an unrelated memory file.

## Designing deterministic checks

A safe hook or validation script should:

- Scope itself narrowly to the action it protects.
- Explain the refusal and name the valid alternative.
- Avoid recursive or latched blocking behavior.
- Treat quoted examples and generated content appropriately.
- Fail open when hook failure would otherwise disable unrelated work, unless
  security or data-loss risk requires fail-closed behavior.
- Be tested against both allowed and rejected inputs.

## Auditing

`bin/cc-rule-audit` can inspect Claude Code transcripts when that local archive
is available. Its results describe observed behavior in that environment, not a
universal compliance rate for every model or provider.

When auditing a rule:

1. Define an observable action or output pattern.
2. Deduplicate transcript records that describe the same model response.
3. Separate opportunities from actual violations.
4. Inspect false positives and false negatives.
5. Promote the rule only when the added enforcement costs less than recurring
   failures.

Keep old experiments and rejected instruction drafts out of the active setup.
Version control already preserves history when it is worth revisiting.
