---
name: keep-feature-prs-scoped
description: "Don't fold unrelated mainline bugfixes into a feature PR; surface them, let the owner decide"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 39ad7cf0-fb87-4e7a-b259-0ee6550e3537
---

While building the local-FE-QA tool, QA surfaced a mainline fun-mode `openBet` regression (player-service `transaction-orchestrator` now sends the wallet `gameId_skin_rtp`; the demo wallet + e2e harness still key balance by the bare gameId). I diagnosed it, then tried to *fix* it inside the feature branch — and got the direction wrong.

User's correction: **"you can't just revert to gameId everywhere - just leave this out of this PR."** The integration-id gameId format (`<gameId>_<skin>_<rtp>`) in transaction methods is **intentional** and needed elsewhere — reverting it is wrong. The demo-wallet/harness still keying by bare gameId is a known gap the owner will reconcile, not something to "fix" by reverting.

**Why:** a feature PR should carry the feature. A mainline bug it merely *surfaces* is the owner's call — especially when the "right" direction needs domain knowledge (which gameId format the real wallet expects) I don't have.

**How to apply:** when a task surfaces an unrelated mainline bug, surface it with a precise, verified diagnosis and stop — don't fold a fix into the feature branch unless explicitly told which direction. Formatting a stray master file to pass the commit gate is fine (a separate `style:` commit); reverting a teammate's deliberate change is not. See [[verify-real-functionality]].
