# Backing up the Claude Code transcripts

`~/.claude/projects` holds every session transcript this machine has produced —
6.9 GB across 114 project directories as of 2026-08-14. Nothing else records what
was decided, measured or tried in a session, and Claude Code never prunes it. It
is also the corpus `cc-rule-audit` measures against, so losing it loses the
baseline as well as the history.

`bin/cc-transcript-backup` pushes it to MEGA on a timer.

## Why not MEGAcmd

MEGAcmd (`mega-sync`, `mega-login`) is available as `megacmd` in the
`DEB_Arch_Extra` repo, and it is the wrong tool here for two reasons.

MEGAsync is already running and already syncing `~/_dev/my-claude-workflow`,
`~/_dev/_unity/ironvale`, `~/_dev/_unity/voxelmission` and `~/Documents/ARDOUR`.
MEGAcmd carries its own independent sync engine and its own session; two engines
on one account contend over the same remote state.

More importantly, a live sync is the wrong shape for this data. Transcripts are
append-only JSONL that grow while a session runs, and the largest here are 52 MB.
MEGA replaces a whole file when it changes, so a live sync re-uploads 52 MB on
every append. The goal is durability, not liveness.

## Why `copy` and not `sync`

`rclone sync` makes the destination match the source, which means a local
deletion propagates and the remote copy disappears. `rclone copy` only ever adds
and overwrites. Delete a project directory locally, or lose the disk, and the
remote still has it. "Never lost" is the literal behaviour of `copy`.

The cost is that the remote grows monotonically and never reclaims space from
deleted sessions. That is the intended trade.

## Why `--min-age 15m`

A transcript being appended to by a live session would upload, change, and upload
again. `--min-age` skips anything touched in the last 15 minutes, so each file
uploads once it has settled. An active session's transcript arrives on the next
run instead of the current one.

## Setup

The MEGA login is interactive and has to be done by hand:

```
rclone config
```

`n` for a new remote, name it `mega`, pick the `mega` backend, enter the account
email and password, decline the advanced config. Then confirm it works:

```
rclone about mega:
rclone lsd mega:
```

`rclone about` prints the quota — 6.9 GB needs to fit alongside whatever MEGAsync
is already storing. A free account is 20 GB total.

First run, without uploading anything:

```
cc-transcript-backup --dry-run
```

Then install the timer:

```
mkdir -p ~/.config/systemd/user
ln -sf ~/_dev/my-claude-workflow/share/systemd/cc-transcript-backup.{service,timer} \
       ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now cc-transcript-backup.timer
systemctl --user list-timers cc-transcript-backup.timer
```

The first run uploads the full 6.9 GB and will take as long as the uplink takes;
every run after that moves only what changed. Progress lands in
`~/.claude/transcript-backup.log`.

## Restoring

A backup nobody has restored is a hypothesis. Verify the round trip once, into a
scratch directory rather than over the live tree:

```
rclone copy mega:claude-transcripts/-home-midori /tmp/restore-test --max-depth 1
```

Full restore:

```
rclone copy mega:claude-transcripts ~/.claude/projects
```

## Knobs

Environment variables, all optional:

| Variable | Default |
|---|---|
| `CC_BACKUP_REMOTE` | `mega:claude-transcripts` |
| `CC_BACKUP_SRC` | `~/.claude/projects` |
| `CC_BACKUP_LOG` | `~/.claude/transcript-backup.log` |
| `CC_BACKUP_SETTLE` | `15m` |

To include the small configuration alongside the transcripts — `settings.json`,
`memory/`, `todos/` — point `CC_BACKUP_SRC` at `~/.claude` instead. That pulls in
`statsig/` and the shell snapshots too, which are churn with no recovery value,
so an `--exclude` list is the price of doing it.

## What is in these files

Everything typed into and read out of a session: source, file contents, command
output, and anything pasted, including a credential pasted by mistake. The
archive is as sensitive as the most sensitive thing that ever crossed a prompt.
Compression is not encryption — MEGA encrypts at rest under the account key, and
that account's password is what guards 6.9 GB of working history.
