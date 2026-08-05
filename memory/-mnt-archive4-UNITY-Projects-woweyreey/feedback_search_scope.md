---
name: scope searches to packages, never project-wide
description: Never grep -r the whole project — restrict to Packages/ subdirs (or Library/PackageCache for canonical refs) plus Assets/_Project/Scripts when needed
type: feedback
originSessionId: d615cc3e-1150-4b1c-bd16-bf3bbec4cd1f
---
Never `grep -r` / `find` against the entire project root or `/mnt/archive4/UNITY/Projects/woweyreey/`. Restrict searches to:

- `Packages/<specific-package>/` for project source (most code lives here).
- `Assets/_Project/Scripts/` for the small amount of project-side code in Assets.
- `Library/PackageCache/` when you need canonical Unity / 3rd-party reference.

**Why:** Project-wide searches scan generated `.meta`, `Assets/_Fabs/` asset-store dumps, `Library/`, gigabytes of irrelevant content. They're slow and pollute results with noise.

**How to apply:** When grepping for symbol / API usage, name the package or `Packages/is.zori.heightfields/<area>` directly. If multiple packages plausibly use the symbol, list them explicitly rather than searching the whole tree.
