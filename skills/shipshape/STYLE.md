# shipshape style canon (binding for all shipshape agents)

The calibration target is the cross-cutting property of the regarded C# codebases (dotnet/runtime, ppy/osu, Cysharp/UniTask, VContainer, FreyaHolmer/Mathfs): every convention is applied uniformly within the repo, comments exist only where the code cannot speak for itself, and the public API surface is deliberate. Internal consistency and subtractive discipline are the signal; no individual formatting choice is. The strongest "a careful expert wrote this" property is negative space: no comment deletable without information loss, no defensive check the type system already rules out, no doc that restates a member name.

## Naming

- Instance fields `m_PascalCase`, static fields `s_PascalCase`, constants `k_PascalCase` (the Unity engine-package family, preferred here for everything — it survives the `[SerializeField]` boundary where inspector nicification expects `m_`, and it makes field reads visible in long methods).
- Public types and members PascalCase per the Framework Design Guidelines: no Hungarian, no abbreviations, suffix conventions respected (`Async`, `EventArgs`, `Attribute`). Parameters and locals `camelCase`.
- ECS component data follows the Unity.Entities convention of the surrounding package (existing public `IComponentData` field casing is API — renaming it is an API break, not a style fix).
- New type names earn their suffix: a `*Pass` records render work, a `*System` is an ECS system. `Helper`, `Manager`, `Utils`, `Processor`, `Wrapper` are banned for new types — a type that cannot be named for what it owns is not yet a type.

## Layout and structure

- Allman braces, four-space indent, one type per file except trivially-coupled private nested types. File length follows concept boundaries, not a line budget — a 180-line complete concept and a 900-line overload family are both fine; splitting a coherent family to look short is not. Large API families split by feature via `partial` (the UniTask pattern), never by line count.
- Overload families are written in strict parameter-progression order with identical body shapes, so adjacent overloads diff by exactly the added parameter.
- Visibility is always explicit and first. `readonly` wherever applicable. Expression bodies for true one-liners only.
- `var` when the type is named on the right-hand side or is obvious from context; explicit types in public-facing sample code.
- No `#region` (one exception: a deliberately table-like math/constants file using regions as a table of contents).
- No legacy shims, no dead parameters, no "kept for compatibility" residue inside a package that controls its own consumers.
- Duplication is cheaper than the wrong abstraction. A near-duplicate family is unified into one block only when the instances share one reason to change and their differences reduce to data — values, a type (a generic), a selector (a delegate or small config struct) — never when a `bool`/enum flag must select which *unrelated* branch runs (the flag-argument smell), and never into a block nameable only by listing what it does (a `Helper`/`Manager` by another name). Default to leaving look-alikes duplicated; the full six-test discriminator and the discover → adjudicate → extract protocol are the commonality (E) pass in `SKILL.md`. A merge deliberately *not* made is recorded in the orchestration journal, never as a source comment.
- When a family IS true commonality, the proper form follows its cohesion and is whatever drastically improves the design — frequently architectural, not a method: a value type, a stateful owner of a scattered responsibility, a new seam, a data asset, a restructured subsystem, or a shape those examples do not name (the form space is open, not a closed set). A timid method-regroup chosen because it is the smaller change, when the cohesion points at a new type or seam, is a half-measure to reject — the bar is the architect's form, not the smallest diff (this counters the default pull toward minimal change). The two failures are symmetric: merging false commonality (over-abstraction), and under-solving true commonality (a shallow regroup). Go deep into the right abstraction; never a deep wrong one. The conviction for this — why the deep change beats the minimal one, grounded in the CS-design literature — is *On architectural courage* in `SKILL.md`; read it before an S or E item.

## Comments and documentation (the agreed policy)

- Every public symbol gets a one-line `<summary>` carrying information not derivable from the signature (the `Cbrt` standard: document the negative-value behavior that distinguishes it from `Pow(v, 1/3)`, not "returns the cube root"). `<exception>`/`<param>` tags where the contract is non-obvious. Internals are not doc-commented unless the invariant is load-bearing.
- Inline `//` comments state *why*, never *what*: compat constraints, allocation warnings, invariants, known defects (`TODO:` carries the actual defect), and algorithm citations by source URL or paper.
- One canonical home per fact. A contract stated in `Documentation~/` is referenced from code with a one-line pointer, not restated; a fact needed at four sites lives at one and is pointed to from three.
- Comments describe the current state of the code, never its history. "X removed", "the old code did Y", quoted deleted code, tuning-session numbers, and orchestration step references belong in git history or `Documentation~/` design notes — their presence in source is a tell.
- A citation is legitimate only when the reader of the *shipped* artifact can reach what it points at: upstream source they can fetch (`REF/<file>:<line>`, an upstream commit SHA), a paper, a URL, or a `Documentation~/` page that ships. A reference that resolves only against the producing process — an orchestration journal, a design document that does not ship, a chunk or phase plan (`chunk C3`, `design D4`, `design §6`, "the C4a core solve chain") — is a dangling pointer the moment it leaves the session that wrote it, so it is stripped to the self-contained fact it stood for, not preserved as provenance. This is the line a port-fidelity rule must not blur: faithful-port provenance keeps the reachable upstream citations and drops the process bookkeeping, never both as one undifferentiated mass.
- Target density band: 5–20% comment lines (XML docs on public API count toward the healthy side; in-body narration toward the pathological side).
- **Consolidation must compress, not relocate.** The canonical statement of a fact is itself subject to brevity: the fewest sentences that state the constraint, normally well under 8 lines — longer means the content is a contract that belongs in `Documentation~/` behind a one-line pointer.
- A canonical comment never enumerates its consumers or downstream effects — the pointer comments at the consumer sites encode that relation, and an enumeration drifts stale with the first new consumer.
- One fact, one paragraph: never write "exactly like X" and then restate X's content anyway. Cross-reference, don't mirror.
- Proportionality check: a comment block substantially longer than the code it guards is suspect by default (22 lines over three one-line predicates is the canonical counter-example). The audience test for every sentence: would a maintainer of *this file* make a mistake without it? Drop everything that only proves the author understood the system.

## Unity-specific

- Runtime math in DOTS-adjacent packages: `using static Unity.Mathematics.math;`, `float3`/`float4x4` over `Vector3`/`Matrix4x4`, per the consuming project's conventions.
- Unity message methods and `[SerializeField]` fields are engine-referenced: never delete as "unused", never rename serialized fields without `[FormerlySerializedAs]`.
- HLSL: `#pragma once`, not `#ifndef` guards.
- csharpier is the formatter; a trailing `//` preserves a hand-authored break — use it only where the break carries meaning csharpier would destroy, never as a reflex on every line.
- csharpier has no model of the *logical* grouping inside a multi-argument literal, so it flattens a structured constructor to either one long line or one-argument-per-line, both of which hide the structure a reader needs. Restore the grouping with the trailing-`//` idiom at logical-group boundaries: a `floatNxN` matrix is one row per line, a color is RGBA on one line, a vector's components stay together. The `//` makes the layout survive every later csharpier pass. The regrouping must be token-identical to what csharpier produced — only whitespace and the trailing markers change; a matrix transposed or an element dropped during regrouping is a correctness bug, so it is verified token-equal (`git diff --ignore-all-space` shows only `//` additions) and behind the test gate.

```csharp
// csharpier output (flattened — row structure lost):
Value = new float4x4(c, -s, 0f, p.x, s, c, 0f, p.y, 0f, 0f, 1f, 0f, 0f, 0f, 0f, 1f),

// repaired (one matrix row per line, survives future csharpier passes):
Value = new float4x4(
    c, -s, 0f, p.x, //
    s, c, 0f, p.y, //
    0f, 0f, 1f, 0f, //
    0f, 0f, 0f, 1f //
),
```

## The tell blacklist (zero tolerance in new/edited code)

1. Narration comments (content overlaps the line below: `// Increment the counter`).
2. Tautological XML docs (`<summary>Gets the value.</summary>` on `GetValue`).
3. Marketing vocabulary in comments: robust, comprehensive, seamless, gracefully, easily, simply, "ensures that", "it's important to note", "for clarity".
4. Emoji or checkmark glyphs in source or log strings.
5. Blanket `catch (Exception)` as defensive wrapping; log-and-continue where an invariant should throw.
6. Null checks the type system or construction order already rules out.
7. New `Helper/Manager/Utils/Handler/Processor/Service/Wrapper` types.
8. Dead parameters, unused usings, "for backward compatibility" remarks without an external consumer.
9. Enumerated boilerplate where a computation or existing API expresses it directly; redundant `else` after `return`.
10. Idiom inconsistency with the host file (mixed `var`/explicit, `Mathf` beside `Unity.Mathematics`).
11. Change-history narration in comments, and references to a non-shipping process artifact — chunk/phase labels (`chunk C3`), design-decision tags (`design D4`, `motion-drive D6`), design-section pointers (`design §6`, `design section 5`) — that a reader of the shipped package cannot resolve (see Comments section).

## Calibration excerpts

VContainer (`ContainerBuilder.cs`, github.com/hadashiA/VContainer) — names carry all meaning, zero comments, nothing missing:

```csharp
[MethodImpl(MethodImplOptions.AggressiveInlining)]
public IScopedObjectResolver BuildScope()
{
    var registry = BuildRegistry();
    var container = new ScopedContainer(registry, root, parent, ApplicationOrigin);
    container.Diagnostics = Diagnostics;
    EmitCallbacks(container);
    return container;
}
```

dotnet/runtime (`Random.cs`) — the only inline comment records a *why* (compat constraint) no signature could carry:

```csharp
/// <summary>Initializes a new instance of the <see cref="Random"/> class using a default seed value.</summary>
public Random() =>
    // With no seed specified, if this is the base type, we can implement this however we like.
    // If it's a derived type, for compat we respect the previous implementation, so that overrides
    // are called as they were previously.
    _impl = GetType() == typeof(Random) ? new XoshiroImpl() : new CompatDerivedImpl(this);
```

Mathfs (`Mathfs.cs`, github.com/FreyaHolmer/Mathfs) — a `<summary>` that adds real information, and an algorithm citation:

```csharp
/// <summary>Returns the cube root of the given value, properly handling negative values unlike Pow(v,1/3)</summary>
[MethodImpl( INLINE )] public static float Cbrt( float value ) => MathF.Cbrt( value );

/// <summary>Returns the binomial coefficient n over k</summary>
public static ulong BinomialCoef( uint n, uint k ) {
    // source: https://blog.plover.com/math/choose.html
```
