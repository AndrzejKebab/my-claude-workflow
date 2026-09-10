# Backing up agent transcripts

Agent transcripts may contain useful decisions and evidence, but also source
code, command output, images, paths, personal data, and accidentally pasted
credentials. Treat a transcript archive as sensitive project data.

## Decide whether to back them up

Prefer promoting durable knowledge into repository documentation. Back up raw
transcripts only when their recovery or audit value justifies the privacy,
storage, and retention cost.

Claude Code and Codex use provider- and version-specific local storage. Discover
the active locations from the installed client's documentation or settings;
do not hard-code another user's home directory or assume both tools share a
format.

## Backup properties

A safe transcript backup should be:

- **Copy-oriented:** local deletion should not silently delete the archive.
- **Settled:** skip files still being written, or use a snapshot mechanism.
- **Encrypted:** protect data in transit and at rest with credentials stored
  outside the repository.
- **Excluded from Git:** transcripts are not normal source files.
- **Restorable:** test recovery into a separate scratch directory.
- **Retained deliberately:** define when old data expires.

## Windows example with `rclone`

Configure an encrypted or trusted remote interactively:

```powershell
rclone config
rclone listremotes
```

Dry-run a copy from the transcript directory discovered for the active client:

```powershell
$transcriptSource = 'C:\path\to\agent-transcripts'
$backupTarget = 'remote-name:agent-transcripts'

rclone copy $transcriptSource $backupTarget --min-age 15m --dry-run
```

After reviewing the dry run, repeat without `--dry-run`. Use Windows Task
Scheduler if recurring backup is wanted. Keep source, destination, retention,
and exclusions in a user-owned configuration outside this repository.

Do not use destructive mirroring by default. A sync operation can propagate a
local deletion to the archive.

## Restore test

Restore a small subset into a new temporary directory, never over the live
client state:

```powershell
$restoreTarget = Join-Path $env:TEMP 'agent-transcript-restore-test'
rclone copy 'remote-name:agent-transcripts' $restoreTarget --max-depth 1
```

Confirm that files open, expected metadata is present, and encrypted storage can
be recovered with the credentials available to the user.

## Repository scripts

`bin/cc-transcript-backup` and `share/systemd/` are legacy Claude Code/Linux
helpers. They are not installed as the Windows backup mechanism and should only
be used after reviewing their configured source, remote, and retention behavior.
