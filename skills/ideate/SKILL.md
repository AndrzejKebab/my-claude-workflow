---
name: ideate
description: Clean-room idea generation with platform funnel. Two-agent pipeline — a generation agent sees ONLY the problemspace (never existing ideas) and writes draft concept docs; a separate classification agent reads both the drafts and existing concepts, deletes duplicates, and classifies survivors. Use when you want fresh creative directions uncontaminated by what already exists.
---

# ideate — Clean-Room Idea Generation

Two-agent creative ideation pipeline that enforces absolute anchoring isolation. Agent 1 (generator) sees the full problemspace but is never exposed to existing ideas — not for style matching, not for dedup, not for anything. It writes draft concept docs. Agent 2 (classifier) reads both the drafts and existing concepts, deletes duplicates, and classifies survivors into platform/technology camps.

## When to use

- Brainstorming game concepts, product ideas, feature directions, architectural approaches
- Any creative exploration where existing options might anchor thinking
- When the user says "generate ideas", "brainstorm", "what else could we do", "fresh ideas"
- When the existing idea pool feels stale or too similar

## Input

`/ideate <path to ideation-context file, or topic description>`

The argument is either a path to a context bundle file or a short description of what to ideate about. The orchestrator assembles the full context from the conversation, project state, and context file.

If no argument is given, infer the topic from the current conversation context.

## Procedure

### Step 1 — Assemble the context bundle

The orchestrator (you) reads the relevant files and assembles four things:

**Part A — Problemspace context.** Everything the generator agent needs to produce grounded ideas:

- Architecture / platform constraints (what the technology can and cannot do, cost model)
- User constraints (budget, team size, timeline, monetisation model, art pipeline, target platforms)
- Ecosystem reality (what exists, what has shipped, what patterns work)
- Asset/resource inventory (what the user already has to work with)
- User's stated interests and preferences (from the conversation)
- Market context (gaps, opportunities, proven models)
- Any domain-specific knowledge the agent needs

Inline this directly in the generator brief. Do not point the agent at files to read — the context must be self-contained in the prompt so the agent starts generating immediately without a research phase. Read the relevant files yourself and distill the key facts.

**Part B — Existing concept paths.** The file paths to all existing concept documents. For game-design ideation these live in `docs/gd-exploration/concepts/`, the canonical concept corpus. These go ONLY to the classifier agent (Step 3), never to the generator.

**Part C — Classification funnel.** Camp definitions, cross-cutting gates, and classification criteria. For game-design ideation the canonical source is `docs/gd-exploration/platforms/`: its funnel index (`README.md`) defines the current camp set and any **cross-cutting gates** (a camp shelved for the project, or a quantitative gate that routes between two camps), and the per-platform docs give capability detail. Point the classifier at the index first, then the per-platform docs — cite rather than restate. The classifier MUST apply the cross-cutting gates, not only per-platform architectural fit: a concept can fit a platform on capability yet be excluded by a gate. Do not rely on the classifier inferring gates from individual platform docs — the gates are stated in the index for exactly this reason.

**Part D — Output directory.** Individual concept docs are written to `docs/gd-exploration/concepts/` — the canonical game-design corpus, alongside the existing concepts the classifier dedups against. Preserve the assembled problemspace bundle (Part A) under `docs/gd-exploration/context/` so the session's inputs stay with the corpus. (For ideation outside the game-design domain, substitute the project's own `concepts/` directory.)

### Step 2 — Dispatch the generator agent

Dispatch a single agent (default: Opus) with Part A context only. The generator agent:

1. **Generates** N ideas (default 8-12, adjust based on scope)
2. **Writes each idea as a separate markdown file** in the output directory

The generator agent never reads existing concept docs. It never reads the output directory to match style. It writes its ideas using the default concept doc format (below) and returns a short status listing the files written.

#### Concept doc format

Each idea is written as `<output_dir>/<slug>.md` where slug is kebab-case from the title (e.g., `golem-pit.md`). The header table matches the shared structure used across `docs/gd-exploration/concepts/`, so a generated doc is indistinguishable from the existing corpus.

```markdown
# <Name>: <Short Genre Description>

| Field | Value |
|-------|-------|
| Elevator pitch | <one sentence — the hook, ≤ ~30 words> |
| Platform | <one of the camps in the project's platform funnel index (for game-design: `docs/gd-exploration/platforms/README.md`); the classifier sets this authoritatively in Step 3> |
| Est. cost at 1K CCU | <TeV/mo for SpacetimeDB; $/mo tier for Photon; VPS $/mo for Colyseus or custom> |
| Time to MVP | <N months> |
| Content pipeline | <Low / Medium / High — short note on art/content burden> |
| Asset coverage | <NN% from the owned library, or —> |

---

## Pitch

<2-4 sentences. What the player does, what makes it multiplayer, what the hook is.>

## Why it fits

<Which platform and why the core loop matches. Which owned assets help. How session structure aligns with monetisation.>

## What makes it interesting

<The angle nobody has explored. The mechanic that creates depth. The market gap.>
```

The generator writes no annotations, no dedup notes, no meta-commentary. Clean concept docs only.

### Step 3 — Dispatch the classifier agent

After the generator returns, dispatch a second agent with:

- The list of newly written draft files (from Step 2)
- The paths to all existing concept docs (Part B)
- The classification funnel definitions (Part C, if any)

The classifier agent:

1. **Reads all existing concept docs** to understand the current idea landscape
2. **Reads each new draft doc**
3. **Deletes** any new draft that substantially duplicates an existing concept (the file is removed from disk)
4. **Classifies** each surviving draft into a platform/technology camp by updating the `Platform` field in the doc's metric table (if a funnel is defined). Apply the funnel's **cross-cutting gates first** (e.g. a platform shelved for the project, or a quantitative gate that routes between two camps), then per-platform architectural fit. A concept that fits a platform on capability is still routed elsewhere if a gate excludes that platform.
5. **Returns** a short status: how many drafts reviewed, how many deleted as duplicates, how many survived, and the list of surviving files

The classifier writes no annotations into the surviving docs. It does not create summary files. It does not list what was deleted or why. It simply deletes dupes and updates the Platform field.

### Step 4 — Present results

When the classifier returns, present a concise summary to the user: a table of the new concept docs with name, platform camp, MVP estimate, and the one-line hook. Mention how many were generated and how many survived (as a single number, e.g., "12 of 15 survived"), but do not enumerate what was cut or why.

## Classification funnel

For game-design ideation, the canonical camp definitions are the per-platform docs in `docs/gd-exploration/platforms/` — read those and cite them rather than restating; the example below is illustrative and may lag the corpus. For other domains the funnel is the orchestrator's job to define. Each camp needs:

1. **Name** — the platform or technology stack
2. **Architectural profile** — what it is good at, what it costs, what it cannot do
3. **Classification signal** — the features of an idea that make it belong here

The classifier assigns camps based on architectural fit, not preference — but only after applying the funnel's cross-cutting gates (shelved platforms, quantitative routing gates). The question is two-stage: first, "does any gate exclude a platform or force a routing for this idea?"; then, "among the platforms the gates leave, which one's strengths does this core loop lean on?"

### Example: Game platform funnel (SpacetimeDB vs FishNet)

The two primary camps for this corpus, split by the `w_p` persistent-write-cadence gate. (Photon is shelved for the web-first roadmap — see the funnel index — so it is not a camp here.)

```
### Camp: SpacetimeDB

**Architectural profile:** Server-side Rust/WASM database — the authoritative state *is* the
database. Clients subscribe to SQL queries; the server pushes row diffs on change. TeV billing
penalizes high-frequency full-table scans. Single-threaded. No built-in physics.

**Best fit for:** Persistent / event-driven worlds whose state outlives the session and changes
on player action, not on a tick — turn-based, async, social, trading, crafting, building,
persistent open worlds.

**Classification signal:** State must persist and keep changing independent of any match — the
world exists when you are not in a match (`w_p` ≳ 10 writes/player/min). Built-in persistence
and a zero-infra backend are a fit.

### Camp: FishNet

**Architectural profile:** Self-hosted, server-authoritative Unity netcode (client-side
prediction, lag compensation, interest management) on per-match containers. In-match state
lives in the server's RAM; only boundary events persist (to Turso). Web-first over WebSocket
(Bayou) or WebRTC.

**Best fit for:** Real-time / session (room/match) games — racing, shooters, physics combat,
arena PvP — where the match is the unit of state and only outcomes persist between matches.

**Classification signal:** Authoritative state lives for the match and persists only at
session/match boundaries (`w_p` < 1 write/player/min). Continuous simulation *during* the match,
but no durable world *between* matches.

### The gate, and hybrids

Classify by `w_p` (persistent-write cadence): boundary-write ⇒ FishNet, continuous-persistence ⇒
SpacetimeDB — the ~1000× Turso write-cost cliff between them is the boundary. A concept needing
both a persistent world AND real-time matches is a hybrid (persistence on SpacetimeDB, live
matches on FishNet); classify as the dominant loop and note the other.
```

## Key principles

- **Absolute isolation.** The generator agent never sees existing concepts. Not for dedup, not for style matching, not for any reason. The clean-room guarantee is the entire value of this skill.
- **Two agents, two jobs.** Generator creates. Classifier curates. They never share context. The generator's output is the classifier's input.
- **Context quality over quantity.** The generator does not need every detail — it needs the constraints that shape what a good idea looks like. Distill, don't dump.
- **Honest dedup.** The classifier should genuinely delete duplicates, not stretch definitions to keep everything. A good dedup pass removes 10-30% of generated ideas.
- **Clean output.** No process artifacts in the concept docs. No annotations, no dedup notes, no meta-commentary. The surviving docs are indistinguishable from hand-written concept docs.
- **Opus for generation.** Creative ideation benefits from the largest model. The classifier can run on Sonnet — it is doing comparison and deletion, not creative work.
