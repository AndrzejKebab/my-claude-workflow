#!/usr/bin/env bash
# install.sh: Install shared skills for Codex and the Claude-specific workflow into ~/.claude/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
CODEX_DIR="${CODEX_HOME:-${HOME}/.codex}"

echo "Installing my-claude-workflow..."
echo ""

link_dir() {
    local name="$1"
    local destination="$2"
    local target="${3:-$SCRIPT_DIR/$name}"
    local link="$destination/$name"

    if [[ -d "$link" && ! -L "$link" ]]; then
        local backup_name="${name}.bak.$(date +%Y%m%d-%H%M%S)"
        echo "Backing up existing $name to $destination/$backup_name"
        mv "$link" "$destination/$backup_name"
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

restore_legacy_claude_skills() {
    local skills_dir="$CLAUDE_DIR/skills"

    # Earlier installers linked the entire Claude skills directory to this
    # repository. Convert that layout before installing per-skill links.
    if [[ -L "$skills_dir" && "$(readlink -f "$skills_dir")" == "$(readlink -f "$SCRIPT_DIR/skills")" ]]; then
        echo "Replacing legacy Claude skills-directory symlink"
        rm "$skills_dir"
    fi

    mkdir -p "$skills_dir"

    # Preserve user-installed skills that an earlier whole-directory install
    # moved aside. Do not overwrite a current skill or one this repo owns.
    local backup skill name destination
    for backup in "$CLAUDE_DIR"/skills.bak.*; do
        [[ -d "$backup" ]] || continue
        for skill in "$backup"/*; do
            [[ -d "$skill" ]] || continue
            name="$(basename "$skill")"
            destination="$skills_dir/$name"
            if [[ ! -e "$destination" && ! -e "$SCRIPT_DIR/skills/$name" ]]; then
                echo "Restoring user skill: $name"
                cp -a "$skill" "$destination"
            fi
        done
    done
}

restore_legacy_claude_skills
mkdir -p "$CODEX_DIR/skills"

link_dir agents "$CLAUDE_DIR"

# Both Claude and Codex discover individual skill directories. Linking the
# repository's skills one at a time leaves skills installed from other sources
# in place instead of moving the whole directory into a timestamped backup.
install_skills() {
    local tool_name="$1"
    local destination="$2"

    echo ""
    echo "Installing skills for $tool_name..."
    for skill in "$SCRIPT_DIR"/skills/*; do
        [[ -d "$skill" ]] || continue
        link_dir "$(basename "$skill")" "$destination" "$skill"
    done
}

install_skills Claude "$CLAUDE_DIR/skills"
install_skills Codex "$CODEX_DIR/skills"

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

# The bare `unity` name may collide with an installed Unity CLI. Whichever PATH
# entry comes first wins, so automation should use an unambiguous command.
#
# unity-editor is the unambiguous name; `unity` is kept as a compatibility alias
# for existing interactive usage.
echo ""
echo "Unity launcher:"
if resolved=$(command -v unity 2>/dev/null); then
    if [[ "$(readlink -f "$resolved")" == "$(readlink -f "$SCRIPT_DIR/bin/unity-editor")" ]]; then
        echo "  unity -> $resolved (ours) — OK"
    else
        echo "  WARNING: 'unity' resolves to $resolved, NOT this repo's launcher."
        echo "           It may be Unity CLI or another launcher. Use"
        echo "           'unity-editor' explicitly for this repo's wrapper, or"
        echo "           put $SCRIPT_DIR/bin earlier on PATH for compatibility."
    fi
else
    echo "  WARNING: no 'unity' on PATH — add $SCRIPT_DIR/bin"
fi

echo ""
echo "Hooks:"
# Refuses no-op spin loops (`echo .`, `true`) and any command repeated 7+ times
# in 120s. See docs/no-op-spin.md for why. Fails open if jq is missing.
install_hook PreToolUse Bash cc-nospin

# Deterministic checks for rules that prose alone cannot guarantee. See
# docs/rule-compliance.md; cc-rule-audit can inspect Claude transcripts.
install_hook SessionStart "" cc-doctrine
install_hook Stop "" cc-no-hedge
install_hook PreToolUse "Read|Bash" cc-whole-file-reads
install_hook PostToolUse "Write|Edit" cc-comment-wall

# cc-context-warn, cc-cost-tick and cc-statusline are deliberately NOT wired any
# more. They grew up into cha-ching, which does the same job better: it chains to
# an existing statusline instead of taking the slot, reads cost and context from
# the payload rather than parsing transcripts, and rate-limits the bell so a
# tool-heavy turn lands as a few weighty numbers instead of a stream of small
# ones.
#
#   claude plugin marketplace add api-haus/cha-ching
#   claude plugin install cha-ching@cha-ching
#   /cha-ching:setup
#
# The scripts stay in bin/ because docs/context-usage.md explains its findings
# through them, and because they are the smallest working version of the idea —
# useful to read, and to fall back on. Wiring both would give you two statuslines
# fighting for one slot and two bells for one turn.

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
