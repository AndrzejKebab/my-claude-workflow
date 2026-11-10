# A refused command is a config fact, not an ownership rule

Symptom: a command is refused by approvals.deny and you are about to say the work belongs to someone else by rule
Domain: fleet
Verified: pending

## What to do

Before you write 'X is mine (or yours) by rule', quote the rule: its file and line. A refusal from approvals.deny only says the config refuses it. When the refusal contradicts a skill (fleet-seat lets Workers build with the seat), that is a config gap: send it to the Advisor with both quotes in this turn, and do not take the work over. Check a machine fact (an installed Editor, a running process) with a command before you state it.

## Evidence

2026-11-10 Manager told Worker-5 and the owner 'player builds are mine by rule' and 'the a12 editor is gone'. No SOUL or skill says so: fleet-seat and decision #35 give Workers the seat for player builds, the editor_slot_build.sh deny entries were a rollout leftover, and F:/Unity Editors/7000.0.0a12 was still installed. Worker-5's build waited behind Manager for hours and nobody told the Advisor.
