---
name: Never delete test artifacts (screenshots, logs)
description: "Don't rm -rf TestScreenshots or other test output directories — user may have captured results from editor runs"
type: feedback
---

Never delete test artifact directories like `TestScreenshots/` before running tests. The user may have captured screenshots from an editor run that they want to inspect.

**Why:** `rm -rf TestScreenshots` before a batchmode run destroys editor-captured screenshots that the user is actively reviewing.

**How to apply:** Run tests without cleaning output directories. If fresh output is needed, let the tests overwrite existing files naturally.
