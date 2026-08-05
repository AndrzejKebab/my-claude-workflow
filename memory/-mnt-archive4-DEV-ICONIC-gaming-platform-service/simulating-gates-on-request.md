---
name: simulating-gates-on-request
description: "Simulation, capture-parity and cheat gates run ONLY when the user asks — never as a close-out reflex; routine set is `verify` + integration"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: adf1d5fa-6553-435b-90c5-fbc63686fc19
  modified: 2026-07-24T10:52:01.746Z
---

Established 2026-07-24. Two sets of gates in gaming-platform-service, and the line is binding:

- **Routine, run freely:** `pnpm --filter @gps/game-service verify` (typecheck, format:check,
  test:gate, test:games), plus the integration tier (`pnpm stack up` → `pnpm stack test`) whenever
  a change touches a seam between services. This is what "is it green?" is answered from.
- **Requested only:** `test:gates` (simulation integrity, RTP, capture parity, cheats, tapes),
  `test:local` (contains test:gates), `capture:check`, `certify`. **Never started unasked — not on
  a timer, not "just in case", and explicitly NOT as a reflex before handing work over or at
  session close.**

Second half of the rule: when a long suite was just run and **one** test in it was fixed, re-run
**that test only** to confirm (`--test-name-pattern`, plus `GAMES=<game>` when the gate is
per-game, since `GAMES` narrows before fixtures are built and `--test-name-pattern` does not). A
full re-sweep is its own separate request.

**Why:** these gates simulate whole rounds — cost is rounds × games × profiles and grows with every
game added. One unrequested `test:gates` sweep cost 32 minutes of wall clock in the session this
was agreed in, to re-confirm a one-line fix that a 1.9 s narrowed run had already confirmed. The
user pays for that time and wants it spent on their terms.

**How to apply:** never launch a simulating run to satisfy a readiness check. Instead *say* that a
change could have moved a game's mathematics or what the service publishes, and let the user call
for the run. This deliberately amends the global "entire test suite green before answering
readiness" rule for this repo: a readiness answer must **name which set was run** — "green on the
routine set and the integration tier; the simulating gates were not run" is complete and honest.

Recorded in the repo at `AGENTS.md` § *The regimen* and `docs/game-service/testing.md` § *The
gates*. Related: [[no-local-typecheck-gate]], [[verify-real-functionality]], [[keep-feature-prs-scoped]].
