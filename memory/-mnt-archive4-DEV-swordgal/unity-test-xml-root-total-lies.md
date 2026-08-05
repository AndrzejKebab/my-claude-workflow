---
name: unity-test-xml-root-total-lies
description: Unity -runTests XML root total/passed attributes undercount; sum test-case elements or per-assembly test-suite rows instead
metadata: 
  node_type: memory
  type: reference
  originSessionId: 03f5969b-7b24-48c3-a48b-7e2be2e5f4e2
  modified: 2026-07-24T13:11:57.866Z
---

Unity's `-testResults` NUnit XML has a root `<test-run total=… passed=…>` whose numbers do **not**
cover every assembly. Measured 2026-07-24 on an EditMode run: root said `total 28`, while iterating
`test-case` elements gave 37 and the per-assembly `<test-suite type="Assembly">` rows summed to the
same 37 (Box3D 14 + Rukhanka 13 + Swordgal.Editor.Tests 9 + Addressables 1). Reading the root
attribute made the project's own 9 editor tests look like they had silently stopped running — a
regression that did not exist.

**How to apply:** parse results by iterating every `test-case` element, or by reading the
`test-suite type="Assembly"` rows. Never quote the root `total`/`passed`. A suspiciously round drop
in test count is this bug before it is a real one.

Related: [[netcode-6-inprocess-session-harness]].
