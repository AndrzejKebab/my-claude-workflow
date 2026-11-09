---
name: fleet-seat
description: Use before a player build, a player run or Play mode in the Editor, and when a script exits 75 saying you do not hold the Unity seat. One bot at a time holds the seat; the owner's own Editor always comes first.
---

# Unity seat

The machine has one Unity licence seat and one box of memory, so player builds, player runs and Play-mode runs
happen one at a time. Compiles and EditMode tests do not need the seat.

```
python F:/Programowanie/my-claude-workflow/skills/fleet-seat/scripts/seat.py take --minutes 30 --purpose "client build for #431"
python .../seat.py renew --minutes 30     # before the lease runs out (it has 10 min grace)
python .../seat.py release                # as soon as the run is done
python .../seat.py status                 # holder, queue, whether the owner's Editor is open
```

`take` exits 0 when you hold the seat, 2 when you are queued (it says your place and who holds it): ask again
later. Order: the owner's Editor on the project first (no lease is given while it is open, and a lease
ends when he opens it: the watchdog stops your `fleet_run` runs with `stopped by owner`), then the Advisor,
then everyone else in the order they asked. The build and play scripts refuse with exit 75 unless you hold
the seat.

The caller is the bot whose Hermes profile runs the command. State is `Hermes/fleet-watchdog/seat.json`; the
owner's projects are listed in `seat-config.json` next to it. spawns: none. Tests:
`python -m unittest discover -s scripts/tests`.

Example run:

```
$ python seat.py status
{"holder": null, "expired": false, "queue": [], "owner_editor": false}
$ bash bot-tools/unity/editor_slot_build.sh ...
worker-1 does not hold the Unity seat. Take it first: seat.py take --minutes N --purpose "..."
(exit 75)
```
