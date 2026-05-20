---
name: prune
description: Prune context and memories — strip redundancy, preserve sharp rules, surface misplaced memories
---

# prune — Configuration Pruning Agent

Two jobs:

1. **Compact** all Claude configuration files. Every token costs context window space every session. Strip redundancy, preserve sharp rules.
2. **Review memory placement.** Surface memories that violate the persistence-layer rules (skill > memory > handoff > nothing). Memory is residue, not a dumping ground.

## Targets

1. `~/.claude/CLAUDE.md` — global rules
2. `CLAUDE.md` — project rules (repo root)
3. Auto-memory files in `.claude/projects/*/memory/`

## Workflow

### Step 1: Read all targets

Read all three layers. Build a mental model of what each one says.

### Step 2: Identify waste (compression)

Flag for removal:

- **Redundancy across files**: same rule stated in CLAUDE.md AND memory — keep in CLAUDE.md, remove from memory.
- **Redundancy with code**: implementation details obvious from source (function signatures, field names, module structure).
- **Redundancy with docs**: info already in `docs/ARCHITECTURE.md` or other checked-in docs.
- **Verbose phrasing**: multi-sentence explanations where one line suffices.
- **Stale information**: references to removed features, old APIs, resolved issues.
- **Generic advice**: rules that restate Claude's default behavior ("read files before editing").
- **Examples within rules**: if the rule is clear without the example, drop it.

Flag for preservation:

- **Sharp corrections**: "do X, NOT Y" gotchas from real bugs.
- **Non-obvious gotchas**: pixel format surprises, warmup frame counts, driver workarounds.
- **Hard rules**: user-mandated overrides of defaults.
- **Practical shortcuts**: constructor patterns, test helpers, paths that save lookup time.

### Step 3: Review memory placement

For each memory file, ask: **is this in the right persistence layer?** The rule (from global CLAUDE.md) is:

> Memory is ONLY for repeat-potential framework-level gotchas. Must be a token-saving prevention mechanism for future sessions. Order: skill file > memory > handoff > nothing. Memory is residue.

Categorize every memory:

- **KEEP** — sharp gotcha, environment-specific surprise, project-context fact, or framework-level rule the user explicitly mandated. Belongs in memory.
- **RELOCATE → skill** — the memory describes methodology (how a task should be done, how to dispatch agents, what to put in briefs, how to structure phases). This belongs **next to the work it governs**, in the canonical skill file at `/home/midori/_dev/my-claude-workflow/skills/<name>/SKILL.md` or the agent definition at `agents/<name>.md`. Memory is the wrong layer because methodology doesn't decay — once true, it should govern every invocation of that skill, not wait to be recalled.
- **RELOCATE → project CLAUDE.md** — the memory is a project-wide hard rule (no Bevy-only divergence, never run X as verification, etc.) that should be loaded every session for this project, not on-demand. If it's binding and project-scoped, it belongs in the project's `CLAUDE.md`.
- **RELOCATE → global CLAUDE.md** — the memory is a general behavioral rule that applies across all projects (e.g. "once user picks an approach, proceed; don't bounce back with implied-cost follow-ups"). If it's not project-specific, it belongs globally.
- **DELETE** — the memory is session-state masquerading as canon: a mid-session pivot that never validated across sessions, an obvious-from-defaults restatement, or a fact rendered moot by codebase changes. If it has no repeat-potential, it's dead weight.

**Heuristics for the categorize call:**

- If the memory body reads like "when dispatching X, do Y, Z" — that's methodology. RELOCATE → skill or agent definition.
- If the memory has the word "MUST" applied to every dispatch in this project — that's project-wide canon. RELOCATE → project CLAUDE.md.
- If the memory documents a one-time incident with no transferable rule extracted — DELETE.
- If the memory describes a sharp environment gotcha (TLS conflict, headless WebGPU dying, OS-specific package quirk) — KEEP. That's exactly what memory is for.
- If the memory contains "Why:" + a real incident + "How to apply" that generalizes — KEEP unless RELOCATE applies more strongly.

**Surfacing the review:** before relocating or deleting, present the user with the list of RELOCATE / DELETE candidates and their target layer (or deletion rationale). Don't move silently — relocations cross persistence layers and warrant confirmation. KEEP candidates need no surfacing.

### Step 4: Rewrite (compaction)

For each KEEP file, produce a compact version:

- One line per rule/fact where possible.
- Group related items under minimal headers.
- Use `code formatting` for identifiers, paths, commands.
- Remove all filler words ("Note that", "It's important to", "Make sure to").
- Merge near-duplicate entries.
- Remove section headers that have only one item (inline into parent).

### Step 5: Apply changes

- For KEEP files: overwrite with compact version.
- For RELOCATE → skill: read the target skill file, append the memory's load-bearing content in the appropriate section, then delete the memory file. The skill file's existing structure dictates phrasing — compact further when integrating.
- For RELOCATE → CLAUDE.md (project or global): append to the relevant section, then delete the memory file.
- For DELETE: remove the memory file.
- Update `MEMORY.md` index: drop entries for moved/deleted memories.

### Step 6: Verify

Count tokens before and after with `ttok` (e.g. `ttok < file`). Report:

- Per-file token reduction percentage.
- Always-loaded vs on-demand subtotals (CLAUDE.md + MEMORY.md index are always-loaded; individual memory files are on-demand).
- Count of relocations (memory → skill, memory → CLAUDE.md) and deletions, with a one-line justification for each.

## Rules

- **Never remove hard user mandates** (git rules, attribution rules, verification requirements, WASM build/test gates, worktree rules).
- **Never add new content.** This is subtraction-and-relocation only. When relocating into a skill or CLAUDE.md, the content is moving, not being authored.
- **Memory is cheapest to cut.** If something is in both CLAUDE.md and memory, delete it from memory.
- **CLAUDE.md is most expensive.** It's loaded every session. Every line must earn its keep.
- **Don't compact skills.** Skill files are only loaded on invocation and have their own structure; don't strip them. Moving content INTO a skill is allowed (Step 5) — compacting the skill itself is not.
- **Don't relocate silently.** RELOCATE / DELETE candidates are surfaced to the user before moving. KEEP-and-compact is done without confirmation.
- **A relocation is a one-way move.** After integrating memory content into a skill/CLAUDE.md and deleting the memory file, also remove its entry from `MEMORY.md`.
