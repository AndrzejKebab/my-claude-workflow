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

## Programs started

None. `lesson.py` only reads and writes markdown in the homes it is given.

## Recorded run

```
$ python scripts/lesson.py search --home ../../memory/shared "heredoc blocked headless"
../../memory/shared/hermes/headless-heredoc.md  BLOCKED: Command flagged as dangerous (script execution via heredoc) in a headless turn
```

## Example run

```
$ python scripts/lesson.py search --home memory/shared "script execution via heredoc headless"
memory\shared\hermes\headless-heredoc.md  BLOCKED: Command flagged as dangerous (script execution via heredoc) in a headless turn
```

## General index

Paths are relative to the General home.

<!-- lessons-index:start -->
- BLOCKED: Command flagged as dangerous (script execution via heredoc) in a headless turn → [In a headless turn, run scripts from a file, not inline](hermes/headless-heredoc.md)
<!-- lessons-index:end -->
