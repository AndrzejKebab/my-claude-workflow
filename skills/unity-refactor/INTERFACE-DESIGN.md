# Interface Design

When the user wants to explore alternative interfaces for a chosen deepening candidate, use this parallel sub-agent pattern. Based on "Design It Twice" (Ousterhout) — your first idea is unlikely to be the best, and in Unity the design space is wider than usual because paradigm (managed vs Burst, OO vs data-oriented) is itself a design axis.

Uses the vocabulary in [LANGUAGE.md](LANGUAGE.md) — **module**, **interface**, **seam**, **adapter**, **humble shell**, **leverage**.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem space for the chosen candidate:

- The constraints any new interface must satisfy — including Unity-specific ones: does it sit on a hot path (Burst/jobs required)? Which world/thread does it run on? What must remain designer-editable in the inspector or defs? What does netcode need to see (server-authoritative? predicted)?
- The dependencies it relies on, each classified per [DEEPENING.md](DEEPENING.md) — engine-free, engine-value, engine-loop-bound, remote-owned, external.
- A rough illustrative code sketch to ground the constraints — not a proposal, just a way to make them concrete.

Show this to the user, then immediately proceed to Step 2. The user reads and thinks while the sub-agents work in parallel.

### 2. Spawn sub-agents

Spawn 3+ sub-agents in parallel using the Agent tool. Each must produce a **radically different** interface for the deepened module.

Prompt each with a separate technical brief (file paths, coupling details, dependency categories, what sits behind the seam, hot-path/threading/netcode constraints from Step 1). The brief is independent of the user-facing explanation. Give each agent a different design constraint:

- Agent 1: "Minimize the interface — 1–3 entry points max. Maximise leverage per entry point."
- Agent 2: "Data-oriented — the interface is component data / blittable structs plus static Burst-compatible functions. No managed types across the seam. Design for jobs and chunk iteration."
- Agent 3: "Optimise for the most common caller — and in Unity the most common caller may be a *scene author or designer*, not code. Make the default case trivial in the inspector / defs, even at the cost of a wider code surface."
- Agent 4 (when the candidate has category 3–5 dependencies): "Design around a humble shell / ports & adapters — pure decision core, thin engine or transport adapters, EditMode-testable by construction."

Include the [LANGUAGE.md](LANGUAGE.md) vocabulary and the project's CONTEXT.md vocabulary in each brief so every design names things consistently with the architecture language and the domain language.

Each sub-agent outputs:

1. Interface — types, methods/systems, params, component data — plus invariants, ordering constraints, error modes, execution/world placement, and the **serialized surface** (what appears in the inspector or data defs)
2. Usage example showing how callers use it — code callers *and*, where relevant, what the scene/prefab/def setup looks like
3. What the implementation hides behind the seam
4. Dependency strategy and adapters per [DEEPENING.md](DEEPENING.md), including which asmdef it lives in
5. Test plan across the seam — what runs in EditMode, what (if anything) genuinely needs PlayMode
6. Trade-offs — where leverage is high, where it's thin, and the performance shape (allocations, virtual calls on hot paths, Burst compatibility)

### 3. Present and compare

Present designs sequentially so the user can absorb each, then compare in prose. Contrast by **depth** (leverage at the interface), **locality** (where change concentrates), **seam placement** (managed/Burst, code/data, client/server), and **iteration cost** (compile-time impact, EditMode vs PlayMode testability, designer workflow).

After comparing, give your own recommendation: which design is strongest and why, for *this* project's paradigm and performance envelope. If elements from different designs combine well, propose a hybrid. Be opinionated — the user wants a strong read, not a menu.
