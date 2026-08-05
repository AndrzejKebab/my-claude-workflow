---
name: replay-is-m2m-open
description: "replayWager/replayBet are service-to-service, intentionally open (no auth) until M2M exists — don't re-add player ownership"
metadata: 
  node_type: memory
  type: project
  originSessionId: 0e725b27-d2cb-49c2-a9a2-774b5e63b14c
  modified: 2026-07-23T07:43:03.867Z
---

`replayWager`/`replayBet` are a **service-to-service** call (operator/back-office re-derives a
wager), scoped to no player. They are **intentionally open** — exempt from the session policy
(`app/plugins/mercurius-auth.plugin.ts`) and check no ownership (`replay.ops.ts`), so any caller
with no token can replay any wager. Both carry `TODO(m2m-auth)`.

**Why:** they belong behind machine-to-machine auth, which does not exist yet. The prior
player-session scope was the bug: it threw "Wager not found" for any caller that wasn't the exact
session that staged the wager (decided 2026-07-23, branch `fix/replay-open-until-m2m`, commit
878bc06e).

**How to apply:** do NOT re-add `useSession()` ownership to replay as a "security fix" — that
reverts a deliberate decision. When M2M auth lands, gate on the calling *service*, not a player
session, and update `replay-access.integration.ts` (which currently pins the no-token contract).
A player-facing `getBetById` is the opposite case — it *should* scope to the session
([[game-figures-have-a-source]] is unrelated; see docs/todo/bet-ownership.md). Replay re-derives the
rate from `Wager.rate`, not from any session.
