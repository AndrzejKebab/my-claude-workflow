# P7 Platform Memory

## Architecture Insights
- [player-api notes](player-api.md) — TypeScript gotchas, test infrastructure DSL
- Reward data flows transiently: game-api → player-api GraphQL → transactionHandler → adapter
- Adapters consume reward from `processTransaction` args (not from DB directly)

## Workflow Rules
- **Always use `/commit` skill** to commit — never manually run git commit

## Shell Pitfalls
- `status` is a **read-only variable** in fish shell — use `st` or another name
- **tokf filter** adds branch tracking info to `git status --porcelain` — use `| wc -l` or `| cat` for accurate counts

## Feedback
- [Always test before push](feedback_always_test_before_push.md) — run pnpm test before every git push
- [Clean install before testing](feedback_clean_install_before_test.md) — run `pnpm install --frozen-lockfile` after resetting lockfiles
- [Use origin/master](feedback_use_origin_master.md) — always fetch and compare against origin/master, not local master
- [Use [] over Array](feedback_array_syntax.md) — ESLint bans `Array<T>`, use `T[]` syntax
- [No git checkout](feedback_no_git_checkout.md) — never use `git checkout` to restore files, manually edit instead
- [All tests must pass](feedback_all_tests_pass.md) — 0 failures is the acceptance criteria, no "pre-existing" excuse
- [Consistent randoms required](feedback_consistent_randoms.md) — all RNG-dependent tests must use file-backed consistent randoms, not just cheats
- [Commit on current branch](feedback_commit_on_current_branch.md) — don't create new branches when already on a feature branch
- [GraphQL validates non-nullable](feedback_graphql_validation.md) — don't manually check fields, let GraphQL API enforce constraints
- [No conditional assertions](feedback_no_conditional_assertions.md) — never wrap expect() in if branches, use marker-driven flow
- [CI rebuilds only on feat/fix](feedback_ci_trigger_commit_types.md) — other conventional types commit fine but don't trigger a release rebuild
- [REDIS_SESSION_CACHE_TTL is auth state](feedback_redis_session_ttl_not_bypass.md) — never set to 0; it goes straight to Redis EXPIRE/EX and deletes the key, breaking auth
- [Env-active currency list only](feedback_env_active_list_only.md) — never reference modern or legacy currency lists directly in client-api config pathways; always go through the env-active selector
- [gcb = git checkout -b](feedback_gcb_means_new_branch.md) — "gcb, commit, preflight" means create a new branch first, then preflight, then commit
- [Use production code paths](feedback_use_production_codepaths.md) — tests/tools that evaluate live config must run through the real view/service layer with an in-memory fake of the slow boundary, not reimplement the transformation chain
- [decoupleClientOnSlot is the catalog build](feedback_decouple_is_catalog_build.md) — never use it for full-catalog sweeps in unit tests; it's slow; full sweeps belong in `pnpm test:integration` against the seeded DB
- [Hard-coded assertions in tests](feedback_hardcoded_assertions_in_tests.md) — RHS of every expect() must be a literal, never a derived/helper-computed value
- [E2E only with published fixtures](feedback_e2e_only_with_published_fixtures.md) — currency/bet tests use real `slot-catalog/public/clients` + slots + GraphQL client, not synthetic `IClientOnSlot`
- [Assert printable real amounts](feedback_real_amount_assertions.md) — currency/bet test literals are `'USD 0.20'` / `'BTC 0.00000400'`, never raw minor units like 20 / 400
