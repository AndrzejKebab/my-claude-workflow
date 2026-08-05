---
name: No managed vertex/index arrays in mesh pipelines
description: Mesh generation & readback paths must stay on NativeArray/NativeSlice of float3/ushort — never propose Vector3[]/int[] even in interface signatures
type: feedback
originSessionId: d77e5e84-01cd-4696-8fe1-10eff67f70e9
---
Never propose `Vector3[]` / `int[]` / other managed arrays in mesh-generation, readback, or mesh-upload code paths. Use `NativeArray<float3>` / `NativeArray<ushort>` / `NativeSlice<T>` with `Unity.Mathematics` types, and upload via `Mesh.SetVertexBufferData` / `Mesh.SetIndexBufferData` directly from native memory.

**Why:** The heightfield collision pipeline already operates entirely on raw `NativeArray<byte>` readback decoded as native float3/ushort spans with zero managed allocation. Proposing managed array APIs — even just in an interface — signals willingness to break that invariant and drags managed GC into a per-frame mesh path. User called it out explicitly while reviewing a plan that had `Vector3[] verts, int[] tris` in an interface sketch.

**How to apply:** In every plan, design doc, and implementation touching mesh vertex/index data (collision meshing, stamp proxies, RWVT readback, any job producing mesh output), default to NativeCollections + Unity.Mathematics. This also aligns with the existing `feedback_native_collections.md` and `feedback_unity_mathematics_style.md` rules — treat this as their mesh-pipeline-specific corollary.
