# VOICE — write like someone on the team (binding)

Governs docs, code comments, commit messages and chat. [[PROSE.md]] governs how a sentence is
built; this governs who it is built for and how much of it there should be.

The reader is a developer who works on this code. They know what a cursor is, what a page is, and
why a list needs a count. Write to them, not to a stranger who has never seen software.

## Cut

- **Justification of the obvious.** A standard choice gets stated, not defended. Explaining why a
  paged list publishes `count` condescends to the reader and adds a sentence to misread.
- **Restated trivia.** Default values, env names already in `.env.example`, figures already in the
  code. One home per fact.
- **Self-narration.** Your own mistake, your own reasoning, "this used to be X" — none of it goes in
  a source file. The commit message, or nowhere.
- **Unverified causes.** "Tool Y ignores pattern Z" is a claim. Never commit one you have not tested;
  a matching precondition is not a proven effect.

## Register

Plain subject-verb-object — a sentence a colleague would say out loud in review. Real examples,
all shipped and all wrong:

- ✗ "Two histories hang off the read side, and they are one query asked of two tables."
  ✓ "`betHistory` and `wagerHistory` are the same paged query over two tables."
- ✗ "What is only true of wagers is the state: a wager enters its history when it closes."
  ✓ "A wager only enters its history when it closes."
- ✗ "a client handed a list with none of that cannot tell a history that ends from one that was cut
  off, and has no way to phrase 'more'."
  ✓ delete it — the reader already knows.

## Dose

Comments are one-liners. A longer one earns its place only by saying something the code cannot: a
constraint, a gotcha, a reason someone would otherwise "fix" it. Eight lines of comment on a
two-line change is always wrong, and so is a paragraph of prose where a clause would do.
