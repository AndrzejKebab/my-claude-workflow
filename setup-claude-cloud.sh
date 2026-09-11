#!/usr/bin/env bash

set -euo pipefail

WORKFLOW_REPO_URL="${WORKFLOW_REPO_URL:-https://github.com/AndrzejKebab/my-claude-workflow.git}"
WORKFLOW_BRANCH="${WORKFLOW_BRANCH:-kebab-unity}"
WORKFLOW_DIR="${WORKFLOW_DIR:-$HOME/my-claude-workflow}"
PROJECT_DIR="${1:-$PWD}"

fail() {
    echo "Error: $*" >&2
    exit 1
}

command -v git >/dev/null 2>&1 || fail "Git is required."
command -v curl >/dev/null 2>&1 || fail "curl is required."
command -v claude >/dev/null 2>&1 || fail "Claude Code is required."
[[ -d "$PROJECT_DIR" ]] || fail "Project directory does not exist: $PROJECT_DIR"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

echo "Installing Graphify..."
export UV_HTTP_TIMEOUT="${UV_HTTP_TIMEOUT:-300}"

install_graphify() {
    if command -v uv >/dev/null 2>&1; then
        uv tool install --upgrade graphifyy
    elif command -v python3 >/dev/null 2>&1; then
        python3 -m pip install --user --upgrade --timeout 300 --retries 5 graphifyy
    else
        fail "uv or Python 3 is required to install Graphify."
    fi
}

for attempt in 1 2 3; do
    if install_graphify; then
        break
    fi
    [[ "$attempt" -lt 3 ]] || fail "Graphify installation failed after 3 attempts."
    echo "Graphify download failed; retrying attempt $((attempt + 1)) of 3..."
    sleep "$((attempt * 5))"
done

export PATH="$HOME/.local/bin:$PATH"
hash -r
command -v graphify >/dev/null 2>&1 || fail "Graphify installed but is not available on PATH."

echo "Installing FFF MCP server..."
FFF_INSTALLER="$(mktemp)"
trap 'rm -f -- "$FFF_INSTALLER"' EXIT
curl -fsSL https://raw.githubusercontent.com/dmtrKovalenko/fff/main/install-mcp.sh -o "$FFF_INSTALLER"
bash "$FFF_INSTALLER"

FFF_BINARY="$HOME/.local/bin/fff-mcp"
[[ -x "$FFF_BINARY" ]] || fail "FFF was not installed at $FFF_BINARY"

claude mcp remove -s user fff >/dev/null 2>&1 || true
claude mcp add -s user fff -- "$FFF_BINARY"

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

"$WORKFLOW_DIR/install.sh"

# Refresh after install.sh so the current Graphify package owns Claude's
# integration even when the workflow contains an older managed skill copy.
graphify install --platform claude

echo "Preparing Graphify for $PROJECT_DIR..."
(
    cd "$PROJECT_DIR"
    if [[ -f graphify-out/graph.json ]]; then
        graphify update .
    else
        graphify . --no-viz
    fi
    graphify hook install
)

echo "Setup complete. Restart Claude Code so it loads FFF and the updated instructions."
