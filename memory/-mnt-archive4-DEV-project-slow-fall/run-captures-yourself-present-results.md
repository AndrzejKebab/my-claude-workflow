---
name: run-captures-yourself-present-results
description: "For /delegate visual-verification gates and similar artefact-producing runs — execute the commands yourself (via a delegated sub-agent), report absolute PNG paths + one-line \"what to look for\" briefs. Don't hand command lines to the user to run themselves."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 807dbff4-fffb-4ea4-8567-bc0f2e698b8e
---

When a /delegate orchestration reaches a user-visual hard gate (e.g. bisection
capture, screenshot regression, build-output preview), the orchestrator
should run the commands itself — via a delegated sub-agent — and present:

1. **Absolute paths to every artefact** produced (e.g.
   `/mnt/archive4/DEV/.../naadf-captures/<file>.png`), not relative paths,
   not "look in the build dir".
2. **One-line "what to look for" brief per artefact** anchored to the
   prediction-vs-outcome falsification line (the design's predicted
   appearance after the change).
3. **The visual itself if Read can render it** — orchestrator's Read tool
   renders PNG/JPG visually, so absolute path + a Read call brings the
   image into the user's view inline.

**Why:** the user has explicitly stated they prefer this flow. Handing
them command lines to run themselves adds friction. The only legitimate
reason NOT to is a hard environment block — GUI editor lockfile, missing
DISPLAY, agent sandbox can't reach the X server — and in those cases the
brief explains the block specifically rather than punting the command.

**How to apply:** at any visual-gate dispatch in /delegate (the
post-impl gate, an iteration re-capture, a diagnostic visualization), the
capture is itself a delegated step — not a "now you run this" handoff.
The capture sub-agent's deliverable is: paths + one-line what-to-look-for
per artefact, written as a status message and (if relevant) appended to
the orchestrate doc. The orchestrator then surfaces the absolute paths
to the user.

If the capture environment is blocked (GUI lockfile, sandbox limit, etc),
the orchestrator says so explicitly with the specific blocker + how to
unblock — NOT "here's the command, please run it".

Related: [[naadf-render-bisection-workflow]] documents the specific
unity-batchmode capture commands for this project.
