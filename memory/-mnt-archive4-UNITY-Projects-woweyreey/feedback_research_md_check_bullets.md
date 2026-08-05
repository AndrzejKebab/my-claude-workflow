---
name: Research markdown — verify bullets + speaker notes both present before reasoning
description: docs/research/*.md exports can drop slide bullets and keep only speaker notes; this strips structural facts. Cross-check both sections before drawing canonical conclusions.
type: feedback
originSessionId: 11a36976-71c3-49cf-80d6-21ddc4880efe
---
When `docs/research/*.md` is missing the bulleted slide content and only has the speaker-notes block, drawn conclusions can be load-bearingly wrong. Concrete incident (2026-05-07): on `bauer-2019-rdr2-atmospherics.md` slide 44 my export only had speaker notes; I concluded "Bauer iterates fog volumes brute-force, no z-bin acceleration." The slide's actual bullet was **"Up to 32 fog volumes stored in cluster grid · Z-Binning [Drobot17]"** — completely inverting the recommendation.

**Why:** The PPTX-extract pipeline can drop bullet groups when slide layout splits them oddly. Speaker notes are usually preserved verbatim. The asymmetry means a research file looks fine on quick read but is missing the structural callouts.

**How to apply:**
- When a research file's slide section has only `> **Speaker Notes:**` with no preceding bullets, treat it as suspect — re-extract or ask the user to verify.
- Before citing canon ("X uses Y / X does not use Y"), confirm both bullets *and* speaker notes are present for the slide making the claim.
- If speaker notes mention something the bullets don't (or vice versa), that's a red flag the export is incomplete.
- Workflow signal: when the user says "re-read X, the cache was incomplete," that's exactly this failure mode — the lesson is to check next time, not just to re-read.
