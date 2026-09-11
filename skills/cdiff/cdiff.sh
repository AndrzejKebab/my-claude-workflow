#!/usr/bin/env bash
# cdiff — open a git diff for a scope (repository root or a submodule) in a
#         separate terminal window.
#
# Usage: cdiff [scope] [range]
#   scope  root | . | ''        → the superproject (default)
#          <submodule name|path> → that submodule (e.g. gameplay-package
#                                   or Packages/com.example.gameplay)
#   range  any git diff range   → default: the branch's own commits since its
#                                 rebase base (the commit it was last replayed
#                                 onto, from the branch reflog), else upstream,
#                                 else main...HEAD; working-tree diff if none
#
# Examples:
#   cdiff                              # superproject branch diff vs main
#   cdiff gameplay-package             # that submodule's branch diff vs main
#   cdiff root HEAD~3                  # last 3 commits at the root
#   cdiff gameplay-package d2a2e69..HEAD
#
# Run from anywhere inside the repo or a worktree; the scope resolves against
# that checkout's root and its .gitmodules.

set -euo pipefail

# ---- render mode: this branch runs inside the spawned terminal ------------
if [[ "${1:-}" == "--render" ]]; then
	export CDIFF_RENDER=1 CDIFF_DIR="$2" CDIFF_RANGE="$3"
	shift 3
fi

if [[ "${CDIFF_RENDER:-}" == "1" ]]; then
	cd "$CDIFF_DIR"
	printf '\033]0;cdiff %s %s\007' "${CDIFF_DIR##*/}" "${CDIFF_RANGE:-working-tree}"
	if git diff --quiet $CDIFF_RANGE 2>/dev/null; then
		printf '\n  no changes — %s [%s]\n\n' "${CDIFF_DIR##*/}" "${CDIFF_RANGE:-working tree}"
		read -rsn1 -p '  press any key to close… ' _ || true
		exit 0
	fi
	if command -v delta >/dev/null 2>&1; then
		git diff $CDIFF_RANGE | delta --paging=always
	else
		git -c color.ui=always diff $CDIFF_RANGE | less -R
	fi
	exit 0
fi

# ---- launch mode ----------------------------------------------------------
scope="${1:-root}"
range="${2:-}"

root="$(git rev-parse --show-toplevel)"

case "$scope" in
	root | . | "")
		dir="$root"
		;;
	*)
		# match a submodule by exact path or by basename against .gitmodules
		sub=""
		if [[ -f "$root/.gitmodules" ]]; then
			sub="$(git config --file "$root/.gitmodules" --get-regexp 'path$' |
				awk '{print $2}' |
				grep -E "(^|/)$(basename "$scope")$" | head -1 || true)"
		fi
		[[ -z "$sub" && -d "$root/$scope" ]] && sub="$scope"
		if [[ -z "$sub" ]]; then
			echo "cdiff: no submodule or path matching '$scope'" >&2
			echo "known submodules:" >&2
			git config --file "$root/.gitmodules" --get-regexp 'path$' 2>/dev/null |
				awk '{print "  "$2}' >&2
			exit 1
		fi
		dir="$root/$sub"
		;;
esac

# default_range DIR — the range showing DIR's branch-local commits: those added
# since the branch's rebase base, excluding whatever it was replayed on top of.
# A local `main` ref can be stale or on a divergent line, so the merge-base
# against it sweeps in commits the branch was rebased onto. Resolve, in order:
# the last rebase target recorded in the branch reflog; the upstream branch;
# then main. Empty output → caller falls back to the working-tree diff.
default_range() {
	local d="$1" head branch base up
	head="$(git -C "$d" rev-parse HEAD 2>/dev/null)" || return 0
	[[ -n "$head" ]] || return 0

	# (1) last rebase target from the branch reflog — the precise base the
	#     branch was replayed onto, which `main` may no longer reflect.
	branch="$(git -C "$d" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
	if [[ -n "$branch" ]]; then
		base="$(git -C "$d" reflog show "$branch" 2>/dev/null |
			sed -n 's/.*: rebase (finish): .* onto \([0-9a-f]\{7,40\}\)$/\1/p' |
			head -1 || true)"
		if [[ -n "$base" ]] &&
			git -C "$d" merge-base --is-ancestor "$base" "$head" 2>/dev/null &&
			[[ "$head" != "$(git -C "$d" rev-parse "$base" 2>/dev/null)" ]]; then
			printf '%s..HEAD' "$base"
			return 0
		fi
	fi

	# (2) upstream tracking branch, when one is set.
	up="$(git -C "$d" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true)"
	if [[ -n "$up" ]] && [[ "$head" != "$(git -C "$d" rev-parse "$up" 2>/dev/null)" ]]; then
		printf '%s...HEAD' "$up"
		return 0
	fi

	# (3) local main.
	if git -C "$d" rev-parse --verify -q main >/dev/null 2>&1 &&
		[[ "$head" != "$(git -C "$d" rev-parse main)" ]]; then
		printf 'main...HEAD'
	fi
}

if [[ -z "$range" ]]; then
	range="$(default_range "$dir")"
fi

self="$(realpath "$0")"
export CDIFF_RENDER=1 CDIFF_DIR="$dir" CDIFF_RANGE="$range"

case "$(uname -s)" in
MINGW* | MSYS* | CYGWIN*)
	if command -v wt.exe >/dev/null 2>&1; then
		bash_exe="$(cygpath -w "$(command -v bash)")"
		title="cdiff ${dir##*/}"
		wt.exe -w new nt --title "$title" "$bash_exe" -lc 'exec "$0" "$@"' \
			"$self" --render "$dir" "$range" >/dev/null 2>&1
		echo "cdiff: opened ${dir##*/} [${range:-working tree}] in Windows Terminal"
		exit 0
	fi
	;;
esac

if command -v ghostty >/dev/null 2>&1; then
	nohup ghostty -e "$self" >/dev/null 2>&1 &
elif command -v kitty >/dev/null 2>&1; then
	nohup kitty "$self" >/dev/null 2>&1 &
else
	exec "$self" # no GUI terminal — render inline in the calling terminal
fi
disown 2>/dev/null || true
echo "cdiff: opened ${dir##*/} [${range:-working tree}] in a new window"
