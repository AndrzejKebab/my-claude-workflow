---
name: Never reference modern or legacy currency lists in config pathways
description: In client-api currency config, never import modernCurrencyConfigList or legacyCurrencyConfigList directly — always use the env-active selector/const that respects COIN_FRACTIONS_ENABLED
type: feedback
originSessionId: 56150942-269c-4528-a42b-1bed750a1eec
---
In `client-api`'s currency config, no production or test pathway should reference either the modern list (`modernCurrencyConfigList`, any `modern*Remapped` derivative) or the legacy list (`legacyCurrencyConfigList`) directly. Every consumer must go through the env-active selector — either `getActiveCoinValueSettings()` or the module-level `coinValueSettings` in `src/slot-catalog/public/defaults/active-coinvalue-settings.ts` (which calls it at module load).

**Why:** Referencing the modern list directly bakes the assumption that overrides merge on top of modern fractions, which silently violates the `COIN_FRACTIONS_ENABLED=false` contract. Operators running with the flag off would get modern fractions anyway. The user explicitly rejected a rename-and-keep approach (`modernCoinValueSettingsRemapped`) with: "at no point we must reference either modern or legacy lists in the actual configuration pathways — those must ALWAYS pick the env-active list; we cannot ASSUME that we're working in modern list whenever we're going to apply overrides on top of it."

**How to apply:** When adding or reviewing code that consumes currency config in `client-api` — slot defaults, validation, limit calculation, bet multipliers, merge/override logic — import from `public/defaults/active-coinvalue-settings` (or call `getActiveCoinValueSettings()` for lazy evaluation). If you find a direct import of `coinValueSettings` (pre-refactor name), `modernCurrencyConfigList`, or `legacyCurrencyConfigList` outside `currencyConfig.ts` itself, flag it — that's a bug waiting to happen when the flag flips. Same principle likely applies to `coinCurrencyMultipliers` and any other pre-flag-gated snapshot in that file.
