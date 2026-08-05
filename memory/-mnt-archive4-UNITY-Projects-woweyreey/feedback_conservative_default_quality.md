---
name: Conservative default quality preset
description: New quality-tier defaults must start at Medium or Low — never High/Cinematic — so first-load impression is "I can crank this up" not "this lags my PC"
type: feedback
originSessionId: ea56371e-bdd8-4b48-b0e2-18ee38f4212b
---
When introducing a new quality preset / tier system to any subsystem (fog, sky, clouds, GI, shadows, post, etc.), the default value (both in-code `Default` constructors AND the seeded values in any new `.asset`/preset shipped to players) must start at the **conservative end** — Medium or Low — not at High/Cinematic, even when the dev machine and target consoles handle High fine.

**Why:** Players' first impression of the game is "I think I can go to settings and make it look better" rather than "this lags my PC, I'm refunding." Discovering headroom is a positive UX moment; discovering stutter is a negative one. Stated by the user 2026-04-18 while approving the atmospherics quality-tier framework — they explicitly overrode the handoff's "do not regress from High default" instruction.

**How to apply — every default code path, not just the public one:**
- New `[Default]` static for any `*Settings` struct → start at Low or Medium; choose Medium when the subsystem is visually load-bearing (fog, sky), Low when it's pure-perf overhead with subtle quality gain (subres, accumulation frames).
- New `.asset` files seeded into the project for first-time setup → same rule.
- **Internal fallback arms in `*QualityTiers.For(level)` switch expressions** — both the `Custom` arm (when the spec is needed but the field is unlocked) and the unknown-enum `_ =>` arm must fall back to Medium or Low, never High. This catches the silent "version skew bumped you up a tier" failure mode.
- Any helper that builds a default spec, default settings struct, or fresh ScriptableObject seed value → same rule.
- Do NOT override existing serialized `.asset` values that artists/QA have explicitly tuned — only the *fresh-construction default* changes.
- This overrides handoff instructions like "High is the current default — do not regress." If a handoff prescribes High as default, push back and propose Medium.
- Companion principle to `project_deck_60fps_target.md`: Steam Deck 60 FPS is the perf floor; conservative defaults make sure even non-Deck hardware lands in a smooth-by-default state.
