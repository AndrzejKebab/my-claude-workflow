---
name: unity-cli test runs EditMode by default
description: unity-cli test defaults to EditMode — must run both modes separately with --mode flag
type: reference
---

`unity-cli test` defaults to `--mode EditMode`. To run both modes:

```bash
unity-cli test --filter "Namespace.Class" 2>&1           # EditMode (default)
unity-cli test --mode PlayMode --filter "Namespace.Class" 2>&1  # PlayMode
```

Filter requires full namespace path (e.g. `UnityJS.Entities.EditModeTests.ComponentsImportReloadE2ETests`).
