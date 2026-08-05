---
name: hardcoded-assertions-in-tests
description: "In p7 client-api tests, assertions must be hard-coded literals — never derived from helpers/constants/getters that mirror the production formula."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a9a66a85-19ed-4627-8340-ac72a41766bf
---

When writing tests, assertion right-hand sides must be hard-coded literal values, not values computed by a helper or pulled from a shared constant. The whole point of the test is that a future production-side change shows up as a diff in the test file — if the test re-derives the value through the same code path it's "verifying," that signal disappears.

**Do:**
```ts
expect(bif.coinFraction).toBe(2);
expect(settings!.realBetCoinAmounts).toEqual([150_000, 300_000, 450_000]);
```

**Don't:**
```ts
expect(bif.coinFraction).toBe(getExpectedCoinFraction(currency, slotVersion));
expect(settings!.realBetCoinAmounts).toEqual(deriveExpectedRealBets(coinAmounts, paylines, multiplier));
```

**Why:** Pulled-through helpers couple test expectations to the very chain that's being validated. If the chain regresses, both sides move together and the test stays green. Literals stay frozen by definition — they're the contract.

**How to apply:** Every `expect(...).toBe(X)` / `.toEqual([...])` / `.toMatchObject({...})` must use literal X / literal array / literal object. If recomputing the expected value is too tedious, that means the test is too coarse — split into smaller cases, each with a small hard-coded expected value. Acceptable to reference IDs/codes from real published config imports (e.g. `Hub88B2BEU.id`, `P7_028S_MAVIAN_WREATH.id`) since those are identity strings, not derived numeric facts.
