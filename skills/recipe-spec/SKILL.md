---
name: recipe-spec
description: Author a language- and stack-agnostic, recipe-grade technical specification of an existing system, written for an implementor (human or agent) who will rebuild it in another language. Orchestrates one compound sub-agent per minimally-scoped document, each reading the source code (the authority) plus any reference paper/talk (context only) and writing its own doc to disk. Enforces one abstract form (never per-language examples, never us-vs-them comparisons), explicit step-by-step recipes (no black boxes), and Markdown/Mermaid hygiene. Use when asked to document a messy or convoluted codebase as a clean spec, to write a rewrite/porting spec, or to produce implementor-grade technical docs from working code.
---

# Write the spec as a recipe book an implementor can build from, not a tour of the code.

The deliverable is **explicit, language-agnostic technical documentation that hands an implementor solutions**, not a description of the existing program. The reader is rebuilding the system from scratch in a language and stack you do not know, assuming only industry-standard methodology (a thread pool, a hash map, floored integer division, a row-major buffer). Two failure modes define the work by their absence: vagueness (a step named but not walked) and concreteness-to-the-wrong-thing (tying the abstraction to one language, or to the reference implementation's incidental choices). Everything below fences off those two.

## Source of truth (binding)

- **The code at current HEAD is the authority.** Every load-bearing claim is verified against `file:line`, not against memory, not against the doc's own prose tables, not against a paper.
- **A reference paper, talk, or design doc is *context only*** — intent, naming, lineage. It is never authoritative on the algorithm. Where it and the code disagree, the code wins, and you write what the code does.
- The orchestrator reads enough of the code and the source material first-hand to design the document set and author the shared vocabulary; the per-document detail is the sub-agents' job, read by them, from the code.

## One abstract form — never N examples, never us-vs-them (binding)

This is the rule the work most often gets wrong, and the one to hold hardest.

- **"Abstract" means one generalised form, not a worked example per language.** When the brief lists target languages (C++, C#, Rust, Zig, …), those are the set to generalise *across*, not content to enumerate. A column-per-language table, a per-language declaration block, or a "here's how each language does it" mapping is the precise opposite of what was asked — delete it and state the single form that subsumes them.
- **The only legitimate generalisation is over a property or category, not over named instances.** "A contract is realised by monomorphization or by a vtable." "A type system either models aliasing or it does not." "The safe-travel margin is half the scheduling cell." Those are abstract. "Rust uses a trait, C# an interface, C++ a concept, Zig a vtable" is four examples wearing a table.
- **No us-vs-them dichotomy.** Do not run a "the reference does X, whereas the source/talk does Y" comparison; it is redundant and it frames the system as a debate. State the method directly. Cite the reference's canonical numbers and names **once, as lineage** (the algorithm's name, the worked figures), never as a rival to argue against across the document.
- Name techniques generically — "an associative map", "a mutable handle", "a build-time-specialised generic" — never a host framework, library, or language keyword in the body. Host-stack names appear only in an agent's author-facing *Side notes*, never in the spec text.

## Fixed vs movable — document the design space, mark the altitude (binding)

A spec serves the implementor only when it separates what they **must preserve** from what they **may choose**. Two kinds of fact live in it:

- **Invariants** — properties the method breaks if violated: the atomic operation, a scheduling non-adjacency guarantee, a co-indexing relationship between layers, a sentinel value's meaning, a coordinate's signedness. The rewrite must honour these exactly.
- **Reference choices** — one valid point in a design space that the reference happened to pick: a packed struct for an element, a tile size, a field's byte width, the existence of a stored field, an array-of-structs versus a structure-of-arrays storage layout. A different workload will want a different point, and the rewrite is free to take it.

**Documenting a reference choice as if it were an invariant is a defect — the rigid-shape failure — and it is as harmful as vagueness.** "Here is the array; it has exactly this shape, these four bytes" reads as a requirement when it is one option; it over-constrains the implementor and hides the design space they are entitled to explore. A movable element is documented instead as **the invariant it must satisfy, plus the factors that decide the choice, plus the reference's pick as one worked example** — never as a fixed shape. (For a per-element storage layout, the invariant might be "each cell is a co-indexed point across layers; the behavioural basis is mandatory", the factors are co-access set, write cadence, output-path membership, width and growth, spatial resolution, optionality, and lifetime, and the reference's packed struct is one example.)

This is the counterweight to *one abstract form*, and the two are reconciled by a single question: **does a fixed contract pin one right realization, or is there a genuine workload trade-off?** Equivalent realizations of a fixed contract (the same interface in four languages) collapse to the one abstract form — never enumerate them. A genuine trade-off the implementor must make for their workload (a storage layout, a resolution, an algorithm with a different cost profile) is the opposite: surface the design space and the deciding factors, because pretending there is one answer is the same defect as enumerating fake ones.

**The abstraction altitude of any element is a dial the user can turn, per element, at any time.** "Treat this more abstractly" raises it to the design-space form; "pin this" lowers it to a concrete reference layout. Do not assume the altitude chosen first is final — re-treat an element on request, and when an element's altitude is genuinely uncertain (is this load-bearing or incidental?) ask rather than silently freezing it. Make the **core/periphery split visible**: the behavioural basis the rules run on is the stable spine, while presentational and transient-control data are the movable periphery, and the implementor needs to see which is which to know where their freedom lies. Apply the marking *uniformly* — a spec that flags its algorithmic choices as tunable but pins its data-layout choices as rigid has simply not noticed that both are choices. Surfacing what is deliberately left open is as load-bearing as stating what is fixed.

## Recipe-grade, no black boxes (binding)

- **Every load-bearing step is walked.** "The view resolves which chunk holds it" is a failure: spell out decompose → look up → index → boundary case, as numbered steps. If the implementor must execute a named algorithm (marching squares, Douglas–Peucker, flood fill, a ray-march), the document walks the procedure, not just the name and a formula.
- **Separate the hot inner loop from cold seams, and make the hot loop the most explicit thing in the spec** — it is what the implementor builds first and cannot get from anywhere else. A worked scenario ("simulating one tile, step by step") is the strongest form.
- Algorithms as numbered steps or short language-neutral pseudocode; **no implementation code** in the method documents. Data structures as field tables. Flows, state machines, and sequences as Mermaid. Quantitative facts as LaTeX, one equation per `$$` block. Reference a formula's canonical home rather than restating it.
- A small worked illustration (a tiny input → its trace) earns its place wherever the prose alone would leave ambiguity.

## The document set

- A **README** (index, explicit in-scope / out-of-scope, reading order, one-line purpose) and an **architecture anchor** (glossary, the data and spatial model, the master loop, conventions, reference constants) come **first and are authored by the orchestrator**, because they pin the shared vocabulary every other document must use. Scope tightly: exclude incidental infrastructure and UX (spawning, console, persistence, streaming) unless that infrastructure *is* the subject.
- Then **minimally-scoped numbered documents, one concern each.** A document owns its facts and **cross-links rather than restates** a neighbour's — one canonical home per fact. Mark optional layers optional. An implementation-contract layer (data schemas, ownership/memory, interface seams) is its own tier, distinct from the method docs.
- Each document is self-contained at the level of *what to build and why*, links to siblings by relative path, and ends with a `## Side notes / observations / complaints` section (below).

## Orchestration shape

- The orchestrator **scopes, briefs, and verifies; it does not absorb agent prose and rewrite it.** Sub-agents do the analysis *and* write their own document to disk, returning a one-line status (`done — wrote <path>, N sections`). Content passes through context once (code → agent → doc), never twice.
- **One compound sub-agent per document**, dispatched in parallel when they write distinct files (no write contention). Each agent's brief: read the anchor for vocabulary; read its specific code files (the authority) and the relevant source-material scenes (context); write its doc under the binding rules above; never touch another doc; preserve any generalisation already done.
- For a coherent multi-document deliverable, author the anchor yourself first, then fan out, then do a harmonisation read-pass (terminology drift, cross-links).
- Put the binding rules of this skill into **every brief** — abstraction, recipe-grade, source-of-truth, hygiene — because an unbriefed agent reverts to per-language tables and named-not-walked algorithms by default.

## Markdown & Mermaid hygiene (binding)

- **Mermaid `sequenceDiagram` message text is not free-form.** `;` and `+` are lexer-level statement delimiters; either one inside a message label ends the message early and the parser then demands an arrow ("got NEWLINE"). Keep message text to commas, "and", em-dashes. `<br/>` is fine.
- **Pixel grids and spatial layouts render tiny and misaligned inside Mermaid nodes.** Draw them in a monospace ```` ```text ```` block with hand-aligned ASCII instead; reserve Mermaid for flows, sequences, and state machines — the things that are actually graphs. A flowchart laid `LR` with many nodes goes wide and unreadable; prefer `TD` / stacked when it must stay compact.
- Quote node and edge labels; valid shape syntax (`(( ))`, `([ ])`, quoted edge labels) is not a leak.

## Writing register

Match the prepared-notes voice of a confident speaker's slide notes: complete sentences that state the structural fact, not telegraphic fragments and not runtime narration of an actor performing actions. No hard-wrapping — one source line per paragraph, let the renderer wrap. Preserve list structure when the content is a list. Drop ceremony, not load-bearing content (keep the index and range on a `\prod`, the arity on a tuple). This is the global writing register; it binds here too.

## Verification before "done"

Confirm, per file, by running the checks — never by asserting:

- Balanced code fences and balanced `$$` (even counts).
- Cross-link anchors resolve: GitHub slugifies a heading to lowercase, spaces→hyphens, punctuation dropped, ` / ` leaving a double hyphen — check the target heading exists in that form.
- No leaked framework/language tokens in document **bodies** (grep for the host stack and the target-language names; allow them only inside `## Side notes`).
- Mermaid blocks parse and pixel art aligns (read the rendered shape, not just the source).

## Negative space — the Side-notes discipline

Every dispatched document ends with `## Side notes / observations / complaints`: what the agent found that the spec author should know but that does not belong in the spec body — rotten code, a gap between the intended design and what the code actually does, surprising ownership, a dead field, a step the code takes that contradicts the prose. **These are load-bearing for a rewrite:** "this layer is intended but unimplemented", "this guarantee is upheld by convention, not by the type system", "this contour walk does not normalise winding" are exactly the bricks a re-implementor hits in the dark. What the system *does not do*, and why, is documented as deliberately as what it does.
