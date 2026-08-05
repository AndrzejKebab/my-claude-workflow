# Memory index

- [No proprietary base references](no-proprietary-base-references.md) — never name the prior private reference repos in this codebase
- [Stealth framing, not porting](stealth-framing-not-porting.md) — say "implementing"; never frame work as transferring/porting from the reference
- [Game framework contract shape](game-framework-contract-shape.md) — `games/<g>/manifest.ts` GameManifest seam, multi-game auto-discovery, class uses its own types
- [Biome JSON churn](biome-json-churn.md) — useSortedKeys kept; package.json+biome.json exempted via overrides; ai:* scripts are master's
- [Player-service session connector](player-service-session-connector.md) — game↔player seam implemented + e2e-green; m2m-token HS256; two runtime tiers; player-service = wallet proxy; demo-mode owns external REST seam
- [RTP noise threshold](rtp-noise-threshold.md) — sub-significance RTP movement is noise; report only if catastrophic
- [Single-RTP games are valid](single-rtp-games-are-valid.md) — single-math is legitimate, not unfinished; fix the over-strict gate, don't exclude/flag
- [Verify real functionality](verify-real-functionality.md) — run the actual command + the FULL suite before "done"/recommending; `--print` and single-file runs hid two bugs
- [Keep feature PRs scoped](keep-feature-prs-scoped.md) — surface unrelated mainline bugs, don't fix them in the feature branch; wallet txn gameId is intentionally `<gameId>_<skin>_<rtp>`
- [player-service e2e green since PR #34](player-service-e2e-red-at-master.md) — the six wallet-counterparty tests are a documented park, not rot; 0 fail is the bar
- [git diff redirect is empty](git-diff-redirect-is-empty.md) — an rtk git wrapper kills redirected diffs; pipe instead, and resolve refs to SHAs first
- [Shared postgres, cross-checkout push](shared-postgres-cross-checkout-push.md) — another worktree's service drops your branch's columns; re-`db:push` before diagnosing mass e2e failures
- [Game figures have a source](game-figures-have-a-source.md) — max-win etc. exist upstream; look up, never guess; re-skins inherit by construction
- [Replay is M2M, open until auth](replay-is-m2m-open.md) — replayWager/replayBet are service-to-service, intentionally unauthenticated; don't re-add player ownership
- [Real target games](real-target-games.md) — only vikings + seven-wonders matter; sunspire is broken, tidalspin family mis-declares, both ignored
- [No local typecheck gate](no-local-typecheck-gate.md) — hooks are biome-only; cold `pnpm typecheck` is 26 s vs a 30 s hook budget, so run it yourself
- [Simulating gates run on request](simulating-gates-on-request.md) — `test:gates`/`capture:check`/`certify` only when asked, never as a close-out reflex; routine set is `verify` + integration; after a one-test fix re-run that test only
