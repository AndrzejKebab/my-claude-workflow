---
name: fleet-supervision
description: Advisor only. Use when you check a first-line bot's work (an answer, an analysis, a review, a plan approval) to record agree or disagree, before each item to learn whether it gets a full or a spot check, and for escalations, final-review prep, long-PR triggers and the daily audit.
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
   Run the list once with one-line heads to see the shape, then write the full bodies of the substantive
   ones (`select(.body|length>300)`, plus each PR's `/pulls/<N>/reviews` since the date) into one scratch
   file and `read_file` it once. Paging through comments one call at a time costs many round trips.
2. If nothing turns up, check that the bots ran before writing "nothing to audit". Quickest:
   `cd <my-claude-workflow>/tools/hermes-fleet/watchdog && python -c "import board;[print(p, repr(board.provider_down(p))) for p in board.FLEET]"`
   (empty string = up). Fallback: grep `profiles/<bot>/logs/agent.log` for `Non-retryable client error`,
   `402`/`429`, and a later `Turn ended: reason=text_response` that clears it. An outage goes first in the
   owner's notes; it is his (provider or config). When he says it is fixed, re-run the same check to confirm.
   Note: a provider outage that is not 401–403/429 (e.g. 5xx) is not detected by `provider_down`.
3. For each item: `should-check`, judge it against the issue, the decision records (and the records that
   amend them) and the owner's rulings, then `record`. Record nothing when there were no items.
   Judge a recommendation on the facts it had at the time. When the owner later changed it with a fact that
   was not on the item yet, it is not a disagreement. Check what the issue said then with the body's edit
   history: `gh api graphql -f query='query{repository(owner:"<o>",name:"<r>"){issue(number:<N>){userContentEdits(first:20){nodes{editedAt diff}}}}}'`.
   An "owner chose X" claim counts only when the item carries it: an `Owner chose` comment, or a criterion
   in the issue body marked as the owner's ruling.
4. A wrong item goes back to the Worker next morning as an Issue to Fix ("revert item N from yesterday,
   because …"), and one notes line per disagreement.

## Escalations (a blocker handed to you)

1. **Check the premise against the environment it names.** Read where the "control" ran before accepting the
   claim. A compile or test claim about `main` proven in a lane worktree measures that worktree's setup
   (embedded or untracked packages, `Library`, package resolution), not the code. The owner's main clone is
   the reference for `main`. Ask Manager which tree each count came from before ruling on options built on it.
2. **Check the frame of the options.** If every option is owner-reserved (package bump, rollback, upgrade),
   look for the cheap one it missed, such as an environment difference or a stale artefact, before anyone pings
   the owner.
3. **Never park a blocker on your own session window.** If the diagnosis would wait for your reset (session
   above 90%), hand it to Manager in one DM: the method (which trees to diff, what to compare), the guardrails
   (one lane first, a fresh log with its mtime beside every count, no package-version edits, no recursive
   delete under `Packages/` because of the junctions there), and the exit (labels back, lanes resume). Ask
   him to report the fix back to you; you audit it afterwards. Waiting hours for your reset stalls every lane.
4. If the owner answers the item's question in chat, record it on the item (`Owner: <answer> (<date>, via
   chat)`) and tell Manager in the same turn.

## Final review prep (the `passes` category)

- Clean tree first, and keep your own files out of it. Anything you write into the main clone, such as a
  lesson accepted into the project home, must be committed and pushed in the same turn. Otherwise it leaves
  the tree dirty, and the next final review has to stop and ask the owner. Files you did not write: ask the
  owner to keep or discard them. Never discard them yourself.
- Check that an Editor is up before planning the runs: `unity status --project-path <main clone> --format json`,
  `seat.py status`, `unity_procs.py busy`. If it is closed, ask the owner to open it, or to allow a
  headless batch run. Ask in one message that lists what you will run once it is up. Never launch an Editor
  yourself.
- No red commit, because the test commit also carries the code it tests: do not break the code to make one.
  Use an output comparison or a probe reading instead (your SOUL, Job 4), and say in the review comment that
  the PR had no red commit; the missing red-first commit is a finding for the Worker's lesson.
- Also name what the test cannot catch. A unit test of an extracted helper does not prove the caller still
  calls it. Point to the caller line as the evidence for the wiring.

## Long-PR triggers

Procedure and cause table: `references/long-pr-diagnosis.md`. Always run the liveness check above first:
a stall during an outage is not a Worker, scope or Reviewer cause.

## Owner notes file and follow-through

- The batch notes file may already exist from an earlier batch the same day. `write_file` refuses to
  overwrite it without a full fresh `read_file`; `patch` the top instead (new batch first, earlier batch
  kept under a `---` divider). Fix a wrong line in place when the owner corrects it.
- Do not end with "I can fix X if you want". When a fix follows from the finding and is not owner-reserved
  (your SOUL's list: your own SOUL, every `config.yaml`, who may do what), do it or check whether it is already done (e.g. `git log` in
  `my-claude-workflow` for a watchdog commit) and report the result. The owner expects follow-through.
- **Where a board rule actually lives, before editing it.** Label handling is in
  `tools/hermes-fleet/watchdog/board.py` (`stray_labels`, and `hold_of`/`parked` for `on-hold`); status and label vocabulary (what
  `blocked` + `on-hold` versus `blocked` + `question` means for a nudge) is in the `fleet-github` skill, and the
  two must agree — a code change that skips the label the items actually carry is inert. A watchdog code change
  also never retro-fixes items: the running rule reads their labels each pass, so the items must be labelled (or
  relabelled) for the new branch to be taken.
- Verify a watchdog fix is live, not only committed: the cron job `fleet-board-audit`
  (`Hermes/cron/jobs.json`) runs `Hermes/scripts/fleet_board_audit.py`, a shim that imports `board.py` from
  the `my-claude-workflow` checkout, so a commit there is live on the next 15-min run. Check `last_status`
  in jobs.json, `python -m unittest discover -s tools/hermes-fleet/watchdog/tests`, and the tail of
  `Hermes/fleet-watchdog/watchdog.log`. (`profiles/manager/scripts/fleet_watchdog.py` is the retired copy.)

## Programs started

None. The ledger is one JSON line per check.

## Recorded run

Example run:

```
$ python scripts/supervision.py status --ledger ledger.jsonl
manager/answers: spot, 20/20 agreed in the last 20 checks
```
