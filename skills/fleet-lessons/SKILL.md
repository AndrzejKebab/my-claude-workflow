---
name: fleet-lessons
description: Use before reporting an error, setting `blocked` or saying you cannot do something, before writing a new lesson, and when a symptom looks familiar. Searches what the fleet has already learned and records new lessons as drafts.
---

# Fleet lessons

A lesson is something a bot learned from its own work that a later turn, or another bot, needs. Lessons
live in two homes:

- **General** (holds for all work): `${HERMES_SKILL_DIR}/../../memory/shared/`
- **Specific** (holds for one project): `<repo>/.memory/lessons/` in the project you work on

The index below is the General home as of this session's start. Lessons accepted since then are found
only by searching, so search at every decision point instead of trusting the index alone.

## Search before you conclude

Run this before a self-check, before writing a lesson, and when a symptom matches an index line:

```
python ${HERMES_SKILL_DIR}/scripts/lesson.py search \
    --home ${HERMES_SKILL_DIR}/../../memory/shared --home <repo>/.memory/lessons "<symptom words>"
```

Quote the result in your self-check's "tried" line, including `no lesson matches`.

## Write a draft lesson

Only about your own mistake, and only with evidence: the exact command and its real result.

```
python ${HERMES_SKILL_DIR}/scripts/lesson.py add --home <General or Specific home> [--domain hermes] \
    --slug <short-name> --title "<the rule>" --symptom "<what you saw, one line>" \
    --evidence "<command> -> <result>" --body "<what to do instead>"
```

The test for the home: does it hold outside this project? Yes is General, no is Specific. A draft is not
found by search until the Advisor accepts it (the owner, until the Advisor exists); `accept` and `retire`
are not yours to run.

## Accept, retire (Advisor only)

```
python F:\Programowanie\my-claude-workflow\skills\fleet-lessons/scripts/lesson.py accept --home <home> --sha <commit> \
    --skill F:\Programowanie\my-claude-workflow\skills\fleet-lessons/SKILL.md <slug>
python F:\Programowanie\my-claude-workflow\skills\fleet-lessons/scripts/lesson.py retire --home <home> --reason "<why untrue now>" <slug>
```

- `--sha` is required: the commit the lesson was verified at, stamped as `Verified: <date> at <sha>`. Use
  the head the evidence came from (the PR head, or `origin/main` for a process lesson).
- Pass `--skill` with this SKILL.md, or the General index above stays stale until someone refreshes it.
- `add --domain <d>` files the accepted lesson under `<home>/<d>/`; use `fleet` for process lessons that
  hold for every bot, `hermes` for tool and runtime behaviour.
- After `add`, read the "related, check it is not the same lesson" line: merge into the named lesson
  instead of accepting a second copy of one rule.
- Accepting into a project home writes the lesson and `INDEX.md` into that repo's working tree, which is
  usually the owner's main clone. Commit and push them in the same turn: stage only those paths, check the
  staged diff for local paths, and commit as `docs: <summary>` with no scope. The repo's commit hook
  rejects scopes that are not on its list, and `lessons` is not on it. Uncommitted lesson files leave the
  main clone dirty, which blocks the next final review.

## Programs started

None. `lesson.py` only reads and writes markdown in the homes it is given.

## Recorded run

```
$ python scripts/lesson.py search --home ../../memory/shared "heredoc blocked headless"
../../memory/shared/hermes/headless-heredoc.md  BLOCKED: Command flagged as dangerous (script execution via heredoc) in a headless turn
```

```
$ python scripts/lesson.py accept --home ../../memory/shared --sha 1eb1ec8f --skill SKILL.md owner-question-check-decisions
accepted: ..\..\memory\shared\fleet\owner-question-check-decisions.md
```

## Example run

```
$ python scripts/lesson.py search --home memory/shared "script execution via heredoc headless"
memory\shared\hermes\headless-heredoc.md  BLOCKED: Command flagged as dangerous (script execution via heredoc) in a headless turn
```

## General index

Paths are relative to the General home.

<!-- lessons-index:start -->
- A census or invariant counter reads the same large number in every run, across different worlds → [A defect counter needs a test on the legitimate shape it must not count, not only on the defect](fleet/counter-red-on-legit-shape.md)
- a command is refused by approvals.deny and you are about to say the work belongs to someone else by rule → [A refused command is a config fact, not an ownership rule](fleet/deny-entry-is-not-an-ownership-rule.md)
- A Worker asks A or B on a contract (what a pass reads, what a stage waits on) and you are about to open a needs-owner question → [Before asking the owner a spec question, check the accepted decision records; a question they answer is decided, not asked](fleet/owner-question-check-decisions.md)
- You are writing a label reason or a Waiting line that says what the author is still doing → [Before writing what a PR still owes, read its latest review round; do not restate an older status](fleet/read-latest-round-before-status.md)
- a second Worker reports a failure you have already seen in another lane (a toolchain upgrade, a cache, a process nobody can kill) → [The same blocker in two lanes goes to the Advisor at once](fleet/same-blocker-in-two-lanes-goes-to-the-advisor.md)
- A PR or issue shows no author or Manager activity for days and you are about to name a cause (Worker stuck, lane capacity, baseline moved) → [Before naming why work stalled, check that the bots ran at all](fleet/stall-check-bot-alive.md)
- BLOCKED: Command flagged as dangerous (script execution via heredoc) in a headless turn → [In a headless turn, run scripts from a file, not inline](hermes/headless-heredoc.md)
<!-- lessons-index:end -->
