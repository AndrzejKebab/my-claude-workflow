# A defect counter needs a test on the legitimate shape it must not count, not only on the defect

Symptom: A census or invariant counter reads the same large number in every run, across different worlds
Domain: fleet
Verified: 2026-11-10 at ad6e8eb5

## What to do

Before trusting a counter, write two tests: the defect shape counts 1, and the closest legitimate shape (here a deep stack plus cap) counts 0. A constant reading across different inputs means the counter matches something the code does on purpose; read the writer before guessing at data.

## Evidence

PR #133 SNOW CENSUS twoLayers=5120 in three runs: SnowCover.cs:283-296 stacks full snow blocks plus a cap, and the census (:756-761) counts every snow cell, so every deep column read as 'two layers'; Worker-1 guessed Air in SnowLayers instead (Advisor, issuecomment-6755554588)
