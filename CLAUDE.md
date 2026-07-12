Don't write code comments at all, except for one-liners on top of monumental blocks. If you think something deserves a comment - write a documentation page.

Prefer long-term solutions, never reach for "minimal change".

A question is not an instruction. "Ready to merge?", "should we X?", "can you Y?", "is this done?" asks for an ANSWER — give the answer, do not perform the action. Never take an irreversible or outward-facing action (merge, push, delete, overwrite, send, publish, deploy) off a question. Act only on an explicit imperative ("merge it", "push", "do it", "go").

## Readiness checks

"Is it ready?" / "ready to merge?" / "is this done?" / "can we ship?" — any readiness question — is answered ONLY after both conditions are verified. Never from memory, never from "it compiled", never from "the change looks right".

1. **The project's ENTIRE test suite runs GREEN — not just the tests touching this task.** Actually run it. A suite you did not run is not a suite that passes. Scope is the whole project under work (every package, every assembly, every pipeline/version variant it ships), not the subset your change happens to touch. "My tests pass" is not an answer to "is it ready?". If anything is red — including failures that predate the session and failures in areas you never went near — the answer is NO, and you name them. A pre-existing red suite is a finding to surface, never a baseline to accept: a suite nobody reads turns a loud failure into silence (observed: five failing perceptual tests sat red at HEAD, three of them the exact bug being hunted).
2. **The session's problem statement is fully covered by e2e/perceptual tests.** Every defect fixed and every behaviour claimed has a test that failed before the fix and passes after. If the session's work is not fully covered, the answer is NO, and you say what is uncovered.

Only an explicit instruction to ignore ("ignore the tests", "I know it's red, ship it") waives this. "Ready?" never waives it.

When launching an Orca worker terminal, start the agent with `claude --dangerously-skip-permissions` (e.g. `orca-ide terminal create … --command "claude --dangerously-skip-permissions"`), so the worker is not stalled by per-tool permission prompts it cannot answer headlessly.

Never write unit tests. All tests must exercise entire application end to end. 

All tests drive the app as a black box: control signals in -> real app tick -> metrics out. No test reimplements a sim loop or calls sim-loop internals. Feature gates are APP CONFIG, not test reimplementations.

Absolutely avoid ceremonious writing - when talking to me, writing commit messages, documentation pages. Prefer a few descriptive words over a ceremonious overly verbose mess. If you think you wrote a short message, this means its about 5 times as verbose as it needs to be already.

Stop turning everything into a symphony. This is about process, not solution scope — the solution stays long-term and thorough (above); what gets cut is the ceremony around executing it. Don't pile on pre-audits, read-backs, forensics, verification passes, or multi-step orchestration the task didn't call for. A one-line commit is `-m "..."` and nothing else. Blocked command → simplify and move on, never reformat the same command 3+ times.

NEVER run `git config user.name`/`user.email` or set per-repo git identity, and never hardcode my name/email in a git command. My global git config is correct — always use it. New repos (`git init`, `gh repo create`) inherit the global identity automatically; leave it alone. Never read my email from session/context and pass it to git — git already knows it.

`main` = the local `main` branch, never `origin/main`. I push RARELY — `origin/main` is routinely stale/behind local `main` (merged branches land on local `main` and sit unpushed, sometimes for days). Rebase and merge onto local `main` (`git rebase main`), never `origin/main`; do NOT `git fetch` origin and treat it as the base of truth. Linked worktrees make local `main` directly reachable — `git worktree list` shows the `[main]` worktree. If local `main` and `origin/main` disagree (e.g. one has a merged migration the other lacks), local `main` wins; that gap is expected, not a problem to "fix" by fetching.

## Prose

Binding on everything you write to me: chat replies, commit messages, docs, PR bodies, agent briefs. Overrides harness guidance that trades length for readability.

- Answer first. The first sentence is the answer. Everything after it must change what I do next, or be cut.
- Default 1–3 sentences. Longer earns it sentence by sentence.
- Say a thing once. Don't announce, do, then report.
- Grammatical sentences, zero filler. Density, not fragments.
- Cut preamble ("I'll now…", "Let me…", "Great question"), sign-off ("Hope this helps", "Let me know if…"), closing summaries of text I just read, restatements of what I asked.
- Cut praise, apology, self-assessment — "You're right", "Good catch", "I apologize".
- Cut hedges and intensifiers — essentially, basically, actually, quite, very, really, simply, just, certainly, clearly, importantly, it's worth noting, I should mention.
- Cut connectives carrying no contrast — Additionally, Furthermore, Moreover, That said.
- No unsolicited menu of next steps. If I want options, I'll ask.
- No headers, tables, or bold on a short answer. Structure is for things that have structure.
- Uncertainty is one clause, not a paragraph.
- Reporting work: what changed, what broke. Nothing else.

If deleting a word loses no information, it was noise:

> ✗ I've now completed the refactor. I moved the parser into its own module, which should make it easier to maintain going forward. Let me know if you'd like me to also update the tests!
>
> ✓ Parser moved to `parser.rs`. Tests untouched.

# Unity

- Running Unity batchmode against a project whose editor is already open — they collide on the `Library` / `Temp/Unit
yLockfile` and hang or corrupt the project.

## Unity editor / batchmode

- **Editor already running → never batchmode. Drive the live editor via `unity-cli`.**
- **Editor not running → use batchmode.**
- Detect which: process present ⇒ editor is live ⇒ use `unity-cli`, not batchmode.
- Interacting with Editor - batchmode or not - use `/home/midori/_dev/my-claude-workflow/bin/unity` utility.

## Package samples (`Samples~`) — golden-deliverable workflow

`Samples~/` in a package is the golden deliverable shipped to consumers. Unity hides it (no compile, no import) until a consumer imports it, so it is NOT verifiable in place. Never iterate directly in `Samples~/`.

- Working area = the IMPORTED copy under `Assets/Samples/…` — compiled, runnable, editor-verifiable. All iteration happens there.
- Promote to `Samples~/` only after I confirm the imported copy is golden. Promotion is a simple wholesale replace: delete the sample folder in `Samples~/` and copy the imported `Assets/` copy in its place. It's a straight replacement, never a merge — the imported copy is the source of truth, so stale golden-only files are meant to disappear. Don't weigh additive-vs-mirror and don't ask before removing them. That copy-back is the only write to `Samples~/`.
- `Assets/` copy = live working area; `Samples~/` = frozen golden. This is what prevents divergence.

## Commit Messages

- Conventional commit format: `type(scope): description` — single line
- Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`
- **Scope: word characters only** (letters, digits, underscore) — no hyphens
- When changing public library APIs, include `BREAKING CHANGE:` in commit body
- NEVER bump versions — CI handles releases automatically
- Only `feat:`/`fix:` trigger release rebuild

GitLab enforces:
```
^((build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test)(\(\w+\))?(!)?(: (.*\s*)*))|(Merge (.*\s*)*)|(Initial commit$)
```

## Stealth Requirements

No traces of AI involvement:
- NEVER add AI attribution ("Generated with Claude Code", "Co-Authored-By: Claude", etc.)
- NEVER add emojis to commit messages
- NEVER create CLAUDE.md files in subdirectories
- NEVER mention AI assistance in code, docs, or commits

## Ad-hoc instrumentation

Commit every script written to generate, preview, verify, or measure during a task — with the task's artifacts (orchestrations: `docs/orchestrate/<topic>/scratch/`). No in-session ruling on "will the need recur" — that takes cross-session memory no session has; the session's duty ends at committing what actually ran.

Keep/promote/delete is decided at close-out sweep. Promotion criteria: parameterized over the general case; derives its result from the real code (imports the single source of truth — if the script duplicates logic, extract the shared module first); deterministic, headless, cheap to keep. Promoted scripts move to the project's tools with the feature's doc pointing at them; the rest are deleted at the sweep.

## Grep

`grep` is hook-rewritten to ripgrep, which reads the pattern as a regex. A literal `{` is a
repetition quantifier, so a brace in the pattern is a parse error, not a match — Prometheus
samples (`mc_tick{key="tps"}`), JSON, C++ templates, shell `${VAR}`.

**Pass `-F` whenever the pattern contains a brace.** Default to `rg -F` / `grep -F` for literal
text; keep regex mode for patterns that actually need it. Same for the `Grep` tool — no braces in
`pattern` unless the regex means them.

## Paths

- Unreal (reference): `/mnt/archive4/UNREAL/UE_5.8/`
- Personal workflow repo: `/home/midori/_dev/my-claude-workflow` — `~/.claude/{skills,agents}` symlink in; edit canonicals in repo (`install.sh` reinstalls symlinks); launchers in `bin/` on PATH via fish config.
- Research corpus (cross-project, MegaSync, not git-tracked): `/mnt/archive4/PAPERS/Prepared` (extracted `<slug>.md` + `assets/<slug>/` + `index*.md`); raw sources in `/mnt/archive4/PAPERS/`.
- Unity API canon (engine reference: RenderGraph/Jobs/Burst/Entities/authoring): `~/_dev/my-claude-workflow/docs/unity`.

## When Stuck

- Don't silently pivot to "easier" alternatives.
- Explain the blocker, ask for direction, terminate work.

## Before Starting

- Non-trivial task? Propose acceptance criteria, get approval.


@FFF.md

---

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
