---
name: fleet-github
description: "Use for every GitHub post a bot makes: a review, a PR or issue comment, a status-label move, a plan approval. Raw `gh pr review`, `gh pr comment`, `gh issue comment` and label edits are blocked; these tools are the route, and their refusals say what to fix."
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

**The privacy refusal names the offending LINE, and a quoted command is the usual offender.** A body that pastes
a build or compile command verbatim carries an absolute path (`--project F:/…`, `--root C:/…`) and is refused with
`line N: <the line>` — rewrite that line to a placeholder (`--project <worktree>`, `<repo>`) or to a repo-relative
path before posting. The same gate runs on `gh pr create`/`gh issue create` bodies, so fix it at draft time rather
than after a refusal.

**`gh exited 143:` is the shell timeout killing `gh`, not a refusal.** Re-run the same call with a longer timeout
before reading it as a policy block; the body and the checks were never evaluated.

**When a raw `gh pr comment` starts being denied mid-run, switch tools rather than rewording.** The deny
list is per subcommand, so the same session can still allow `gh pr create`, `gh pr edit --body-file`,
`gh pr ready` and `gh pr view` while `gh pr comment` and `gh issue comment` return
`BLOCKED … approvals.deny`. Do not retry the comment with different quoting: take the body to
`comment.py`, and expect one extra edit on the way — a body drafted for raw `gh` opens `# Worker 5`
(space), and `comment.py` requires its own spelling `# Worker-5` on line 1, so rewrite that line before
posting. Body edits and draft→ready stay on raw `gh`; only the comment and the label move go through the
fleet scripts.

**A deny glob can match a flag combination, not just a subcommand.** `gh pr create … --label in-progress` is
refused as `matches the user-defined deny rule '*gh pr create*--label*in-progress*'`, while the same `gh pr
create` with only `--label worker:N` passes. Open the draft with the owner label alone and let `label.py` set
the status label once the plan is approved — that is the order the gates want anyway.

**A deny match is a substring test on the whole command line, so quoting a forbidden name in prose trips it.**
`label.py … --reason "waiting on the build because build_player.py is denied for me"` is refused by
`'python* *build_player.py*'` — the rule cannot tell a filename you are writing *about* from one you are invoking.
The refusal names the rule, so read it as "that token must not appear in this command": reword the reason to
describe the step without the literal (`the build step is denied for me`) and post the full explanation in the
comment body instead. Never route around it by splitting the token; the point of the rule is that the command
line stays free of it.

A report that carries a self-check plus log output is over the cap almost every time — lead with the point and the
ask, and put the transcript in the `<details>` block before the first post rather than trimming after a refusal.

**Read the item's newest comments before posting a note you have posted before.** `gh pr view <N> --json comments`
(and the issue equivalent) is one call, and it is what stops a `Label:` line, a `Waiting:` line or a blocker
write-up landing twice: a duplicate reads to the owner as churn and buries whatever newer evidence sits under it.
If nothing has changed since the earlier copy, say nothing on the item and let the label carry the state.

### Issue and PR bodies come from the repo's templates

In the repository: `.github/ISSUE_TEMPLATE/template_issue.md` when something is wrong (What is happening,
Expected, Reproduction, Cause), `template_feature.md` for new behaviour (What, Why), and
`.github/PULL_REQUEST_TEMPLATE/template_pr.md` for every PR (What this PR does, Why, Work plan, Evidence). Headings
unchanged, your own signer on line 1. A bug's `## Reproduction` and `## Cause` live in the issue, filled by diagnosis;
a `<...>` placeholder left in them does not count. `## Evidence` in the PR proves the change: one
`- <criterion>: <command> -> <result>` bullet per acceptance criterion of the issue, an unproven one saying so in
its own bullet. Sections win over prose: content under any other heading does not satisfy a gate.

### Always pass the body as a file, never inline

Any body containing code, identifiers or backticks goes to a file first (`--body-file`, and the same for
`gh pr create --body-file` / `gh pr edit --body-file`). An inline `--body "..."` argument is shell-interpreted before
the tool receives it: a backticked identifier becomes a command substitution, the shell runs it, and the post lands
with holes where the evidence was - or the command prints `command not found: <identifier>` and still posts the
half-built body.

The failure is quiet because the post succeeds, and it bites hardest where the content matters most: a PR body full
of counter names, log-line formats and file paths. Write the markdown to a scratch file, then post the path.

## Label — `scripts/label.py`

```
python F:\Programowanie\my-claude-workflow\skills\fleet-github/scripts/label.py <number> --to <status> --signer Worker-4 --reason "<one line>"
```

`label.py` takes the item number as a **positional argument** — there is no `--issue` flag, and passing one is
rejected as `unrecognized arguments` before any check runs. It moves exactly one status label and posts the
`Label: <from> → <to> — <reason>` line itself.

### Signer spellings and gate refusals: [references/label-moves.md](references/label-moves.md)

Two spellings of the same identity (`comment.py` wants `--signer "# Worker-4"`, `label.py` wants
`--signer Worker-4`), every gate's exact refusal and its fix (`blocked` self-check, the first `in-progress`,
`waits-for-review` on a bug), the `question`/`on-hold`/`blocked` vocabulary and the owner-answer rules all live
there. Read it when a label move is refused or when a question needs to land somewhere.

- `--to blocked` needs `--self-check-file` with the self-check.
- The first `--to in-progress` needs the draft PR's `## Work plan` and Reviewer's `Plan approved`
  (`--pr <draft PR>` when labelling the issue). **An issue whose work rides another item's PR takes that PR's
  number** — an umbrella slice implemented inside a larger PR is still "started" only once you name where; pass
  `--pr <that PR>`. When the item has **no PR anywhere yet** (its work is queued behind two others), the gate is
  right and `ready` is the honest label: post the ruling as a comment so the item is not silent, and move it to
  `in-progress` when the draft PR exists. Never fake the move by labelling it `in-progress` without a PR.
- `--to waits-for-review` on a PR needs `## Evidence` with one line per acceptance criterion; on a bug,
  also the issue's filled `## Reproduction` and `## Cause` and an `Approach approved` comment from the Advisor or
  the owner. A body full of verification prose under a `## Verification` heading does **not** satisfy it: the
  heading must be `## Evidence` and each line must read `- <criterion>: <command> -> <result>`. When that is the
  refusal, append the section with `gh pr edit <N> --body-file` (still allowed) and re-run the label once; do not
  retype the whole body and do not retry the label unchanged.
  - **The section name must be exactly `## Evidence`.** A heading like `## Evidence at <sha> (built client)`
    wins the lookup and then contains no `- ` lines, so the tool reports `0 line(s) for N acceptance criteria`
    while a correct-looking section sits further down. Give the run log its own heading (`## Run at <sha>`) and
    keep `## Evidence` for the bare bullet list.
  - **The bullet count must equal the number of acceptance criteria on the issue**, not the number of things you
    verified: seven criteria with six bullets is refused. Write one bullet per criterion, and where a criterion is
    unproven say so in its own bullet (`... -> not exercised; open for an Editor Play run`) instead of dropping it.
  - **`Approach approved` counts only from an Advisor-signed comment or an unsigned one.** The rule reads a
    comment's first line as a signature: signed `# Advisor` passes; **any other signature is treated as that bot's
    own statement and ignored** — including a `# Manager`-signed comment posted from the owner's account, which is
    how an owner approval arrives and still gets refused. Only an unsigned comment counts as the owner speaking.
    When that is the refusal, tell the coordinator that the phrase must come from the Advisor or be posted
    unsigned; do not reword the body, and never write the approval in yourself.
- **The owner's label meanings.** `blocked` = cannot continue; **`blocked` + `on-hold` = behind another PR or
  issue**; **`blocked` + `question` = behind a question** (Manager is told it waits for an answer); **`question`
  alone = a question that blocks nothing** (never reported). An item behind another gets `blocked` + `on-hold` and
  names it as `Blocked by #N` in the body and the label reason: the watchdog keeps it quiet while #N is open, and
  nudges once when #N closes or when no number is named (prose such as "behind the measurement issue" does not count).
- **When the only open box is another lane's run, review is the honest label — not `blocked`.** Code
  complete and compiled, with one acceptance item that requires a build, a seat or a click only the
  coordinator holds, is a PR a reviewer can already read. Park it as `blocked` only if stopping is the
  instruction; otherwise move it to `waits-for-review`, put the missing item in the body as an explicit
  unproven line, and say in the DM exactly which run fills it. A lane that keeps a finished diff parked for
  a day has hidden reviewable work behind a scheduling fact. The reverse also holds: never leave a box
  unmentioned — an unproven criterion must be visible before the reviewer finds it.
- **`label.py` moves the one status label, and `--add` / `--remove` handle the side labels `question` and
  `on-hold` in the same call** (no other label is accepted there). `label.py <n> --to blocked --add on-hold --reason
  "Blocked by #N"` needs #N open and no self-check; `--to blocked --add question` puts the question in the reason;
  bare `--to blocked` keeps the self-check. Leaving `blocked` drops `on-hold` by itself; `--remove question` clears
  an answered question in the same move, because a `question` left on keeps the owner reading it as open. The tool
  writes both into the `Label:` line and reads the result back. Raw `gh pr edit`/`gh issue edit` with
  `--remove-label` **and** with `--add-label` stay refused by `approvals.deny`, so the fleet tool is the only route —
  never reach the same edit through `gh api`, and never fake a side label with a status move it does not describe.
  A side label the holder cannot set is still a one-line ask on the item, but it is no longer the default
  assumption: try `--add` first, and couple the answering move with `--remove` so the label and the record agree.
- **Every question carries `question`, and where it lands is decided by whether work has started.** The owner's rule:
  `question` is mandatory on any item that needs an answer from him; a question that stops progress carries
  `blocked` as well; and **the question goes on the PR when the work is under way with an open PR, on the issue only
  when nothing has started and no PR exists**. He does not scan issues for questions once a PR is open — a question
  parked on the issue reads to him as "nothing needs me" and goes unanswered. So when a decision is needed on a
  slice whose PR is open, post the owner-inbox question on the **PR** and label it `blocked` + `question`; keep the
  issue's own copy out of the way (one line saying the question lives on the PR), because two copies of one ask is
  churn.
- **A status label you set can be reversed by someone else; reversing it back is your move to make, out loud.**
  When an item you parked as `blocked` or `waits-for-review` comes back `in-progress` with no new answer and no new
  review on the item, do not flip it silently and do not argue: move it back with `label.py`, and have the `--reason`
  say what state is being restored and why (`author has answered the only open item and is waiting on a build slot`).
  If it flips a second time, say in one line on the item that something else is managing that label and that a single
  line naming the intended state will settle it. The label churn itself is the information: a reversed status with no
  matching event means two agents disagree about whose turn it is.
- **GitHub is the record, a DM is the prompt.** When `message_agent` refuses a thread
  (`this bot-to-bot exchange already reached its limit`), stop replying to that thread: the substance is already
  owed on the item, and the lane reads it there. Do not re-send the same instruction by another route.
  A refusal reading `messaged you this turn and your final response already goes back to them` is not a failure at
  all: the reply you were about to send is delivered as this turn's final message, so put it there and do not retry.
  **That final message also lands in the owner's chat, so it is a line, not a report** — answer the teammate in at
  most three lines, point at the item for the substance, and never paste a bot-directed brief into the owner's
  window. Everything longer belongs on the item the turn is about. **Name items, never count them:** "#449, #450 and
  #451" is actionable and "three of the five" is not — a reader cannot open a number, and a count also drifts stale
  the moment a sixth item joins the set. Applies to chat replies and to GitHub text alike.
- **A watchdog nudge is not an answer.** A report that says an item was “answered 15m ago” only means the item
  has a recent comment; when that comment was the coordinator reserving a run, or naming the one box still
  missing, nothing has changed. **Read the newest comment's author before reacting** — your own `Label:` or
  `Waiting:` line is the most common false positive, and a nudge counting your own note as the answer is how a
  correctly parked item gets flipped to `in-progress` for no reason. Do not flip the label to satisfy the nudge. Post a fresh `Waiting: <reason>,
  until HH:MM` line (it must be newer than your last push to count) and keep the label matching reality; if
  the nudge repeats, answer it once on the item with the exact remaining item and the evidence that the slot is
  in use, then stop replying to the nudges. Flipping `blocked` to `in-progress` to quiet the report is the one
  thing that makes the board lie.
- **An answer that re-slices the work re-points the PR, not just the umbrella's label.** When the owner splits a
  milestone into slices, the PR serving one slice must name that slice in its `Refs`/`Closes` line, and the umbrella
  must stop being `blocked` on a question it has now answered (move it on, with the reason naming the slices).
  Leave it blocked and two items claim the same work while the board reports a PR naming no issue. Record the
  owner's choice and date on the item in the owner-inbox form — `Owner chose X (<date>, via <channel>)` — and never
  re-ask a question the owner has answered, even in passing.
- **A question the owner cannot answer from the chat line is not yet asked.** When the item carries the options, the
  chat line that announces it must carry them too (`#298: A stress flight, B wait for the frame gate — recommend A`),
  not only a link: the owner reads chat for the decision and GitHub for the record, and a bare
  `Need your decision on #<n> -> <link>` gets the reply `I don't see any decision to choose`. Same for a follow-up
  after he pushes back: restate A and B in one line each, then take the letter he answers with as the whole decision.

- **An evidence-only PR whose tree equals `main` closes unmerged, and its evidence moves to a tracked file first.**
  `git diff origin/main <head>` empty means a squash lands no commit, so the PR cannot be the home of what it proves:
  put the measurements in a `.memory/notes/<topic>.md` on `main` (one docs commit), then close the PR unmerged as
  superseded and close or re-scope the issue citing that note. Do this *before* asking anyone to close it — a PR
  whose evidence lives only in its body dies with the branch, and the reviewer's question ("where does this evidence
  go?") is answered by the note, not by another comment. No bot closes a PR; the author or the coordinator does.

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

`label.py --to blocked` refuses a `Tried:` line that does not quote a session search. Run one first and paste what it
returned — including `only this session's own output, no earlier occurrence`, which is a real and useful answer — then
the lesson search, then the other route you tried. Three attempts at one error is the point to stop and write this up,
not the point to start a fourth.

**Run the label command with `--dry-run` before rewriting a refused self-check.** The refusal names only the field
that failed (`Tried: must quote the lesson search result (even "no lesson matches")`), so one dry-run says which of
the four lines to fix. Rewriting the whole file to guess costs a round-trip and can break a field that already passed.
A lesson search returning only near-misses is still a result: quote it and say it does not match.

**Write the self-check file to an explicit scratch directory, not `$TMPDIR` or `/tmp`.** Under the fleet shell `$TMPDIR`
can expand to a path with a broken segment (the tool then reports `FileNotFoundError` on the whole file), and `/tmp` is
refused outright by the workspace guard, so the label move fails for a reason that looks like the label. Use the
agent's own scratch path spelled out in full, and delete the file once the move is read back.

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
