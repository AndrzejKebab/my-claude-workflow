---
name: validate-real-entry-points
description: "pre-close validation must run the platform's real entry points (just web, native run), not just the gated just check proxy"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 02766960-5f90-462d-a8a3-24b63f55ff2a
---

Pre-close validation must exercise the **real entry points the user actually invokes** — `just web` (builds + serves the editor-web target) and the native app run — not only the gated `just check` path. User (2026-07-04) after the hlslpp port declared green: "why is checking if just web and just linux at least work is not part of your pre-close validation? … at least run just web and just native of your platform."

**Why:** `just check`'s web coverage goes through a Playwright `test-web` proxy (`ht_web_suite`/bench web); it never builds/serves the editor-web target `just web` uses, so a break in the real entry point passed green. Same proxy-vs-real-artifact hole as [[suite-may-be-vacuous]] and [[representative-e2e-not-manual-qa]] — a green gate on a proxy is not proof.

**How to apply:** close the hole MECHANICALLY, not as an ambient "remember to run it" (AGENTS.md enforcement-locus rule — ambient obligations fail silently). A pre-close gate builds + smoke-launches the real entry points (`just web` editor-web build, native app run) and is proven to bite (red on the break, green after fix). The methodology line lives in `AGENTS.md` pointing at that mechanical check as its locus.
