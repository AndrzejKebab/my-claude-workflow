# E2e gate authoring discipline (binding)

Sidecar to `SKILL.md` — read this when an orchestration's scope includes adding or modifying an e2e gate that captures a **user-visible artefact** (a visual glitch, a runtime behaviour, anything whose ground-truth is "what the user sees"). The gate is NOT considered analytically valid until the user has visually confirmed that its captures show the artefact. A passing/failing variance ratio + a numerical threshold are **not sufficient** — they only prove the metric responds to the captured pixels, not that the captured pixels are the artefact.

This rule exists because the dominant failure mode of this orchestration mode is: an agent builds an e2e gate that compiles and passes a pre-fix/post-fix smell test, but the captured framebuffers are smeary, mis-timed, off-camera, or otherwise not actually showing the symptom the user described. The fix lands, the gate is green, and the artefact is still there because the gate was measuring something else.

## How this changes the dispatch shape

E2e gate authoring is split into a **separate phase** from the fix-implementation phase. The two are NEVER bundled into a single dispatch — not "two stages of a consolidated dispatch", not "two steps of one impl agent's brief". **Separate dispatches with a hard user-verification gate between them.**

1. **Gate-authoring phase.** Dispatch an implementer to:
   - Add the e2e gate (binary entry, capture system, mode flag, driver wiring).
   - **Mandatory: capture screenshots.** One per captured frame — not just a summary frame. Save them to a predictable absolute path the user can browse, e.g. `target/e2e-screenshots/<gate-name>-frame-<N>.png`. Every new visual-capturing gate MUST land with on-disk screenshots; a gate that only emits a numerical metric is not finishable.
   - Run the gate ONCE on the **current** (pre-fix) worktree.
   - Report: path to each captured frame, the pre-fix metric value(s).
   - Do **NOT** apply any fix yet. Do **NOT** calibrate the threshold yet. Do **NOT** propose post-fix expectations yet.

2. **Visual verification hard gate (user-facing, mandatory).** Present the captured screenshots to the user as absolute paths in chat — one line per frame, so they can open each frame and judge. Ask explicitly: *"Do these captures show the artefact you described? Is the timing right (capturing the shift frame, not a frame before/after)? Is the camera path right? Are the captures sharp, not smeary?"*
   - **If the user says "yes, the captures clearly show the artefact"** → proceed to step 3.
   - **If the user says "no" / "kind of" / "the timing is off" / "this isn't what I see" / "they're smeary"** → **redirect**. Dispatch a fix to the gate's capture mechanism (camera path, capture trigger, frame indexing, screenshot timing, exposure, scene state). Do NOT proceed to the fix until the captures are clean. **Re-loop the user verification after each capture-mechanism fix.** A smeary, wrong-timing, or wrong-content capture is a *broken gate*, not a finishable one — perfecting it before moving on is the entire point of this phase.

3. **Threshold calibration phase.** Only after the captures are user-confirmed: dispatch the metric + threshold authoring. The threshold is calibrated against the user-confirmed-artefact pre-fix run.

4. **Fix-implementation phase.** Now (and only now) dispatch the actual fix. Re-run the gate post-fix; the gate must PASS. Optionally re-present the post-fix screenshots to the user for a second visual confirmation — recommended for symptoms where the post-fix expectation isn't a sharp binary (e.g. "this should be eliminated" vs "this should be reduced").

## Why this is mandatory, not optional

If the captures are smeary or mis-timed, no threshold calibration can save the gate. A 1.40× ratio reduction between "wrong frames pre-fix" and "wrong frames post-fix" tells you the fix changed something — but says nothing about whether it changed the thing you cared about. The visual verification gate is what bounds the gate to the user-reported artefact rather than a coincidentally-correlated GPU signal.

The shape that fails: bundling gate-authoring + threshold-calibration + fix-implementation into one dispatch, then declaring victory because pre-fix FAILED and post-fix PASSED. The threshold calibration *can* still be tuned to make almost any pair of captures produce a FAIL→PASS transition — that doesn't make the gate analytically valid.

The shape that succeeds: split the dispatches, hand the screenshots to the user before the metric is even calibrated, and accept that gate-authoring may need its own redirect loop before the fix can land.

## When this rule does NOT apply

- Pure logic / unit tests with no visual component — Rust unit tests, property tests, parser tests, etc.
- Existing gates being re-run as part of verification — only NEW or MODIFIED visual-capturing gates trigger the visual-verification dispatch shape.
- Gates whose ground-truth is byte-exact equality against a fixed reference (e.g. oracle tests where the reference framebuffer is itself the spec). The reference image IS the verification surface.

The rule applies whenever the e2e gate's job is to capture a user-described visual symptom and reduce it to a metric — that's where the smear/timing failure mode lives.

## E2e-specific anti-patterns

- **Bundling e2e-gate authoring with fix implementation in one dispatch.** Defeats the visual verification step. Gate captures are validated only by the variance ratio, not by the user's eye. If the captures are smeary, the fix gets credited (or blamed) for moving a metric on the wrong frames.
- **Validating a gate by pre-fix FAIL / post-fix PASS alone.** That ratio proves the metric moved; it does NOT prove the metric moved because of the artefact. Visual confirmation of the captured frames is mandatory. The threshold can be calibrated to make almost any pair of pre/post captures produce the FAIL→PASS transition — the load-bearing question is "are these captures actually the artefact?", and only the user can answer that.
- **Treating "the gate compiled and the variance ratio looks reasonable" as completion.** It is not completion. Completion is "the user has looked at the captured screenshots and confirmed they show the artefact, AND the metric responds to that artefact correctly."
