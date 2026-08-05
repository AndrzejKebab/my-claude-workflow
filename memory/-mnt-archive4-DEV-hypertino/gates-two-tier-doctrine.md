---
name: gates-two-tier-doctrine
description: "User banned permanent scenario-walkthrough gates (2026-07-06) — acceptance retires after landing, check battery holds invariant gates only, UI acceptance is user live QA"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 95643680-19f6-42f0-8101-4faf8ea4085d
---

User verdict on milestone gate scripts (E2, hypertino): "one-time use, don't protect from regressions, too slow to write, tailored toward exact scope of what we wrote — unit tests disguised as e2e tests." Directive: "rip that from the very workflow."

**Why:** Proven in-session: full gate battery green while the app was visibly Y-inverted (gate validated the implementation against its own copy); a reference gate sat silently red for days; an intended convention change forced coordinate recalibration + reference rebakes across the walkthrough gates. The roadmap ([[hypertino-continuation-state]], docs/spec/10-appendix/05-roadmap.md) is continuous landscape change — scope-tailored walkthroughs tax every milestone.

**How to apply:** Two tiers. Acceptance gates (scripted scenario, bite proofs) run green once at landing, evidence in the log, then retire — never wired into `just check`. The permanent battery holds invariant-shaped gates only: wire/store/hash identity, determinism, lint fences, golden parity, real-entry-point boot smoke ([[validate-real-entry-points]]). UI-visible behavior is accepted by the user's live QA session. Durable regression vehicle = record/replay + divergence + metrics (roadmap TL2) — scenario scripts retire into replays. Gate authorship must not dominate a dispatch's tokens. Canonical text: delegate SKILL.md "Gate tiering" guard + hypertino AGENTS.md. See [[suite-may-be-vacuous]], [[representative-e2e-not-manual-qa]] (still holds for proving a mechanism at landing — the ban is on permanence).
