---
name: research-skill-sonnet-only
description: "For /research skill pipeline runs, use Sonnet for every sub-agent dispatch, including the Pass 3 refiner (overriding the skill's default Opus pin)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 36fefae0-c5c9-46b6-aeb8-095a1c486408
  modified: 2026-08-04T19:04:08.402Z
---

When running the `/research` extraction pipeline (research-extractor, research-vision, research-refiner), dispatch every sub-agent with `model: "sonnet"` — including Pass 3 (research-refiner), which the skill's own SKILL.md pins to Opus 4.7 1M-context by default for math/equation quality control.

**Why:** user explicitly said "use only sonnets" (2026-08-04) while multiple /research extractions were running concurrently (4 papers in flight). Read as a standing cost/model preference for this skill, not a one-off for a single dispatch.

**How to apply:** On every future `/research` invocation (this session or later ones), pass `model: "sonnet"` on all Agent tool calls for research-extractor, research-vision, and research-refiner — do not fall back to the skill's Opus default for the refiner pass unless the user says otherwise. If a paper is unusually math-heavy and a Sonnet refiner seems likely to miss subtle equation errors, it's fine to flag that tradeoff to the user, but don't silently switch to Opus.

**Known failure mode — regression after context compaction (2026-08-04):** mid-session, after a context-compaction summary, the orchestrator reverted to dispatching Pass 3 refiner agents on `model: "opus"` for several papers in a row (Merchant, Neelakantan, Frame Timing Latency, and had 3 more in flight — Shao, Fortnite Creators Podcast, Oztalay — when caught). The likely cause: the /research skill's own SKILL.md text is reloaded verbatim on every invocation and argues at length for Opus-on-refiner with a specific worked example (dropped exponent in a Rayleigh phase function) — that in-context argument is more salient than a fact buried in a compacted summary, and won without an active check. User had to re-issue "dont dispatch to opus, use sonnets for everything" to correct it; the 3 in-flight Opus agents were stopped (`TaskStop`) and redispatched fresh on Sonnet, losing their partial progress. **Mitigation:** treat this memory file, not the skill text, as authoritative on model choice — re-check it explicitly before the first Agent dispatch of any `/research` session, and especially right after a compaction event, since that's exactly when the skill's own persuasive Opus-rationale is freshest in context and this memory is not.
