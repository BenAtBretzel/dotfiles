#!/bin/bash

# Default action
ACTION="link"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --link) ACTION="link" ;;
        --unlink) ACTION="unlink" ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Ensure $HOME/bin exists for linking
if [[ "$ACTION" == "link" && ! -d "$HOME/bin" ]]; then
    mkdir -p "$HOME/bin"
    echo "Created directory $HOME/bin"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts"
BIN_DIR="$HOME/bin"

if [[ ! -d "$SCRIPT_DIR" ]]; then
    echo "Error: Directory $SCRIPT_DIR does not exist."
    exit 1
fi

ERROR_COUNT=0

for script_path in "$SCRIPT_DIR"/*; do
    # Check if it's an executable file
    if [[ -f "$script_path" && -x "$script_path" ]]; then
        script_name="$(basename "$script_path")"
        target_link="$BIN_DIR/$script_name"

        if [[ "$ACTION" == "link" ]]; then
            if [[ -e "$target_link" || -L "$target_link" ]]; then
                # Check if it's already a symlink pointing to our script
                if [[ -L "$target_link" && "$(readlink "$target_link")" == "$script_path" ]]; then
                    echo "Checked: $target_link already points to $script_path"
                else
                    echo "Error: $target_link already exists and does not point to $script_path. Skipping."
                    ERROR_COUNT=$((ERROR_COUNT + 1))
                fi
            else
                ln -s "$script_path" "$target_link"
                if [[ $? -eq 0 ]]; then
                    echo "Linked: $target_link -> $script_path"
                else
                    echo "Error: Failed to link $target_link -> $script_path"
                    ERROR_COUNT=$((ERROR_COUNT + 1))
                fi
            fi
        elif [[ "$ACTION" == "unlink" ]]; then
            if [[ -L "$target_link" ]]; then
                if [[ "$(readlink "$target_link")" == "$script_path" ]]; then
                    rm "$target_link"
                    if [[ $? -eq 0 ]]; then
                        echo "Unlinked: $target_link"
                    else
                        echo "Error: Failed to unlink $target_link"
                        ERROR_COUNT=$((ERROR_COUNT + 1))
                    fi
                else
                    echo "Checked: $target_link points elsewhere. Skipping."
                fi
            elif [[ -e "$target_link" ]]; then
                echo "Error: $target_link is not a symlink. Skipping."
                ERROR_COUNT=$((ERROR_COUNT + 1))
            else
                echo "Checked: $target_link does not exist."
            fi
        fi
    fi
done

if [[ $ERROR_COUNT -gt 0 ]]; then
    echo "Completed with $ERROR_COUNT error(s)."
    exit 1
fi

echo "Success."
exit 0
