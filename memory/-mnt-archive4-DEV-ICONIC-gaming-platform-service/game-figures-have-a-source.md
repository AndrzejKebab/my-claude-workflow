---
name: game-figures-have-a-source
description: "Load-bearing per-game figures (max win, etc.) already exist upstream — look them up, never derive or guess"
metadata: 
  node_type: memory
  type: project
  originSessionId: 4601ff42-8c81-44aa-8a2d-863f6e2f5d7d
  modified: 2026-07-21T15:25:40.928Z
---

Per-game load-bearing figures already exist in the upstream codebase and must be looked up, not
invented. The max-win ceiling is `slotMaxWinXBet`, one file per game under
`~/_dev/p7/client-api/src/slot-catalog/public/client-slot-settings/slots/`. Map a target game to its
upstream file via the codename table in `~/_dev/p7/PORTING.md` §9 — that file is the only place the
two naming schemes may appear together, so never copy the mapping anywhere else, including here.

A re-skin's settings file *imports* its parent's settings block (e.g. a re-skin importing
`…_DATA_SETTINGS` from the parent), so re-skins share the parent's figure by construction — that is
evidence in the source, not an inference.

**Why:** these are published, client-facing, regulator-relevant numbers, and the RTP gate fails if a
simulated round exceeds the declared ceiling. A guessed one is wrong in a way that looks right —
exactly what [[verify-real-functionality]] and the repo's "refuse, don't guess, a load-bearing
value" rule exist to prevent.

**How to apply:** when a merge or a new game demands such a figure, search upstream first. Only when
a game was never catalogued (unreleased) may it be derived — and then derive it from the game's own
rules arithmetically, corroborate with a measured simulation run, and record in
`docs/game-service/design/divergences.md` that it is derived rather than supplied.

Related: [[no-proprietary-base-references]], [[stealth-framing-not-porting]].
