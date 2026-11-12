# Status and side labels: the gates, the spellings, and the vocabulary

Depth for `label.py`. The body of the skill keeps the few rules that apply on every call; everything that only
matters when a gate refuses, or when two agents disagree about whose turn it is, lives here.

## Two spellings of the signer, one per tool

The accepted signers are spelled `# Worker-1` … `# Worker-5` — **hyphen, never a space** — plus `# Advisor`,
`# Manager`, `# Reviewer`, `# Watchdog`. The body's **first line must equal the signer you passed**, character for
character, followed by a blank line. Passing `--signer "# Worker 4"` is refused even though the space form is how
the repo template writes the header: the tool compares against its own list, and a mismatch is reported as
`the first line must be the signer, one of: …`, which reads like a body problem when it is a signer problem.
Wrong signer string plus right body, or right signer plus a body whose line 1 still says the other spelling, both
produce that same refusal — fix both together.

- **`comment.py` wants `--signer "# Worker-4"`; `label.py` wants `--signer Worker-4`.** Same identity, two
  spellings. Giving `label.py` the `# ` form is refused as `invalid choice: '# Worker-4' (choose from 'Advisor',
  'Manager', … 'Worker-4' …)`, which reads like a wrong name rather than a wrong spelling for that tool. If a
  signature refusal appears, check which tool you called before editing the body.
- A `label.py` run that prints `<from> -> <to>` and *then* a transport error has not necessarily moved the
  label: read it back with `gh pr view <N> --json labels` and re-run once if it is unchanged. Retrying a run
  that already applied would only churn the timeline; guessing that it applied is how an item sits under the
  wrong status for hours. If the read-back still disagrees after one re-run, say so on the item instead of
  looping — it is the token or a deny rule, not the label.

## The gates

- `--to blocked` needs `--self-check-file` with the four-line self-check.
- The first `--to in-progress` needs the draft PR's `## Work plan` and Reviewer's `Plan approved`
  (`--pr <draft PR>` when labelling the issue). **An issue whose work rides another item's PR takes that PR's
  number** — an umbrella slice implemented inside a larger PR is still "started" only once you name where; pass
  `--pr <that PR>`. When the item has **no PR anywhere yet** (its work is queued behind two others), the gate is
  right and `ready` is the honest label: post the ruling as a comment so the item is not silent, and move it to
  `in-progress` when the draft PR exists. Never fake the move by labelling it `in-progress` without a PR.
- `--to waits-for-review` on a PR needs `## Evidence` with one line per acceptance criterion; on a bug,
  also the issue's filled `## Reproduction` and `## Cause` (a `Cause:` line in the issue or PR also counts; a
  `<...>` placeholder does not) and an `Approach approved` comment from the Advisor or the owner. A body full of
  verification prose under a `## Verification` heading does **not** satisfy it: the heading must be `## Evidence`
  and each line must read `- <criterion>: <command> -> <result>`. When that is the refusal, append the section
  with `gh pr edit <N> --body-file` (still allowed) and re-run the label once; do not retype the whole body and do
  not retry the label unchanged.
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

## What `blocked` means, and the two-label vocabulary

- **A dependency chain is not a question.** The owner's rule: `blocked` = cannot continue; **`blocked` + `on-hold` =
  behind another PR or issue** (quiet while it is open), **`blocked` + `question` = behind a question** (reported to
  Manager), and **`question` alone = a question that blocks nothing** (never reported). Name the item as `Blocked
  by #N` in the body and the label reason: the watchdog reads only that form, so "blocked by the measurement issue"
  gets one nudge to name it. An item already labelled bare `blocked` for a dependency moves with `label.py <n> --to
  blocked --add on-hold --reason "Blocked by #N"`, once, instead of answering each nudge.
- **Every question carries `question`, and where it lands is decided by whether work has started.** `question` is
  mandatory on any item that needs an answer from him; a question that stops progress carries `blocked` as well;
  and **the question goes on the PR when the work is under way with an open PR, on the issue only when nothing has
  started and no PR exists**. He does not scan issues for questions once a PR is open — a question parked on the
  issue reads to him as "nothing needs me" and goes unanswered. So when a decision is needed on a slice whose PR
  is open, post the owner-inbox question on the **PR** and label it `blocked` + `question`; keep the issue's own
  copy out of the way (one line saying the question lives on the PR), because two copies of one ask is churn.
  When the answer lands, clear the label in the same move (`--remove question`) so the item stops reading as open.
- **When the only open box is another lane's run, review is the honest label — not `blocked`.** Code complete and
  compiled, with one acceptance item that requires a build, a seat or a click only the coordinator holds, is a PR a
  reviewer can already read. Park it as `blocked` only if stopping is the instruction; otherwise move it to
  `waits-for-review`, put the missing item in the body as an explicit unproven line, and say in the DM exactly
  which run fills it. A lane that keeps a finished diff parked for a day has hidden reviewable work behind a
  scheduling fact. The reverse also holds: never leave a box unmentioned — an unproven criterion must be visible
  before the reviewer finds it.

## When a status label gets reversed, or a question comes back

- **A status label you set can be reversed by someone else; reversing it back is your move to make, out loud.**
  When an item you parked as `blocked` or `waits-for-review` comes back `in-progress` with no new answer and no new
  review on the item, do not flip it silently and do not argue: move it back with `label.py`, and have the `--reason`
  say what state is being restored and why (`author has answered the only open item and is waiting on a build slot`).
  If it flips a second time, say in one line on the item that something else is managing that label and that a single
  line naming the intended state will settle it. The label churn itself is the information: a reversed status with no
  matching event means two agents disagree about whose turn it is.
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
