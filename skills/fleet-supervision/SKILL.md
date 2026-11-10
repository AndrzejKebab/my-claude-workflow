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

## Daily-batch audit (Reviewer's Issues to Fix, Manager's explanatory answers)

1. List what they actually posted since the last batch. Bots post through the owner's account, so filter by
   the signer on the first line, not the author:
   ```
   gh api "repos/<owner/name>/issues/comments?since=<ISO>&per_page=100" --paginate \
     --jq '.[]|select(.body|test("^# (Reviewer|Manager)"))|"\(.created_at) \(.issue_url|split("/")|last) \(.id)"'
   ```
   Reviews (`gh pr view <N> --json reviews`) for PRs from `gh search prs --updated ">=<date>"`. Manager's
   answers to Workers are DMs: read the tail of its newest `profiles/manager/sessions/request_dump_*.json`.
2. If nothing turns up, check that the bots ran before writing "nothing to audit": grep
   `profiles/<bot>/logs/agent.log` for `402`/`429`/`Insufficient Balance`. The watchdog's "worked since
   yesterday" counts failed turns too. An outage goes to the owner's notes first; it is his (provider or config).
3. For each item: `should-check`, judge it against the issue, the decision records (and the records that
   amend them) and the owner's rulings, then `record`. Record nothing when there were no items.
4. A wrong item goes back to the Worker next morning as an Issue to Fix ("revert item N from yesterday,
   because …"), and one notes line per disagreement.

## Programs started

None. The ledger is one JSON line per check.

## Recorded run

Example run:

```
$ python scripts/supervision.py status --ledger ledger.jsonl
manager/answers: spot, 20/20 agreed in the last 20 checks
```
