# Burst inventory template

Use this page to record how Burst is used in the current Unity project. It is
an inventory, not a list of rules: update it when a new compilation pattern is
introduced or an existing one is removed.

From the Unity project root on Windows, start with:

```powershell
rg -n '\[BurstCompile' Assets Packages
```

Then review the surrounding code and classify each use. Generated code and
package-cache results can be excluded unless the project owns or depends on
that code directly.

| Pattern | What to record | Example questions |
| --- | --- | --- |
| Jobs | Job type and scheduling site | Is the job struct blittable and free of managed references? |
| `ISystem` | System type and update method | Does the system stay on the Burst-compatible path? |
| Field access | Component, buffer, or lookup access | Are read/write attributes accurate? |
| Non-default options | Any `FloatMode`, `FloatPrecision`, or `DisableSafetyChecks` setting | Why is the default unsuitable, and how was the trade-off verified? |
| Static direct calls | Methods using `CompileFunctionPointer` or direct-call generation | Is the call site valid in all target builds? |
| Function pointers | Delegate signature and initialization owner | Does initialization happen before the pointer is used? |
| `SharedStatic` | Stored value and lifetime | Is initialization deterministic and safe across domain reloads? |

## Current-project notes

Keep concrete findings here, with file paths relative to this Unity project.
Remove stale entries instead of treating this section as an archive.

```text
- [pattern] path/to/File.cs — short reason this pattern is used
```

## Verification

After changing a Burst call site, recompile and check the Unity Console:

```text
unity-recompile
unity-cli console --filter error --lines 5
```

Use the Burst Inspector or generated-code inspection when the change depends
on a particular optimization, CPU feature, or safety-check setting.
