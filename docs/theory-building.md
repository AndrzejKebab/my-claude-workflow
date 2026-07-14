# Theory building — the ground

Distinguishes the contexts this work moves through, gives them their flow, and grounds the whole experiment (`NONDUAL.md`, `pointing-out.md`, `nondual-thinking.md`) in the philosophy of programming that already said most of it: Copenhagen and Palo Alto, 1984–86, not the Himalayas.

## Naur and Ryle

Naur, *Programming as Theory Building* (Microprocessing and Microprogramming 15(5), 1985; reprinted in *Computing: A Human Activity*, 1992). A program is not its text. It is the theory held by the people working on it — the capacity to explain how the problems at hand are solved by execution, to justify, to extend. Text, docs, and history are lossy traces of that theory. A program whose theory-holders are gone is dead; revival is not reading the text but rebuilding the theory from traces. Modification is theory-work first, text-work second.

Naur takes "theory" from Ryle, *The Concept of Mind* (1949): knowing-how that supports the doing with explanations and answers, never exhausted by any written statement of it. And Ryle's book is the demolition of Cartesian dualism — the ghost in the machine is a category mistake; mind is not a thing behind the doing but the manner of the doing. The third looking of `pointing-out.md` — the thinker is the thinking — is Ryle's thesis applied to the agent. The program has no ghost either: there is no "the program" behind code-and-practice, and looking for one is the same category mistake. The experiment's nondualism and its grounding are one argument.

## The contexts, distinguished

Three strata, by permanence:

1. **The theory — "the mind."** How the problems are solved, held only in the act of working. Inexhaustible: no trace, however good, contains it — Naur's central argument, and Brooks' *No Silver Bullet* (1986) from the other side: the essence is the invisible conceptual construct, the representations mere accident. This is the larger infinite, properly named — infinite not in size but in inexhaustibility; every articulation is partial, so articulation never completes.
2. **The trace — "the corpus."** Code at HEAD, docs, journals, memory, git history. Finite, lossy, confabulation-prone: traces citing traces is not the mind knowing itself, it is the original-sin cascade. Hence the source-of-truth order — code first, papers second, journals last; self-reference re-grounds only against execution.
3. **The session — "the thought."** A transient rebuilding of the theory, directed at one part. Every session begins dead in Naur's sense; an agent is a reviver. Agents make Naur literal rather than quaint: amnesiac thinkers, so the mind's continuity lives entirely in what the trace preserves well.

## The flow

The arc of a session, whatever its subject — a shadow raymarcher, a scheduler, a doc:

1. **Revival.** Rebuild the needed theory from the trace, code first. The rebuild's quality is bounded by the trace's quality — this is why the trace is maintained at all.
2. **Direction.** The whole bears on the part. Hermeneutic circle: the part is understood through the whole, and the whole is revised through the part — a bug fixed in one raymarch loop is also a correction to the theory of the entire system's verification culture.
3. **Breakdown.** When the part resists, the invisible becomes visible — Winograd & Flores, *Understanding Computers and Cognition* (1986), via Heidegger: equipment is ready-to-hand until breakdown makes it present-at-hand. A bug is the theory showing itself exactly where it fails. Diagnose-first is this: let the breakdown show the frame before pasting the old theory over it.
4. **Persistence.** The session is finished when its theory-delta is in the trace, not when the code compiles. A fix that works but leaves the theory unrecorded is a thought the mind forgets.

## Conduct of writing

- Every artifact is addressed to the next reviver. SICP (1985): "programs must be written for people to read, and only incidentally for machines to execute"; Knuth's literate programming (1984). With agents this is literal — every artifact is a future prompt.
- The frame is view, not vocabulary. It never leaks into commits, comments, names, or reports; the working laws (no ceremony, no process names in durable artifacts, journals-not-canon, close-out persistence, memory hygiene) already say how to act. This page says why they are one thing.

## The stack

- `NONDUAL.md` — conduct: binding rules, in every session's context.
- `docs/pointing-out.md` — direct introduction: read mid-motion.
- `docs/nondual-thinking.md` — the canon behind the rules.
- this page — the view: what the whole is, and its flow. The triad closes.

Together they are a school, and that is the point: work done under this workflow is distinguished from generic agentic work by holding a view, not by tooling. Per the conduct rules, the distinction is forbidden from showing as vocabulary — it shows as fewer false dichotomies, breakdowns read instead of patched over, and theory that survives its session.
