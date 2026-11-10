# Before naming why work stalled, check that the bots ran at all

Symptom: A PR or issue shows no author or Manager activity for days and you are about to name a cause (Worker stuck, lane capacity, baseline moved)
Domain: fleet
Verified: 2026-11-10 at ad6e8eb5

## What to do

Grep each involved bot's logs/agent.log for API errors (402, 429, 'not processed') since the last activity before naming a cause. An outage is the owner's (provider or config), so say it first and give the other causes only for the time before it.

## Evidence

2026-11-10 long-PR batch blamed #431/#353/#133 stalls on baseline, lane and instrument; profiles/*/logs/agent.log show HTTP 402 Insufficient Balance (provider deepseek) for manager, reviewer, worker-1/3/4 from 2026-11-06 18:22, and Manager's session holds 86 'Your request was not processed' replies
