---
name: biome-json-churn
description: "biome re-sorts JSON keys via useSortedKeys; package.json + biome.json exempted via overrides; ai:* scripts are master's"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 74f45ba9-c39f-466f-8988-4fad6238abdf
  modified: 2026-07-23T15:29:50.355Z
---

Standing facts for this repo's biome config:

1. **`ai:*` package.json scripts are origin/master's** (`ai:check`, `ai:mcp:codex/claude`, `ai:hooks:codex/claude`, `ai:setup`) — thin `node .agents/scripts/*.mjs` wrappers in a human/logical order, NOT alphabetical. Do not delete or reorder them.

2. **`useSortedKeys` stays in `biome.json`** (`assist.actions.source`, master's config). It alphabetizes JSON object keys whenever biome runs (`biome check --write`, incl. the post-edit hook), which churns manifests and destroys human key order.

3. **`package.json` is exempted from key sorting** via an `overrides` block. Verified 2026-07-23: the override is narrower than it once was — `includes: ["**/package.json"]` with only `assist.actions.source.useSortedKeys: "off"`. Formatting and linting still apply to it, and `biome.json` is no longer in the list at all. That exemption is what preserves authored key order while useSortedKeys stays on elsewhere.

   Because of it, **`biome check` no longer reorders `package.json` `exports`**. AGENTS.md carried a warning that `check` would silently break module resolution that way; it was stale and was removed on 2026-07-23. `biome format` remains the right tool for formatting alone, but not for that reason.

**Biome gotchas learned:**
- `files.includes` exclusion needs the `**/` prefix: `!**/package.json` works, bare `!package.json` / `!biome.json` do NOT match.
- Biome ALWAYS processes its own config file — you cannot self-exclude `biome.json` via `files.includes` (it gets checked/formatted anyway). Use `overrides` with `formatter.enabled:false` for that.

**Why:** user repeatedly flagged re-sorted JSON diffs as noise; human key order (esp. ai: scripts, package.json script grouping) is meaningful.

**How to apply:** keep feature branches free of repo-wide biome reformat of files they don't functionally change; don't alphabetize package.json/biome.json; if adding new manifest-like files whose order matters, add them to the biome `overrides` exemption. Related: [[game-framework-contract-shape]].

**Post-edit hook = biome integration via origin/master's generic mechanism (INTENDED — keep it).** The branch integrates biome as a file-scoped post-edit autofix; that integration is wanted ("we're trying biome out — actually integrate it"). Final design keeps master's generic command-LIST runner and only adds file-scoping:
- `.agents/hooks/hooks.json` `postEdit` keeps master's generic shape: `{ enabled, commands: ["pnpm exec biome check --write --no-errors-on-unmatched --files-ignore-unknown=true {files}"], timeoutSeconds }`. Biome is ONE swappable command in the list; `{files}` makes it file-scoped. A single `biome check --write {files}` both autofixes AND exits non-zero on unfixable errors (verified) — no separate verify step needed.
- `hook-runner.mjs` = master's `for (const command of policy.commands)` loop + `{files}` substitution (getEditedFiles/shellQuote) + master's generic feedback ("Post-edit verification failed. Fix before continuing."). Reads `policy.commands`, NOT any biome-specific key.
- `hook-config.mjs` = origin/master, unchanged (statusMessage "Running post-edit verification"); it just wires `PostToolUse → hook-runner post-tool-use`.

Keep biome ONLY in the command string. Do NOT introduce biome-specific keys (`postEdit.biome`, `autofix`/`verify` slots) or labels — an earlier attempt did (`postEdit.biome`, `"Applying biome autofix"`, `policy.biome`, then `autofix`/`verify` keys); the generic `commands` list is closer to master and more swappable. Do NOT rip out the integration either — keep it, just keep the mechanism generic.

**Churn corrupts review, not just noise:** useSortedKeys reordering the `PreToolUse`/`PostToolUse` blocks in hook-config.mjs made a diff that looked like the matcher changed `"Bash"` → `"Edit|Write|MultiEdit|NotebookEdit"` (i.e. Bash dropped) when nothing actually changed — the blocks were just re-sorted. Reordered object keys produce misleading diffs.
