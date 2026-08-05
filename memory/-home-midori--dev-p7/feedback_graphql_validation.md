---
name: GraphQL validates non-nullable fields
description: Don't manually validate fields — just query through the full GraphQL API and check response.errors
type: feedback
---

When testing GraphQL non-nullable constraints, don't write manual field validation logic. Just query through the full e2e GraphQL HTTP API call — GraphQL itself will return errors if any non-nullable field is null. Assert `response.errors` is undefined.

**Why:** The user explicitly said "we dont need to verify fields - just query the thing through full e2e GraphQL HTTP API call - it will fail if something is wrong." Manual validation is redundant overhead.

**How to apply:** In integration tests, prefer full GraphQL queries with all union fragments over manual field checks. Let the schema enforce correctness.
