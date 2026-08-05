---
name: suite-may-be-vacuous
description: "hypertino's e2e test/suite cases may be AI slop that assert nothing — never trust a green gate without proving it bites"
metadata: 
  node_type: memory
  type: project
  originSessionId: 02766960-5f90-462d-a8a3-24b63f55ff2a
---

The user has NOT verified that hypertino's existing test/suite cases actually assert anything useful — their words (2026-07-04): "those are full-on ai slop, i haven't verified them actually asserting anything useful, i just know they exist."

**Why:** a green `just check` / passing suite is therefore NOT trustworthy proof of correctness on its own. The cases exist but may be vacuous.

**How to apply:** for any change whose correctness a gate is supposed to protect, prove the gate BITES — deliberately break the behavior, confirm the gate goes RED, record which specific check caught it. A visibly-wrong result that stays green is a blocking finding: the gate is slop and a real one (e.g. reference-capture pixel diff on real GPU, headful) must be built before the change can be trusted. This is the concrete local instance of AGENTS.md's "green on a proxy is not proof" and [[representative-e2e-not-manual-qa]].
