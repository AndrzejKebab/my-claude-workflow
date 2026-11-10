---
name: fleet-discord
description: Use to ping the owner on Discord from a bot, in that bot's own thread with his mention - never by typing a channel id. Moved from bot-tools/discord.
---

# Fleet Discord

```
python F:/Programowanie/my-claude-workflow/skills/fleet-discord/scripts/ping_owner.py --as <profile> "Need your decision on #<n>: <question> -> <link>"
```

`scripts/ping_owner.py` reads the thread from the profile's `DISCORD_HOME_CHANNEL`, adds the owner's mention, and
sends through that profile's own account (`hermes -p <profile> send`). `--dry-run` prints the target. The old
`bot-tools/discord/ping_owner.py` is a shim. spawns: hermes.

Example run:

```
$ python ping_owner.py --as manager --dry-run "test line"
would send to discord:1555644542299013230 as manager: <@384732396806733846> test line
```
