---
name: feedback-real-amount-assertions
description: "All currency/bet test assertions must compare formatted real-amount strings (\"USD 0.20\", \"BTC 0.00000400\"), never raw minor-unit integers"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ad5b8bb8-166b-4073-b9a7-e30bdcd564a8
---

When a test asserts on currency amounts (realBetCoinAmounts, minBet, maxBet, betCoinAmountSettings, any reward/payout amount in cents/satoshi), the RHS must be the formatted **real** value with the currency code prefix and full coinFraction-padded major-unit number — e.g. `'USD 0.20'`, `'BTC 0.00000400'`, `'CLF 0.0001'`. Never assert on raw minor-unit integers (20, 400, …).

**Why:** Minor-unit integers obscure what the test actually pins down — a "400" sitting in a BTC array reads as 400 BTC to anyone scanning the diff, when it's really 0.00000400 BTC. The two recent confusions both started with "why is the minimum bet 400 BTC?" — they wouldn't have happened if the test said `'BTC 0.00000400'` to begin with. The formatted string also collapses the coinFraction shift between modern (BTC cf=8) and legacy (USD cf=2) into a self-describing format that's stable under either gate.

**How to apply:**
- For `realBetCoinAmounts` / similar arrays: `.map(minor => formatMajor(minor, code, cf))` before `.toEqual([...])`. Use the response's own `coinValueSettings[code].coinFraction` so the format reflects what the resolver returned, not a static global. A reusable helper lives at `client-api/src/test/integration/utils/formatMajor.ts`.
- Format string: `` `${currency} ${(minor / 10**cf).toFixed(cf)}` `` — currency code + space + zero-padded major-unit number. Matches the `Intl.NumberFormat({ style: 'currency', currencyDisplay: 'code' })` shape used in `betb2b-legacy-cf.spec.ts` but without Intl's quirks on unknown currency codes (BTC, CLF, FUN).
- Trivial assertions on `coinValue` / `currencyMultiplier` / `variants` stay as integers — they're metadata, not amounts. Only amount lists need the format.

Related: [[feedback-hardcoded-assertions-in-tests]] — the formatted string is still a hard-coded literal, not a derived value.
