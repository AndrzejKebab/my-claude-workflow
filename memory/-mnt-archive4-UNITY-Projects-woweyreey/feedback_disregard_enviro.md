---
name: Disregard Enviro entirely
description: Enviro 3 is a temporary placeholder in the project — never reference it, compare to it, or use it as a pattern source
type: feedback
originSessionId: af2be8bc-0bba-4c00-a645-34e1fb23a601
---
Enviro 3 is in the project only as a temporary controller and is considered inappropriate and slow. It will not be utilised anywhere going forward.

**Why:** The user regards Enviro as a stopgap they plan to remove. Treating it as a reference implementation or integration target (even just to "ignore" or "coexist with" it) pulls plans in the wrong direction and suggests Enviro is architecturally relevant — it is not.

**How to apply:**
- Never cite Enviro files (`Assets/Enviro 3 - Sky and Weather/**`) as reference patterns, even for "how X is done in this codebase."
- Never propose coexistence, replacement, bridging, or disabling of Enviro modules — just act as if Enviro isn't there.
- Don't mention Enviro in plans, comparisons, or render-order discussions. For URP RenderGraph patterns use `Packages/com.api-haus.*` (rwvt, sdf-rendering, heightfields) or other non-Enviro code only.
- If the user's request could be read as integration with sky/weather/fog, assume it means the project's own `CelestialTimeSystem` / custom code, never Enviro.
