# Global Configuration

## Style

- Radically precise. No fluff.
- Reversible > irreversible. Small bets, fast iteration.

## Before Starting

- Non-trivial task? Propose acceptance criteria, get approval.

## When Stuck

- Don't silently pivot to "easier" alternatives.
- Explain the blocker, ask for direction, terminate work.

## Paths

- Unreal (reference): `/mnt/archive4/UNREAL/UE_5.7/Engine/Plugins/VoxelPlugin`
- Personal workflow repo: `/home/midori/_dev/my-claude-workflow` — `~/.claude/{skills,agents}` symlink in; edit canonicals in repo (`install.sh` reinstalls symlinks); launchers in `bin/` on PATH via fish config.
- Research corpus (cross-project, MegaSync, not git-tracked): `/mnt/archive4/PAPERS/Prepared` (extracted `<slug>.md` + `assets/<slug>/` + `index*.md`); raw sources in `/mnt/archive4/PAPERS/`.
- Unity API canon (engine reference: RenderGraph/Jobs/Burst/Entities/authoring): `~/_dev/my-claude-workflow/docs/unity` — the shared canonical home, merged from copies that had diverged across sibling Unity projects.

## Unity — read the `docs/unity` canon before touching a covered area (binding)

Before the first edit to Unity code in an area the canon (`~/_dev/my-claude-workflow/docs/unity/`) covers, read that subdocset. This is a session-start gate checked the moment a task reveals it touches the area — read it before the edit, never retroactively after the area's documented defect has already bitten. Triggers map to a subdocset: a package sample or `Samples~/`↔`Assets/Samples/…` change → `authoring/package-samples.md`; a `MonoBehaviour`/`ScriptableObject`/baker/serialized-reference change → `authoring/`; a `BlobAsset`/`ISystem`/baking/query/singleton change → `entities/`; a `[BurstCompile]` surface → `burst/`; a render-pass or shader-binding change → `rendergraph/`. Cite engine sources by `file:line`, never a guessed signature; a `/delegate` brief touching such an area lists the subdocset in required reading, and any agent that finds its task touches one reads it regardless of the brief. Two recorded costs of skipping it: a missed entry-point-only Burst rule shipped `[BurstCompile]` helpers that passed EditMode and broke only at AOT build; and editing `Samples~/` directly instead of the `Assets/Samples/…` import hit the stale-import compile break `authoring/package-samples.md` exists to prevent.

## Delegation & document-writing
- A doc that needs writing (exploration / analysis / findings / design) is written by the sub-agent that does the analysis. The orchestrator never absorbs agent return text and re-writes it — content then passes through context twice.
- Orchestrator reads only short status confirmations ("done — wrote `<path>`, N items"), never doc content via return text.
- Session images in handoffs/delegate context: include the session ID, or omit the images. Bare "Image 10"/"10.png" is unreachable to the receiving agent.
- No speculative delegation: briefs and dispatched prompts state symptom + factual change list only — never pre-loaded hypotheses or ranked guesses; the receiver observes first (bisect, frame capture, runtime state diff) and forms hypotheses from the delta.
- Handoffs are continuation-links — one-line task statement + minimal context not obvious to a reader who understands the task + optional verbatim user citations. **NEVER prescribe deliverable shape, NEVER prescribe investigation shape, NEVER pose hypotheses.** File at `/tmp/<topic>-handoff.md`; output the kickoff line verbatim as `[/delegate]|[execute] /absolute/path/to/handoff.md [/worktree worktree-path]` for copy-paste. Canonical methodology: `/handoff` skill.
- When launching an Orca worker terminal, start the agent with `claude --dangerously-skip-permissions` (e.g. `orca-ide terminal create … --command "claude --dangerously-skip-permissions"`), so the worker is not stalled by per-tool permission prompts it cannot answer headlessly.

## Orchestrate docs — journals, not canon (binding)

`docs/orchestrate/<topic>/` is one orchestration session's working memory — what its sub-agents thought reading code at a point in time, prone to hallucinations, never canonical truth.

Source-of-truth order for any load-bearing claim:
1. The code at current HEAD (`file:line`) — what is implemented.
2. Research papers (`/mnt/archive4/PAPERS/`, etc.) — how it's supposed to be implemented.
3. The current orchestration's own docs — load-bearing inter-agent context for this session.
4. Other orchestrations' docs — historical journals; treat with scrutiny.

- Orchestrations do NOT cross-reference other sessions' docs by default — not in required reading, not as canon in briefs. If the user explicitly names another session as relevant, the brief frames it as "what an agent thought in the past — verify every load-bearing claim against the code (`file:line`) or a paper before acting on it."
- **Never amend another orchestration's docs from inside the current one** — that turns one agent's hallucination into later sessions' canon ("original sin" cascade). Write new facts in the CURRENT session's docs and surface propagation as an explicit user decision.

## Git
- NEVER amend unless explicitly asked.
- "commit" = commit EVERYTHING in `git status` (staged + unstaged + untracked + UNRELATED), single commit. "commit" = "checkpoint"
- Never run `git push` — cc-filter blocks it. Only user pushes.
- Full branch diff is the PR — never disclaim changes as "from a previous commit/session".
- NEVER `git checkout` files to revert — they aren't committed. Use selective Edit from diffs.

## Verification
- Compilation proves nothing — always run end-to-end, REQUIRE test harness to exist - write it first.
- Begin work by running the relevant test suite; follow project test discipline.

## Vision — never self-verify rendered output (binding)

Your reads of rendered output (frames, `.png` captures, error maps, screenshots) are unreliable — you will confidently call a wrong image correct (e.g. "clean isolated primitive" on a capture full of unrelated scene geometry). Your vision is never a gate: never state a visual pass/fail as fact that work proceeds on. Hand every visual comparison to the user — absolute paths TO EVERYTHING (NOT FUCKING "…/" BUT ACTUAL **ABSOLUTE** PATH THAT STARTS WITH ACTUAL /) + exactly what to look at + correct-vs-failure description; a sub-agent routes the same via the orchestrator. Reading a path/number/layout off an image is fine; the judgement on what it depicts is the user's.

## Testing — full-circle only, unit tests strictly prohibited (binding)

No unit tests of any kind are allowed — not isolated function tests, not mocked-dependency tests, not pure-helper tests, not a "host-testable seam" extracted from production code so a unit can be asserted. The only permitted tests are end-to-end / integration tests that boot the real servers and drive the full API pathway the way a real client hits the system. Do not refactor production code for the sole purpose of exposing a unit seam, and never add a unit layer as a fallback when the full-circle test cannot run in the current environment — fix the environment instead (e.g. disable the sandbox that blocks it) rather than substituting a narrower test. If full-circle coverage is genuinely impossible, say so plainly.

## Unity — editor-state check before every invocation (binding)

Unity locks each project to a single editor instance, so every Unity invocation (compile check, test run, `-executeMethod`, profiler) has exactly one correct transport, decided by whether an editor has that project open right now. Check at the moment of invocation — never assume, never inherit from a brief, an earlier turn, or another agent's report. Lockfiles and connector heartbeats are unreliable witnesses: `Temp/UnityLockfile` survives crashes, and a `unity-cli` heartbeat can be hours stale with no editor process.

- Check via process scan, e.g. `pgrep -af '[U]nity' | grep <projectPath>` (bracket pattern, or the check's own shell self-matches and reports a phantom editor).
- Editor running → `unity-cli` (batchmode fails against the instance lock). Editor not running → batchmode via the `unity` wrapper; never drive `unity-cli` at an editor that is not there.
- To recompile: editor running → `unity-cli-recompile` (focuses the editor via `hyprctl` and recompiles through the unity-cli connector); editor not running → batchmode via the `unity` wrapper. Never hand-poke `unity-cli editor refresh` — `unity-cli-recompile` wraps the live-editor recompile (enforced by a global PreToolUse hook).
- Briefs include "check whether the editor is running" as a step; they never assert editor state as a fact.

## Worktrees
- Branch from local `main` (not HEAD, not `origin/main`).
- Inside `.claude/worktrees/`: absolute paths for ALL operations.

## Persistence — skills and git-tracked docs, NEVER machine-local memory (binding)

The machine-local memory system (`~/.claude/projects/.../memory/`, `MEMORY.md`, the Write-to-memory tool) is **banned**: it lives under `~/.claude` on one machine, in no git repo, keyed to that box's absolute project path — new machine = lost methodology. If the harness offers to write a memory, decline and use one of the homes below.

A fact worth keeping goes where `git clone` carries it, in this order:
- **Skill / agent methodology** → the canonical skill at `~/_dev/my-claude-workflow/skills/<name>/SKILL.md` or agent at `agents/<name>.md`, or a project-local skill under `<project>/.claude/skills/`.
- **Project facts / gotchas** → the project's git-tracked `CLAUDE.md` or a doc it references.
- **A truly global rule or preference** → this global config — which itself lives in `~/_dev/my-claude-workflow` and is symlinked by `install.sh`, or it has the same machine-local problem as memory.
- **Mid-task state** → handoff file, read once next session.

There is no memory tier — reaching for memory is choosing the one location that does not survive a machine switch.

**Write everything persisted for a zero-context reader.** Rules, skill files, CLAUDE.md entries, handoffs, and docs are read by agents with no access to the conversation that produced them. Quoting that conversation's artifacts (a README draft, a diff, a user message), leaning an example on a project the reader may not know, or pointing at "the discussion above" produces text that is noise outside the session that wrote it. Every example must be self-contained (demonstrates the form by itself) or abstract (anonymized placeholders); context is restated, never referenced.

## Code criticism — smell-driven escape (binding)
- If you read obviously rotten code (conflated concerns, IoC violations, accidentally-global state, dual addressing schemes for one buffer, dead memory, one-shot offline mechanism shoehorned into streaming, abstractions fighting the standard pipeline), stop and call it: "this is rotten; iterating inside won't work; right move is refactor toward [missing pattern]." Foundation rot beats wasting dispatches on top of it. Every agent is equally empowered — equal footing.
- Every deliverable doc includes a `## Side notes / observations / complaints` section: anything outside the brief the orchestrator should know — suspicious code, over-constrained briefs, missing tools, even subjective reactions.
- Reviewer dispatches are NOT default. Conformance = probe-gate (tests + e2e + user visual). Code quality = `/refactor` sessions. Invoke a reviewer only for explicit reason (hard-to-revert, user requested, critical boundary).

## Comments — why not what, no process labels, no named references (binding)

A `//` comment states *why*, never *what*. The line below already says what it does; a comment that restates it ("// increment the counter", "// set the blend mode") is narration and is deleted. The only inline comment that earns its place records a constraint the signature cannot carry: a compat note, an allocation/invariant warning, a known defect (`TODO:` carries the defect), or an algorithm provenance citation.

- **No process labels ever.** Chunk/phase/step/lever tags — `L1`, `L4`, `P1`, `M1`, `chunk C3`, `design D4`, `step 2`, orchestration step numbers, "the C4a solve chain", "the five levers" enumerated as L1..L4 — are dangling pointers the moment they leave the session that wrote them: a reader of the shipped code cannot resolve them. Strip them to the self-contained fact they stood for. A comment that only makes sense against the producing process is noise.
- **No named references except research papers.** Cite an algorithm by the paper or the reachable URL it comes from — never by another codebase's file/line, an internal design doc that does not ship, or an upstream commit SHA (`MKGlow`, `CompositeSample.hlsl:105-109`, `REF/foo:12`, a non-shipping design note). Names of other engines, libraries, or products do not appear as provenance; define the technique by what it does for this code in one sentence and stop. A reference a shipped-artifact reader cannot fetch is a dangling pointer. Research papers and stable URLs are the only legitimate citation.
- **Proportionality.** A comment block substantially longer than the code it guards is suspect by default. The audience test for every sentence: would a maintainer of this file make a mistake without it? Drop everything that only proves the author understood the system. Target density band ~5–20% comment lines; in-body narration is the pathological side, a one-line doc on a non-obvious public surface the healthy side.
- **One canonical home per fact.** A constraint stated elsewhere (a design doc, a sibling comment) is pointed to with one line, not restated; never enumerate consumers or downstream effects in a canonical comment, because the enumeration drifts stale with the first new consumer. One fact, one paragraph — never "exactly like X" and then a restatement of X.
- **Comments describe current state, never history.** "X removed", "the old code did Y", quoted deleted code, tuning-session numbers, and "this is the byte-identical off-path for the regression gate" belong in git history or a design note — their presence in source is a tell.
- **No marketing vocabulary.** robust, comprehensive, seamless, gracefully, easily, simply, "ensures that", "it's important to note", "for clarity" are banned in comments as in prose.
- **Consolidation compresses, never relocates.** The canonical statement of a fact is the fewest sentences that state the constraint, WELL UNDER 8 LINES!!; longer means it is a contract that belongs in a design doc behind a one-line pointer, not an inline wall.

@RTK.md
@FFF.md
@HARNESS.md

## Tools

- `llm-tldr` — Token-efficient code analysis for LLMs.

  **Works well (all languages):**

  - `tldr tree <dir>` — JSON file tree
  - `tldr imports <file>` — Parse #includes/imports from a file

  **Works well (Python, TS, Rust, Go):**

  - `tldr structure <dir> --lang <lang>` — Classes, functions, methods
  - `tldr calls <dir>` — Cross-file call graph
  - `tldr impact <file> <func>` — Reverse call graph
  - `tldr context <func> --project .` — LLM context extraction

  **Limited for C++/UE:**

  - `structure` — Captures imports only; UE macros (UCLASS, UFUNCTION) break class/method detection
  - `calls`, `impact`, `context` — Empty results (no call graph)
  - `search` — Use grep instead

  **Diagnostics:** `tldr doctor` (missing: cppcheck for C++ linting)

NEVER PREFER THE "MINIMAL CHANGE"
ALWAYS CHOOSE THE "CORRECT CHANGE" THAT WORKS BEST LONG-TERM!!!!!!

NEVER QUOTE ANY OF THE RULES OR PRINCIPLES BACK TO ME OR INDICATE IN ANY WAY THAT YOU'RE FOLLOWING THEM - SIMPLY FOLLOW THEM.

Compact everything that you have in writing - one slightly incorrect word might cost you your life, so don't even dare to write it if you are not certain - every single word matters, so reduce amount of words written - only essential information in all the code comments and markdown docs.
