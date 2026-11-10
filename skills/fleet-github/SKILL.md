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
with no grounds is a spec question: send it to the Advisor, not to the Worker. Every review posts
as a plain comment review (GitHub refuses approve or request-changes on your own PR): an open `- [ ]`
item means fixes are needed, none means clean. `--approve` is refused while one is open.

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
  also `Cause:`, `Reproduction:` and an `Approach approved` comment from the Advisor or the owner.

## Board order — `scripts/fleet_board.py`

Orders open issues and PRs from their `Blocked by #N` lines and prints the work queue in waves, plus the faults
that make a queue lie (blocked with no dependency named, dependency on a closed issue, a PR naming no issue, an
issue in progress with no PR, two status labels, cycles). `--faults-only` (exit 1 on faults), `--markdown`,
`--json`, `--all`. Run it before answering "what is the order". Moved from `bot-tools/github`.

## Self-check

```
Failure: <exact command> -> <output>
Own cause ruled out: <what you changed since it last worked, and why that is not it>
Tried: <session search result>; <lesson search result>; <the other route and its result>
Claim: <what is broken, where, shown by what>
```

## Setup and upkeep

- `scripts/deny_apply.py --profile <profile-dir> [--globs file] [--dry-run]` adds the raw-`gh` deny globs to a
  profile's `approvals.deny` through `hermes config set`.
- `scripts/docs_push.py --repo-dir <repo> --allow <paths> [--validate <cmd>] [--dry-run]` pushes Manager's
  markdown-only commits after the doc validator and the privacy grep, fast-forward only.
- `scripts/label_hygiene.sh` (`REPO=owner/name`, `--apply` to remove) strips in-flight labels from closed items.

## Programs started

`gh` only (`deny_apply.py`: `hermes`; `docs_push.py`: `git`).

## Recorded run

Example run:

```
$ python scripts/fleet_board.py --faults-only --repo AndrzejKebab/VoxelGame
#390 is a draft PR without in-progress
#433 (PR) names no issue: add Refs/Closes
#433 is a draft PR without in-progress
$ python scripts/label.py 431 --to in-progress --signer Watchdog --reason "example" --repo AndrzejKebab/VoxelGame --dry-run
(none) -> in-progress
gh issue edit 431 --add-label in-progress --repo AndrzejKebab/VoxelGame
# Watchdog

Label: (none) → in-progress — example
$ python scripts/review.py 431 -f .scratch/rv.md --repo AndrzejKebab/VoxelGame --dry-run
--comment with .scratch/rv.md
gh pr review 431 --comment -F .scratch/rv.md --repo AndrzejKebab/VoxelGame
$ REPO=AndrzejKebab/VoxelGame bash scripts/label_hygiene.sh
PR #354: -ready-to-merge
PR #286: -needs-owner
(report only — re-run with --apply to remove)
$ python scripts/deny_apply.py --help
usage: deny_apply.py [-h] --profile PROFILE [--globs GLOBS] [--dry-run]
$ python scripts/docs_push.py --help
usage: docs_push.py [-h] --repo-dir REPO_DIR --allow ALLOW [--validate VALIDATE] [--dry-run]
$ python scripts/comment.py --pr 431 --body-file ack.md --signer "# Worker-1" --dry-run
refused:
- no acknowledgements on GitHub: a PR comment is history (a decision, its reason, or what went wrong). Tell the bot by DM instead
```
