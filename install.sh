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
