# ADR Format

ADRs live in `docs/adr/` and use sequential numbering: `0001-slug.md`, `0002-slug.md`, etc.

Create the `docs/adr/` directory lazily — only when the first ADR is needed.

## Template

```md
# {Short title of the decision}

{1-3 sentences: what's the context, what did we decide, and why.}
```

That's it. An ADR can be a single paragraph. The value is in recording *that* a decision was made and *why* — not in filling out sections.

## Optional sections

Only include these when they add genuine value. Most ADRs won't need them.

- **Status** frontmatter (`proposed | accepted | deprecated | superseded by ADR-NNNN`) — useful when decisions are revisited
- **Considered Options** — only when the rejected alternatives are worth remembering
- **Consequences** — only when non-obvious downstream effects need to be called out

## Numbering

Scan `docs/adr/` for the highest existing number and increment by one.

## When to offer an ADR

All three of these must be true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will look at the code and wonder "why on earth did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If a decision is easy to reverse, skip it — you'll just reverse it. If it's not surprising, nobody will wonder why. If there was no real alternative, there's nothing to record beyond "we did the obvious thing."

### What qualifies

- **Architectural shape.** "The simulation runs at a fixed tick, decoupled from frame rate." "Sim is ECS; presentation is MonoBehaviour reading sim state."
- **Paradigm placement.** "Pathfinding lives in Burst jobs; job *assignment* stays managed because it touches modded C#." Where the managed↔ECS/Burst line sits is one of the most re-litigated decisions in a Unity project — write it down once.
- **Netcode authority and replication model.** "Server-authoritative; clients send Commands, never state." "Pawn positions are ghosted; inventories are not — they replicate on demand." These shape everything downstream and are brutal to reverse.
- **Serialization and save-format decisions.** Format, versioning strategy, what's guaranteed stable for old saves. Saves are a public contract with players.
- **Technology choices that carry lock-in.** Netcode stack, DI container, serializer, render pipeline, target Unity/package versions and the upgrade policy. Not every asset-store package — just the ones that would take a quarter to swap out.
- **Boundary and scope decisions.** "Presentation never writes sim state." "Mod DLLs may reference Chrust.ModApi only; the sim assembly is off-limits." The explicit no-s are as valuable as the yes-s — especially for a modding surface, where every accidental yes becomes a compatibility promise.
- **Deliberate deviations from the Unity-obvious path.** "We don't use OnValidate for def validation because X." "No singletons/`.Instance` — everything through DI." "Custom serializer instead of Unity's because Y." Anything where a reasonable Unity dev would assume the opposite — these stop the next person from "fixing" what was deliberate.
- **Constraints not visible in the project.** "Sim must stay deterministic across platforms for lockstep-style verification." "Frame budget for meshing is 2ms on the min-spec CPU." "Mods must load without recompiling the game."
- **Rejected alternatives when the rejection is non-obvious.** If you evaluated reflection-based system registration for mods and rejected it for stability reasons, record it — otherwise someone will suggest it again in six months.
