---
name: scratch-captures-are-arm-stamped
description: A committed CSV under docs/orchestrate/*/scratch may have been produced on either rotation arm and does not say which — re-drive the control before treating one as a baseline
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 0dea0b5e-5c2c-44aa-95dc-1a57e852cc29
  modified: 2026-07-25T13:39:17.798Z
---

The fixtures under `Assets/Tests/Runtime` write their captures to
`docs/orchestrate/<topic>/scratch/*.csv` on every run, whichever arm the run was on. The files carry
no arm column, so a committed capture and a working-tree one can differ entirely because the arm
differed and not because the code did.

**Why:** on 2026-07-25, `search-settling.csv` in the working tree showed loop fraction falling on
three datasets and speed falling on all six against its committed version, which read as a clean
before/after for a regression under investigation. It was a **referential-arm** run left over from
the previous session's full-suite sweep. Re-driven on the shipped arm at the same HEAD it reproduced
the committed baseline exactly — 1.000 / 1.000 / 1.000 / 0.540 / 0.369 / 0.369, identical speeds. A
whole hypothesis was built on the difference before the control was run.

**How to apply:** never read a scratch CSV as a baseline without re-driving it on the arm you mean.
The arm is set by env knobs on `NetcodeSessionHarness` (`SWORDGAL_ROTATION`, `SWORDGAL_MMWEIGHTS`,
`SWORDGAL_WARP`), absent means shipped, and the fixtures that print an `arm:` line do so only in the
log — not in the CSV. Related: [[transition-regimen-reproduce-first]], which is the same lesson
about the same class of file.
