---
name: fleet-github
description: Use for every GitHub post a bot makes: a review, a PR or issue comment, a status-label move, a plan approval. Raw `gh pr review`, `gh pr comment`, `gh issue comment` and label edits are blocked; these tools are the route, and their refusals say what to fix.
---

# Fleet GitHub posts

All three tools take `--repo owner/name` when you are outside the repository, and `--dry-run` to run
the checks without posting. A PR comment is the PR's history: a new agent reading it should learn what
happened and why. No acknowledgements, no progress reports.

## Review — `scripts/review.py`

```
python ${HERMES_SKILL_DIR}/scripts/review.py <PR> -f <body.md>
python ${HERMES_SKILL_DIR}/scripts/review.py <PR> --approve-plan "<phase plan §step>"
```

Body: `# Reviewer`, then `### Issues to Fix`, one `- [ ]` item each, ending with its grounds:
`(criterion: "<quote from the issue>")`, `(rule: <file or rule>)` or `(breakage: <evidence>)`. An item
with no grounds is a spec question: send it to the Advisor, not to the Worker. Open items post as
request-changes; `--approve` is refused while one is open.

## Comment — `scripts/comment.py`

```
python ${HERMES_SKILL_DIR}/scripts/comment.py --pr <N> --body-file <body.md> --signer "# <You>"
```

Refused: a wrong signer, an acknowledgement opener, more than 2000 characters outside
`<details><summary>Evidence</summary> … </details>`, and local paths. Saying honestly what you could
not do is welcome; claiming you are blocked goes through `label.py --to blocked` with the self-check.

## Label — `scripts/label.py`

```
python ${HERMES_SKILL_DIR}/scripts/label.py <N> --to <status> --signer <You> --reason "<one line>"
```

- `--to blocked` needs `--self-check-file` with the self-check.
- The first `--to in-progress` needs the draft PR's `## Work plan` and Reviewer's `Plan approved`
  (`--pr <draft PR>` when labelling the issue).
- `--to waits-for-review` on a PR needs `## Evidence` with one line per acceptance criterion; on a bug,
  also `Cause:`, `Reproduction:` and an `Approach approved` comment from the Advisor (the owner until
  the Advisor exists).

## Self-check

```
Failure: <exact command> -> <output>
Own cause ruled out: <what you changed since it last worked, and why that is not it>
Tried: <session search result>; <lesson search result>; <the other route and its result>
Claim: <what is broken, where, shown by what>
```

## Programs started

`gh` only. `label_hygiene.sh` (REPO=owner/name, `--apply` to remove) strips in-flight labels from
closed items.

## Recorded run

```
$ python scripts/comment.py --pr 431 --body-file ack.md --signer "# Worker-1" --dry-run
refused:
- no acknowledgements on GitHub: a PR comment is history (a decision, its reason, or what went wrong). Tell the bot by DM instead
```
