---
name: feedback-handler-style
description: "When wiring graphile-worker handlers into runService, write the handler body inline under the task identifier — do not extract it into a named const above the runService call."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1ef75796-de11-43da-964e-8048438dcb0b
---

In `src/services/<svc>/main.ts`, write each handler inline inside the `handlers: { … }` object passed to `runService(…)`. Annotate the payload parameter inline: `[TASK_NAME]: async (payload: TaskType, { log, db }) => { … }`. Do not pull the body out into a `const fn: Handler<T> = …` declared above.

**Why:** Explicit user preference — they prefer the call-site to read top-to-bottom without indirection. The intermediate `const` adds a name to scan past without any payoff.

**How to apply:** Whenever editing or scaffolding a new service entrypoint in `src/services/*/main.ts`. The `Handler<TPayload = any>` type in `src/app/run-service.ts` is permissive enough that inline annotation alone gives full payload typing.
