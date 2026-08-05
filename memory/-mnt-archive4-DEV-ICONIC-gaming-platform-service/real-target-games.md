---
name: real-target-games
description: Only slot-vikings and slot-seven-wonders are real product targets; the other games are framework-coverage vehicles
metadata: 
  node_type: memory
  type: project
  originSessionId: 26bf1ec1-0ba1-4d33-b6ad-51e64be65f68
  modified: 2026-07-23T14:39:21.438Z
---

**`slot-vikings` and `slot-seven-wonders` are the only games whose mathematics is a real
target.** Every other game in `apps/game-service/src/games/` exists to carry framework test
coverage across, not to ship as a calibrated game.

`slot-sunspire` is known broken and is to be ignored: it declares a return of 7891.55% under a
profile keyed `rtp96`, and measures ~7980% — its origin declares no RTP profiles at all, so the
figure is a self-measurement of uncalibrated math. Its σ is 532 stakes a round, so no gate-sized
run can resolve it.

The `slot-tidalspin` family (`tidalspin`, `coralburst`, `pearldrift`, `cindergate`) declares a
`total` about 7–8 points below what it actually pays, while its `buyFeature` column matches the
measurement within ~1σ on every rung — the two look transposed. **Measured, 10–12σ out, and
deliberately not fixed**: coverage vehicles are not worth the churn.

**Why:** the games came across to move framework coverage, and calibrating twenty-one games'
returns was never the point.

**How to apply:** when a gate reddens on a game that is not Vikings or Seven Wonders, check
whether it is a coverage vehicle before spending time on its mathematics — say what was found
and move on. Do not add per-game exemption lists to gates; where a gate genuinely cannot resolve
a claim, widen it from the game's own measured error so the widening is a stated fact rather than
a quarantine. See [[game-figures-have-a-source]] and [[keep-feature-prs-scoped]].
