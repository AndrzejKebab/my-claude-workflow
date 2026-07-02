Don't write code comments at all. If you think something deserves a comment - write a documentation page.

Prefer long-term solutions, never reach for "minimal change".

A question is not an instruction. "Ready to merge?", "should we X?", "can you Y?", "is this done?" asks for an ANSWER — give the answer, do not perform the action. Never take an irreversible or outward-facing action (merge, push, delete, overwrite, send, publish, deploy) off a question. Act only on an explicit imperative ("merge it", "push", "do it", "go").

When launching an Orca worker terminal, start the agent with `claude --dangerously-skip-permissions` (e.g. `orca-ide terminal create … --command "claude --dangerously-skip-permissions"`), so the worker is not stalled by per-tool permission prompts it cannot answer headlessly.

Never write unit tests. All tests must exercise entire application end to end. 

All tests drive the app as a black box: control signals in -> real app tick -> metrics out. No test reimplements a sim loop or calls sim-loop internals. Feature gates are APP CONFIG, not test reimplementations.

Absolutely avoid ceremonious writing - when talking to me, writing commit messages, documentation pages. Prefer a few descriptive words over a ceremonious overly verbose mess. If you think you wrote a short message, this means its about 5 times as verbose as it needs to be already.

Stop turning everything into a symphony. This is about process, not solution scope — the solution stays long-term and thorough (above); what gets cut is the ceremony around executing it. Don't pile on pre-audits, read-backs, forensics, verification passes, or multi-step orchestration the task didn't call for. A one-line commit is `-m "..."` and nothing else. Blocked command → simplify and move on, never reformat the same command 3+ times.

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
