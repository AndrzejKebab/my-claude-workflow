# Long-PR diagnosis (5 rounds or 7 days open)

## Gather

1. Dump each PR once: `gh pr view <N> --json number,title,state,isDraft,labels,createdAt,updatedAt,headRefName,headRefOid,body,comments,reviews,commits,closingIssuesReferences`
   into your scratch. Histories reach ~1 MB (hundreds of comments); never read the raw dump whole.
2. Condense to one line per event: `time kind(C comment/R review/K commit) signer open-checkboxes | text`,
   with an optional `since` filter, and read the last ~2 weeks at full width. The signer is the body's first
   line (`# Worker-N`, `# Reviewer`, `# Manager`); unsigned = the owner.
3. Read the linked issue's last comments and any issue the PR waits on (`Refs`/`Blocked by`).
4. Check whether the bots were alive during the quiet stretch (SKILL.md liveness check).
5. Re-check `updatedAt`/`headRefOid` just before posting; post nothing on a PR that moved since you read it.

## Name the cause (fixed set) and the matching action

| Cause | Signs in the history | Action |
|---|---|---|
| Spec not settled | A/B question parked in `needs-owner`; Worker holding correctly | Search `.memory/decisions` for the pass/stage named, then every record whose `Amends:`/`Follow-up to:` names it; newest wins. If answered, rule it with the quote and clear `needs-owner`/`blocked`. Only a gap or conflict goes to the owner. |
| Scope grew | Owner rulings mid-PR reopened finished code; findings unrelated to the criteria | Freeze scope to the named rulings; everything else becomes its own issue. |
| Worker stuck | Rounds about the instrument (counters, probes, wrong world/seed), not the feature | Read the code that writes what the counter counts before trusting a constant reading; demand a red test on the legitimate shape; one decision run with an exact recipe. |
| Reviewer moving goalposts | New asks not tied to a criterion or measured breakage | Reviewer lesson + reviewer miss. Verify first: a round that self-corrects from a fact is not goalposts. |
| Not in the set (say so plainly) | Owner hold on a dependency; lane capacity; baseline moved (editor/main upgrade); two PRs doing the same switch; provider outage | Keep `on-hold` for a dependency wait; move lanes for capacity; merge `origin/main` (merge, not rebase) for a moved baseline; shrink one PR so each change has one home. |

## Also check every time

- The body's `Closes #M` names the issue, not the PR itself; a stale queue label on the issue.
- The latest review round before restating what the PR still owes (label notes go stale).
- Whether the result changes visible output: then the PR ends at the owner's eye review, say so up front.

## Post

- One history comment per PR via `fleet-github` `comment.py --signer "# Advisor" --dry-run` first: bodies over
  2000 chars outside `<details>` are refused — tighten, do not split.
- Shape: bold line with age and cause; 2–3 bullets of history with SHAs; the decision; a Next list for the
  named Worker. A ruling on an issue gets its own comment there, plus a label change via `label.py`.
- Then one DM to Manager with numbered routing per PR, and one owner-notes line per PR.
