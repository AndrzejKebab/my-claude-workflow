---
name: Tooltip no punctuation
description: Unity shader Tooltip() attribute prohibits any punctuation characters
type: feedback
---

Unity shader `[Tooltip(...)]` attributes must not contain any punctuation (hyphens, periods, commas, etc). Use plain words only.

**Why:** ShaderLab parser treats punctuation as syntax tokens inside `Tooltip()`, causing parse errors.
**How to apply:** When writing `[Tooltip(...)]` in .shader files, use only alphanumeric characters and spaces.
