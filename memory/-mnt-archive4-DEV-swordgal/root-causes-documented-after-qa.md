---
name: root-causes-documented-after-qa
description: "swordgal working rule: a confirmed root cause earns a durable doc under docs/ (not just an orchestrate journal) — but only once the owner's manual QA confirms the fix, because QA success is the truth, not a green suite"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d5380412-70fb-441c-9555-683830c3509a
  modified: 2026-07-24T10:36:35.919Z
---

Ruled by the owner 2026-07-24, mid motion-matching session.

**When a root cause is genuinely identified, record it durably under `docs/`** — a real reference
page, not only a `docs/orchestrate/<topic>/` journal entry. The orchestrate docs are one session's
working memory ([[../../../../../../home/midori/.claude/CLAUDE.md]] ranks them below code and
papers); a confirmed mechanism deserves better standing than that.

**Write it only after the owner's manual QA confirms the fix.** Their words: *"only after manual
QA — we treat success as truth."* A green suite is not the trigger. This is the same law as
[[character-controls-manual-qa-over-e2e]] applied to documentation: for feel-shaped defects the
owner's eye is the oracle, so a mechanism is not "understood" until the symptom is observed gone.

Practical order: diagnose → fix → hand the owner a QA session → **wait** → on confirmation, write
the durable doc naming the mechanism, the measurement that proved it, and the fix. A cause that QA
does not confirm stays a hypothesis in the session journal, however good the story is.

Related: [[free-mode-turn-is-a-transform-arc]] (where a confident story survived a green gate and
was still wrong twice).
