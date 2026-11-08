# Bot fleet

Hermes profiles that work on one game repo as a team: Manager, Reviewer, Workers and the Advisor, driven by the owner.

## Language

### Roles

**Advisor**:
The bot above the rest of the fleet. Owns final review, merging and troubleshooting, and teaches the first line so it is needed less over time. Treats every option set another bot offers as a suggestion, not the full space.
_Avoid_: supervisor, lead, senior reviewer

**First line**:
The bot that handles an item before the Advisor: Manager for Worker questions and self-check reports, Reviewer for review disputes.
_Avoid_: triage, front desk

**Escalation**:
A first-line bot handing an item to the Advisor, with its own analysis attached. Each one should end in a lesson that lets the first line handle the next such item alone.
_Avoid_: forwarding, relay

**Eye review**:
The owner looking at a change himself before it merges. Required when the change makes any difference to how the game looks or plays, however small; not required when the output is shown to be identical. The owner may waive it for one PR.
_Avoid_: final review (that is the Advisor's check), owner approval

### Sessions and turns

**Canonical session**:
The single long-lived conversation a bot has. Every owner message, peer DM and wake for that bot runs as a turn in it.
_Avoid_: chat, thread, context

**Compaction**:
The replacement of a canonical session's older turns by a written summary, so the session keeps fitting its model's context.
_Avoid_: compression, reset, new session

**Bot Chat turn**:
A turn the owner starts by typing to the bot. The owner is present and can answer an approval.
_Avoid_: interactive turn, desktop turn

**Headless turn**:
A turn started by a peer DM or a watchdog wake. Nobody is present to answer an approval.
_Avoid_: background turn, CLI turn, wake (a wake is one cause of a headless turn)

### Review and proof

**Issue to fix**:
One item of a Reviewer's review that the Worker must fix. Always names what it violates: an acceptance criterion, a repo rule, or a breakage shown by evidence.
_Avoid_: blocking, should-fix, nit, finding

**Spec question**:
A Reviewer's view that the work should differ from what was requested, with no criterion, rule or breakage behind it. Goes to the Advisor, never to the Worker.
_Avoid_: design suggestion, should-fix

**Reviewer miss**:
A PR the Reviewer cleared that then failed the Advisor's final review or the owner's eye review. The measure of how well the Reviewer did its job.
_Avoid_: regression, bad review

**Merge proof**:
The evidence needed to merge without eye review, from runs the Advisor started itself: each test it relies on seen failing on the base and passing on the PR head, identical output shown by direct comparison, and every acceptance criterion matched to its evidence.
_Avoid_: green tests, CI pass, the author's verification

**Self-check**:
The four lines a bot writes before it reports an error, sets `blocked` or says "cannot": the failure quoted, its own cause ruled out, the other route tried, and the claim with its evidence.
_Avoid_: error report, blocker note

### Tools

**Toolbox skill**:
A tool packaged as a skill: a description written by the symptom it answers, how to call it, the programs it starts, and one recorded run. Specific or General like a lesson.
_Avoid_: bot-tool, script, helper

**Fleet job**:
The container one toolbox run executes in, holding the tool and every process it starts. Ends with one stop line naming why it ended.
_Avoid_: process tree, run

### Learning

**Lesson**:
Something a bot learned from its own work that a later turn, or another bot, needs: a fact about the project, the fleet, or how a tool behaves.
_Avoid_: memory (that is one bot's store), note, tip

**Draft lesson**:
A lesson a bot has written about its own mistake, not yet reviewed by the Advisor. Not found by lesson search until the Advisor accepts it.
_Avoid_: pending lesson, queued memory write

**Lesson digest**:
The daily message to the owner listing the lessons accepted that day, which he can correct or retire.
_Avoid_: approval queue, memory review

**Specific**:
Knowledge that holds only for one project: its lessons, tools, decisions and memory. Lives in that project's directory.
_Avoid_: project-local, fleet lesson

**General**:
Knowledge that holds for all work: Unity, coding, git, Hermes and the fleet's way of working. Lives in this repository, shared by every project and bot.
_Avoid_: global memory, shared lesson

**Bot memory**:
One bot's own small store of facts about itself, such as its workspace and its signature. Holds no lessons other bots need.
_Avoid_: MEMORY.md as a synonym for all learning

**Queued memory write**:
A change to a bot memory proposed by Hermes's automatic review, waiting for the owner's approval. Tied to the entry text it was written against.
_Avoid_: pending lesson

## Flagged ambiguities

- "Final review" was the Reviewer's check in the main Editor before the owner's approval. With the Advisor it is the Advisor's check; the owner's look is **eye review**.

## Example dialogue

> **Owner:** Worker-1 ran that heredoc fine this morning, now it says it cannot.
> **Dev:** This morning was a Bot Chat turn. The DM from Manager started a headless turn, and there the same command is refused. Its canonical session also went through a compaction in between, so the earlier success is now a one-line summary. Its self-check should have searched the session and found the script-file route.
