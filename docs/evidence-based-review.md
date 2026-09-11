# Evidence-based review

A review must test the behavior against an independent source of truth. Checking that code agrees with comments, plans, or reports written alongside that code only proves internal consistency; the same omission can exist in all of them.

## Start from the observable outcome

State the consequence that matters to the user before reading the implementation. Trace from input to that outcome across the real execution path. For a game, this may be the rendered frame, saved world state, player-visible interaction, frame time, or memory behavior—not merely an intermediate buffer or counter.

Use specifications, behavior on the base branch, authoritative engine documentation, or an acceptance criterion agreed before implementation as the oracle. Treat branch-local plans and summaries as claims to verify, not evidence.

## Search for omissions systematically

Fluent line-by-line review is weak at finding cases nobody considered. Enumerate the relevant state space when behavior depends on states, variants, platforms, or pipeline stages.

For each state, identify:

- who creates or writes it;
- who reads or advances it;
- its terminal behavior;
- the test or observation that covers it.

In Unity work, apply the same method to system groups, entity states, chunk lifecycle stages, shader variants, quality levels, graphics APIs, and supported package or editor versions. An unhandled row is a concrete finding even when every documented example passes.

## Report verification scope exactly

A green command proves only the cases and environment it actually exercised. Report which suite or scenario ran, which target and configuration it used, and which required tier did not run. Never let a local smoke test stand in for an unavailable player, device, GPU, integration environment, or perceptual check.

If the proving tier is unavailable, either change the task to an outcome the available environment can genuinely prove or report the remaining verification gap. Do not manufacture a different green check and give it the unavailable tier's name.

## Review the diff without its narrative

For risky or extensive changes, perform a cold pass using the code and diff before reading the implementation report. Ask what changed at every externally meaningful boundary and what can now happen that could not happen before. This reduces anchoring on the author's vocabulary and chosen success story.

Large changes are not improved merely by splitting them. Keep behavior, its meaningful verification, and any required test mechanism together; remove unrelated prose, tooling, and archaeology that obscure the atomic change.

## Allocate effort to product risk

Automate deterministic product invariants before formatting or documentation preferences. Look for missing callers, unread states, unreachable branches, unexercised variants, and assertions against intermediate values. Documentation checks are useful, but they cannot compensate for an unverified runtime path.

For unattended work, define the pass condition before execution and make it independent of the worker producing the result. If the worker cannot run that condition, it must stop with the unmet condition rather than redefine success.
