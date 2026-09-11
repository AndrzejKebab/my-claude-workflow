---
name: refine
description: Turn a conversation, file, directory, URL, or pasted notes into a reusable Claude-and-Codex skill. Use when the user asks to preserve or refine a repeatable workflow, technique, or decision pattern.
---

# Refine a reusable skill

Use `/refine [source or description]` to extract durable, actionable guidance and save it in this workflow repository.

## Understand the source

Read only what is needed to understand the reusable technique:

- For this conversation, use the problem, evidence, corrections, and successful outcome already present in context.
- For local files or directories, inspect the relevant implementation and documentation rather than scanning unrelated content.
- For a URL, retrieve the referenced source with the available web tooling and preserve source attribution where it materially supports the skill.
- For pasted notes, distinguish tested guidance from hypotheses or personal preference.

Do not merely summarize the source. Identify:

- the repeatable outcome;
- the requests or situations that should trigger the skill;
- non-obvious constraints, failure modes, and stopping conditions;
- the smallest reliable workflow or supporting script;
- which details are examples rather than universal rules.

## Decide what should be created

A reusable capability belongs in `skills/<skill-name>/SKILL.md` in this repository. Use lowercase letters, digits, and hyphens for the folder and skill name, keep the name under 64 characters, and write a concise description that makes activation clear.

Do not create a skill when the extracted material is only:

- a project-specific fact that belongs in that project's documentation;
- a general preference that belongs in shared Claude/Codex instructions;
- a one-off fix with no repeatable decision or procedure;
- speculative guidance without enough evidence to act on safely.

If the best destination is an existing instruction document such as `CLAUDE.md` or `AGENTS.md`, explain the proposed change and obtain the user's confirmation before editing it. If a skill with the chosen name already exists, inspect it and ask before replacing or substantially changing its scope unless the user explicitly requested that update.

## Write the skill

Keep `SKILL.md` focused on guidance that changes an agent's decisions. Use this minimum structure:

```markdown
---
name: skill-name
description: What the skill does and when it should be used.
---

# Skill title

Purpose and essential workflow.

## Constraints

Only the non-obvious safety rules, invariants, or boundaries needed for reliable use.
```

Add `scripts/`, `references/`, or `assets/` only when they provide a concrete reusable benefit. Keep conditional or substantial detail in a linked reference instead of bloating `SKILL.md`. Do not add placeholder resources, a separate README, or duplicated instructions.

Preserve the user's intent without turning one incident or local path into a universal rule. Use project-neutral examples unless the skill is deliberately project-specific. Never copy credentials, private transcript content, machine-specific paths, or unrelated source material into the skill.

## Validate and report

Run the available skill validator against the completed folder. Also check that:

- YAML frontmatter parses and the folder name matches `name`;
- every referenced file exists;
- included scripts pass syntax checks and a meaningful safe test;
- the description is specific enough for Claude and Codex to discover correctly;
- no existing user content was overwritten unintentionally.

Keep the repository's `skills/` folder canonical; do not edit installed copies directly. Run the repository installer only when the user asks to update the active installations.

Report the source used, the extracted skill name, its exact repository path, and validation performed. If the source was not reusable enough for a skill, say where the knowledge belongs instead.
