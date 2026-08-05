---
name: JsGameCodegen requires dotnet build
description: After changing JsGameCodegen~ source generator, must run dotnet build to copy Roslyn DLL — Unity uses the built DLL, not the source
type: feedback
---

After any change to `Packages/com.api-haus.unity.js/JsGameCodegen~/`, run `dotnet build` in that directory before relaunching Unity. Unity loads the pre-built Roslyn analyzer DLL, not the raw .cs files. Skipping this step causes Unity to use the old generator and may crash.

**Why:** JsGameCodegen~ is a standalone Roslyn incremental source generator. The dotnet build compiles it and copies the DLL to where Unity expects it.

**How to apply:** Every time you edit files in `JsGameCodegen~/`, run `dotnet build` there before refreshing/relaunching Unity.
