---
name: Target specific test files
description: When modifying tests, run only the specific test file via --testPathPattern instead of the full suite
type: feedback
---

Target specific test files when running integration tests — don't run the full suite just to check one file.

**Why:** Full integration suite takes ~4-5 minutes. Running a specific file takes ~8 seconds. Running full suite repeatedly wastes massive amounts of time.

**How to apply:** Use `pnpm test:integration -- --testPathPattern 'filename'` to run just the modified test file. Only run the full suite as a final verification before committing.
