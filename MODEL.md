# MODEL — constructive data modeling (binding)

Governs how data types are defined, in any language with product and sum types. [[NONDUAL.md]]
governs the reasoning and [[PROSE.md]] the sentence; this file governs the shape of the data the
reasoning runs on. Wrong shape and every downstream defence — the validator, the assert, the
comment — is maintaining an invariant the type could have held for free.

Distilled from Alexis King, *The Unreasonable Effectiveness of Constructive Data Modeling*, SSW
2026. Store the full extraction in `research-library/Prepared/` when it is available locally.

## The move

Encode an invariant by choosing a representation whose **representable values are already exactly
the legal values**. Build the type up out of constructors until it admits what you want, instead of
declaring a wider type and carving the illegal states back out with a comment, an assert, or a
validator.

The payoff runs opposite to the usual expectation, and that inversion is the reason to reach for it:
constructing needs *less* type-system machinery than restricting. `NonEmptyList<T> = (T, List<T>)`
is a tuple and a generic. `List<T> where length > 0` needs a solver inside the type checker. Same
invariant; the constructive form runs on a type system from the 1970s.

Required ingredients, in full: product types, sum types, and exhaustiveness the compiler actually
checks. Everything past that is convenience — welcome, never a precondition.

## The four rules

1. **Define the positive space, not the negative space.** `type Natural = Int where >= 0` subtracts
   from a set and needs refinement types. `NonEmptyList<T> = (T, List<T>)` adds to one and needs
   nothing. Reach for the additive form first.
2. **Decouple representation from interpretation.** "My data is an array, so it has an array type"
   is the move that blocks rule 1. "My data is a sequence of one or more elements, which *can be*
   represented by an array" leaves the representation free — and changing the representation is
   where the invariant gets encoded. `TimeRange { start, end } where start <= end` becomes
   `TimeRange { start, duration }`, and the ordering invariant is now structural because a
   `Duration` cannot be negative.
3. **Encode the obligations needed to write total functions.** A total function returns a value for
   every input it accepts. Strengthen a type at exactly the sites where a weaker one would force an
   unreachable branch.
4. **Push obligations to the place best equipped to handle them.** Types relocate obligations, they
   do not delete them. `notifyAboutFailure(user: Option<User>)` looks generous at the call site and
   hands the callee a `None` branch with no answer; `notifyAboutFailure(user: User)` makes the
   callee total and pushes the hole back to the caller, which usually knows what to do with it.
   Choosing a signature is choosing *where* failure gets handled.

## The test that decides how much type to spend

**Precision is not the target. Panic-count is.** At each site, ask: *where would I have to write
"this can't happen"?*

- `calculateTotal(entries: List<LogEntry>)` — `List` is right. Summing an empty list is zero, and
  no branch goes unreachable.
- `getLastChanged(entries: List<LogEntry>)` — `List` is wrong. `.head` forces a `None` branch with
  nothing to put in it. Take `NonEmptyList` and the branch is gone.

Same domain, same data, different answer, decided per function. This applies one function at a time
and needs no adoption decision.

It cuts against over-typing just as hard as against under-typing, which is the failure mode readers
of "parse, don't validate" hit most often. King represents email addresses as `String`, because no
code in her system inspects their structure — it hands them to an email service. A wrapper type
there buys a speed bump, not safety. **Types as simple as possible, no simpler.** A type consumed
in one place buys nothing at all.

## The mechanism

A type system is an **obligation propagation machine**. Each definition wires the places that
produce a value to the places that consume it, and exhaustiveness checking is the wire. Add a case
to an enum and the compiler names every consumer that must now handle it, however far apart producer
and consumer sit — across modules, across a database round-trip.

That gives "which representation?" an operational answer: **pick the one whose case structure
matches the cases the code actually has to handle.**

It also tells you what to do when a requirement arrives. A system user with no email and no phone
is not a `contact: Option<UserContact>` beside an `isSystemUser: Boolean` — that pair reintroduces
the comment stating a rule nothing enforces, and admits `contact: None, isSystemUser: false`. It is
a **fourth case on the existing sum type**. Two fields collapse to one and the illegal combinations
stop existing.

## Where this does not hold

Rule-shaped guidance that never loses is guidance that was never checked. This one has a known
domain:

- **A domain still in motion.** The ripple that makes rule 3 valuable — a new case reaching every
  consumer — is churn when the case set changes weekly. One mechanism reads as the feature while
  the case set is stable and as the cost while it moves. Name which regime you are in before
  committing.
- **Boundaries you do not own.** DB rows, JSON payloads, generated ORM/protobuf/OpenAPI types
  arrive already in the negative-space shape. The constructive type becomes a mapping layer, and it
  earns its place only if enough code lives behind the mapping to amortise it.
- **Languages without real sum types.** Go, C, pre-sealed Java: a sum costs a visitor or a tagged
  struct plus discipline — and once discipline is load-bearing the invariant is no longer enforced
  by construction, which was the whole premise. The ingredient list is a precondition, not a wish.
- **Exhaustiveness that is not actually checked.** Rust and Scala 3 check it. TypeScript needs a
  `never`-assertion idiom or a lint rule; Java needs sealed interfaces plus pattern switches.
  Without the check the propagation argument fails silently, which is the worst way for it to fail.
- **When the constructive form breaks the operations you need.** `EvenList<T> = List<(T, T)>` makes
  `first` return a pair, so the host language's list interface stops applying. A judgment call, not
  a defect — but make it knowingly.
- **When recomputation is real.** `start` + `duration` makes every query for `end` arithmetic. Let
  the representation follow which quantity the surrounding code actually asks for; the choice is
  local and reversible.
- **Hot paths where layout dominates.** A sum type per element is not a flat array. Out of scope
  for this file — see the performance canon, not this one.

## How to apply

1. Write down the invariant you are about to put in a comment or an assert. That comment is the
   signal this file exists for.
2. Ask whether a different representation makes the illegal state unrepresentable. Prefer adding a
   constructor over adding a constraint.
3. Check the ingredient list and the exhaustiveness check for the target language before assuming
   enforcement.
4. Size the type by panic-count, per function. Do not widen the blast radius past the functions that
   need it.
5. When a signature forces an unanswerable branch, move the obligation across the call boundary
   instead of inventing an answer.
6. When you decline — boundary type, moving domain, missing sum types — say which of the cases above
   applies. A skipped rule with a named reason is a decision; a skipped rule without one is drift.
