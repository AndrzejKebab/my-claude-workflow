#!/usr/bin/env bash
# Read-only summary of local Claude Code sessions and their Git working trees.

set -euo pipefail

CLAUDE_DIR="${CLAUDE_HOME:-${HOME}/.claude}"
PROJECTS_DIR="${CLAUDE_DIR}/projects"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=python
else
    echo "claude-status requires Python to read Claude session metadata" >&2
    exit 2
fi

show_help() {
    cat <<'EOF'
Usage: claude-status [OPTIONS]

Show local Claude Code sessions and the current Git state of their recorded
working directories. No sessions or repositories are modified.

OPTIONS:
    --here       Show only sessions associated with the current directory
    --attention  Show sessions older than 24h whose working tree has changes
    -h, --help   Show this help
EOF
}

session_cwd() {
    "$PYTHON_CMD" - "$1" <<'PY'
import json
import sys

path = sys.argv[1]
cwd = None
try:
    with open(path, encoding="utf-8") as stream:
        for line in stream:
            try:
                item = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(item, dict):
                continue
            candidate = item.get("cwd")
            if not isinstance(candidate, str):
                data = item.get("data")
                candidate = data.get("cwd") if isinstance(data, dict) else None
            if isinstance(candidate, str) and candidate:
                cwd = candidate
except OSError:
    pass
if cwd:
    print(cwd)
PY
}

shell_path() {
    local path="$1"
    if command -v cygpath >/dev/null 2>&1 && [[ "$path" =~ ^[A-Za-z]:[\\/] ]]; then
        cygpath -u "$path"
    else
        printf '%s\n' "$path"
    fi
}

project_cwd() {
    local project_dir="$1" session cwd
    for session in "$project_dir"/*.jsonl; do
        [[ -f "$session" ]] || continue
        cwd="$(session_cwd "$session")"
        if [[ -n "$cwd" ]]; then
            printf '%s\n' "$cwd"
            return
        fi
    done
}

get_session_age_hours() {
    local session_file="$1" epoch_file epoch_now
    epoch_file=$(stat -c %Y "$session_file" 2>/dev/null || stat -f %m "$session_file" 2>/dev/null) || {
        echo 0
        return
    }
    epoch_now=$(date +%s)
    echo $(( (epoch_now - epoch_file) / 3600 ))
}

format_age() {
    local hours="$1"
    if (( hours < 1 )); then
        echo "<1h"
    elif (( hours < 24 )); then
        echo "${hours}h"
    else
        echo "$((hours / 24))d"
    fi
}

git_summary() {
    local path="$1" count
    if ! git -C "$path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "no-git"
        return
    fi
    count=$(git -C "$path" status --porcelain=v1 2>/dev/null | wc -l | tr -d ' ')
    if (( count == 0 )); then
        echo "clean"
    else
        echo "$count changes"
    fi
}

worktree_count() {
    local path="$1"
    git -C "$path" worktree list --porcelain 2>/dev/null | grep -c '^worktree ' || true
}

show_status() {
    local here_only="${1:-false}" project_dir project_path project_shell display_name
    local session session_id age status indicator total=0 attention=0 worktrees
    local current_shell
    current_shell="$(pwd -P)"

    [[ -d "$PROJECTS_DIR" ]] || { echo "No Claude projects found at $PROJECTS_DIR"; return 1; }
    echo
    echo "Active Claude Sessions"
    echo "═══════════════════════════════════════════════════════════════"
    echo

    for project_dir in "$PROJECTS_DIR"/*; do
        [[ -d "$project_dir" ]] || continue
        project_path="$(project_cwd "$project_dir")"
        [[ -n "$project_path" ]] || continue
        project_shell="$(shell_path "$project_path")"
        if [[ "$here_only" == true && "$project_shell" != "$current_shell" ]]; then
            continue
        fi
        display_name="$(basename "$project_shell")"
        status="$(git_summary "$project_shell")"
        worktrees="$(worktree_count "$project_shell")"
        printf "${BLUE}%-24s${NC} %s\n" "$display_name" "$project_path"

        for session in "$project_dir"/*.jsonl; do
            [[ -f "$session" ]] || continue
            session_id="$(basename "$session" .jsonl)"
            age="$(get_session_age_hours "$session")"
            indicator="${YELLOW}[IDLE]${NC}"
            if (( age > 24 )) && [[ "$status" != clean && "$status" != no-git ]]; then
                indicator="${RED}[ATTENTION]${NC}"
                attention=$((attention + 1))
            elif (( age < 2 )); then
                indicator="${GREEN}[ACTIVE]${NC}"
            fi
            printf "  ├─ %-12s %6s ago  %-14s %b\n" "${session_id:0:8}..." "$(format_age "$age")" "$status" "$indicator"
            total=$((total + 1))
        done
        if (( worktrees > 1 )); then
            printf "  └─ ${YELLOW}%d additional worktrees${NC}\n" "$((worktrees - 1))"
        fi
        echo
    done

    echo "─────────────────────────────────────────────────────────────────"
    printf "Total: ${BLUE}%d${NC} sessions\n" "$total"
    (( attention == 0 )) || printf "${YELLOW}%d session(s) need inspection; ownership is not implied${NC}\n" "$attention"
    echo
}

show_attention() {
    local project_dir project_path project_shell session age status found=0
    [[ -d "$PROJECTS_DIR" ]] || { echo "No Claude projects found at $PROJECTS_DIR"; return 1; }
    echo "Claude Sessions Requiring Attention"
    echo "═══════════════════════════════════════════════════════════════"
    for project_dir in "$PROJECTS_DIR"/*; do
        [[ -d "$project_dir" ]] || continue
        project_path="$(project_cwd "$project_dir")"
        [[ -n "$project_path" ]] || continue
        project_shell="$(shell_path "$project_path")"
        status="$(git_summary "$project_shell")"
        [[ "$status" != clean && "$status" != no-git ]] || continue
        for session in "$project_dir"/*.jsonl; do
            [[ -f "$session" ]] || continue
            age="$(get_session_age_hours "$session")"
            (( age > 24 )) || continue
            printf "%-16s %6s ago  %-14s %s\n" "$(basename "$session" .jsonl | cut -c1-12)..." "$(format_age "$age")" "$status" "$project_path"
            found=$((found + 1))
        done
    done
    (( found > 0 )) || echo "No sessions currently match the attention heuristic."
    echo
}

case "${1:-}" in
    "") show_status ;;
    --here) show_status true ;;
    --attention) show_attention ;;
    --clean)
        echo "--clean was renamed to --attention; no cleanup is performed" >&2
        show_attention
        ;;
    -h|--help|help) show_help ;;
    *) echo "Unknown option: $1" >&2; show_help; exit 1 ;;
esac
