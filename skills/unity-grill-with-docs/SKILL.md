---
name: unity-grill-with-docs
description: Grilling session for Unity plans that challenges the design against the project's domain model, sharpens terminology, and updates documentation (CONTEXT.md, ADRs) inline as decisions crystallise. Use when the user wants to stress-test a Unity/game plan against their project's language and documented decisions, or says "grill me with docs".
---

<what-to-do>

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

If a question can be answered by exploring the project, explore instead — the codebase, but also where Unity plans hide their answers: asmdefs and the package manifest, project settings, prefabs and scenes, data defs and ScriptableObjects.

Make sure the Unity design-tree branches get walked — paradigm & placement, data & authoring, hot path & budget, lifecycle & ordering, persistence, multiplayer authority, failure & editing, testing seam. The full branch list with phrasing lives in [../unity-grill/SKILL.md](../unity-grill/SKILL.md); skip a branch only out loud, in one line.

</what-to-do>

<supporting-info>

## Domain awareness

During project exploration, also look for existing documentation:

### File structure

Most projects have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-fixed-tick-simulation.md
│       └── 0002-server-authoritative-commands.md
├── Assets/
└── Packages/
```

If a `CONTEXT-MAP.md` exists at the root, the project has multiple contexts. In Unity these usually follow asmdef or feature-slice lines:

```
/
├── CONTEXT-MAP.md
├── docs/adr/                          ← project-wide decisions
├── Assets/Scripts/
│   ├── Sim/
│   │   ├── CONTEXT.md                 ← simulation domain (ECS world, defs)
│   │   └── docs/adr/
│   ├── Presentation/
│   │   └── CONTEXT.md                 ← rendering, VFX, UI vocabulary
│   └── Netcode/
│       └── CONTEXT.md                 ← replication, authority, prediction
└── Packages/com.studio.modapi/
    └── CONTEXT.md                     ← the modder-facing vocabulary
```

Create files lazily — only when there is something to write. No `CONTEXT.md`? Create it when the first term is resolved. No `docs/adr/`? Create it when the first ADR is needed.

## During the session

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'Block' as the def-level type and 'Voxel' as a placed instance — you just said 'spawn a block', which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. Game projects overload brutally: "spawn" (instantiate a prefab? create an entity? bake?), "item" (the def, an instance in the world, or a stack in an inventory?), "tick" (frame, fixed step, or sim turn?), "load" (scene, subscene, save, or asset?). Pick one meaning per word and name the others.

### Discuss concrete scenarios

Stress-test domain relationships with specific play scenarios that force precision at concept boundaries: "A colonist is hauling a stack when the chunk it came from unloads — does the Item still exist, and who owns it?" Invent the scenario that makes the fuzzy boundary hurt.

### Cross-reference with the project — not just the code

When the user states how something works, check whether the project agrees, and in Unity the project speaks in more than C#:

- **Code**: does the type structure match the claimed relationship?
- **Data defs / ScriptableObjects**: do def fields and asset names use the glossary's terms? A def field named `blockType` when the glossary says "Voxel" is a real conflict, not cosmetics — defs are designer- and modder-facing interface.
- **Prefabs/scenes**: does the hierarchy reflect claimed ownership? ("You said the Pawn owns its inventory, but the prefab has it on a sibling.")
- **Component data** (ECS): do the components that exist match the concepts being discussed?

Surface contradictions: "Your code despawns the whole stack, but you just said partial pickup is possible — which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch — capture as they happen. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).

`CONTEXT.md` stays totally devoid of implementation details. Not a spec, not a scratch pad, not a home for implementation decisions — a glossary and nothing else. Engine mechanics (which system updates it, whether it's Bursted, which prefab hosts it) never belong in a definition.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — genuine alternatives existed and one was picked for specific reasons

If any is missing, skip it. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).

</supporting-info>
