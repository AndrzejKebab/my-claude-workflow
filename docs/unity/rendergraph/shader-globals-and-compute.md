# Shader globals and compute kernels

`Shader.SetGlobal*` and `CommandBuffer.SetGlobal*` populate the graphics pipeline's global constant buffers and texture bindings. Those bindings are read by raster shaders (the vertex and fragment stages) and by the Blitter; a compute kernel is not given them. Every value a compute dispatch reads is bound to its kernel explicitly, per dispatch, through the `SetCompute*Param` family. This holds on every graphics backend — it is not a Vulkan quirk and not a "reads as zero" bug; graphics globals and compute kernel parameters are two separate binding models. A value a raster consumer reads from a global must therefore be set on the kernel separately when a compute path consumes the same value, alongside the `SetGlobal*` call that still feeds the raster path.

## Binding a compute kernel

A compute dispatch reads only what is bound to its `ComputeShader` and kernel index: scalars and vectors through `SetComputeFloatParam` / `SetComputeIntParam` / `SetComputeVectorParam`, matrices through `SetComputeMatrixParam` / `SetComputeMatrixArrayParam`, and textures and buffers through `SetComputeTextureParam` / `SetComputeBufferParam`. The texture and buffer setters take the kernel index because a resource binds to one kernel's slot rather than to a global slot.

## A declared resource must be bound every dispatch

A `StructuredBuffer`, `RWStructuredBuffer`, or texture declared in a kernel must be bound on every dispatch that runs the kernel, or the dispatch is invalid — Unity reports a missing property, and with the backend validation layers enabled the dispatch is rejected. An empty-frame path binds a shared dummy resource to the slot rather than leaving it unset.

## Compute keywords

A compute kernel's shader keyword is enabled on the dispatch's own command buffer or declared as a local keyword. The global `Shader.EnableKeyword` that selects raster material variants does not select a compute kernel's variant.

## What does reach a compute kernel

A constant buffer is a separate mechanism from the per-value globals above: a buffer bound by name and declared as a matching `cbuffer` block in a kernel can be read by a compute dispatch on some backends. Treat that as backend- and version-dependent — confirm it with a test, and bind the buffer for the kernel explicitly rather than relying on a global binding to carry it into compute.
