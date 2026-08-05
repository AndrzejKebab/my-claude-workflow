---
name: hypertino-continuation-state
description: "Main line as of 2026-07-04: the E-track (editor+game per docs/editor-spec.md); heightfields/cosmetics parked in docs/todo"
metadata: 
  node_type: memory
  type: project
  originSessionId: 70c7af47-439e-4181-bfc7-f5d7fc10f7f4
---

The 2026-07-03 orchestration run (RHI redesign → Noesis-on-WebGPU → Slang port → zori ground-prep → heightfields VT slice) merged to main and wound down deliberately. Continuation plans live IN THE REPO at `docs/todo/` (README is the index; heightfields-port.md, cosmetics-and-tooling.md, decision-queue.md); the handoff is `docs/todo/HANDOFF.md` (mirror of /tmp copy). Kickoff: `/delegate /tmp/hypertino-continuation-handoff.md` (recreate from the docs/todo mirror if /tmp is gone).

**Why:** user cannot afford Fable-5 orchestration — continue on Opus, per-dispatch model economy (sonnet mechanical / opus judgment).

**How to apply:** read `docs/todo/README.md` first; the heightfields P2+ briefs must start from "coarse mips fulfilled directly" (P1 proved the foreign mip-gen compute is dead code — journals' stitching claim is wrong). Recommended order: lint/format → hlslpp spike → cosmetics → heightfields P2+.

**Update 2026-07-04 (evening) — E-track is now the main line.** A full design session produced `docs/editor-spec.md` (E-track canon, committed on `api-haus/editor-ui` = main + `3bb6283`): world-as-module (hosting = deployment), NFE co-simulation adopted, GL family retired by decision (E0 executes), box3d replaces Jolt, minimal-own actor-component store — see also `docs/embedded-ecs.md` "Direction update (2026-07-04)". An unsupervised overnight /delegate run was handed off (`/tmp/editor-etrack-handoff.md`): E0 → E1 while gates green. **Model policy superseded:** user now explicitly runs Fable 5 as orchestrator with opus/sonnet workers (replaces the "continue on Opus" rule below). Heightfields/cosmetics tracks in docs/todo are parked until the E-track settles.

**Update 2026-07-04:** the **hlslpp track is DONE** — glm entirely removed, hlslpp is the single CPU math lib (bare-name behind the `ht` seam in `src/core/gpumath.hpp`, `packMvp`/`unpackMat` at GPU byte boundaries). **MERGED to main 2026-07-04** — main fast-forwarded to `eb30c10` (local only, **29 ahead of `origin/main`, NOT pushed** — push is the user's call). glm gone from main (0 source refs). Was branch `api-haus/hlslpp` (worktree `/mnt/archive4/ORCA/hypertino/hlslpp`), warden-clean, full `just check` green. Full record: `docs/orchestrate/hlslpp-port/` (00-audit → 07-warden-fixes) + `docs/orchestrate/warden-hlslpp-port-20260704/`. Durable assets created: the reference-pixel gate (`tools/reference-gate*.sh`) + platform-run gate + `tools/lint_bare_name_idiom.sh`. Related open thread: the **test-suite-rigor** effort (handoff `/tmp/test-suite-rigor-handoff.md`) — the suite was proven vacuous for matrix-convention errors ([[suite-may-be-vacuous]], [[validate-real-entry-points]]). Remaining docs/todo tracks: cosmetics pass, heightfields P2+.
