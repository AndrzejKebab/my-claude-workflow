---
name: Only E2E tests — no trivial assertions
description: "Don't test constants, struct sizes, or obvious getters. Only E2E tests that prove the full pipeline works."
type: feedback
---

Don't write tests for trivial things like `Assert.AreEqual(48, default(Lattice).PackedSize)` or struct size checks. These are constants — they can't fail without a compiler error.

**Why:** Wastes time, clutters the test suite, proves nothing. The only tests worth writing exercise the real code path end-to-end: Burst compilation succeeds, generic system discovers entities, data flows through packing into buffers, round-trips correctly.

**How to apply:** When writing tests, ask "could this fail without a compiler error?" If no, don't write it. Focus on E2E: create entities → system runs → verify output.
