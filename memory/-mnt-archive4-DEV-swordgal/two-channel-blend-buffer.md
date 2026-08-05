---
name: two-channel-blend-buffer
description: "swordgal's animation state holds exactly two blend channels, and both the search blackout and the fade-lead rule descend from that"
metadata: 
  node_type: memory
  type: project
  originSessionId: b1d18ea3-5e04-4cd5-9bfe-185c86944e87
  modified: 2026-07-24T11:46:44.945Z
---

`CharacterAnimationState` holds exactly two playbacks (Current + Outgoing). Both references hold
many — MxM's mixer renormalises across N live `m_animationStates`, Unreal's `AnimNode_BlendStack`
likewise — so several project rules that look like motion-matching design are really artifacts of
the two-channel buffer:

- `MotionMatchingSearch.FadeSettled` blanks the search for the middle 70% of every fade, because a
  jump landing in the visible band would hard-drop a channel the eye still carries. MxM searches
  every `m_updateInterval` (0.012 s) regardless. This welds responsiveness to blend length:
  `MatchBlendSeconds` is simultaneously the ease time and the input blackout (0.7x it).
- A fade may not outlive the content on either side of it, so every hand-off leads by the fade that
  will carry the outgoing playback out (`LocomotionBlendTree.FadeOutLead`). A clamped one-shot has
  `PhaseDelta == 0` and contributes blend weight with no travel. MxM ships the same lead as the
  optional `m_blendOutEarly` and defaults it *off* — it can afford to, this project cannot.

Undoing the two-channel limit is what dissolves both trades. Until then, treat any
"responsiveness vs blend quality" tuning as a symptom of it. See [[motion-matching-reference-split]].
