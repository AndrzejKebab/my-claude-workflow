---
name: enforce
description: Load and audit repository instructions before work. Use when the user asks to enforce or inspect active agent constraints.
---

# Enforce Skill

Pre-loads constraints from CLAUDE.md into session context.
Prevents common failure patterns before they start.

## Usage

```bash
/enforce           # Load constraints for current project
/enforce --strict  # Fail on any rule violation (CI mode)
/enforce --list    # Show all active constraints
```

## What It Does

1. **Reads CLAUDE.md** from project root
2. **Extracts hard rules** (NEVER, ALWAYS, MUST, etc.)
3. **Injects into context** as system-level constraints
4. **Sets guardrails** for the session

## Example Output

```
╔════════════════════════════════════════════════════════════╗
║  CONSTRAINTS LOADED                                        ║
╠════════════════════════════════════════════════════════════╣
║  From: ./CLAUDE.md                                         ║
║  Rules: 6 enforced                                         ║
╠════════════════════════════════════════════════════════════╣
║  HARD STOPS:                                               ║
║  • NEVER push — user pushes after review                   ║
║  • NEVER add Cargo features — this is a game               ║
║  • ALWAYS apply #[cfg] at exact point of divergence        ║
╚════════════════════════════════════════════════════════════╝
```

## Integration

Works with `/resume` — if a project has CLAUDE.md, constraints auto-load.

## Rules Detection

Extracts constraints from:
- **Code blocks** with "Wrong/Right" or "✓/✗"
- **Sentences** starting with NEVER, ALWAYS, MUST, DON'T
- **Section headers** like "Git", "Testing", "Pre-Commit Rules"
- **Signal phrases** from llm-cases ("This is getting complex")
