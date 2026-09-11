# Shared development memory

This directory stores verified knowledge that is reusable across projects. Organize notes by stable technical domain, such as `unity/ui-toolkit`, `unity/ecs`, `rendering`, or `development`.

Project-specific facts belong in the owning repository under `docs/agent-memory/`. A procedure with a reliable trigger belongs in `skills/`.

Each note should state when it was verified, relevant Unity or package versions, supporting evidence, and what would require revalidation. Update existing notes instead of accumulating near-duplicates.

When a Graphify graph already exists in this directory, update it after changing the corpus. Do not commit generated graph output unless the repository policy explicitly chooses to track it.
