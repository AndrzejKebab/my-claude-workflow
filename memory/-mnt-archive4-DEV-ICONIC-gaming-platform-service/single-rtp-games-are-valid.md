---
name: single-rtp-games-are-valid
description: "A single-RTP (\"single-math\") game is legitimate, not unfinished — don't conflate it with broken, and don't exclude or special-case it"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 35b7a52b-72fd-486e-8dac-b8be3400ead9
---

A game whose class takes an `rtp` profile but plays identically under every profile ("single-math" /
single-RTP) is a **legitimate, finished game** — one mathematical model, not tuned by launch profile.
The origin ships several (kraken-clash, onsen-fortune, african-animals, dice-quest). It is NOT an
"unfinished/unplayable" marker and is NOT grounds to exclude, special-case, or add an
`rtpIndependent` flag as if it were exceptional.

**Why:** the user pushed back hard ("what is wrong with being single-math? wtf") when I treated
single-math as a defect requiring a decision. I had conflated "reddens the target's multi-profile
test gate" with "the game is broken." The games are fine; the **gate** is the bug — it hard-requires
every game declare >1 *distinct* RTP profile (`given(profiles.length>1)` as assert.ok,
`assertProfileSteersTheGame` = notDeepEqual, integrity distinctness), wrongly assuming all games are
multi-RTP.

**How to apply:** when a legitimate design trips an over-strict gate, fix the gate, don't exclude or
flag the design. Profile-steering/distinctness checks should apply only to games that actually
declare >1 profile; a single-RTP game declares its real profile(s) and passes. Genuine exclusion
grounds are real brokenness (crashes with no graceful carve-out, dead features) AND not
feature-test-depended — never "single-RTP". Related: [[stealth-framing-not-porting]],
[[rtp-noise-threshold]].
