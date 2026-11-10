# Long-PR triage: reading a stalled PR's history and posting the history comment

For the Advisor's long-PR trigger (many rounds, or many days open). The goal is one cause, one decision,
and one comment per PR.

## 1. Pull each PR once, then condense it

The history of a long PR can run to megabytes, with hundreds of comments. Never read it raw.

```
gh pr view <N> --repo <owner/name> \
  --json number,title,body,isDraft,labels,headRefOid,updatedAt,closingIssuesReferences,comments,reviews,commits \
  > "$TMPDIR/prs/pr<N>.json"
```

Condense that file with a script (kept in your scratch) into one line per event, sorted by time:

- the kind: C for a comment, R for a review, K for a commit;
- the timestamp;
- the signer: the post's first line if it starts with `#` (`# Worker-3`, `# Reviewer`), otherwise the owner;
- the number of open `- [ ]` items;
- the first N characters of the text.

The script takes a width and a `since` ISO-date prefix. Read the whole timeline narrow (about 120–220
characters per line) to see its shape. Then re-run it from the last few days at full width to read what
was actually said.

- Every bot posts through the owner's account, so the GitHub author is meaningless. Identify the signer
  from the first line only.
- Paths that contain a literal `$` (for example a directory named `profiles$p`) must be single-quoted in
  bash. Double quotes expand `$p` to nothing, and `cd` fails on a path that looks almost right.

## 2. Name the cause

**First rule out an outage.** Grep each involved bot's `profiles/<bot>/logs/agent.log` for API errors (`402`,
`429`, `Insufficient Balance`) and its newest session dump for `Your request was not processed`, from the
PR's last real activity on. If the bots were not running, that is the cause for that stretch (the owner's:
provider or config). Say it first, and give the causes below only for the time before it. Otherwise a
silent outage reads as "Worker stuck" or "lane capacity".

The watchdog offers four causes: spec not settled, scope grew, Worker stuck, Reviewer moving the goalposts.
The real cause is often one of these instead:

| Cause | What the timeline shows |
|---|---|
| Dependency wait / owner hold | Since a dated hold, only label flips or reassignments, and no commits. |
| Lane capacity | Every dependency has merged; the only reason given is another item ahead on the same worker. |
| Baseline moved | The review is clean or nearly clean; `main` changed under the PR (an editor or package bump) and the PR was never resumed. |
| Scope overlap | Another open PR does the same switch or dependency swap, so both PRs park. |
| Fleet outage | No post from any bot since one moment; bot logs show API refusals. |
| Question the records answer | A `needs-owner` A/B sits for days, but an accepted decision record already settles it. Read `.memory/decisions/` for the stage or contract named, then every later record whose `Amends:` / `Follow-up to:` names it: the newest wins, and it may make the question moot. |
| Worker stuck on the instrument | Rounds argue about the measurement (wrong world, wrong window, a constant reading), not about the feature. |

Before calling it "Reviewer moving the goalposts", check every round's grounds. If each item cites a
criterion, a rule or measured breakage, it is not goalposts. A round the Reviewer corrects himself from a
fact is not goalposts either.

Also check these on the way:

- the body's `Closes` / `Refs` line: it must not name the PR itself, and it must name an issue;
- stale status labels on the linked issue;
- the latest round, not an older label note, as the statement of what is still owed.

## 3. Act, then post

- Act first: rule on the question, freeze the scope, split or shrink the PR, or move it to another lane.
  Route the Worker's next steps through Manager in a single DM covering all the PRs.
- Comment shape:
  - a bold first line, **Long-PR check (N days). Cause: …**;
  - history bullets, kept short;
  - **Decision:**;
  - **Next (who):** steps.

  Say whether the output changes visibly; if it does, eye review follows.
- When you rule on a question parked on an issue, post the full reasoning on the issue and point to it
  from the PR. Do not repeat it on every PR that waits on that issue.
- Post with `comment.py --dry-run` first. The cap is 2000 characters outside `<details>`. Tighten the
  prose rather than hiding the decision in `<details>`.
- Just before posting, re-read each PR's `updatedAt` and `headRefOid`. If either moved since you read the
  PR, re-read the new events before you post.
- For each first-line answer you judged, record a supervision outcome (`fleet-supervision`). Write a draft
  lesson for each disagreement, and for each bot error that let the PR stall.
