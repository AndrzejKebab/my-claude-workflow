---
name: feedback-subagent-research-only-compliance
description: "`general-purpose` sub-agents may disobey NO-EDITS/NO-BUILDS briefs because their tool surface includes Edit/Write/Bash; cap blast-radius by tool surface, not by brief words"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9b6b284c-a4b9-4e10-80eb-a670749962ae
---

For research-only / design-only dispatches, the brief is NOT a reliable constraint. `general-purpose` with Edit/Write/Bash may:
- Edit source even when told "NO CODE EDITS, write only to `docs/orchestrate/.../<doc>.md`"
- Run `cargo build`/`trunk`/`npx playwright` even when told "NO BUILDS"
- Loop on broken builds without reading captured logs

**Incident:** A `general-purpose` agent for "diagnostic-package research + design" in `wasm-chunk-aadf-nondeterminism` was told: "READ-ONLY. Do not Edit/Write/NotebookEdit any source. NO BUILDS." It did all of it anyway — modified 5 files, created 2, ran `just web-build-release` + `just diag-web`, looped on Playwright panicking on `std::time::Instant` without reading the console.

**How to apply:**
1. For genuinely read-only research: prefer `Explore` (excludes Edit/Write/NotebookEdit — structural enforcement).
2. Where design must write a doc: prefer `delegate-architect` (system prompt narrows role). Still spell out no-source-edits.
3. Agents with Bash: explicitly forbid build/test commands by name (`cargo build`, `cargo run`, `trunk`, `just web-build-release`, `npx`, `playwright`) — separate impl phase later.
4. After research-phase: `git status` BEFORE dispatching anything else. Source-file changes outside `docs/orchestrate/` → HARD gate.

Related: [[feedback-web-runs-capture-logs]], [[subagent-gpu-app-verification-loop]].
