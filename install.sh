#!/usr/bin/env bash
# install.sh: Install shared skills for Codex and the Claude-specific workflow into ~/.claude/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"
CODEX_DIR="${CODEX_HOME:-${HOME}/.codex}"
INSTALL_STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_RETENTION="${WORKFLOW_BACKUP_RETENTION:-5}"

echo "Installing my-claude-workflow..."
echo ""

install_claude_item() {
    local name="$1"
    local target="${2:-$SCRIPT_DIR/$name}"
    local installed="$CLAUDE_DIR/$name"
    local manifest="$CLAUDE_DIR/my-claude-workflow-managed-items.txt"
    local backup_dir="$CLAUDE_DIR/backups/my-claude-workflow/$INSTALL_STAMP/claude-items"
    local legacy_backup legacy_name managed=0

    for legacy_backup in "$CLAUDE_DIR/${name}.bak."*; do
        [[ -e "$legacy_backup" ]] || continue
        mkdir -p "$backup_dir"
        legacy_name="$(basename "$legacy_backup")"
        echo "Moving legacy backup: $legacy_name"
        mv "$legacy_backup" "$backup_dir/$legacy_name"
    done

    if grep -Fxq "$name" "$manifest" 2>/dev/null; then
        managed=1
    elif [[ -L "$installed" && "$(readlink -f "$installed")" == "$(readlink -f "$target")" ]]; then
        managed=1
    elif [[ -f "$installed" && -f "$target" ]] && cmp -s "$installed" "$target"; then
        managed=1
    elif [[ -d "$installed" && -d "$target" ]] && diff -qr "$installed" "$target" >/dev/null 2>&1; then
        managed=1
    fi

    if [[ -e "$installed" || -L "$installed" ]]; then
        if [[ "$managed" -eq 1 ]]; then
            case "$installed" in
                "$CLAUDE_DIR"/*) rm -rf -- "$installed" ;;
                *) echo "Refusing to replace unexpected path: $installed" >&2; exit 1 ;;
            esac
            echo "Updating managed Claude item: $name"
        else
            mkdir -p "$backup_dir"
            echo "Backing up user Claude item: $name"
            mv "$installed" "$backup_dir/$name"
        fi
    else
        echo "Installing Claude item: $name"
    fi

    cp -a "$target" "$installed"
    printf '%s\n' "$name" >> "$CLAUDE_ITEMS_NEXT_MANIFEST"
}

install_codex_item() {
    local name="$1"
    local target="${2:-$SCRIPT_DIR/$name}"
    local installed="$CODEX_DIR/$name"
    local manifest="$CODEX_DIR/my-claude-workflow-managed-items.txt"
    local backup_dir="$CODEX_DIR/backups/my-claude-workflow/$INSTALL_STAMP/codex-items"
    local managed=0

    if grep -Fxq "$name" "$manifest" 2>/dev/null; then
        managed=1
    elif [[ -L "$installed" && "$(readlink -f "$installed")" == "$(readlink -f "$target")" ]]; then
        managed=1
    elif [[ -f "$installed" && -f "$target" ]] && cmp -s "$installed" "$target"; then
        managed=1
    elif [[ -d "$installed" && -d "$target" ]] && diff -qr "$installed" "$target" >/dev/null 2>&1; then
        managed=1
    fi

    if [[ -e "$installed" || -L "$installed" ]]; then
        if [[ "$managed" -eq 1 ]]; then
            case "$installed" in
                "$CODEX_DIR"/*) rm -rf -- "$installed" ;;
                *) echo "Refusing to replace unexpected path: $installed" >&2; exit 1 ;;
            esac
            echo "Updating managed Codex item: $name"
        else
            mkdir -p "$backup_dir"
            echo "Backing up user Codex item: $name"
            mv "$installed" "$backup_dir/$name"
        fi
    else
        echo "Installing Codex item: $name"
    fi

    cp -a "$target" "$installed"
    printf '%s\n' "$name" >> "$CODEX_ITEMS_NEXT_MANIFEST"
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

CLAUDE_ITEMS_MANIFEST="$CLAUDE_DIR/my-claude-workflow-managed-items.txt"
CLAUDE_ITEMS_NEXT_MANIFEST="$CLAUDE_ITEMS_MANIFEST.tmp"
: > "$CLAUDE_ITEMS_NEXT_MANIFEST"
install_claude_item agents

# Claude can import Markdown files, but Codex reads AGENTS.md directly without
# following Claude-style @imports. Assemble every binding shared guide into the
# AGENTS.md installed for both providers so their active instructions match.
COMBINED_AGENTS="$(mktemp)"
trap 'rm -f -- "$COMBINED_AGENTS"' EXIT
cat "$SCRIPT_DIR/AGENTS.md" > "$COMBINED_AGENTS"
for instruction_file in \
    FFF.md \
    MODEL.md \
    NONDUAL.md \
    PROSE.md \
    VERIFY.md \
    EDITING.md \
    VOICE.md \
    DISPATCH.md \
    HARNESS.md; do
    printf '\n\n' >> "$COMBINED_AGENTS"
    cat "$SCRIPT_DIR/$instruction_file" >> "$COMBINED_AGENTS"
done

# Install repository skills as managed copies. A manifest distinguishes copies
# owned by this installer from unrelated user skills with the same name.
# Backups live outside skills/ so neither Claude nor Codex discovers them.
install_skills() {
    local tool_name="$1"
    local tool_root="$2"
    local destination="$tool_root/skills"
    local manifest="$tool_root/my-claude-workflow-managed-skills.txt"
    local backup_dir="$tool_root/backups/my-claude-workflow/$INSTALL_STAMP/skills"
    local next_manifest="$manifest.tmp"
    local legacy_install=0
    local old_backup old_name skill name installed

    echo ""
    echo "Installing skills for $tool_name..."

    mkdir -p "$destination"

    # Older versions wrote name.bak.<timestamp> beside active skills. Move
    # those preserved originals out of the discovery directory. Their presence
    # also proves the matching active directory was installed by this script.
    for old_backup in "$destination"/*.bak.*; do
        [[ -e "$old_backup" ]] || continue
        mkdir -p "$backup_dir"
        old_name="$(basename "$old_backup")"
        echo "Moving legacy backup out of skills: $old_name"
        mv "$old_backup" "$backup_dir/$old_name"
        legacy_install=1
    done

    : > "$next_manifest"
    for skill in "$SCRIPT_DIR"/skills/*; do
        [[ -d "$skill" ]] || continue
        name="$(basename "$skill")"
        installed="$destination/$name"

        if [[ -e "$installed" || -L "$installed" ]]; then
            if [[ "$legacy_install" -eq 1 ]] || grep -Fxq "$name" "$manifest" 2>/dev/null; then
                case "$installed" in
                    "$destination"/*) rm -rf -- "$installed" ;;
                    *) echo "Refusing to replace unexpected path: $installed" >&2; exit 1 ;;
                esac
                echo "Updating managed skill: $name"
            elif [[ -L "$installed" && "$(readlink -f "$installed")" == "$(readlink -f "$skill")" ]]; then
                rm "$installed"
                echo "Updating legacy managed symlink: $name"
            else
                mkdir -p "$backup_dir"
                echo "Backing up user skill: $name"
                mv "$installed" "$backup_dir/$name"
            fi
        else
            echo "Installing skill: $name"
        fi

        cp -a "$skill" "$installed"
        printf '%s\n' "$name" >> "$next_manifest"
    done

    mv "$next_manifest" "$manifest"

    if [[ -d "$backup_dir" ]]; then
        echo "  Backups: $backup_dir"
    fi
}

install_skills Claude "$CLAUDE_DIR"
install_skills Codex "$CODEX_DIR"

# Global config files — installed as managed copies so this works consistently
# on Windows systems where Git Bash may copy instead of creating symlinks.
# RTK.md is intentionally excluded: it is private (mode 600) and stays machine-local,
# so its @import in CLAUDE.md resolves only where it exists.
install_claude_item CLAUDE.md
install_claude_item FFF.md
install_claude_item HARNESS.md
install_claude_item VERIFY.md
install_claude_item NONDUAL.md
install_claude_item PROSE.md
install_claude_item MODEL.md
install_claude_item AGENTS.md "$COMBINED_AGENTS"
install_claude_item docs
mv "$CLAUDE_ITEMS_NEXT_MANIFEST" "$CLAUDE_ITEMS_MANIFEST"

CODEX_ITEMS_MANIFEST="$CODEX_DIR/my-claude-workflow-managed-items.txt"
CODEX_ITEMS_NEXT_MANIFEST="$CODEX_ITEMS_MANIFEST.tmp"
: > "$CODEX_ITEMS_NEXT_MANIFEST"
install_codex_item AGENTS.md "$COMBINED_AGENTS"
install_codex_item docs
mv "$CODEX_ITEMS_NEXT_MANIFEST" "$CODEX_ITEMS_MANIFEST"

prune_workflow_backups() {
    local tool_root="$1"
    local backup_root="$tool_root/backups/my-claude-workflow"
    local old_backup

    [[ "$BACKUP_RETENTION" =~ ^[0-9]+$ ]] || {
        echo "WORKFLOW_BACKUP_RETENTION must be a non-negative integer" >&2
        exit 1
    }
    [[ -d "$backup_root" ]] || return

    while IFS= read -r old_backup; do
        [[ -n "$old_backup" ]] || continue
        case "$old_backup" in
            "$backup_root"/*) rm -rf -- "$old_backup" ;;
            *) echo "Refusing to prune unexpected path: $old_backup" >&2; exit 1 ;;
        esac
        echo "Pruned old workflow backup: $old_backup"
    done < <(find "$backup_root" -mindepth 1 -maxdepth 1 -type d -print | sort -r | tail -n "+$((BACKUP_RETENTION + 1))")
}

prune_workflow_backups "$CLAUDE_DIR"
prune_workflow_backups "$CODEX_DIR"

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
# Deferred tool install: graphify + FFF, cloud-only, backgrounded after launch
install_hook SessionStart "" "\"$SCRIPT_DIR/bin/install-tools.sh\""
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
