# Before asking the owner a spec question, check the accepted decision records; a question they answer is decided, not asked

Symptom: A Worker asks A or B on a contract (what a pass reads, what a stage waits on) and you are about to open a needs-owner question
Domain: fleet
Verified: 2026-11-10 at 1eb1ec8f

## What to do

Search .memory/decisions for the stage or pass named in the question and read its contract row. Then search for later records whose `Amends:` or `Follow-up to:` line names that record, and read those too: the newest one wins. If it answers the question, give that answer with the quote and send the Worker on; the owner sees any visible result at eye review. Only a gap or a conflict between records goes to the owner.

## Evidence

#164 A/B (does drainage read pre-erosion heights?) sat 7 days in needs-owner with Manager recommending B; D059 pass table row 5a says 'Input: pass 4 heights', so A was already decided and B kept a contract break (Advisor, 2026-11-10, issuecomment-6755550247). The Advisor then missed D064 (Amends: D059 pass 5b): droplet erosion retires, which made the question moot; the owner had to point it out (issuecomment-6755651678)
