#!/usr/bin/env bash
# setup-claude-cloud.sh: install the workflow and its tools in a Linux cloud
# container. Install only — it never touches a project directory.

set -euo pipefail

WORKFLOW_REPO_URL="${WORKFLOW_REPO_URL:-https://github.com/AndrzejKebab/my-claude-workflow.git}"
WORKFLOW_BRANCH="${WORKFLOW_BRANCH:-kebab-unity}"
WORKFLOW_DIR="${WORKFLOW_DIR:-$HOME/my-claude-workflow}"

fail() {
    echo "Error: $*" >&2
    exit 1
}

command -v git >/dev/null 2>&1 || fail "Git is required."
command -v curl >/dev/null 2>&1 || fail "curl is required."
command -v claude >/dev/null 2>&1 || fail "Claude Code is required."

# graphify and uv install their executables here. A container starts without it
# on PATH, so everything installed by this script is reachable afterwards.
export PATH="$HOME/.local/bin:$PATH"
export UV_HTTP_TIMEOUT="${UV_HTTP_TIMEOUT:-300}"
hash -r 2>/dev/null || true

echo "Installing the shared workflow..."
if [[ -d "$WORKFLOW_DIR/.git" ]]; then
    CURRENT_BRANCH="$(git -C "$WORKFLOW_DIR" branch --show-current)"
    [[ "$CURRENT_BRANCH" == "$WORKFLOW_BRANCH" ]] || fail \
        "Workflow checkout is on '$CURRENT_BRANCH', expected '$WORKFLOW_BRANCH': $WORKFLOW_DIR"
    git -C "$WORKFLOW_DIR" pull --ff-only origin "$WORKFLOW_BRANCH"
elif [[ -e "$WORKFLOW_DIR" ]]; then
    fail "Workflow destination exists but is not a Git checkout: $WORKFLOW_DIR"
else
    git clone --branch "$WORKFLOW_BRANCH" --single-branch "$WORKFLOW_REPO_URL" "$WORKFLOW_DIR"
fi

# The installer owns the skills, instructions, hooks, and the tool installs
# (graphify, fff, semantica). Every prompt is pre-answered here because a
# container session has no terminal and no human to answer one.
"$WORKFLOW_DIR/install.sh" --action install --targets claude --tools all --yes

if command -v graphify >/dev/null 2>&1; then
    echo ""
    echo "Graphify: $(graphify --version 2>/dev/null | head -n 1)"
fi

echo ""
echo "Setup complete. Restart Claude Code so it loads FFF and the updated instructions."
