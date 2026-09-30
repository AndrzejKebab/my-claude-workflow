#!/usr/bin/env bash
# install.sh: install or update the shared workflow for each AI CLI on this machine.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_STAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_RETENTION="${WORKFLOW_BACKUP_RETENTION:-5}"

CLAUDE_DIR="${HOME}/.claude"
CODEX_DIR="${CODEX_HOME:-${HOME}/.codex}"
HERMES_DIR="${HERMES_HOME:-${HOME}/.hermes}"

ALL_TARGETS=(claude codex hermes)

# Tools this workflow installs once per machine, then registers per agent.
ALL_TOOLS=(graphify fff semantica)

# Skills whose on-disk copy another product owns and refreshes. Replacing one
# would desync its version marker, so this workflow leaves those alone.
HERMES_UNMANAGED_SKILLS=(graphify)

ACTION=""
TARGETS=""
TOOLS=""
# "none" and "not specified" both leave the list empty, so the two are tracked
# separately: only an unset list may be filled from the defaults.
TARGETS_GIVEN=0
TOOLS_GIVEN=0
TOOLS_FAILED=""
ASSUME_YES=0
INTERACTIVE=0
COMBINED_AGENTS=""

usage() {
    cat <<'USAGE'
Usage: install.sh [options]

On a terminal with no options, the installer asks what to do and which AI CLIs
to touch. With options it runs unattended.

  --action install|update   install (default), or refresh only what is installed
  --targets LIST            claude,codex,hermes or "all" (default: detected)
  --tools LIST              graphify,fff,semantica or "all"/"none" (default: all)
  --no-tools                shorthand for --tools none
  --yes                     accept every default and skip the prompts
  -h, --help                show this help

An update skips a selected tool that carries no managed manifest, because there
is nothing of this workflow's to refresh there yet. Use install the first time.

Tools are installed once per machine and then registered with each selected
agent. graphify registers itself with claude, codex and hermes. fff is
registered as an MCP server. semantica needs Python < 3.14, so it is installed
into its own virtual environment; registering its MCP server needs a project
graph path and stays a per-project step.

Environment:
  CODEX_HOME                Codex configuration root (default ~/.codex)
  HERMES_HOME               Hermes configuration root (default ~/.hermes)
  SEMANTICA_VENV            Semantica virtual environment
                            (default ~/.local/share/semantica/venv)
  UV_HTTP_TIMEOUT           graphify download timeout (default 300)
  WORKFLOW_BACKUP_RETENTION retained install backup sets (default 5)
USAGE
}

target_label() {
    case "$1" in
        claude) echo "Claude" ;;
        codex) echo "Codex" ;;
        hermes) echo "Hermes" ;;
        *) echo "$1" ;;
    esac
}

target_root() {
    case "$1" in
        claude) echo "$CLAUDE_DIR" ;;
        codex) echo "$CODEX_DIR" ;;
        hermes) echo "$HERMES_DIR" ;;
        *) echo "" ;;
    esac
}

target_root_var() {
    case "$1" in
        claude) echo "HOME" ;;
        codex) echo "CODEX_HOME" ;;
        hermes) echo "HERMES_HOME" ;;
        *) echo "HOME" ;;
    esac
}

# A file that proves the configuration root belongs to a real install.
target_marker() {
    local root="$1"
    case "$2" in
        claude) echo "$root/settings.json" ;;
        codex) echo "$root/config.toml" ;;
        hermes) echo "$root/config.yaml" ;;
    esac
}

target_command() {
    case "$1" in
        claude) echo "claude" ;;
        codex) echo "codex" ;;
        hermes) echo "hermes" ;;
    esac
}

target_detected() {
    local key="$1" root
    root="$(target_root "$key")"
    [[ -e "$(target_marker "$root" "$key")" ]] && return 0
    command -v "$(target_command "$key")" >/dev/null 2>&1
}

target_manifest() {
    echo "$(target_root "$1")/my-claude-workflow-managed-items.txt"
}

target_installed() {
    [[ -f "$(target_manifest "$1")" ]]
}

target_state() {
    if target_installed "$1"; then
        echo "installed"
    elif target_detected "$1"; then
        echo "detected"
    else
        echo "not found"
    fi
}

validate_target() {
    local candidate="$1" known
    for known in "${ALL_TARGETS[@]}"; do
        [[ "$candidate" == "$known" ]] && return 0
    done
    echo "Unknown target: $candidate (known: ${ALL_TARGETS[*]})" >&2
    exit 1
}

# Resolve a comma-separated selection against a known list. "all" and "none"
# are accepted; anything else is validated and normalized to a space list.
normalize_selection() {
    local raw="$1" noun="$2"
    shift 2
    local known_names=("$@")
    local parts part normalized=""

    if [[ "$raw" == "all" ]]; then
        echo "${known_names[*]}"
        return 0
    fi
    if [[ "$raw" == "none" ]]; then
        echo ""
        return 0
    fi

    IFS=',' read -r -a parts <<< "$raw"
    for part in "${parts[@]}"; do
        part="${part// /}"
        [[ -n "$part" ]] || continue
        local candidate ok=0
        for candidate in "${known_names[@]}"; do
            [[ "$part" == "$candidate" ]] && ok=1
        done
        if [[ "$ok" -eq 0 ]]; then
            echo "Unknown $noun: $part (known: ${known_names[*]})" >&2
            exit 1
        fi
        normalized="${normalized:+$normalized }$part"
    done
    [[ -n "$normalized" ]] || { echo "--$noun selected nothing" >&2; exit 1; }
    echo "$normalized"
}

selected_in() {
    [[ " $TARGETS " == *" $1 "* ]]
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --action)
                [[ $# -ge 2 ]] || { echo "--action needs a value" >&2; exit 1; }
                ACTION="$2"
                shift 2
                ;;
            --targets)
                [[ $# -ge 2 ]] || { echo "--targets needs a value" >&2; exit 1; }
                TARGETS="$2"
                TARGETS_GIVEN=1
                shift 2
                ;;
            --tools)
                [[ $# -ge 2 ]] || { echo "--tools needs a value" >&2; exit 1; }
                TOOLS="$2"
                TOOLS_GIVEN=1
                shift 2
                ;;
            --no-tools)
                TOOLS="none"
                TOOLS_GIVEN=1
                shift
                ;;
            --yes|-y)
                ASSUME_YES=1
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1" >&2
                usage >&2
                exit 1
                ;;
        esac
    done

    if [[ -n "$ACTION" && "$ACTION" != "install" && "$ACTION" != "update" ]]; then
        echo "--action must be install or update, not '$ACTION'" >&2
        exit 1
    fi

    [[ -n "$TARGETS" ]] || TARGETS=""
    if [[ -n "$TARGETS" ]]; then
        TARGETS="$(normalize_selection "$TARGETS" target "${ALL_TARGETS[@]}")"
    fi
    if [[ -n "$TOOLS" ]]; then
        TOOLS="$(normalize_selection "$TOOLS" tool "${ALL_TOOLS[@]}")"
    fi
}

# A first install offers every detected tool; an update offers only what this
# workflow already installed.
default_targets() {
    local action="$1" key selected=""
    for key in "${ALL_TARGETS[@]}"; do
        if [[ "$action" == "update" ]]; then
            target_installed "$key" || continue
        else
            target_detected "$key" || continue
        fi
        selected="${selected:+$selected }$key"
    done
    if [[ -z "$selected" && "$action" == "install" ]]; then
        selected="${ALL_TARGETS[*]}"
    fi
    echo "$selected"
}

prompt_action() {
    local reply
    echo "What do you want to do?" >&2
    echo "  1) Install   create or refresh the selected tools" >&2
    echo "  2) Update    refresh only what this workflow already installed" >&2
    printf 'Choice [1]: ' >&2
    read -r reply < /dev/tty || reply=""
    case "${reply:-1}" in
        1|install|i) ACTION="install" ;;
        2|update|u) ACTION="update" ;;
        *) echo "Unrecognized choice: $reply" >&2; exit 1 ;;
    esac
}

prompt_targets() {
    local action="$1" key root index=0 reply choice part chosen="" hint
    local -a keys=()
    local -a preselect=()
    local -a parts=()

    echo "" >&2
    echo "$action — select the tools:" >&2
    for key in "${ALL_TARGETS[@]}"; do
        index=$((index + 1))
        keys+=("$key")
        root="$(target_root "$key")"

        if [[ "$action" == "update" ]]; then
            if target_installed "$key"; then
                preselect+=("$index")
                printf '  [x] %d) %-7s %-40s %s\n' "$index" "$(target_label "$key")" "$root" "$(target_state "$key")" >&2
            else
                printf '  [ ] %d) %-7s %-40s %s\n' "$index" "$(target_label "$key")" "$root" "$(target_state "$key")" >&2
            fi
        elif target_detected "$key"; then
            preselect+=("$index")
            printf '  [x] %d) %-7s %-40s %s\n' "$index" "$(target_label "$key")" "$root" "$(target_state "$key")" >&2
        else
            printf '  [ ] %d) %-7s %-40s %s\n' "$index" "$(target_label "$key")" "$root" "$(target_state "$key")" >&2
        fi
    done

    if [[ ${#preselect[@]} -eq 0 ]]; then
        hint="all"
        echo "  (nothing preselected — the default installs all three)" >&2
    else
        hint="$(IFS=,; echo "${preselect[*]}")"
    fi

    printf 'Select targets (1,3 — or "all" / "none") [%s]: ' "$hint" >&2
    read -r reply < /dev/tty || reply=""
    choice="${reply:-$hint}"

    case "$choice" in
        all) chosen="${ALL_TARGETS[*]}" ;;
        none) chosen="" ;;
        *)
            IFS=',' read -r -a parts <<< "$choice"
            for part in "${parts[@]}"; do
                part="${part// /}"
                [[ -n "$part" ]] || continue
                [[ "$part" =~ ^[0-9]+$ ]] || { echo "Not a number: $part" >&2; exit 1; }
                [[ "$part" -ge 1 && "$part" -le ${#keys[@]} ]] || { echo "Out of range: $part" >&2; exit 1; }
                chosen="${chosen:+$chosen }${keys[$((part - 1))]}"
            done
            ;;
    esac

    TARGETS="$chosen"
}

prompt_tools() {
    local reply
    printf 'Install the shared tools (%s)? [Y/n]: ' "${ALL_TOOLS[*]}" >&2
    read -r reply < /dev/tty || reply=""
    case "${reply:-y}" in
        y|Y|yes|"") TOOLS="${ALL_TOOLS[*]}" ;;
        n|N|no) TOOLS="" ;;
        *) TOOLS="$(normalize_selection "$reply" tool "${ALL_TOOLS[@]}")" ;;
    esac
}

# Claude can import Markdown files, but Codex and Hermes take a single guide
# without following Claude-style imports. Assemble every binding shared module
# once so the installed instructions match across tools.
build_combined_agents() {
    local instruction_file
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
}

# Install or refresh one item under a tool's configuration root, recording what
# this workflow owns in that root's manifest.
install_item() {
    local root="$1" tool="$2" name="$3"
    local target="${4:-$SCRIPT_DIR/$name}"
    local installed="$root/$name"
    local manifest="$root/my-claude-workflow-managed-items.txt"
    local next_manifest="$manifest.tmp"
    local backup_dir="$root/backups/my-claude-workflow/$INSTALL_STAMP/items"
    local legacy_backup legacy_name managed=0

    for legacy_backup in "$root/${name}.bak."*; do
        [[ -e "$legacy_backup" ]] || continue
        mkdir -p "$backup_dir"
        legacy_name="$(basename "$legacy_backup")"
        echo "Moving legacy backup: $legacy_name"
        mv "$legacy_backup" "$backup_dir/$legacy_name"
    done

    if [[ -f "$manifest" ]] && grep -Fxq "$name" "$manifest"; then
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
                "$root"/*) rm -rf -- "$installed" ;;
                *) echo "Refusing to replace unexpected path: $installed" >&2; exit 1 ;;
            esac
            echo "Updating managed $tool item: $name"
        else
            mkdir -p "$backup_dir"
            echo "Backing up user $tool item: $name"
            mv "$installed" "$backup_dir/$name"
        fi
    else
        echo "Installing $tool item: $name"
    fi

    cp -a "$target" "$installed"
    printf '%s\n' "$name" >> "$next_manifest"
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

# Install repository skills as managed copies. A manifest distinguishes copies
# owned by this installer from unrelated user skills with the same name.
# Backups live outside skills/ so no tool discovers them.
# Names passed after the root are skipped: another product owns those copies.
install_skills() {
    local tool_name="$1"
    local tool_root="$2"
    shift 2
    local skips=" $* "
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

        if [[ "$skips" == *" $name "* ]]; then
            echo "Skipping $tool_name skill another product owns: $name"
            continue
        fi

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

install_claude_items() {
    local manifest="$CLAUDE_DIR/my-claude-workflow-managed-items.txt"

    : > "$manifest.tmp"
    install_item "$CLAUDE_DIR" Claude agents

    # Global config files, installed as managed copies so this works on Windows
    # where Git Bash may copy instead of creating symlinks.
    # RTK.md is intentionally excluded: it is private (mode 600) and stays
    # machine-local, so its @import in CLAUDE.md resolves only where it exists.
    install_item "$CLAUDE_DIR" Claude CLAUDE.md
    install_item "$CLAUDE_DIR" Claude FFF.md
    install_item "$CLAUDE_DIR" Claude HARNESS.md
    install_item "$CLAUDE_DIR" Claude VERIFY.md
    install_item "$CLAUDE_DIR" Claude NONDUAL.md
    install_item "$CLAUDE_DIR" Claude PROSE.md
    install_item "$CLAUDE_DIR" Claude MODEL.md
    install_item "$CLAUDE_DIR" Claude AGENTS.md "$COMBINED_AGENTS"
    install_item "$CLAUDE_DIR" Claude docs

    mv "$manifest.tmp" "$manifest"
}

install_codex_items() {
    local manifest="$CODEX_DIR/my-claude-workflow-managed-items.txt"

    : > "$manifest.tmp"
    install_item "$CODEX_DIR" Codex AGENTS.md "$COMBINED_AGENTS"
    install_item "$CODEX_DIR" Codex docs
    mv "$manifest.tmp" "$manifest"
}

# Hermes loads project rules from the working directory and warns against a
# home-level AGENTS.md, so the shared guide ships as a loadable skill instead.
install_hermes_items() {
    local manifest="$HERMES_DIR/my-claude-workflow-managed-items.txt"
    local generated
    generated="$(mktemp -d)"
    mkdir -p "$generated/references"

    {
        cat <<'FRONTMATTER'
---
name: my-claude-workflow
description: "Use for the shared cross-project agent rules: scope, evidence, verification, comment discipline, reporting, and commit expectations. Applies to every project on this machine."
---

FRONTMATTER
        cat "$COMBINED_AGENTS"
    } > "$generated/SKILL.md"

    cp -a "$SCRIPT_DIR/docs" "$generated/references/docs"

    : > "$manifest.tmp"
    install_item "$HERMES_DIR" Hermes skills/my-claude-workflow "$generated"
    mv "$manifest.tmp" "$manifest"

    rm -rf -- "$generated"
}

# ── required tools ───────────────────────────────────────────────────────
# Installed once per machine, then registered with each selected agent.

semantica_venv() {
    echo "${SEMANTICA_VENV:-$HOME/.local/share/semantica/venv}"
}

# Windows virtual environments use Scripts/, Unix-like systems use bin/.
# Assuming one of them is why an environment built on one machine cannot be
# reused on the other, so the layout is detected rather than assumed.
venv_bin_dir() {
    local venv="$1"
    if [[ -d "$venv/bin" ]]; then
        echo "$venv/bin"
    else
        echo "$venv/Scripts"
    fi
}

# Semantica requires Python < 3.14, which a system 3.14 cannot satisfy.
find_python_below_314() {
    local candidate release
    for candidate in python3.13 python3.12 python3.11 python3.10 python3.9 python3; do
        command -v "$candidate" >/dev/null 2>&1 || continue
        release="$("$candidate" -c 'import sys; print(sys.version_info[0] * 100 + sys.version_info[1])' 2>/dev/null)" || continue
        [[ -n "$release" ]] || continue
        if (( release < 314 )); then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

install_graphify() {
    export UV_HTTP_TIMEOUT="${UV_HTTP_TIMEOUT:-300}"
    local attempt
    for attempt in 1 2 3; do
        if command -v uv >/dev/null 2>&1; then
            if uv tool install --upgrade graphifyy; then
                return 0
            fi
        elif command -v python3 >/dev/null 2>&1; then
            if python3 -m pip install --user --upgrade --timeout 300 --retries 5 graphifyy; then
                return 0
            fi
        else
            echo "  graphify: uv or Python 3 is required." >&2
            return 1
        fi
        if (( attempt < 3 )); then
            echo "  graphify: attempt $attempt failed; retrying."
            sleep "$((attempt * 5))"
        fi
    done
    return 1
}

install_fff() {
    local bin="${FFF_BIN:-$HOME/.local/bin/fff-mcp}"
    local installer
    if [[ -x "$bin" ]]; then
        echo "  fff: present at $bin"
        return 0
    fi
    if ! command -v curl >/dev/null 2>&1; then
        echo "  fff: curl is required." >&2
        return 1
    fi
    installer="$(mktemp)"
    if ! curl -fsSL https://raw.githubusercontent.com/dmtrKovalenko/fff/main/install-mcp.sh -o "$installer"; then
        rm -f -- "$installer"
        echo "  fff: could not download the upstream installer." >&2
        return 1
    fi
    if ! bash "$installer"; then
        rm -f -- "$installer"
        echo "  fff: the upstream installer failed." >&2
        return 1
    fi
    rm -f -- "$installer"
    if [[ ! -x "$bin" ]]; then
        echo "  fff: expected $bin after install." >&2
        return 1
    fi
    echo "  fff: installed $bin"
}

install_semantica() {
    local venv bin py
    venv="$(semantica_venv)"
    bin="$(venv_bin_dir "$venv")"
    if [[ -x "$bin/semantica-mcp" ]]; then
        echo "  semantica: present at $venv"
        return 0
    fi
    if ! py="$(find_python_below_314)"; then
        echo "  semantica: requires Python < 3.14 and none is on PATH." >&2
        return 1
    fi
    echo "  semantica: creating $venv with $py"
    if ! "$py" -m venv "$venv"; then
        echo "  semantica: could not create the virtual environment." >&2
        return 1
    fi
    bin="$(venv_bin_dir "$venv")"
    if ! "$bin/pip" install --upgrade --quiet semantica; then
        echo "  semantica: pip install failed." >&2
        return 1
    fi
    echo "  semantica: installed $bin/semantica-mcp"
}

# graphify owns its own skill and hook registration per agent, so it is told
# which agents to attach to rather than having copies placed by this script.
register_graphify() {
    local key
    for key in $TARGETS; do
        if ! command -v "$key" >/dev/null 2>&1; then
            echo "  graphify: skipping $key (not on PATH)"
            continue
        fi
        # graphify resolves the Hermes home itself. Observed on Windows: it
        # writes the skill to the Hermes install root, not to HERMES_HOME.
        if [[ "$key" == "hermes" ]] && [[ "$(readlink -f "$HERMES_DIR")" != "$(readlink -f "$HOME/.hermes")" ]]; then
            echo "  graphify: note — HERMES_HOME is $HERMES_DIR, and graphify"
            echo "            places its skill outside it. Verify afterwards."
        fi
        echo "  graphify: registering with $key"
        if ! graphify install --platform "$key"; then
            echo "  graphify: registration with $key failed." >&2
        fi
    done
}

register_fff() {
    local bin="${FFF_BIN:-$HOME/.local/bin/fff-mcp}"
    local key
    for key in $TARGETS; do
        if ! command -v "$key" >/dev/null 2>&1; then
            echo "  fff: skipping $key (not on PATH)"
            continue
        fi
        case "$key" in
            claude)
                claude mcp remove -s user fff >/dev/null 2>&1 || true
                if ! claude mcp add -s user fff -- "$bin"; then
                    echo "  fff: Claude registration failed." >&2
                fi
                ;;
            codex)
                codex mcp remove fff >/dev/null 2>&1 || true
                if ! codex mcp add fff -- "$bin"; then
                    echo "  fff: Codex registration failed." >&2
                fi
                ;;
            hermes)
                hermes mcp remove fff >/dev/null 2>&1 || true
                if ! hermes mcp add fff --command "$bin"; then
                    echo "  fff: Hermes registration failed." >&2
                fi
                ;;
        esac
    done
}

# Semantica's MCP server needs a project graph path, so this installs the
# executable and leaves registration with the project that owns the graph.
report_semantica() {
    local bin
    bin="$(venv_bin_dir "$(semantica_venv)")"
    echo "  semantica: register per project with $bin/semantica-mcp"
    echo "             and SEMANTICA_KG_PATH pointing at that project's graph."
}

install_one_tool() {
    case "$1" in
        graphify)
            install_graphify || return 1
            register_graphify
            ;;
        fff)
            install_fff || return 1
            register_fff
            ;;
        semantica)
            install_semantica || return 1
            report_semantica
            ;;
    esac
}

# A failed tool is reported, not fatal: a failed download must not undo an
# install of the workflow itself that already succeeded.
install_tools() {
    local tool
    echo ""
    echo "Tools:"
    for tool in $TOOLS; do
        echo "-- $tool"
        if ! install_one_tool "$tool"; then
            TOOLS_FAILED="${TOOLS_FAILED:+$TOOLS_FAILED }$tool"
        fi
    done
}

install_target() {
    case "$1" in
        claude)
            restore_legacy_claude_skills
            install_skills Claude "$CLAUDE_DIR"
            install_claude_items
            ;;
        codex)
            mkdir -p "$CODEX_DIR/skills"
            install_skills Codex "$CODEX_DIR"
            install_codex_items
            ;;
        hermes)
            mkdir -p "$HERMES_DIR/skills"
            install_skills Hermes "$HERMES_DIR" "${HERMES_UNMANAGED_SKILLS[@]}"
            install_hermes_items
            ;;
    esac
}

prune_workflow_backups() {
    local tool_root="$1"
    local backup_root="$tool_root/backups/my-claude-workflow"
    local old_backup

    [[ "$BACKUP_RETENTION" =~ ^[0-9]+$ ]] || {
        echo "WORKFLOW_BACKUP_RETENTION must be a non-negative integer" >&2
        exit 1
    }
    # Nothing to prune is success, not failure: this runs under set -e.
    [[ -d "$backup_root" ]] || return 0

    while IFS= read -r old_backup; do
        [[ -n "$old_backup" ]] || continue
        case "$old_backup" in
            "$backup_root"/*) rm -rf -- "$old_backup" ;;
            *) echo "Refusing to prune unexpected path: $old_backup" >&2; exit 1 ;;
        esac
        echo "Pruned old workflow backup: $old_backup"
    done < <(find "$backup_root" -mindepth 1 -maxdepth 1 -type d -print | sort -r | tail -n "+$((BACKUP_RETENTION + 1))")
}

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

# Commands this repo owns. Every one of them is removed from EVERY event and
# matcher in settings.json before install, so a file that was hand-edited or
# written by an older installer converges on the canonical layout instead of
# accumulating duplicates across events. Without this step, moving a hook
# between events (e.g. cc-doctrine PreToolUse → SessionStart) leaves the old
# entry behind, and a SessionStart-only hook silently fires on every tool call.
#
# Anything NOT on this list — user hooks, graphify hook-guard, third-party
# plugin hooks — is left untouched.
OWNED_HOOK_COMMANDS=(
    cc-nospin
    cc-doctrine
    cc-no-hedge
    cc-whole-file-reads
    cc-comment-wall
    cc-cost-tick
    cc-context-warn
)

cleanup_owned_hooks() {
    python3 - "$@" <<'PY'
import json, os, sys
owned = set(sys.argv[1:])
p = os.path.expanduser('~/.claude/settings.json')
try:
    with open(p) as f:
        d = json.load(f)
except FileNotFoundError:
    sys.exit(0)
except json.JSONDecodeError as e:
    print(f"  settings.json is not valid JSON ({e}); refusing to clean it")
    sys.exit(0)

hooks = d.get('hooks')
if not hooks:
    sys.exit(0)

removed = []
for event in list(hooks.keys()):
    kept_entries = []
    for entry in hooks[event]:
        inner = entry.get('hooks') or []
        survivors = [h for h in inner if h.get('command') not in owned]
        for h in inner:
            if h.get('command') in owned:
                removed.append((event, entry.get('matcher', ''), h.get('command')))
        if survivors:
            entry['hooks'] = survivors
            kept_entries.append(entry)
    if kept_entries:
        hooks[event] = kept_entries
    else:
        del hooks[event]

if not removed:
    sys.exit(0)

with open(p, 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write('\n')

for event, matcher, cmd in removed:
    print(f"  cleaned {event}({matcher or '-'}) {cmd}")
PY
}

claude_hooks_section() {
    echo ""
    echo "Claude hooks:"
    # Remove any prior installs of the hooks this repo owns, wherever they live
    # (any event, any matcher). This is what lets the canonical layout below be
    # the only layout: a hook that moved events does not leave a stale entry.
    cleanup_owned_hooks "${OWNED_HOOK_COMMANDS[@]}"

    # SessionStart: doctrine, loaded verbatim and re-fired after every compaction.
    # cc-doctrine emits hookSpecificOutput.additionalContext with
    # hookEventName="SessionStart"; PreToolUse ignores both the event name and the
    # field, so the only correct home for it is here.
    install_hook SessionStart "" cc-doctrine

    # Stop: refuse to end a turn that hedges or counts. See docs/rule-compliance.md.
    install_hook Stop "" cc-no-hedge

    # PreToolUse(Bash): no-op and spin guard. Fails open if jq is missing.
    install_hook PreToolUse Bash cc-nospin

    # PreToolUse(Read|Bash): AGENTS.md and CONTEXT.md are read entire.
    install_hook PreToolUse "Read|Bash" cc-whole-file-reads

    # PostToolUse(Write|Edit): a wall of comments is a doc page in the wrong file.
    install_hook PostToolUse "Write|Edit" cc-comment-wall

    # cc-context-warn, cc-cost-tick and cc-statusline are deliberately NOT wired
    # any more. They grew up into cha-ching, which does the same job better: it
    # chains to an existing statusline instead of taking the slot, reads cost and
    # context from the payload rather than parsing transcripts, and rate-limits the
    # bell so a tool-heavy turn lands as a few weighty numbers instead of a stream
    # of small ones.
    #
    #   claude plugin marketplace add api-haus/cha-ching
    #   claude plugin install cha-ching@cha-ching
    #   /cha-ching:setup
    #
    # The scripts stay in bin/ because docs/context-usage.md explains its findings
    # through them, and because they are the smallest working version of the idea —
    # useful to read, and to fall back on. Wiring both would give you two statuslines
    # fighting for one slot and two bells for one turn. cleanup_owned_hooks above
    # still removes any that a prior install left behind.
}

# Codex reads hooks from ~/.codex/hooks.json. Same shape as Claude Code's
# settings.json hooks block, but: matchers are regex (anchor them), non-managed
# hooks must be trusted once via /hooks, and Stop's decision:"block" means
# "continue with reason as a new prompt" rather than "reject the stop".
#
# Only commands this repo owns are replaced. User hooks and the graphify
# hook-check entry are left alone.
CODEX_OWNED_HOOK_COMMANDS=(
    cc-nospin
    cc-doctrine
    cc-no-hedge
    cc-whole-file-reads
    cc-comment-wall
)

install_codex_hook() {
    local event="$1" matcher="$2" cmd="$3"
    python3 - "$event" "$matcher" "$cmd" <<'PY'
import json, os, sys
event, matcher, cmd = sys.argv[1:4]
p = os.path.expanduser('~/.codex/hooks.json')
try:
    with open(p) as f:
        d = json.load(f)
except FileNotFoundError:
    d = {}
except json.JSONDecodeError as e:
    print(f"  ~/.codex/hooks.json is not valid JSON ({e}); refusing to touch it")
    sys.exit(0)

hooks = d.setdefault('hooks', {})

# Drop any prior install of THIS command from EVERY event, so a hook that
# moved events converges instead of duplicating.
for ev in list(hooks.keys()):
    kept = []
    for entry in hooks[ev]:
        inner = [h for h in entry.get('hooks', []) if h.get('command') != cmd]
        if inner:
            entry['hooks'] = inner
            kept.append(entry)
    if kept:
        hooks[ev] = kept
    else:
        del hooks[ev]

# Skip the whole exercise if the entry already exists with this matcher.
entries = hooks.setdefault(event, [])
already = any(
    h.get('command') == cmd
    for e in entries
    if e.get('matcher', '') == matcher
    for h in e.get('hooks', [])
)
if already:
    print(f"  codex: {event}({matcher}) {cmd} — already installed")
    sys.exit(0)

entry = {"hooks": [{"type": "command", "command": cmd}]}
if matcher:
    entry = {"matcher": matcher, **entry}
entries.insert(0, entry)

bak = p + '.bak'
if os.path.exists(p):
    with open(p) as f, open(bak, 'w') as g:
        g.write(f.read())
with open(p, 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write('\n')
print(f"  codex: {event}({matcher}) {cmd} — installed (backup at {bak})")
PY
}

# Analogous to cleanup_owned_hooks, but for ~/.codex/hooks.json. Removes every
# command this repo owns from every event and matcher before installing, so a
# hook that moved events (or a name that dropped out of CODEX_OWNED_HOOK_COMMANDS)
# converges instead of accumulating stale entries.
cleanup_owned_codex_hooks() {
    python3 - "$@" <<'PY'
import json, os, sys
owned = set(sys.argv[1:])
p = os.path.expanduser('~/.codex/hooks.json')
try:
    with open(p) as f:
        d = json.load(f)
except FileNotFoundError:
    sys.exit(0)
except json.JSONDecodeError as e:
    print(f"  ~/.codex/hooks.json is not valid JSON ({e}); refusing to clean it")
    sys.exit(0)

hooks = d.get('hooks')
if not hooks:
    sys.exit(0)

removed = []
for event in list(hooks.keys()):
    kept_entries = []
    for entry in hooks[event]:
        inner = entry.get('hooks') or []
        survivors = [h for h in inner if h.get('command') not in owned]
        for h in inner:
            if h.get('command') in owned:
                removed.append((event, entry.get('matcher', ''), h.get('command')))
        if survivors:
            entry['hooks'] = survivors
            kept_entries.append(entry)
    if kept_entries:
        hooks[event] = kept_entries
    else:
        del hooks[event]

if not removed:
    sys.exit(0)

with open(p, 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write('\n')

for event, matcher, cmd in removed:
    print(f"  codex: cleaned {event}({matcher or '-'}) {cmd}")
PY
}

codex_hooks_section() {
    # Review with /hooks inside Codex once after install; trust is per-hash, so a
    # changed hook script needs re-trust.
    echo ""
    echo "Codex hooks:"

    # Remove any prior installs of the hooks this repo owns, wherever they live in
    # ~/.codex/hooks.json. Lets the canonical layout below be the only layout, and
    # makes CODEX_OWNED_HOOK_COMMANDS the single source of truth for what this repo
    # manages. User hooks (e.g. graphify hook-check) are left untouched.
    cleanup_owned_codex_hooks "${CODEX_OWNED_HOOK_COMMANDS[@]}"

    install_codex_hook SessionStart "" cc-doctrine
    install_codex_hook PreToolUse '^Bash$' cc-nospin
    install_codex_hook PreToolUse '^(Read|Bash)$' cc-whole-file-reads
    install_codex_hook PostToolUse '^(Edit|Write)$' cc-comment-wall
    install_codex_hook Stop "" cc-no-hedge
}

# The bare `unity` name may collide with an installed Unity CLI. Whichever PATH
# entry comes first wins, so automation should use an unambiguous command.
#
# unity-editor is the unambiguous name; `unity` is kept as a compatibility alias
# for existing interactive usage.
unity_launcher_section() {
    local resolved
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
}

make_helpers_executable() {
    local script
    for script in \
        "$SCRIPT_DIR/skills/claude-status/claude-status.sh" \
        "$SCRIPT_DIR/skills/cdiff/cdiff.sh" \
        "$SCRIPT_DIR/skills/enforce/enforce.sh"; do
        if [[ -f "$script" ]]; then
            chmod +x "$script"
        fi
    done

    if [[ -d "$SCRIPT_DIR/bin" ]]; then
        chmod +x "$SCRIPT_DIR/bin"/*
    fi
}

print_summary() {
    local key root

    echo ""
    echo "Done: $ACTION"
    for key in $TARGETS; do
        root="$(target_root "$key")"
        printf '  %-7s %s\n' "$(target_label "$key")" "$root"
    done
    if [[ -n "$TOOLS" ]]; then
        printf '  %-7s %s\n' "tools" "$TOOLS"
    fi
    if [[ -n "$TOOLS_FAILED" ]]; then
        echo ""
        echo "These tools were not installed: $TOOLS_FAILED"
        echo "Re-run with --tools ${TOOLS_FAILED// /,} after fixing the cause."
    fi

    echo ""
    echo "Skills installed:"
    ls -1 "$SCRIPT_DIR/skills" | sed 's/^/  - /'
    echo ""
    echo "Agents installed:"
    ls -1 "$SCRIPT_DIR/agents" | sed 's/^/  - /'

    if selected_in hermes; then
        echo ""
        echo "Hermes receives the shared rules as the skill 'my-claude-workflow',"
        echo "because Hermes reads project rules from the working directory and"
        echo "ignores a home-level AGENTS.md."
    fi

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
}

main() {
    local key

    parse_args "$@"

    if [[ "$ASSUME_YES" -eq 0 && -t 1 && -r /dev/tty ]]; then
        INTERACTIVE=1
    fi

    if [[ -z "$ACTION" ]]; then
        if [[ "$INTERACTIVE" -eq 1 ]]; then
            prompt_action
        else
            ACTION="install"
        fi
    fi

    if [[ "$TARGETS_GIVEN" -eq 0 ]]; then
        if [[ "$INTERACTIVE" -eq 1 ]]; then
            prompt_targets "$ACTION"
        else
            TARGETS="$(default_targets "$ACTION")"
        fi
    fi

    if [[ "$TOOLS_GIVEN" -eq 0 ]]; then
        if [[ "$INTERACTIVE" -eq 1 ]]; then
            prompt_tools
        else
            TOOLS="${ALL_TOOLS[*]}"
        fi
    fi

    echo "my-claude-workflow: $ACTION"
    echo "Targets: ${TARGETS:-none}"
    echo "Tools: ${TOOLS:-none}"

    if [[ -z "$TARGETS" ]]; then
        echo ""
        echo "Nothing selected; nothing to do."
        return 0
    fi

    COMBINED_AGENTS="$(mktemp)"
    trap 'rm -f -- "$COMBINED_AGENTS"' EXIT
    build_combined_agents

    for key in $TARGETS; do
        if [[ "$ACTION" == "update" ]] && ! target_installed "$key"; then
            echo ""
            echo "Skipping $(target_label "$key"): not installed by this workflow yet."
            echo "  Run install first: --action install --targets $key"
            continue
        fi
        install_target "$key"
    done

    for key in $TARGETS; do
        if target_installed "$key"; then
            prune_workflow_backups "$(target_root "$key")"
        fi
    done

    make_helpers_executable

    if selected_in claude; then
        claude_hooks_section
    fi
    if selected_in codex; then
        codex_hooks_section
    fi

    if [[ -n "$TOOLS" ]]; then
        install_tools
    fi

    unity_launcher_section
    print_summary

    # If this script was launched from a Windows shortcut or double-click, the
    # console closes the moment the process exits and the output is unreadable.
    # Pause only when stdout is a terminal so piped/CI runs stay unattended.
    # /dev/tty is used for the read because stdin may be redirected in a shortcut.
    if [[ "$INTERACTIVE" -eq 1 ]]; then
        echo ""
        printf 'Press Enter to close... '
        read -r _ < /dev/tty || true
    fi
}

main "$@"
