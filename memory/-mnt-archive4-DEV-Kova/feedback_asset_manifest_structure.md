---
name: Asset metadata convention
description: Assets use .meta companion files (TOML), not standalone config files. Texture arrays are explicit, reference by path not name. No auto-grouping.
type: feedback
---

Asset pipeline uses `.meta` companion files alongside source assets (e.g., `grass.png.meta`), NOT standalone `.toml` files separate from the asset. The `.meta` file is TOML with generic importer properties + type-specific sections.

`.meta` files are auto-generated with defaults when a new asset file appears (e.g., `.sbsar.meta` auto-populated from exposed substance parameters).

Texture arrays are standalone `.toml` files (they have no source asset) that explicitly list texture paths. Reference assets by path relative to `assets/` root, NEVER by name.

**Why:** The user wants a Unity-like asset+meta convention. Auto-grouping textures into arrays is bad design — arrays must be intentionally constructed. Names are fragile; paths are unambiguous.

**How to apply:** When designing asset config, always use `<asset_file>.meta` pattern. For compound assets (texture arrays) that have no source file, use standalone `.toml`. Always reference other assets by relative path from `assets/` root.
