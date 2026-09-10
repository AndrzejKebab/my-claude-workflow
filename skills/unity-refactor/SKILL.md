---
name: unity-refactor
description: Find deepening opportunities in a Unity codebase — turn shallow MonoBehaviour/system tangles into deep, EditMode-testable modules — informed by the domain language in CONTEXT.md and the decisions in docs/adr/. Use when the user wants to refactor Unity code, improve game architecture, untangle god MonoBehaviours or manager singletons, extract logic from the engine for testing, consolidate coupled systems, or says "unity refactor", "deepen this", "make this testable".
---

# Unity Refactor

Surface architectural friction in a Unity project and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability (EditMode-first), AI-navigability, and iteration speed.

## Glossary

Use these terms exactly in every suggestion. Don't drift into "component," "manager," "service," or "boundary." Full definitions in [LANGUAGE.md](LANGUAGE.md).

- **Module** — anything with an interface and an implementation: function set, class, MonoBehaviour + helpers, ISystem + its component data, asmdef, prefab + scripts.
- **Interface** — everything a caller *or scene author* must know: types, invariants, error modes, ordering — plus serialized fields, required components, lifecycle assumptions, execution order, Burst constraints. **Serialized surface is interface.**
- **Implementation** — the code inside.
- **Depth** — leverage at the interface. **Deep** = a lot behind a little. **Shallow** = interface nearly as complex as the implementation.
- **Seam** — where an interface lives: DI-injected C# interface, ECS component data between systems, asmdef boundary, message topic. (Use this, not "boundary.")
- **Humble shell** — thin MonoBehaviour/ISystem touching engine state, forwarding to a deep engine-free core.
- **Adapter** — a concrete thing satisfying an interface at a seam.
- **Leverage** — what callers and scene authors get from depth. **Locality** — what maintainers get: change concentrated in one place (in code *and* in the scene hierarchy).

Key principles (full list in [LANGUAGE.md](LANGUAGE.md)):

- **Deletion test**: delete the module in your head. Complexity vanishes → pass-through (most `*Manager`s). Complexity reappears across N callers/scenes → it was earning its keep.
- **The interface is the test surface.** If testing needs a scene and pumped frames, the engine is inside the interface.
- **One adapter = hypothetical seam. Two adapters = real seam.**

This skill is _informed_ by the project's domain model: CONTEXT.md names good seams; ADRs record decisions not to re-litigate.

## Process

### 1. Explore

**Detect the paradigm first.** Check what the area under review actually runs on — MonoBehaviour/OO, ECS/DOTS, or a hybrid (common shapes: MonoBehaviour gameplay with jobified hot paths, or ECS sim with MonoBehaviour presentation). Everything downstream is paradigm-relative: friction patterns, seam choices, and test shapes differ, and **deepening never means migrating paradigms** — deepen a MonoBehaviour module *as* a MonoBehaviour module, an ECS module *as* an ECS module. In a hybrid, the managed↔ECS handoff is itself a seam to assess, and each side is deepened in its own idiom. Only raise a paradigm move if the user asks — and then it's a separate conversation, not a deepening candidate.

Read the project's domain glossary and any ADRs touching the area first.

Then use the Agent tool with `subagent_type=Explore` to walk the codebase. Don't follow rigid heuristics — note where you experience friction, watching for Unity's characteristic shapes:

Any paradigm:

- **Shallow extraction** — pure helpers split out "for testability" while the real bugs live in how they're called.
- **asmdef friction** — either none (every change recompiles everything) or speculative ones fencing hypothetical seams.
- Untestable-through-their-interface areas, and PlayMode tests that exist only because the logic never got out of the loop.

MonoBehaviour/OO code:

- **God MonoBehaviours** — one script owning input, rules, presentation, and persistence; understanding one feature means reading one 900-line file *plus* its inspector wiring.
- **Manager/singleton webs** — `X.Instance` chains where the deletion test fails; static state coupling scenes together invisibly.
- **Logic trapped in the engine** — rules readable only by entering play mode; `Update()` bodies mixing deciding with doing; tests that would need scenes.
- **Inspector-smeared behaviour** — a feature spread across five serialized references; no locality even if each script is small.

ECS/DOTS code:

- **God systems and missing data contracts** — systems with no clear "reads these, writes those" contract; everyone touches everything.
- **Managed/Burst seams in the wrong place** — forcing structural changes on hot paths, or managed interfaces where only data can cross.
- **Sync points nobody owns**, and job dependency chains no one can explain.

Hybrid projects:

- **A frayed managed↔ECS handoff** — conversions, copies, and lookups scattered across many call sites instead of concentrated at one owned seam.

Apply the **deletion test** to anything suspected shallow: would deleting it concentrate complexity, or just move it?

### 2. Present candidates

Present a numbered list of deepening opportunities. For each candidate:

- **Files** — files/modules/prefabs involved (inspector wiring counts)
- **Problem** — why the current architecture causes friction
- **Solution** — plain-English description of what would change, naming the dependency category from [DEEPENING.md](DEEPENING.md) and the intended seam
- **Benefits** — in terms of locality and leverage, and concretely how tests improve (what becomes EditMode-testable, which PlayMode tests die)

**Use CONTEXT.md vocabulary for the domain, [LANGUAGE.md](LANGUAGE.md) vocabulary for the architecture.** If CONTEXT.md defines "Job," talk about "the Job assignment module" — not "the JobManager," not "the job service."

**ADR conflicts**: surface a candidate that contradicts an ADR only when the friction justifies reopening it, marked clearly (_"contradicts ADR-0007 — but worth reopening because…"_).

Do NOT propose interfaces yet. Ask: "Which of these would you like to explore?"

### 3. Grilling loop

Once the user picks a candidate, drop into a grilling conversation. Walk the design tree — constraints, dependency categories, hot-path/Burst/netcode requirements, the shape of the deepened module, what sits behind the seam, what tests survive. [DEEPENING.md](DEEPENING.md) governs how each dependency category is handled and tested.

Side effects happen inline as decisions crystallize:

- **Naming a deepened module after a concept not in CONTEXT.md?** Add the term — same discipline as `/grill-with-docs` (see [CONTEXT-FORMAT.md](../grill-with-docs/CONTEXT-FORMAT.md)). Create the file lazily if absent.
- **Sharpening a fuzzy term mid-conversation?** Update CONTEXT.md right there.
- **User rejects a candidate with a load-bearing reason?** Offer an ADR: _"Want me to record this so future reviews don't re-suggest it?"_ Only when a future explorer would need it — skip ephemeral ("not now") and self-evident reasons. See [ADR-FORMAT.md](../grill-with-docs/ADR-FORMAT.md).
- **Exploring alternative interfaces for the deepened module?** See [INTERFACE-DESIGN.md](INTERFACE-DESIGN.md).
