# Lessons

Symptom → lesson. Search with `lesson.py search`.

- A census or invariant counter reads the same large number in every run, across different worlds → [A defect counter needs a test on the legitimate shape it must not count, not only on the defect](fleet/counter-red-on-legit-shape.md)
- a command is refused by approvals.deny and you are about to say the work belongs to someone else by rule → [A refused command is a config fact, not an ownership rule](fleet/deny-entry-is-not-an-ownership-rule.md)
- A Worker asks A or B on a contract (what a pass reads, what a stage waits on) and you are about to open a needs-owner question → [Before asking the owner a spec question, check the accepted decision records; a question they answer is decided, not asked](fleet/owner-question-check-decisions.md)
- You are writing a label reason or a Waiting line that says what the author is still doing → [Before writing what a PR still owes, read its latest review round; do not restate an older status](fleet/read-latest-round-before-status.md)
- a second Worker reports a failure you have already seen in another lane (a toolchain upgrade, a cache, a process nobody can kill) → [The same blocker in two lanes goes to the Advisor at once](fleet/same-blocker-in-two-lanes-goes-to-the-advisor.md)
- A PR or issue shows no author or Manager activity for days and you are about to name a cause (Worker stuck, lane capacity, baseline moved) → [Before naming why work stalled, check that the bots ran at all](fleet/stall-check-bot-alive.md)
- BLOCKED: Command flagged as dangerous (script execution via heredoc) in a headless turn → [In a headless turn, run scripts from a file, not inline](hermes/headless-heredoc.md)
