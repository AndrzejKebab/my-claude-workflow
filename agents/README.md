# Global Claude Agents

The installer copies these definitions to `~/.claude/agents/`.

## Refactoring pipeline

- `refactor-explorer` finds and prioritizes structural problems.
- `refactor-architect` designs the approved target structure.
- `refactor-implementer` performs and verifies the migration.

## Research pipeline

- `research-extractor` performs initial source extraction.
- `research-vision` reconstructs visual slide and figure content.
- `research-refiner` resolves extraction issues and produces clean research notes.

## Unity voxel/ECS review

- `logic-design-reviewer` proves algorithmic correctness, reachable edge cases, and coherent system composition.
- `performance-reviewer` examines measured or statically proven allocation, scheduling, lifetime, bandwidth, and scaling costs.
- `readability-docs-reviewer` checks naming, contracts, comment proportion, and documentation against current code.
- `simplicity-reviewer` identifies removable structure only when required behavior and supported variation remain intact.

Give all reviewers the same bounded scope and a unique report path. A reviewer
must verify source, admit only evidence-backed findings in its own lens, accept
an empty report, and return only its report path, one-line verdict, and blockers.
The advisor deduplicates by mechanism and prioritizes by observable project
consequence rather than counting specialist severity labels as votes.
