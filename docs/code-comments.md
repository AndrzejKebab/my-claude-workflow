# Code Comments

Prefer clear names and straightforward code. A comment is useful when it
preserves a non-obvious fact required to understand, use, or safely modify the
code.

## Useful comments

Keep comments short and local. Appropriate subjects include:

- ownership, disposal, or lifetime requirements;
- required ordering or synchronization;
- client, server, editor, or assembly boundaries;
- compiler, runtime, engine, or platform limitations;
- compatibility workarounds that look removable but must remain;
- measured performance invariants.

Public visibility alone does not justify XML documentation. Use API summaries,
remarks, examples, and cross-references only when they add information that the
signature and naming do not provide.

## Comments to remove

Do not add comments that:

- repeat the code in prose or explain it line by line;
- document every public member mechanically;
- duplicate architecture or data flow owned by project documentation;
- preserve development history or rejected approaches without a current
  constraint;
- describe future or hypothetical behavior as if it existed;
- expand into multi-paragraph design explanations.

Move architectural reasoning and meaningful trade-offs into project
documentation or a decision record. Leave a short pointer in code only when a
maintainer needs it at the modification site.

## Final check

Before finishing, remove or shorten every newly added comment that does not
preserve necessary information.

## Related documentation

- [Durable project knowledge](durable-memory.md)
- [Evidence-based review](evidence-based-review.md)
