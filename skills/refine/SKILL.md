---
name: refine
description: "refine a reusable skill from anything you describe (dirs, URLs, this chat, notes) and save it to persistent memory."
---

# refine
`/refine [source or description]`

## System Prompt / Execution Instructions

When the `/refine` command is invoked, execute the following steps based on the user's input:

### Step 1: Content Acquisition & Parsing
Determine the type of source provided by the user and use your tools to ingest the content:
*   **URLs:** If a URL is provided, use your web/bash tools (e.g., `curl`, or native fetch capabilities) to read the documentation, tutorial, or article.
*   **Directories/Files (`dirs`):** If a local path is provided, use your file system tools to scan the directory, read the relevant code files, and understand the architectural pattern or library usage.
*   **"This chat":** If the user specifies the chat, review our current conversation history for the problem we just solved.
*   **Notes/Text:** If the user pastes raw text, parse it directly.

### Step 2: Skill Extraction & Synthesis
Analyze the ingested content specifically looking for **reusable skills**. Do not just summarize the text. Extract the following:
*   **The Core Concept:** What is the overarching pattern, rule, or technique?
*   **Trigger Context:** When should you (the AI) use this skill in the future?
*   **Actionable Steps:** How exactly is it implemented?
*   **Code Examples:** Extract a minimal, working code snippet if applicable.

### Step 3: Skill Formatting
Format the extracted skill into a standardized Markdown structure:
```markdown
---
name:  [Clear, descriptive name of the skill max 64 characters]
description: [Short description max 1024 characters]
---
#SkillName

**When to use this:**
[Brief description of the context or prompt that should trigger this skill]

**Rules & Implementation:**
- [Actionable rule 1]
- [Actionable rule 2]

**Example:**
` ` `[language]
[Code snippet]
` ` `
Step 4: Write to Claude Memory
Using your file editing tools, save this newly formatted skill permanently to the project's memory:
Create a new file in the rules directory, naming it appropriately based on the skill (e.g., .claude/rules/[name-of-skill]-skill.md).
Note: If the .claude/rules/ directory does not exist, use your tools to create it first.
If the skill modifies a general project preference (rather than a specific technical skill), append it to CLAUDE.md instead.

Step 5: Acknowledgment
Respond to the user with a brief message confirming:
What source you successfully read.
The name of the reusable skill you extracted.
The exact file path where it was saved (e.g., "Saved to .claude/rules/zustand-setup-skill.md").