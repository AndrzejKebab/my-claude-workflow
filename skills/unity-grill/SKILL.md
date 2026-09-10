---
name: unity-grill
description: Interview the user relentlessly about a Unity plan, system design, or feature until reaching shared understanding, resolving each branch of the design tree. Use when the user wants to stress-test a Unity/game design or plan, get grilled on a gameplay system, or mentions "grill me" in a Unity project.
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the project, explore instead — the codebase, but also the things Unity plans hide in: asmdefs and package manifest, project settings, prefabs and scenes, data defs, existing ADRs and CONTEXT.md.

Beyond the plan's own logic, make sure these branches of the tree get walked — Unity plans habitually leave them unresolved:

- **Paradigm & placement** — MonoBehaviour, ECS, or hybrid? Which world/assembly does it live in, and what does it depend on? (Never treat "migrate paradigms" as an implicit part of the plan.)
- **Data & authoring** — where does the data live (defs, ScriptableObjects, baked components), who edits it (programmer, designer, modder), and what happens when it changes at runtime?
- **Hot path & budget** — does any of this run per-frame at scale? What's the frame/memory budget, does it need jobs/Burst, and what must the seam look like to allow that?
- **Lifecycle & ordering** — what creates it, what destroys it, what must run before what, and what happens on scene load/unload, domain reload, and mid-frame structural change?
- **Persistence** — what serializes, in which format, and what happens to saves from the previous version?
- **Multiplayer** — who has authority, what replicates, what's predicted, and what does this feature do under 150ms latency or a rollback? (Skip only if the project is genuinely single-player.)
- **Failure & editing** — what does the user/designer see when the data is invalid, and can the feature be inspected and tweaked without entering play mode?
- **Testing seam** — how will this be tested in EditMode? If the answer is "it can't be", that's a design problem to resolve now, not later.

Skip any branch that is genuinely irrelevant to the plan — but say so out loud, in one line, so the skip is a decision rather than an omission.
