#!/usr/bin/env bash
# install.sh: Symlink skills, agents, and global config (CLAUDE.md + @imports) into ~/.claude/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"

echo "Installing my-claude-workflow..."
echo ""

link_dir() {
    local name="$1"
    local target="$SCRIPT_DIR/$name"
    local link="$CLAUDE_DIR/$name"

    if [[ -d "$link" && ! -L "$link" ]]; then
        local backup_name="${name}.bak.$(date +%Y%m%d-%H%M%S)"
        echo "Backing up existing $name to $CLAUDE_DIR/$backup_name"
        mv "$link" "$CLAUDE_DIR/$backup_name"
    elif [[ -L "$link" ]]; then
        echo "Removing existing symlink at $link"
        rm "$link"
    fi

    echo "Creating symlink: $link -> $target"
    ln -s "$target" "$link"
}

link_file() {
    local name="$1"
    local target="$SCRIPT_DIR/$name"
    local link="$CLAUDE_DIR/$name"

    if [[ -e "$link" && ! -L "$link" ]]; then
        local backup_name="${name}.bak.$(date +%Y%m%d-%H%M%S)"
        echo "Backing up existing $name to $CLAUDE_DIR/$backup_name"
        mv "$link" "$CLAUDE_DIR/$backup_name"
    elif [[ -L "$link" ]]; then
        echo "Removing existing symlink at $link"
        rm "$link"
    fi

    echo "Creating symlink: $link -> $target"
    ln -s "$target" "$link"
}

link_dir skills
link_dir agents

# Global config files — symlinked into ~/.claude so they travel with this repo.
# RTK.md is intentionally excluded: it is private (mode 600) and stays machine-local,
# so its @import in CLAUDE.md resolves only where it exists.
link_file CLAUDE.md
link_file negative-space-expanded.md
link_file FFF.md
link_file HARNESS.md
link_file VERIFY.md
link_file NONDUAL.md
link_file PROSE.md
link_file MODEL.md

# Make shell scripts executable
chmod +x "$SCRIPT_DIR/skills/claude-status/claude-status.sh"
chmod +x "$SCRIPT_DIR/skills/cdiff/cdiff.sh"
chmod +x "$SCRIPT_DIR/skills/enforce/enforce.sh"

# Make launcher scripts in bin/ executable
if [[ -d "$SCRIPT_DIR/bin" ]]; then
    chmod +x "$SCRIPT_DIR/bin"/*
fi

# Hooks. settings.json is NOT a symlink — Claude Code writes to it (permissions,
# model choice, MCP state), so replacing it with a link into this repo would make
# the repo churn on every session. Instead each hook this repo owns is MERGED in
# idempotently, keyed by its command string, leaving everything else untouched.
#
# Without this step a hook lives only in ~/.claude/settings.json, which no repo
# tracks and no machine rebuild restores.
install_hook() {
    local event="$1" matcher="$2" cmd="$3"
    python3 - "$event" "$matcher" "$cmd" <<'PY'
import json, os, sys
event, matcher, cmd = sys.argv[1:4]
p = os.path.expanduser('~/.claude/settings.json')
try:
    d = json.load(open(p))
except FileNotFoundError:
    d = {}
except json.JSONDecodeError as e:
    print(f"  settings.json is not valid JSON ({e}); refusing to touch it"); sys.exit(0)

entries = d.setdefault('hooks', {}).setdefault(event, [])
if any(h.get('command') == cmd for e in entries for h in e.get('hooks', [])):
    print(f"  {event}({matcher}) {cmd} — already installed"); sys.exit(0)

# Events that carry no tool name (UserPromptSubmit, SessionStart) take no matcher,
# and an empty one would be a field the CLI never reads.
entry = {"hooks": [{"type": "command", "command": cmd}]}
if matcher:
    entry = {"matcher": matcher, **entry}

# First, so a refusal short-circuits before other hooks do any work.
entries.insert(0, entry)
bak = p + '.bak'
if os.path.exists(p):
    with open(p) as f, open(bak, 'w') as g:
        g.write(f.read())
with open(p, 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write('\n')
print(f"  {event}({matcher}) {cmd} — installed (backup at {bak})")
PY
}

# statusLine is a single slot, not a list, so installing ours would silently
# destroy whatever is already there. Claim it only when it is free or already
# ours; otherwise say so and leave it alone.
install_statusline() {
    local cmd="$1"
    python3 - "$cmd" <<'PY'
import json, os, sys
cmd = sys.argv[1]
p = os.path.expanduser('~/.claude/settings.json')
try:
    d = json.load(open(p))
except FileNotFoundError:
    d = {}
except json.JSONDecodeError as e:
    print(f"  statusline — settings.json is not valid JSON ({e}); refusing to touch it"); sys.exit(0)

current = d.get('statusLine', {}).get('command')
if current == cmd:
    print(f"  {cmd} — already installed"); sys.exit(0)
if current:
    print(f"  statusline slot is taken by: {current}")
    print(f"  leaving it alone. To switch, set statusLine.command to {cmd}")
    sys.exit(0)

d['statusLine'] = {"type": "command", "command": cmd}
bak = p + '.bak'
if os.path.exists(p):
    with open(p) as f, open(bak, 'w') as g:
        g.write(f.read())
with open(p, 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write('\n')
print(f"  {cmd} — installed (backup at {bak})")
PY
}

# `unity` now collides with Unity Technologies' own unity-cli, which their
# installer drops at ~/.local/bin/unity (134 MB, a completely different tool).
# Whichever bin dir comes first on PATH wins, so a machine that orders them the
# other way silently sends every gate through the wrong binary — same args, no
# error, different semantics.
#
# unity-editor is the unambiguous name; `unity` is kept as a symlink for the
# call sites and docs that already use it. Bind ZORI_UNITY_BIN=unity-editor to
# be immune to PATH order entirely (the zori_skills unity plugin reads it).
echo ""
echo "Unity launcher:"
if resolved=$(command -v unity 2>/dev/null); then
    if [[ "$(readlink -f "$resolved")" == "$(readlink -f "$SCRIPT_DIR/bin/unity-editor")" ]]; then
        echo "  unity -> $resolved (ours) — OK"
    else
        echo "  WARNING: 'unity' resolves to $resolved, NOT this repo's launcher."
        echo "           That is probably Unity's unity-cli. Gates invoking bare"
        echo "           'unity' will run the wrong tool. Fix either by putting"
        echo "           $SCRIPT_DIR/bin earlier on PATH, or by exporting"
        echo "           ZORI_UNITY_BIN=unity-editor"
    fi
else
    echo "  WARNING: no 'unity' on PATH — add $SCRIPT_DIR/bin"
fi

# Per-project memories. Same reasoning as the hooks: they live under
# ~/.claude/projects/<slug>/memory/, which nothing tracks, so every memory ever
# written is one machine rebuild from gone. cc-memory-link moves them into
# memory/ here and symlinks them back; it copies-then-verifies before removing
# anything, and refuses to overwrite a differing file.
echo ""
echo "Memories:"
if [[ -x "$SCRIPT_DIR/bin/cc-memory-link" ]]; then
    "$SCRIPT_DIR/bin/cc-memory-link" | sed 's/^/  /'
else
    echo "  bin/cc-memory-link missing — skipped"
fi

echo ""
echo "Hooks:"
# Refuses no-op spin loops (`echo .`, `true`) and any command repeated 7+ times
# in 120s. See docs/no-op-spin.md for why. Fails open if jq is missing.
install_hook PreToolUse Bash cc-nospin

# Announces each 10% band of the context window as it is consumed. The built-in
# indicator stays hidden until the window is nearly full, and that threshold is
# not configurable. See docs/context-usage.md.
install_hook UserPromptSubmit "" cc-context-warn

echo ""
echo "Statusline:"
install_statusline cc-statusline

echo ""
echo "delegate, warden, diagnose-first and shipshape are no longer here — they live in"
echo "the zori marketplace (~/_dev/zori_skills) and install as a plugin:"
echo "  claude plugin marketplace add ~/_dev/zori_skills && claude plugin install delegate@zori"
echo ""
echo "Installation complete!"
echo ""
echo "Skills installed:"
ls -1 "$SCRIPT_DIR/skills" | sed 's/^/  - /'
echo ""
echo "Agents installed:"
ls -1 "$SCRIPT_DIR/agents" | sed 's/^/  - /'
echo ""
if [[ -d "$SCRIPT_DIR/bin" ]]; then
    echo "Launchers in bin/ (add $SCRIPT_DIR/bin to PATH):"
    ls -1 "$SCRIPT_DIR/bin" | sed 's/^/  - /'
    echo ""
    if ! echo ":$PATH:" | grep -q ":$SCRIPT_DIR/bin:"; then
        echo "  (PATH does NOT currently contain $SCRIPT_DIR/bin —"
        echo "   add it to ~/.bashrc_custom, ~/.zshrc_custom, ~/.config/fish/config.fish)"
        echo ""
    fi
fi
