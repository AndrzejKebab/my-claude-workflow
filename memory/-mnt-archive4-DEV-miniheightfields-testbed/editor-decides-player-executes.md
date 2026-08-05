---
name: editor-decides-player-executes
description: Frozen VT archives are an editor-authored deliverable; the build ships what the editor produced and never re-derives or validates it against source content
metadata: 
  node_type: memory
  type: project
  originSessionId: 90bc27f1-3a15-40e7-9e85-54ecac50244e
  modified: 2026-07-20T19:36:43.149Z
---

Ruling, 2026-07-20. **The editor dictates what was built and how; the player executes.**

Packing and streaming exist as a **content-delivery optimisation**, so a shipped build is
intended to **strip the original procedural content** — stamps, materials, the compositor
inputs. The frozen archive replaces them rather than accompanying them.

Two consequences, both binding:

1. **No runtime content-hash cross-referencing.** The player cannot recompute a content hash
   because the content is not there. `VTArchiveReader` may carry the hash for provenance, but
   nothing in a player validates against it.
2. **The build never re-derives the archive.** A build-time step must not compare hashes and
   implicitly re-bake — that hands the build authority over an authoring decision, and it
   silently overrode the author's chosen mip range once already (a 21 MB freeze became 337 MB
   because the automated path used its own default budget). The build verifies the archive is
   present and fails loudly if it is not; it does not produce one.

**The content hash stays editor-side only** — an author-facing "is this stale?" convenience for
the freeze action and the batchmode entry point, never a build trigger and never a runtime gate.

**Why this matters beyond tidiness:** chasing cross-process hash stability was wasted work that
only existed because the build had been given a decision that was never its to make. If a
comparison seems to need a hash to survive processes, check first whether the comparison should
exist at all.

Related: [[vt-streaming-minimal-then-native-plugin]], [[vt-archive-io-interface-shape]].
Stripping procedural content from builds is future work, not yet implemented.
