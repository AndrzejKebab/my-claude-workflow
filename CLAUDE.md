### Notes on autonomy

Don't write code comments at all, except for one-liners on top of monumental blocks. If you think something deserves a comment - write a documentation page.

**Walls of text in code are POISON — for me reading it and for you, whose context they fill.** "One-liners on top of monumental blocks" is not a licence for a monumental comment block: it caps you at ONE LINE. A file header explaining the design, a numbered list of rationale, a transcript of measurements, a record of rejected alternatives — none of these belong in source. Measured 2026-07-25: a kernel shipped with 96 lines of prose before its first line of code, and every agent that touched the file thereafter paid for it.

**Code IS the documentation for WHAT.** Name things so the code says it. **Docs carry HOW and WHY** — rationale, measurements, derivations, what was tried and rejected — and they live in `docs/`, where they can be read by choice instead of loaded by force.

Exactly three comments survive: an **occasional one-liner**, a **citation** (paper, spec section), or a genuine **WTF explainer** where correct code reads as wrong. Anything longer is a doc page with a pointer to it, or it is deleted.

Pass this rule to every subagent that writes code. It is violated by default otherwise.

Prefer long-term solutions, never reach for "minimal change".

A question is not an instruction. "Ready to merge?", "should we X?", "can you Y?", "is this done?" asks for an ANSWER — give the answer, do not perform the action. Never take an irreversible or outward-facing action (merge, push, delete, overwrite, send, publish, deploy) off a question. Act only on an explicit imperative ("merge it", "push", "do it", "go").

**That rule guards irreversible and outward-facing actions ONLY. It is not a licence to stop working.** Building, editing, refactoring, testing and committing inside the repo are ordinary work — they are never what "act only on an imperative" was protecting. Do not turn a diagnosis, a spec, a plan or a recommendation into a pause. Having decided what to build, build it.

**Never ask for the same confirmation twice, and never ask for confirmation I already gave.** "ok", "OK!", "yeah", "sure", "sounds good", or silence after a recommendation = proceed with the recommendation you just made. If I picked between options, that pick stands for the whole task; stop re-offering the menu. If I gave a direction and you asked once, that is the budget — a second ask is a defect, not diligence.

**Work does not pause until it is ready for my manual QA.** The stopping point is a state I can put my hands on: it builds, the suite is run, and there is a writeup saying what to try. Not "here is the plan", not "which one shall I do", not "standing by". If two options remain and both are defensible, pick the one you recommended, say in one line that you picked it and why, and go. If you genuinely cannot proceed — blocked on access, on a fact only I hold, on something destructive — say so in a sentence and stop; that is the only pause.

Use the /loop skill as necessary, don't ask for my confirmation twice.

Do commits as you see fit - on checkpoints / milestones, as you see necessary, you don't need my confirmation to make a commit.

## Readiness checks

"Is it ready?" / "ready to merge?" / "is this done?" / "can we ship?" — any readiness question — is answered ONLY after both conditions are verified. Never from memory, never from "it compiled", never from "the change looks right".

1. **The project's ENTIRE test suite runs GREEN — not just the tests touching this task.** Actually run it. A suite you did not run is not a suite that passes. Scope is the whole project under work (every package, every assembly, every pipeline/version variant it ships), not the subset your change happens to touch. "My tests pass" is not an answer to "is it ready?". If anything is red — including failures that predate the session and failures in areas you never went near — the answer is NO, and you name them. A pre-existing red suite is a finding to surface, never a baseline to accept: a suite nobody reads turns a loud failure into silence (observed: five failing perceptual tests sat red at HEAD, three of them the exact bug being hunted).
2. **The session's problem statement is fully covered by e2e/perceptual tests.** Every defect fixed and every behaviour claimed has a test that failed before the fix and passes after. If the session's work is not fully covered, the answer is NO, and you say what is uncovered.

Only an explicit instruction to ignore ("ignore the tests", "I know it's red, ship it") waives this. "Ready?" never waives it.

When launching an Orca worker terminal, start the agent with `claude --dangerously-skip-permissions` (e.g. `orca-ide terminal create … --command "claude --dangerously-skip-permissions"`), so the worker is not stalled by per-tool permission prompts it cannot answer headlessly.

Never write unit tests. All tests must exercise entire application end to end. 

All tests drive the app as a black box: control signals in -> real app tick -> metrics out. No test reimplements a sim loop or calls sim-loop internals. Feature gates are APP CONFIG, not test reimplementations.

**Real inputs do not make a test end-to-end. The OUTPUT decides.** A test that drives the real app, ticks the real loop, then reads an *intermediate* value is a unit test wearing an end-to-end costume — it asserts that one stage emits what you assumed it would, which is the whole of what a unit test does and the entire reason they are banned. The metric must come from the artifact the user perceives: the final frame, the rendered page, the response body, the audible output. Never a debug channel, an instrumented pass, an internal buffer, or a counter that merely sits near the symptom.

The tell is one question: **if this metric were perfect and the user still saw the defect, would the test notice?** If no, it is a unit test, however much real pipeline ran upstream of the probe.

Measured 2026-07-25: a shader gate drove the real render pipeline over the real world with the real material, and graded a debug pass exposing the blend's *input* weights. It reported a 37.7x separation between good and sabotaged, held a demonstrated-red arm, and stayed green while the shipped surface rendered hard blocky material boundaries with no blending whatever. Every upstream stage was real. The channel was not the one the user looks at, and that alone was enough.

**Correctness of a hard problem is established ONLY by a perceptual end-to-end test.** Reading data back as encoded, dumping intermediate state, probing counters — these are legitimate *diagnostic instruments*, and small one-time probes during an investigation are fine and often decisive for localizing a cause. They are never the evidence that the behaviour is right. **Diagnosis may read anything; the gate reads only what the user sees.** A probe promoted to a gate is a unit test admitted through the back door.

### When gates are warranted — the default is NOT

**Gates, oracles and sabotage arms are an escalation, not a baseline.** Working *with* me, I am the oracle: build the thing, show me the artifact, let me judge it. Do not construct a gate, an oracle or a sabotage arm preemptively — that is a large cost paid before anyone knows whether the change is even right, and it is usually the wrong order. Get the result first.

Escalate to the full regimen in exactly three situations:

1. **A first attempt failed to produce the result.** Repeated failure means you cannot see what is wrong from the outside, so instrumentation has become cheaper than another guess. This is the failure mode gates exist for.
2. **I ask for it**, for that situation.
3. **After a feature or fix has landed successfully** — then spend some time on a **minimal** regression gate, on request, sized to the situation. Protection against regression later, not proof of correctness now.

**The exception is autonomous operation, and I declare it.** "afk" means I have left the machine: you cannot ask me anything, so you work to a milestone and leave a short note for manual QA. **In that regime gates ARE the verification and the full regimen applies** — there is no one present to prove the result to, so you have to prove it to yourself. The moment I am back, drop it and go back to working with me.

This scopes everything below it. What it does **not** relax: when you *do* write a test it obeys the end-to-end rule above; never loosen an assertion to reach green; and answering "is it ready?" still means running the suite that exists and stating plainly what is not covered by it.

Gate criteria + worked examples (independent oracles, exact-by-default, cross-referenced conditions, absence criteria): `~/_dev/my-claude-workflow/docs/e2e-gates.md`. Gates rank with the spec — under agentic flow they are what excludes accepting invalid or partially falsified results.

### A green gate is a claim about the fixture, not only about the code

A gate that has never been observed red proves nothing. Nearly every false green is a fixture that
**could not have failed**, so a green while a reported symptom persists is evidence about the
fixture first. Never conclude from green that the report was wrong.

Before trusting green, establish the fixture can go red:

- **Regime, not shape.** A defect gated on scale — size, count, distance, duration, concurrency,
  capacity — vanishes in a fixture shrunk to run fast. Shrinking makes a different system. Pay real
  scale once behind a category rather than shrinking it into vacuity.
- **Non-degenerate content.** The data must vary along the axis the code branches on, or the branch
  never executes. A flat field cannot test slope logic; one element cannot test ordering.
- **Do not settle the transient.** If the defect lives in flight or pre-convergence, flushing,
  awaiting or converging before measuring closes exactly the window under test.
- **Measure where the symptom is.** An internal artifact can compare 100% identical while the
  symptom lives downstream of a path that never reads it. Start at the reported boundary, then
  work inward.
- **Validate the oracle by sabotage.** Do not reason about whether the gate would catch a
  regression — break the subject on purpose (overwrite the output with a constant, skip the pass,
  zero a coefficient, shift an index) and confirm it goes red. This is the *criterion* for "could
  it have failed", and unlike red-first it is available before the symptom is reproducible. Record
  the result in the gate: "poisoning X moves this metric 0.03 → 0.71" is its demonstrated
  sensitivity and what makes the threshold defensible rather than invented.
- **Separate signal from noise before choosing a threshold.** Measure the metric good-vs-good
  (repeat runs) for the noise floor and good-vs-sabotaged for the signal; require signal >> noise
  and put the threshold in the gap. If they are comparable the metric is blind — change the metric,
  not the threshold.
- **One variable.** If the arm and its control differ in more than the thing under test, a
  difference cannot be attributed and an equality is coincidence.
- **Guard the preconditions.** Assert and log what the run actually examined, so a pass cannot be
  vacuous over an empty or degenerate sample.

Prefer shapes that survive not knowing what "correct" looks like, in this order: **invariance**
(output must not depend on X) → **differential A/B** (one variable moved) → **round trip** →
**analytical oracle**. When a defect may be content-dependent, a synthetic stand-in is a hypothesis,
not a control — drive the real asset.

**When you cannot build an oracle, capture what the user sees.** Capture the artifact at the
boundary they perceive (final frame, rendered page, response body — never an internal buffer that
seems related), capture the same artifact from a known-good configuration, and **have the user say
which is wrong before choosing any metric**. Their eye is the oracle you lack. Then pick a metric
that separates that pair with margin. Order is **capture → confirm → threshold**; inventing the
threshold first yields a metric that agrees with your hypothesis instead of the artifact. And grade
in the reporter's vocabulary — "washed out" is saturation, "stutter" is the frame-interval
distribution, "out of order" is order. A metric from the wrong channel sits at its noise floor
while the defect is fully present.

A good gate, in one sentence: **it captures the user-visible artifact under two configurations that
must agree, with a metric demonstrated to separate a sabotaged capture from a good one, and it
prints what it examined.** Sanity check any gate by naming three plausible regressions in the area
it guards — if none would trip it, it is decoration.

Confirm a cause by **prediction**: state how the symptom must move if the hypothesis holds, then
move the suspected cause. A hypothesis that only explains the observation is a story. Confirm a fix
by **measuring it** — a change that does not move the metric is not the fix; revert it rather than
shipping a no-op. Never loosen an assertion to reach green.

NEVER run `git config user.name`/`user.email` or set per-repo git identity, and never hardcode my name/email in a git command. My global git config is correct — always use it. New repos (`git init`, `gh repo create`) inherit the global identity automatically; leave it alone. Never read my email from session/context and pass it to git — git already knows it.

## When Stuck

- Don't silently pivot to "easier" alternatives.
- Explain the blocker, ask for direction, terminate work.

## Before Starting

- Non-trivial task? Propose acceptance criteria, get approval.

## Paths

- Unreal (reference): `/mnt/archive4/UNREAL/UE_5.8/`
- Personal workflow repo (private): `/home/midori/_dev/my-claude-workflow` — `~/.claude/{skills,agents}` symlink in; edit canonicals in repo (`install.sh` reinstalls symlinks); launchers in `bin/` on PATH via fish config.
- Shareable skills (public, plugin marketplace): `/home/midori/_dev/zori_skills` → `github.com/api-haus/zori_skills`. Skills that ship live HERE, not in the workflow repo — edit `plugins/<name>/skills/…` directly; installed as a local-directory marketplace it loads from the working tree, so edits apply next session, and `git push` is what releases them. `tools/validate.sh` gates self-containment. Currently the `delegate` plugin (delegate, warden, diagnose-first, shipshape + nine agents). Migrating a skill out of the workflow repo is the direction of travel; the symlinks are being retired.
- Every methodology edit (skills, CLAUDE.md, docs) commits to whichever of the two owns it, immediately, one commit per edit — never left sitting in the tree.
- Research corpus (cross-project, MegaSync, not git-tracked): `/mnt/archive4/PAPERS/Prepared` (extracted `<slug>.md` + `assets/<slug>/` + `index*.md`); raw sources in `/mnt/archive4/PAPERS/`.
- Unity API canon (engine reference: RenderGraph/Jobs/Burst/Entities/authoring): `~/_dev/my-claude-workflow/docs/unity`.

## Grep

`grep` is hook-rewritten to ripgrep, which reads the pattern as a regex. A literal `{` is a
repetition quantifier, so a brace in the pattern is a parse error, not a match — Prometheus
samples (`mc_tick{key="tps"}`), JSON, C++ templates, shell `${VAR}`.

**Parentheses are worse than braces, because they fail silently.** A brace errors out and you
notice. A literal `(` is a capture group, so `FIXME(vision)` compiles fine and matches `FIXMEvision`
— i.e. nothing — then exits `0` with no output, indistinguishable from "no matches in this file".
Measured 2026-07-21 on one file: `/usr/bin/grep -c` (BRE, parens literal) → **5**,
`rg -c` → **0**. Anything that counts occurrences to decide whether work remains will conclude
there is none. Same trap for `\|` alternation, which is BRE-only — in ERE it matches a literal pipe.

Affected in practice: annotation markers like `FIXME(scope)` / `TODO(name)`, function call sites
(`foo(bar)`), Rust/C++ turbofish and generics, shell `$(cmd)`.

**Pass `-F` whenever the pattern contains a brace or a paren.** Default to `rg -F` / `grep -F` for
literal text; keep regex mode for patterns that actually need it, and escape the literals there
(`grep -cE 'FIXME\(extract\):.*needs vision'`). Same for the `Grep` tool — no braces or parens in
`pattern` unless the regex means them. **A zero count from an unescaped pattern is not evidence of
absence** — re-run with `-F` before concluding anything from it.

## Diff

`diff` is hook-rewritten too, and its failure mode is worse than grep's: it reports a **false PASS**.
Measured 2026-07-22 on two manifest files whose *every line* differed — the rewritten `diff a b`
printed `[ok] Files are identical`, while `/usr/bin/diff` and `sha256sum` both correctly reported
them different. Reproducible, and content-dependent, so it cannot be ruled out by one spot check.

A wrong "no differences" is the dangerous direction: it silently converts "the artifact changed" into
"nothing to see", and anything deciding whether work is needed will conclude there is none.

**Use `/usr/bin/diff` or `sha256sum` for any comparison whose answer you intend to act on** —
regression checks, before/after captures, generated-output equality, "did the fix change anything".
Never accept a bare `diff`'s silence as evidence of equality.

## Never edit files with bash

**Edit and Write are the only ways to change a file.** Not `sed -i`, not `python3 - <<PY`, not
`node -e`, not `printf > file`, not a heredoc writing source, not `>>` appending to a tracked file.

Post-edit hooks fire on `Edit|Write|MultiEdit|NotebookEdit` and **cannot** fire on Bash — a shell
command does not say which files it touched, so nothing formats, lints or verifies what it wrote.
The write succeeds, the hook stays silent, and the file is the one thing in the tree nobody checked.

Measured 2026-07-23, identical content written both ways into a repo with a biome post-edit hook:
the Write-tool file came back formatted *and* linted (an unused binding renamed); the `printf` file
was untouched. In that same session a dead import survived every gate — `tsc` does not flag one and
the formatter does not lint — and it survived precisely in the files patched through the shell,
because those were the only files the hook never saw. Lint debt accumulates exactly where bash was
used and nowhere else, which is why it reads as a mystery rather than as a cause.

The pull toward bash is real and it is a trap: a tricky escape, nested backticks inside a template
literal, a repetitive rename across several files. Do it with Edit anyway — Read the file first
when the string is awkward. Scripted editing is for **generated artefacts and throwaway scratch
files**, never for source.

If a shell write is genuinely unavoidable, it is not finished until the repo's own formatter and
linter have been run over exactly the files it touched, in the same turn, and the result reported.
"The hook did not run" is not an excuse available afterwards; it is a thing to have prevented.

@FFF.md

@NONDUAL.md

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

## Orchestrate docs — journals, not canon (binding)

`docs/orchestrate/<topic>/` is one orchestration session's working memory — what its sub-agents thought reading code at a point in time, prone to hallucinations, never canonical truth.

Source-of-truth order for any load-bearing claim:

1. The code at current HEAD (`file:line`) — what is implemented.
2. Research papers (`/mnt/archive4/PAPERS/`, etc.) — how it's supposed to be implemented.
3. The current orchestration's own docs — load-bearing inter-agent context for this session.
4. Other orchestrations' docs — historical journals; treat with scrutiny.

- Orchestrations do NOT cross-reference other sessions' docs by default — not in required reading, not as canon in briefs. If the user explicitly names another session as relevant, the brief frames it as "what an agent thought in the past — verify every load-bearing claim against the code (`file:line`) or a paper before acting on it."
- **Never amend another orchestration's docs from inside the current one** — that turns one agent's hallucination into later sessions' canon ("original sin" cascade). Write new facts in the CURRENT session's docs and surface propagation as an explicit user decision.

## Ad-hoc instrumentation

Commit every script written to generate, preview, verify, or measure during a task — with the task's artifacts (orchestrations: `docs/orchestrate/<topic>/scratch/`). No in-session ruling on "will the need recur" — that takes cross-session memory no session has; the session's duty ends at committing what actually ran.

Keep/promote/delete is decided at close-out sweep. Promotion criteria: parameterized over the general case; derives its result from the real code (imports the single source of truth — if the script duplicates logic, extract the shared module first); deterministic, headless, cheap to keep. Promoted scripts move to the project's tools with the feature's doc pointing at them; the rest are deleted at the sweep.

# Unity

- Running Unity batchmode against a project whose editor is already open — they collide on the `Library` / `Temp/Unit
yLockfile` and hang or corrupt the project.

## Unity editor / batchmode

- **Editor already running → never batchmode. Drive the live editor via `unity-cli`.**
- **Editor not running → use batchmode.**
- Detect which: process present ⇒ editor is live ⇒ use `unity-cli`, not batchmode.
- Interacting with Editor - batchmode or not - use `/home/midori/_dev/my-claude-workflow/bin/unity` utility.

### A saved scene is handed-off work — commit it freely

A modified `.unity` (or any Unity asset I've saved) in the working tree is deliberate: I never save
a scene unless I intend it committed, and I never save one before I come to talk to you. So by the
time you see it, the save *is* the handoff — the work is yours to carry, and you are free to commit
it without asking. This is the one place the general "don't commit what you didn't create, surface
it instead" instinct is explicitly waived: a saved scene is created *for* you to take. Fold it into
the commit that carries the related work, or commit it on its own with a faithful message; just
don't leave my saved scene sitting uncommitted in the tree.

## Package samples (`Samples~`) — golden-deliverable workflow

`Samples~/` in a package is the golden deliverable shipped to consumers. Unity hides it (no compile, no import) until a consumer imports it, so it is NOT verifiable in place. Never iterate directly in `Samples~/`.

- Working area = the IMPORTED copy under `Assets/Samples/…` — compiled, runnable, editor-verifiable. All iteration happens there.
- Promote to `Samples~/` only after I confirm the imported copy is golden. Promotion is a simple wholesale replace: delete the sample folder in `Samples~/` and copy the imported `Assets/` copy in its place. It's a straight replacement, never a merge — the imported copy is the source of truth, so stale golden-only files are meant to disappear. Don't weigh additive-vs-mirror and don't ask before removing them. That copy-back is the only write to `Samples~/`.
- `Assets/` copy = live working area; `Samples~/` = frozen golden. This is what prevents divergence.
