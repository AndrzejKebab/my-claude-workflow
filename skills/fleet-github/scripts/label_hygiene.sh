#!/usr/bin/env bash
# Strip in-flight status labels from closed issues and PRs: REPO=owner/name label_hygiene.sh [--apply]

set -u
REPO="${REPO:?set REPO=owner/name}"
APPLY=0
[ "${1:-}" = "--apply" ] && APPLY=1

STATUS='^(worker:[1-5]|in-progress|ready|blocked|needs-owner|needs-human|waits-for-review|waits-for-final-review|waits-for-eye-review|in-review|ready-to-merge)$'

strip() {
    local kind="$1" number="$2" labels="$3"
    local keep=()
    IFS=',' read -ra names <<< "$labels"
    for name in "${names[@]}"; do
        [ -z "$name" ] && continue
        if [[ "$name" =~ $STATUS ]]; then
            echo "$kind #$number: -$name"
            if [ "$APPLY" = 1 ]; then
                if [ "$kind" = "PR" ]; then
                    gh pr edit "$number" --repo "$REPO" --remove-label "$name" >/dev/null 2>&1
                else
                    gh issue edit "$number" --repo "$REPO" --remove-label "$name" >/dev/null 2>&1
                fi
            fi
        fi
    done
}

while IFS='|' read -r number labels; do
    strip Issue "$number" "$labels"
done < <(gh issue list --repo "$REPO" --state closed --limit 100 \
            --json number,labels --jq '.[]|"\(.number)|\([.labels[].name]|join(","))"')

while IFS='|' read -r number labels; do
    strip PR "$number" "$labels"
done < <(gh pr list --repo "$REPO" --state closed --limit 100 \
            --json number,labels --jq '.[]|"\(.number)|\([.labels[].name]|join(","))"')

[ "$APPLY" = 1 ] || echo "(report only — re-run with --apply to remove)"
