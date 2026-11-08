---
name: fleet-supervision
description: Advisor only. Use when you check a first-line bot's work (an answer, an analysis, a review, a plan approval) to record agree or disagree, and before each item to learn whether this bot and category still get a full check or only a spot check.
---

# Fleet supervision

Each first-line bot earns independence per category. It starts in full checking; 90% agreement over its
last 20 checks earns a 1-in-5 spot check; a disagreement during spot checks restores full checking.

```
python ${HERMES_SKILL_DIR}/scripts/supervision.py should-check --ledger <ledger> --bot reviewer --category issues
python ${HERMES_SKILL_DIR}/scripts/supervision.py record --ledger <ledger> --bot reviewer --category issues \
    --outcome agree|disagree|skipped --item "PR #431 round 2" --why "<one line>"
python ${HERMES_SKILL_DIR}/scripts/supervision.py status --ledger <ledger>
```

Record `skipped` for an item you did not check in spot mode, so the 1-in-5 count stays right. A
disagreement needs `--why` and a draft lesson (`fleet-lessons`). Categories: `self-check-analysis`,
`answers`, `issues`, `passes`, `plans`.

## Programs started

None. The ledger is one JSON line per check.

## Recorded run

```
$ python scripts/supervision.py status --ledger ledger.jsonl
manager/answers: spot, 20/20 agreed in the last 20 checks
```
