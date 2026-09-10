# Unity workflow reference

This guide applies to a Unity game repository without assuming a specific
render pipeline, package layout, editor version, or local tool installation.

## Project conventions

Record the Unity version, render pipeline, package versions, target platforms,
build command, and test command in the game repository's `AGENTS.md`. These are
project facts, not global workflow defaults.

Keep gameplay source, editor tooling, tests, and generated artifacts in clear
separate locations. Use asmdefs to express runtime/editor/test dependencies and
avoid adding editor-only APIs to runtime assemblies.

## DOTS and jobs

Use ECS where large numbers of similar, data-oriented entities benefit from it;
do not force every system into ECS. Keep authoritative simulation data separate
from rendering/presentation entities, especially for streamed voxel chunks.

Declare system ordering with system groups and explicit update attributes. Do
not rely on creation order. Track and chain `JobHandle` dependencies, and use
an `EntityCommandBuffer` for structural changes that cannot occur during query
iteration.

Burst paths must use blittable, supported data and APIs. A player build is the
real validation for Burst/native interop because editor execution can hide AOT
problems.

## Rendering and assets

Treat render-pipeline resources as dependencies with explicit lifetimes and
read/write declarations. Validate changes with the target render pipeline and
hardware; a headless or editor-only result does not establish final rendering
behaviour.

Keep `MonoBehaviour` classes that are serialized by scenes or prefabs in files
whose names match the type. Preserve `.meta` files and asset GUIDs when moving
or packaging content.

## Package and editor maintenance

Use a package's `Samples~/` directory as the distributable source; imported
samples under `Assets/Samples/` are working copies and do not synchronize back
automatically. Before changing Unity or package versions, record a clean build
and test baseline, then make one upgrade at a time.
