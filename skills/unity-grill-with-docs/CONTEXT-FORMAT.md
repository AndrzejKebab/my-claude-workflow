# CONTEXT.md Format

## Structure

```md
# {Context Name}

{One or two sentence description of what this context is and why it exists.}

## Language

**Pawn**:
A simulated colonist or creature the player can observe and (for colonists) direct.
_Avoid_: unit, agent, character, actor

**Voxel**:
A placed instance of a Block occupying one cell of the world grid.
_Avoid_: block (that's the def-level type), tile, cube

**Blueprint**:
A player-placed order to construct something; consumes Items when a Pawn builds it.
_Avoid_: ghost, plan, pending build
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others as aliases to avoid.
- **Flag conflicts explicitly.** If a term is used ambiguously, call it out in "Flagged ambiguities" with a clear resolution.
- **Keep definitions tight.** One or two sentences max. Define what it IS, not what it does.
- **Show relationships.** Use bold term names and express cardinality where obvious.
- **Only include terms specific to this game's domain.** Engine vocabulary — MonoBehaviour, prefab, entity, system, subscene, job, ScriptableObject — never belongs, no matter how often the project says it. Same for general programming concepts. Before adding a term, ask: is this a concept unique to this game, or a Unity/programming concept? Only the former belongs.
- **Def/asset names are part of the language.** The glossary term should be the word used in code identifiers, def files, asset names, *and* player-facing UI where feasible. When the player-facing word must differ from the internal word (localisation, tone), record both: "internally Pawn, shown to players as 'Colonist'."
- **Group terms under subheadings** when natural clusters emerge (World & Terrain, Pawns & Work, Items & Building). A flat list is fine for a single cohesive area.
- **Write an example dialogue.** A conversation between a dev and a designer that demonstrates how the terms interact naturally and clarifies boundaries between related concepts.

## Single vs multi-context projects

**Single context (most projects):** One `CONTEXT.md` at the repo root.

**Multiple contexts:** A `CONTEXT-MAP.md` at the repo root lists the contexts, where they live, and how they relate. In Unity, context lines usually follow asmdef or feature-slice lines — simulation vs presentation vs netcode is the classic split, and a modding API is its own context because modders are its audience:

```md
# Context Map

## Contexts

- [Sim](./Assets/Scripts/Sim/CONTEXT.md) — the deterministic colony simulation: world, pawns, work
- [Presentation](./Assets/Scripts/Presentation/CONTEXT.md) — how the sim is rendered and narrated to the player
- [Netcode](./Assets/Scripts/Netcode/CONTEXT.md) — replication, authority, commands, prediction
- [ModApi](./Packages/com.studio.modapi/CONTEXT.md) — the stable vocabulary exposed to modders

## Relationships

- **Sim → Presentation**: Presentation reads sim state; it never writes it. Terms may differ (Sim "Pawn" is presented as "Colonist").
- **Netcode → Sim**: player intents arrive as Commands; the server-authoritative Sim applies them
- **ModApi ↔ Sim**: ModApi re-exports a stable subset of Sim vocabulary; renames there are breaking changes
```

The skill infers which structure applies:

- If `CONTEXT-MAP.md` exists, read it to find contexts
- If only a root `CONTEXT.md` exists, single context
- If neither exists, create a root `CONTEXT.md` lazily when the first term is resolved

When multiple contexts exist, infer which one the current topic relates to. If unclear, ask. The same concept may legitimately carry different names across contexts (Sim's "Pawn", Presentation's "Colonist") — that's a mapping to record in `CONTEXT-MAP.md`, not a conflict to eliminate.
