# VERIFY — how a gate earns trust

## Prohibited: sabotage arms / biters

Do **not** author, regenerate, or extend **sabotage arms** — patches that deliberately break the
subject so a gate can be watched going red, recorded as sensitivity rows. Same for any "biter" /
mutation-arm variant of the idea. This is a prohibition on the workflow, not a judgement on a
specific repo's existing arms.

Why it is banned rather than merely discouraged: the arms are a second, unbuilt copy of the subject
that has to be kept in sync with it by hand. They rot silently against the real code, they cost more
tokens than the feature they guard, and a rotted arm reports *demonstrated-red* for a gate nothing
has actually tested.

## Do this instead: TDD

Make the test **red first**, then implement the actual feature or fix that turns it green.

A test observed failing — for the right reason, before the code existed — has already proved its own
sensitivity. That is the whole thing the sabotage arm was buying, obtained as a side effect of
writing the test in the right order, at a fraction of the cost and with nothing left over to rot.

## Graphics programming: make it work first

When the work is graphics — shaders, meshing, materials, lighting, anything whose output is looked
at — **make the thing work first**. Get it on screen, look at it, confirm it renders. Gate it
afterwards.

Do not spend the budget standing up verification scaffolding around an image that does not exist
yet. The channel a gate is convenient to read is reliably not the channel the eye judges, so a
threshold invented before the first look is measuring the wrong thing.
