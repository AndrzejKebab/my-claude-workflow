---
name: docs-state-the-rule-not-the-behaviour
description: QA case lists in docs/qa state what the code SHOULD do; current behaviour belongs in the State column and the prose
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 060ef4b6-0770-4c8d-8957-25ae5db66218
  modified: 2026-08-10T17:01:04.858Z
---

In `docs/qa/*-cases.md`, every case row states the rule **as it must be**, never what the platform
does today. Whether we honour it is the `State` column (GREEN / RED / BLOCKED); where a row is red,
the prose beneath the table names the deviation and links the defect.

**Why:** a row that transcribes measured behaviour is green by construction and can never fail — so
the list mirrors the implementation instead of being reviewable against it. `docs/qa/transaction-safety-cases.md`
TS-03 was seven such rows before 2026-08-10.

**How to apply:** derive each row from a stated principle, so the reader can check the derivation
rather than trust the row. TS-03's is *might the wallet be holding the stake?* — the reversal falls
out of it. When a measurement is genuinely useful, label it as today's behaviour and put it outside
the case tables.

Related: [[questions-mean-the-writing-begs-them]]
