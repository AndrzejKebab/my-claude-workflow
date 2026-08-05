---
name: box3d-is-not-box2d
description: "Never attribute Box3D's API vocabulary to Box2D — Box3D is its own engine, not a Box2D variant"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e57a5f50-379e-48cf-9d8f-845283352a82
  modified: 2026-07-21T16:09:01.586Z
---

Do not describe Box3D's types, fields, or naming as "Box2D's" in comments, docs, or
commit messages. Box3D is its own engine; that Erin Catto also wrote Box2D is
biography, not lineage for the API surface. Say "Box3D's own vocabulary".

**Why:** AGENTS.md introduces Box3D as "a new 3D physics engine (Erin Catto, the
Box2D author)", which makes it easy to slide into calling `linearDamping` /
`gravityScale` "upstream Box2D names". The user corrected this directly.

**How to apply:** When justifying the naming exemption for `box3d-unity`'s public
surface, attribute the field names to Box3D and the property names to
`UnityEngine.Rigidbody` (which they deliberately mirror). Related: [[unity-m-prefix-style-enforcement]].
