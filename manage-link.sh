#!/bin/bash

# Manage symbolic links for dotfiles scripts and agent skills.

ACTION="link"
MANAGE_SCRIPTS=0
MANAGE_SKILLS=0
SKILLS_AGENT=""
EXPLICIT_TARGET=0
YES_ALL=0

usage() {
    cat << 'EOF'
Usage: manage-link.sh [ACTION] [OPTIONS]

Manage symbolic links for dotfiles scripts and agent skills.

Actions:
  --link                 Create symbolic links (default)
  --unlink               Remove symbolic links
  --clean                Remove dead symbolic links in $HOME/bin pointing to this repo

Options:
  --scripts              Manage script links to $HOME/bin
  --skills[=AGENT]       Manage skill links for AGENT (default: all)
                         Supported agents: all, aider, agy, codex, vibe
  --yes                  Automatically answer yes to all prompts (for --clean)
  -h, --help             Display this help message

If neither --scripts nor --skills is specified, both will be managed (with --skills=all).
EOF
}

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --link)
            ACTION="link"
            shift
            ;;
        --unlink)
            ACTION="unlink"
            shift
            ;;
        --clean)
            ACTION="clean"
            shift
            ;;
        --yes)
            YES_ALL=1
            shift
            ;;
        --scripts)
            MANAGE_SCRIPTS=1
            EXPLICIT_TARGET=1
            shift
            ;;
        --skills=*)
            MANAGE_SKILLS=1
            EXPLICIT_TARGET=1
            SKILLS_AGENT="${1#*=}"
            shift
            ;;
        --skills)
            MANAGE_SKILLS=1
            EXPLICIT_TARGET=1
            if [[ "$#" -gt 1 && "$2" != --* ]]; then
                SKILLS_AGENT="$2"
                shift 2
            else
                SKILLS_AGENT="all"
                shift
            fi
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: Unknown parameter passed: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

if [[ "$EXPLICIT_TARGET" -eq 0 ]]; then
    MANAGE_SCRIPTS=1
    MANAGE_SKILLS=1
    SKILLS_AGENT="all"
fi

if [[ "$MANAGE_SKILLS" -eq 1 ]]; then
    if [[ -z "$SKILLS_AGENT" ]]; then
        SKILLS_AGENT="all"
    fi
    case "$SKILLS_AGENT" in
        all|aider|agy|codex|vibe) ;;
        *)
            echo "Error: Invalid agent '$SKILLS_AGENT' for --skills. Valid options: all, aider, agy, codex, vibe" >&2
            exit 1
            ;;
    esac
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_DIR="$REPO_DIR/scripts"
SKILLS_DIR="$REPO_DIR/skills"
BIN_DIR="$HOME/bin"

get_agent_skills_dir() {
    local agent="$1"
    case "$agent" in
        agy)
            echo "$HOME/.gemini/antigravity-cli/skills"
            ;;
        codex)
            echo "$HOME/.agents/skills"
            ;;
        vibe)
            echo "${VIBE_HOME:-$HOME/.vibe}/skills"
            ;;
        aider)
            echo "${AIDER_HOME:-$HOME/.aider}/skills"
            ;;
        *)
            echo "Error: Unknown agent '$agent'" >&2
            return 1
            ;;
    esac
}

sync_symlink() {
    local action="$1"
    local source_path="$2"
    local target_link="$3"

    if [[ "$action" == "link" ]]; then
        local target_parent
        target_parent="$(dirname "$target_link")"
        if [[ ! -d "$target_parent" ]]; then
            if mkdir -p "$target_parent"; then
                echo "Created directory $target_parent"
            else
                echo "Error: Failed to create directory $target_parent" >&2
                return 1
            fi
        fi

        if [[ -e "$target_link" || -L "$target_link" ]]; then
            if [[ -L "$target_link" && "$(readlink "$target_link")" == "$source_path" ]]; then
                echo "Checked: $target_link already points to $source_path"
                return 0
            fi
            echo "Error: $target_link already exists and does not point to $source_path. Skipping." >&2
            return 1
        fi

        if ln -s "$source_path" "$target_link"; then
            echo "Linked: $target_link -> $source_path"
            return 0
        fi
        echo "Error: Failed to link $target_link -> $source_path" >&2
        return 1
    elif [[ "$action" == "unlink" ]]; then
        if [[ -L "$target_link" ]]; then
            if [[ "$(readlink "$target_link")" == "$source_path" ]]; then
                if rm "$target_link"; then
                    echo "Unlinked: $target_link"
                    return 0
                fi
                echo "Error: Failed to unlink $target_link" >&2
                return 1
            fi
            echo "Checked: $target_link points elsewhere. Skipping."
            return 0
        fi

        if [[ -e "$target_link" ]]; then
            echo "Error: $target_link is not a symlink. Skipping." >&2
            return 1
        fi

        echo "Checked: $target_link does not exist."
        return 0
    else
        echo "Error: Invalid action '$action'" >&2
        return 1
    fi
}

clean_dead_links() {
    local yes_all="$1"
    local errors=0

    if [[ ! -d "$BIN_DIR" ]]; then
        return 0
    fi

    local link_path
    local found_dead=0
    for link_path in "$BIN_DIR"/*; do
        [[ -e "$link_path" || -L "$link_path" ]] || continue
        if [[ -L "$link_path" && ! -e "$link_path" ]]; then
            local target_path
            target_path="$(readlink "$link_path")"
            if [[ "$target_path" == "$REPO_DIR"* ]]; then
                found_dead=1
                if [[ "$yes_all" -eq 1 ]]; then
                    if rm "$link_path"; then
                        echo "Removed dead link: $link_path -> $target_path"
                    else
                        echo "Error: Failed to remove dead link $link_path" >&2
                        errors=$((errors + 1))
                    fi
                else
                    read -r -p "Remove dead link $link_path -> $target_path? [y/N] " confirm
                    if [[ "$confirm" =~ ^[Yy]$ ]]; then
                        if rm "$link_path"; then
                            echo "Removed dead link: $link_path -> $target_path"
                        else
                            echo "Error: Failed to remove dead link $link_path" >&2
                            errors=$((errors + 1))
                        fi
                    else
                        echo "Skipped: $link_path"
                    fi
                fi
            fi
        fi
    done

    if [[ "$found_dead" -eq 0 ]]; then
        echo "Checked: No dead links pointing to this repo found in $BIN_DIR"
    fi

    return "$errors"
}

manage_scripts() {
    local action="$1"
    local errors=0

    if [[ ! -d "$SCRIPT_DIR" ]]; then
        echo "Error: Directory $SCRIPT_DIR does not exist." >&2
        return 1
    fi

    if [[ "$action" == "link" && ! -d "$BIN_DIR" ]]; then
        if mkdir -p "$BIN_DIR"; then
            echo "Created directory $BIN_DIR"
        else
            echo "Error: Failed to create directory $BIN_DIR" >&2
            return 1
        fi
    fi

    local found_scripts=0
    local script_path
    for script_path in "$SCRIPT_DIR"/*; do
        [[ -e "$script_path" ]] || break
        if [[ -f "$script_path" && -x "$script_path" ]]; then
            found_scripts=1
            local script_name
            script_name="$(basename "$script_path")"
            local target_link="$BIN_DIR/$script_name"
            if ! sync_symlink "$action" "$script_path" "$target_link"; then
                errors=$((errors + 1))
            fi
        fi
    done

    if [[ "$found_scripts" -eq 0 ]]; then
        echo "Checked: No executable scripts found in $SCRIPT_DIR"
    fi

    return "$errors"
}

manage_skills() {
    local action="$1"
    local agent_target="$2"
    local errors=0

    if [[ ! -d "$SKILLS_DIR" ]]; then
        echo "Error: Directory $SKILLS_DIR does not exist." >&2
        return 1
    fi

    local agents=()
    if [[ "$agent_target" == "all" ]]; then
        agents=("aider" "agy" "codex" "vibe")
    else
        agents=("$agent_target")
    fi

    local valid_skills=()
    local skill_path
    for skill_path in "$SKILLS_DIR"/*; do
        [[ -e "$skill_path" ]] || break
        if [[ -d "$skill_path" && -f "$skill_path/SKILL.md" ]]; then
            valid_skills+=("$skill_path")
        fi
    done

    if [[ "${#valid_skills[@]}" -eq 0 ]]; then
        echo "Checked: No valid skills found in $SKILLS_DIR (must contain SKILL.md)"
        return 0
    fi

    local agent
    for agent in "${agents[@]}"; do
        local agent_skills_dir
        if ! agent_skills_dir="$(get_agent_skills_dir "$agent")"; then
            errors=$((errors + 1))
            continue
        fi

        for skill_path in "${valid_skills[@]}"; do
            local skill_name
            skill_name="$(basename "$skill_path")"
            local target_link="$agent_skills_dir/$skill_name"
            if ! sync_symlink "$action" "$skill_path" "$target_link"; then
                errors=$((errors + 1))
            fi
        done
    done

    return "$errors"
}

TOTAL_ERRORS=0

if [[ "$ACTION" == "clean" ]]; then
    clean_dead_links "$YES_ALL" || TOTAL_ERRORS=$((TOTAL_ERRORS + $?))
else
    if [[ "$MANAGE_SCRIPTS" -eq 1 ]]; then
        manage_scripts "$ACTION" || TOTAL_ERRORS=$((TOTAL_ERRORS + $?))
    fi

    if [[ "$MANAGE_SKILLS" -eq 1 ]]; then
        manage_skills "$ACTION" "$SKILLS_AGENT" || TOTAL_ERRORS=$((TOTAL_ERRORS + $?))
    fi
fi

if [[ "$TOTAL_ERRORS" -gt 0 ]]; then
    echo "Completed with $TOTAL_ERRORS error(s)." >&2
    exit 1
fi

echo "Success."
exit 0
