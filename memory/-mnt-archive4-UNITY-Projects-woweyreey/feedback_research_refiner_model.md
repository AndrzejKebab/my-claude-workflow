---
name: research-refiner-model
description: "/research Pass 3 refiner must be dispatched on claude-opus-4-7[1M], overriding the skill's claude-opus-4-6 pin"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c432bf6d-5efa-40a0-94c3-6539035f2fb8
---

When dispatching the Pass 3 `research-refiner` sub-agent in the `/research` skill, override the model to **`claude-opus-4-7` (1M context)** — pass `model: opus` on the Agent tool call and state the 1M-context requirement in the brief.

**Why:** the user explicitly required this on 2026-05-14. The skill's `SKILL.md` frontmatter still pins the refiner to `claude-opus-4-6`; that pin is stale. The refiner is the quality-control gate where OCR-corrupted equations get reconstructed and load-bearing formulas reach final citable form — the user wants the strongest available model plus the 1M window so the refiner can hold an entire long extract (3–5 K lines after vision pass) in context at once.

**How to apply:** every Phase C refiner dispatch in a /research run. Does not affect extractor / vision / indexer agents — those keep their skill-default pins (Sonnet). Only the refiner is upgraded.

Related: [[feedback-no-cpu-marker-fallback]], [[feedback-no-force-extract-research]].
