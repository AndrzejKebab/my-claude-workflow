---
name: Canon discipline — terminate on missing research, never stub
description: When canonical research is required but missing from docs/research/, the only correct action is STOP + report + wait for user to pull the paper. Stubs / "documented deviations" / partial implementations are forbidden silent failure modes.
type: feedback
originSessionId: 22de7076-3343-4170-bc2f-7a5c4f1ee32e
---
When a phase requires canonical research (paper-grounded algorithm, citation-backed parameters) and the source document is **not in `docs/research/*.md`**, the only correct response is:

1. STOP work immediately at the missing-research point.
2. Report the gap to the orchestrator/user with the specific paper / slide / parameter missing.
3. Refuse speculation, stubbing, partial implementation, "deviation" fallbacks, or "I'll skip this and document it".
4. Wait for the user to pull the research, then re-dispatch.

**Why:** During Phase 5 of the volumetrics-foundation orchestrate work (2026-05-09), the implementer encountered "Cuntz07 hierarchical pre-pass" cited in Enshrouded canon (sl. 15/sl. 20) but found no Cuntz07 paper in `docs/research/`. Per a "do not manufacture canon" instruction, the agent shipped pure-JFA-only and documented it as a deviation. The user's correction: that was wrong — "agent prevented speculation, but instead still deviated by effectively stubbing. The only correct course of action would be to terminate and report missing research and refusing any speculation." Without the source paper, you cannot know which algorithm parameters are load-bearing vs incidental — silent corruption of accuracy/performance properties is the failure mode.

**How to apply:** Every dispatched sub-agent brief must reproduce the canon-discipline rule explicitly. When the agent encounters missing research, it must STOP and return to the orchestrator with: (a) the specific paper / slide / parameter missing; (b) the operation that needs it; (c) a refusal to ship a stub. The orchestrator pauses, surfaces the gap to the user, and waits for the research to be added before re-dispatching. Documented deviations ≠ canonical implementation. A phase whose canon is unavailable does not ship. Pulled-canon entries belong in `docs/research/*.md` (extracted via `extract_research.py` or pasted manually). Project rule note added to `CLAUDE.md` § "Canon discipline (research-backed implementations)".
