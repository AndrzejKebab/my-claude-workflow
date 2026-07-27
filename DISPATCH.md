# DISPATCH — how subagents deliver work (binding)

Governs every use of the Agent tool. [[NONDUAL.md]] governs the reasoning, [[PROSE.md]] the sentence;
this file governs the wiring between an orchestrator and the agents it dispatches.

## A dispatched agent writes its report to a file and returns the path

Never ask one to deliver findings as its final message. The brief names the path; the agent `Write`s
there before it returns; the orchestrator reads the file if and when it needs the contents.

The final message carries only what the orchestrator needs to decide what happens next: the path, a
one-line verdict, and anything the agent could not determine. Everything else goes in the file.

## Why

Three reasons, and the third is the one that bites:

- **A report delivered as a message is capped by the message bus.** A thorough code map or a
  reference excavation exceeds it, and what arrives is the tail — the agent's closing summary, with
  the substance silently gone. Observed: a research dispatch returned only its addendum, opening with
  "the main report stands unchanged" for a main report that had never arrived. It had to be asked for
  twice.
- **The orchestrator is a decision maker, not a filesystem router.** Relaying an agent's bytes into
  its own context to sort them by hand spends the one context that has to stay clear, on work a path
  does for free.
- **It is what lets a dispatch be large.** Fan-out over a whole package, a full-tree audit, a
  many-file migration — each produces more than a message can carry, so the file convention is the
  precondition for attempting them at all, not a tidiness preference.

## Where reports land

Prefer a **tracked** location in the repo under work — `.scratch/<topic>/NN-<slug>.md` where the repo
has such a directory — so a finding survives the session that produced it and is reviewable in a diff
like anything else. Check it is not gitignored before choosing it; a repo may carry both a tracked
`.scratch/` and an ignored `tools/scratch/`. Where no tracked location fits, use the session
scratchpad and say so, accepting that the report is then session-lived.

## This picks the agent type, so pick it at dispatch

`Explore` is read-only by construction — no `Write`, and shell redirection is refused too. It
**cannot** honour this convention, and it discovers that only after the work is done, returning a
refusal instead of the report. Dispatch anything that owes a report to a write-capable type
(`general-purpose`, `claude`, a project's own agents). Reserve `Explore` for the case where the answer
genuinely fits in a message.

Retrofitting does not work either: a completed `Explore` agent, resumed and asked to persist what it
already wrote, refuses for the same reason. The choice is made at dispatch or not at all.

## The orchestrator still summarizes

Reading the file to write that summary is the point. Being handed the contents whether or not they
were needed is what this replaces.
