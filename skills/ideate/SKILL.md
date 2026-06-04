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

**Part B — Existing concept paths.** The file paths to all existing concept documents. These go ONLY to the classifier agent (Step 3), never to the generator.

**Part C — Classification funnel (optional).** Camp definitions and classification criteria. Goes to the classifier agent.

**Part D — Output directory.** The concepts directory where individual concept docs are written. Look for an existing `concepts/` directory near the ideation context, or derive one from the project structure.

### Step 2 — Dispatch the generator agent

Dispatch a single agent (default: Opus) with Part A context only. The generator agent:

1. **Generates** N ideas (default 8-12, adjust based on scope)
2. **Writes each idea as a separate markdown file** in the output directory

The generator agent never reads existing concept docs. It never reads the output directory to match style. It writes its ideas using the default concept doc format (below) and returns a short status listing the files written.

#### Concept doc format

Each idea is written as `<output_dir>/<slug>.md` where slug is kebab-case from the title (e.g., `golem-pit.md`).

```markdown
# <Name>: <Short Genre Description>

| Metric | Value |
|--------|-------|
| Platform | <SpacetimeDB / Photon / Either> |
| Est. cost at 1K CCU | <TeV/mo or pricing model> |
| Time to MVP | <N months> |
| Content pipeline | <Minimal / Low / Medium / High> |

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
4. **Classifies** each surviving draft into a platform/technology camp by updating the `Platform` field in the doc's metric table (if a funnel is defined)
5. **Returns** a short status: how many drafts reviewed, how many deleted as duplicates, how many survived, and the list of surviving files

The classifier writes no annotations into the surviving docs. It does not create summary files. It does not list what was deleted or why. It simply deletes dupes and updates the Platform field.

### Step 4 — Present results

When the classifier returns, present a concise summary to the user: a table of the new concept docs with name, platform camp, MVP estimate, and the one-line hook. Mention how many were generated and how many survived (as a single number, e.g., "12 of 15 survived"), but do not enumerate what was cut or why.

## Classification funnel

The funnel is the orchestrator's job to define. Each camp needs:

1. **Name** — the platform or technology stack
2. **Architectural profile** — what it is good at, what it costs, what it cannot do
3. **Classification signal** — the features of an idea that make it belong here

The classifier assigns camps based on architectural fit, not preference. The question is: "given this idea's core loop, which platform's strengths does it lean on?"

### Example: Game platform funnel (SpacetimeDB vs Photon)

```
### Camp: SpacetimeDB

**Architectural profile:** Server-side Rust/WASM database with subscription-based state sync.
Clients subscribe to SQL queries; server pushes row diffs on change. TeV billing penalizes
high-frequency full-table scans. Single-threaded. No built-in physics.

**Best fit for:** Event-driven state changes, turn-based, async, social, trading, crafting,
building — anything where the server is idle between player inputs. Persistent worlds with
durable state. Information asymmetry via subscription filtering.

**Classification signal:** The idea's core loop has state changes triggered by player actions
(not ticks). Update frequency is low (< 1 Hz average per player). The game benefits from
built-in persistence and zero-infra backend. Web-first delivery.

### Camp: Photon (Fusion/Quantum)

**Architectural profile:** Dedicated game server with tick-based simulation, client-side
prediction, state synchronization at 10-60 Hz. Purpose-built for real-time multiplayer.
Mature physics integration, lag compensation, interest management.

**Best fit for:** Continuous physics simulation, real-time movement at high frequency,
competitive twitch-action, fighting games, racing, FPS, any game where sub-100ms latency
matters and the server must run physics every frame.

**Classification signal:** The idea's core loop requires continuous simulation (physics,
projectiles, real-time AI). Update frequency is high (> 2 Hz per entity). The game needs
client-side prediction and rollback. Latency-sensitive competitive play.

### Camp: Either / Hybrid

Some ideas work on both platforms with different tradeoffs. Classify as the BEST fit,
note the alternative.
```

## Key principles

- **Absolute isolation.** The generator agent never sees existing concepts. Not for dedup, not for style matching, not for any reason. The clean-room guarantee is the entire value of this skill.
- **Two agents, two jobs.** Generator creates. Classifier curates. They never share context. The generator's output is the classifier's input.
- **Context quality over quantity.** The generator does not need every detail — it needs the constraints that shape what a good idea looks like. Distill, don't dump.
- **Honest dedup.** The classifier should genuinely delete duplicates, not stretch definitions to keep everything. A good dedup pass removes 10-30% of generated ideas.
- **Clean output.** No process artifacts in the concept docs. No annotations, no dedup notes, no meta-commentary. The surviving docs are indistinguishable from hand-written concept docs.
- **Opus for generation.** Creative ideation benefits from the largest model. The classifier can run on Sonnet — it is doing comparison and deletion, not creative work.
