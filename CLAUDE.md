# Global Configuration

## Writing register — docs / READMEs / write-ups (binding)

Rules inferred from a repeated correction cycle on the advscan README. The
calibration target is the *prepared notes* register of a confident
slide-talk speaker (Bauer 2019 RDR2 PPTX notes are a good exemplar):
complete sentences that state the structural fact, not telegraphic
fragments and not runtime narration.

1. **Observation form, in sentences.** State what the thing IS, not what it DOES at runtime. "Only `intrinsic` is stored; `effective` is computed at read time" is observation in sentence form. "Persisted: intrinsic. Derived on read: effective. Bust scope: …" is an obnoxious telegram that substitutes punctuation for grammar. Phenomenology ("Evaluate writes intrinsic; on change it busts the cache") is the other failure mode — frames the system as an actor performing actions when the goal is to describe its shape. Both fail; the middle path is structural-fact sentences with real verbs.
2. **Don't nominalize verbs to dodge phenomenology.** Reaching for "the bust covers the artifact's own key" instead of "an intrinsic change invalidates the artifact's own cache entry" produces opaque jargon. The fix for runtime narration is the sentence *frame* (subject = the fact, not the worker), not stripping verbs.
3. **One canonical home per load-bearing fact.** If "intrinsic is stored, effective is computed" appears in Schema, evaluate, AND Rationale, the doc is repeating itself. Put each fact once in its most-natural section; downstream sections reference rather than restate. Same rule for technique names (XFetch, Vattani citation, sha512 verification) — introduce once with the citation, then refer.
4. **No hard wrap in markdown sources.** Each paragraph is one source line; the renderer wraps. Hard-wrapping at ~80 cols was 1990s ergonomics, costs an edit per sentence, and serves no purpose for markdown viewed in a browser/IDE preview.
5. **Preserve list structure when the content is a list.** A four-option shape-space comparison is four bullets, not four paragraphs. A three-category test layout is bullets, not three prose blocks. Don't melt enumerable structure into prose to look more conversational.
6. **Each displayed equation in its own `$$ ... $$` block.** Don't chain multiple unrelated equations with `\qquad` into one display line. If three formulas (`inherited`, `effective`, `score`) are conceptually distinct, give them three blocks.
7. **Drop ceremony, not content.** `\prod_{i=1}^{n}` carries information (index, range); collapsing to `\prod_i` loses it. `(x_1, \ldots, x_n)` carries arity; shrinking to `(\bar x)` loses it. Concision means dropping words/symbols that add nothing, not dropping load-bearing notation to look terser.

## Paths
- Unreal voxel plugin (reference): `/mnt/archive4/UNREAL/UE_5.7/Engine/Plugins/VoxelPlugin`
- Personal workflow repo: `/home/midori/_dev/my-claude-workflow` — `~/.claude/{skills,agents}` symlink in; edit canonicals in repo (`install.sh` reinstalls symlinks); launchers in `bin/` on PATH via fish config.
- Research corpus (cross-project, MegaSync, not git-tracked): `/mnt/archive4/PAPERS/Prepared` (extracted `<slug>.md` + `assets/<slug>/` + `index*.md`); raw sources in `/mnt/archive4/PAPERS/`.

## Work ethic
After a significant task, submit and end the session — don't accept further requests.

## Delegation & document-writing
- If a doc needs writing (exploration / analysis / findings / design), dispatch a sub-agent that does the analysis AND writes the doc itself. Never have the orchestrator absorb agent return text and re-write it — content then passes through context twice.
- Orchestrator reads only short status confirmations ("done — wrote `<path>`, N items"), never doc content via return text.
- Never put "if write fails, return content verbatim" escape hatches in briefs — that creates the anti-pattern. If a write fails, re-dispatch.
- Systemic write failures = missing `Write`/`Edit` allow rule in `.claude/settings.local.json` — fix the rule, don't absorb the work.
- Referencing session images in handoffs/delegate context: include session ID, or omit images. Bare "Image 10"/"10.png" is unreachable to the receiving agent.
- No speculative delegation: handoffs / delegate briefs / dispatched prompts state symptom + factual change list only — never pre-loaded hypotheses or ranked guesses; the receiver observes first (bisect, frame capture, runtime state diff) and forms hypotheses from the delta.
- Handoffs are continuation-links — one-line task statement + minimal context not obvious to a reader who understands the task + optional verbatim user citations. **NEVER prescribe deliverable shape, NEVER prescribe investigation shape, NEVER pose hypotheses or ranked guesses.** File at absolute path `/tmp/<topic>-handoff.md`; in chat output the kickoff line verbatim as `[/delegate]|[execute] /absolute/path/to/handoff.md [/worktree worktree-path]` for copy-paste. Canonical methodology: `/handoff` skill.

## Orchestrate docs — journals, not canon (binding)

`docs/orchestrate/<topic>/` is one orchestration session's **working memory** — written by sub-agents who read code at that point in time. It is NOT canonical source of truth — it is a story of what those agents thought, prone to hallucinations.

Source-of-truth hierarchy whenever an agent (orchestrator, architect, impl, diagnostic, reviewer) needs to ground a claim:
1. **The code itself** — `file:line` at current HEAD. Source of truth for what is implemented.
2. **Research papers** (in `/mnt/archive4/PAPERS/`, etc.) — source of truth for how it's supposed to be implemented.
3. **The current orchestration's own `docs/orchestrate/<this-topic>/`** — working memory for the current task; load-bearing for inter-agent context within that session.
4. **Other orchestrations' `docs/orchestrate/<other-topic>/`** — historical journals. Story-of-what-agents-thought, not story-of-what-was-true. Treat with scrutiny.

Binding:
- `/delegate` orchestrations do NOT cross-reference between sessions by default. The orchestrator does not list other sessions' docs in required reading; agent briefs do not cite other sessions' docs as canon.
- Only exception: the user explicitly names another orchestration session as relevant. Even then, the brief frames the reference as "what an agent thought in the past — verify every load-bearing claim against the code (`file:line`) or a research paper before acting on it." Do NOT inherit conclusions as canon; treat claims as hypotheses to test against current code.
- **Do not amend another orchestration's docs from inside the current orchestration.** Cross-orchestration mutation produces "original sin" cascades — agent N's hallucination becomes canon for sessions N+1, N+2, N+3, none of whose agents push back. If a fact discovered in the current orchestration would help future sessions, write it in the CURRENT orchestration's docs and surface it for explicit user decision about whether to propagate.

## Git
- NEVER amend unless explicitly asked.
- "commit" = commit EVERYTHING in `git status` (staged + unstaged + untracked), single commit.
- Never run `git push` — cc-filter blocks it. Only user pushes.
- Full branch diff is the PR — never disclaim changes as "from a previous commit/session".
- NEVER `git checkout` files to revert — they aren't committed. Use selective Edit from diffs.

## Verification
- Compilation proves nothing — always run end-to-end.
- ALWAYS investigate test failures — no "pre-existing failures" excuse.
- Begin work by running the relevant test suite; follow project test discipline.

## Worktrees
- Branch from local `main` (not HEAD, not `origin/main`).
- Inside `.claude/worktrees/`: absolute paths for ALL operations.

## Persistence — skills and git-tracked docs, NEVER machine-local memory (binding)

The machine-local memory system is **banned.** `~/.claude/projects/.../memory/`, `MEMORY.md`, and the Write-to-memory tool all live under `~/.claude` on ONE machine, sit in no git repo, and are keyed to that box's absolute project path. **New machine = lost methodology** — the exact failure mode that makes them worthless. Never persist methodology, gotchas, corrections, or preferences there; if the harness offers to write a memory, decline and use one of the homes below instead.

If a fact is worth keeping, it goes somewhere `git clone` carries it:
- **Skill / agent methodology** (binding patterns for how work is done) → the canonical skill at `~/_dev/my-claude-workflow/skills/<name>/SKILL.md` or agent at `agents/<name>.md` (GitHub-synced, portable to every machine), or a project-local skill under `<project>/.claude/skills/` (travels with the project repo).
- **Project facts / gotchas** (a tooling flag, a build trap, a project-specific constraint) → the project's git-tracked `CLAUDE.md` or a doc it references.
- **A truly global rule or preference** → this global config — which must itself live in `~/_dev/my-claude-workflow` and be symlinked into `~/.claude` by `install.sh`, or it has the very same machine-local problem as memory.
- **Handoff** (mid-task pivot, in-progress state) → handoff file. Read once next session.

Order: skill / agent > project doc or `CLAUDE.md` > handoff > nothing. There is no memory tier — reaching for memory is choosing the one location that does not survive a machine switch.

## Code criticism — smell-driven escape (binding)
- If you read obviously rotten code (conflated concerns, IoC violations, accidentally-global state, dual addressing schemes for one buffer, dead memory, one-shot offline mechanism shoehorned into streaming, abstractions fighting the standard pipeline), stop and call it: "this is rotten; iterating inside won't work; right move is refactor toward [missing pattern]." Foundation rot beats wasting dispatches on top of it. Every agent (orchestrator, architect, impl, diagnostic, reviewer) is equally empowered — equal footing, all Opus.
- Every deliverable doc includes a `## Side notes / observations / complaints` section: anything outside the brief the orchestrator should know — suspicious code, over-constrained briefs, missing tools, even subjective reactions.
- Reviewer dispatches are NOT default. Conformance = probe-gate (tests + e2e + user visual). Code quality = `/refactor` sessions. Only invoke a reviewer for explicit reason (hard-to-revert, user requested, critical boundary).

## Negative space (binding)

From Fabian Giesen, ["Negative space in programming"](https://fgiesen.wordpress.com/2015/01/16/negative-space-in-programming/) (full text: `/mnt/archive4/PAPERS/Articles/negative-space-in-programming.md`). A program's shape comes from what is left out, not what is put in — the rejected alternatives, the omitted features, the dependencies not taken, the errors made impossible by design. These three points are working guidance, not just an aesthetic.

1. **Quality is doing almost nothing else.** An elegant solution is not one that satisfies a feature checklist; it is one that solves the actual problem concisely and does almost nothing besides. Picking the right problem to solve is the hard part and is more art than science — prefer the smallest design that solves the real problem over the one that ticks the most boxes. When "just quickly add that one feature" turns into the straw that breaks the camel's back, reverting is usually the right move.
2. **Document what does not work, not only what does.** When an approach fails, write down what was tried and why it didn't — a few sentences, in a code comment if the failure is local to a design choice, in docs/wiki/handoff if it stems from architecture. What works is usually well-known; what doesn't is the brick wall no one sees until they hit it. Knowing the negative space is at least as load-bearing as knowing the positive. (This is the same instinct as the `## Side notes / observations / complaints` section above and the "no speculative delegation — observe first" rule.)
3. **A rewrite is about unspoken assumptions, not line counts.** Replacing a piece of code is never "delete X lines, write Y lines," and rarely even "re-implement the same idea better." The biggest problem is the implicit contract surrounding it: the API calls it deliberately avoids, the unspecified behaviour and side-effects other code relies on, the problems it never has to handle because they were designed out. Map that negative space before rewriting, or the replacement reintroduces every avoided problem.

When reading code, figuring out what a program *doesn't* do (and why) is as instructive as what it does.

Four further points extend this framing to the brief, the measurement, the verification, and the postmortem:

@negative-space-expanded.md

@RTK.md
@FFF.md
@HARNESS.md
