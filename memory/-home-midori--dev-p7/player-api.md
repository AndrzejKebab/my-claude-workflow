---
name: player-api
description: TypeScript gotchas and test infrastructure patterns for player-api service
type: project
---

## Test Infrastructure

- Integration tests use `TestEnvironment` DSL with `InMemoryAdapter` wrapped by `ErrorSimulatingAdapter`
- Error injection: `env.setErrors({ onCredit: 'server_error' | 'timeout_after_processing' })`
- Operation tracking: `env.operations.filter(op => op.type === 'credit')`
- Transaction queries: `env.transactionsByStatus.settled/failed`
- Retry flow: `env.processFailedTransactions()`
- Types in `TestEnvironmentTypes.ts`, setup in `TestEnvironment.ts`, bootstrap via `setupIntegrationTest()`

## TypeScript Gotchas

- `exactOptionalPropertyTypes` enabled — use `field: T | null` not `field?: T` when the field must exist
- Prisma `ERewardType` conflicts with local type alias in `transaction.types.ts` — use `import { ERewardType as PrismaERewardType }`
