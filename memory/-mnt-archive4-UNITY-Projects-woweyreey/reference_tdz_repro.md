---
name: TDZ bug reproduction command
description: Command to reproduce the "default is not initialized" TDZ bug after domain reload
type: reference
---

**Reliable reproduction** via chaos script:

```bash
./scripts/chaos-tdz.sh 20
```

Reproduces on first cycle with scenario "C# edit → compile → INSTANT play". The script mutates a C# file, compiles, and immediately enters play mode.

**Root cause clue**: `OnStartRunning` logs `VM v1 (existed=True)` — the VM SURVIVES domain reload. The old QuickJS context has stale module state. TDZ is detected immediately after `qjs_shim_eval_module` returns — the module namespace already has `default` uninitialized straight from QuickJS native evaluation.

**Key finding**: the bug is in the QuickJS module cache. When bridges re-register on a SURVIVING VM, the synthetic modules (`unity.js/ecs`, `unity.js/components`) may be cached by QuickJS from the previous session with stale bindings. New module loads that import from them get the stale (TDZ) namespace.

`JsRuntimeManager.SimulateDomainReload()` is available for test harness use. `JsDomainReloadSimulator.ReRegisterAll()` is codegen-generated.
