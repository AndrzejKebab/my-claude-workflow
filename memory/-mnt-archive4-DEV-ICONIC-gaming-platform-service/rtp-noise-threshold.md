---
name: rtp-noise-threshold
description: "Don't report RTP movement that isn't significant — sub-1pp with a CI spanning zero is noise, not a finding"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 971c6d91-6879-43d5-b990-ca7d818891d3
---

RTP movement below significance is noise. Do not report it unless it is **catastrophic**.

Observed: a fair-permutation fix measured −0.53pp (98.01 → 97.48) with 95% CI [−1.85, +0.80] over
9M rounds/arm — reported as a headline finding, and it is nothing.

**Why:** a measurement whose interval spans zero says nothing happened. Surfacing it as a finding
buries the findings that matter, and invites a decision where there is no question. The user reads
every line; a line that cannot change what they do is a cost.

**How to apply:** measure when the mathematics changes, then say nothing unless the result is
significant or catastrophic. Block SD on a slot's RTP is percentage points — an effect smaller than
that cannot be pinned at any feasible sample size, so "not significant" is the expected answer, not
a caveat worth narrating. Certification is a separate question with its own instrument; never let a
noise reading masquerade as a certification claim. Related: [[stealth-framing-not-porting]].
