# Context usage

Long agent sessions become less efficient and less reliable as their context
grows. Every additional request must reason over the accumulated conversation,
tool output, file contents, and injected instructions. Monitor context early,
not only when the client warns that the window is nearly full.

## Practical rules

- Keep tool output scoped: filter searches, cap logs, and avoid dumping generated
  files or large transcripts into the conversation.
- Prefer durable repository notes for decisions that must survive compaction.
- Finish coherent units of work and commit them separately.
- Start a fresh task when the subject changes substantially.
- After compaction, verify current goals and working-tree state instead of
  assuming every earlier detail survived.
- Count usage per model request, not per serialized transcript block; one
  response may contain several blocks sharing the same usage record.

## Claude Code helpers in this repository

The `cc-statusline`, `cc-context-warn`, and `cc-cost-tick` scripts are optional
Claude Code integrations. Their behavior depends on the hook and status-line
payloads exposed by the installed Claude Code version. They are not a portable
interface for Codex and should not be presented as one.

When enabled:

- `cc-statusline` displays the context payload supplied by Claude Code.
- `cc-context-warn` reports context bands without requiring repeated manual
  transcript inspection.
- `cc-cost-tick` reports changes in the client-provided session estimate.

Treat displayed cost as an estimate unless it comes from the provider's billing
or usage interface. Subscription limits, API billing, cached-token accounting,
and model pricing are separate concerns.

## What belongs in project documentation

Record only stable facts: important decisions, verified commands, constraints,
and unresolved risks. Do not preserve raw investigative output merely to avoid
losing it from context. A short evidence-backed note is easier for both Claude
and Codex to retrieve and maintain.
