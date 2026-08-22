#!/usr/bin/env bash
#
# partition_citations.sh - Discover, parse, and partition .meta.toml citations into N groups (default: 4).
#
# Dependencies: yq (v4+), jq (v1.6+), and optionally gh (for PR mode).
#

set -euo pipefail

usage() {
    cat << 'EOF'
Usage: partition_citations.sh [OPTIONS]

Discover, parse, and partition .meta.toml citations into balanced groups for parallel verification.

Options:
  -d, --dir <PATH>         Search directory for *.meta.toml files (default: current directory)
  -f, --file <PATH>        Specific .meta.toml file to include (can be specified multiple times)
  -p, --pr <PR_NUMBER>     Extract changed .meta.toml files from a GitHub Pull Request via gh CLI
  -g, --groups <NUM>       Number of partition groups (default: 4)
  -o, --output <FORMAT>    Output format: json (default), summary, files
  -h, --help               Display this help message

Examples:
  # Scan current workspace and partition into 4 groups (JSON output)
  ./partition_citations.sh --dir . --groups 4

  # Scan specific directory and output summary
  ./partition_citations.sh --dir /path/to/sdlcbot/personas/ext --output summary

  # Review changed citations in a GitHub PR
  ./partition_citations.sh --pr 42
EOF
}

check_dependencies() {
    local missing=()
    if ! command -v yq >/dev/null 2>&1; then
        missing+=("yq")
    fi
    if ! command -v jq >/dev/null 2>&1; then
        missing+=("jq")
    fi
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo "Error: Required dependencies missing: ${missing[*]}" >&2
        echo "Please install missing tools before proceeding." >&2
        return 1
    fi
}

SCAN_DIR=""
SPECIFIC_FILES=()
PR_NUMBER=""
GROUP_COUNT=4
OUTPUT_FORMAT="json"

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -d|--dir)
            [[ -n "${2:-}" ]] || { echo "Error: --dir requires a path argument" >&2; exit 1; }
            SCAN_DIR="$2"
            shift 2
            ;;
        -f|--file)
            [[ -n "${2:-}" ]] || { echo "Error: --file requires a file argument" >&2; exit 1; }
            SPECIFIC_FILES+=("$2")
            shift 2
            ;;
        -p|--pr)
            [[ -n "${2:-}" ]] || { echo "Error: --pr requires a PR number" >&2; exit 1; }
            PR_NUMBER="$2"
            shift 2
            ;;
        -g|--groups)
            [[ -n "${2:-}" ]] || { echo "Error: --groups requires a number" >&2; exit 1; }
            GROUP_COUNT="$2"
            shift 2
            ;;
        -o|--output)
            [[ -n "${2:-}" ]] || { echo "Error: --output requires a format (json|summary|files)" >&2; exit 1; }
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

check_dependencies

TARGET_FILES=()

# Case 1: GitHub PR inspection
if [[ -n "$PR_NUMBER" ]]; then
    if ! command -v gh >/dev/null 2>&1; then
        echo "Error: gh CLI is required for --pr mode" >&2
        exit 1
    fi
    echo "Fetching changed files for PR #${PR_NUMBER} via gh..." >&2
    while IFS= read -r pr_file; do
        [[ -n "$pr_file" ]] || continue
        if [[ "$pr_file" == *.meta.toml ]] && [[ -f "$pr_file" ]]; then
            TARGET_FILES+=("$pr_file")
        fi
    done < <(gh pr diff "$PR_NUMBER" --name-only 2>/dev/null || true)
fi

# Case 2: Explicit files
if [[ ${#SPECIFIC_FILES[@]} -gt 0 ]]; then
    for f in "${SPECIFIC_FILES[@]}"; do
        if [[ -f "$f" ]]; then
            TARGET_FILES+=("$f")
        else
            echo "Warning: Specified file not found: $f" >&2
        fi
    done
fi

# Case 3: Directory search (default if no explicit PR or files provided)
if [[ -z "$PR_NUMBER" && ${#SPECIFIC_FILES[@]} -eq 0 ]]; then
    SEARCH_ROOT="${SCAN_DIR:-.}"
    if [[ ! -d "$SEARCH_ROOT" ]]; then
        echo "Error: Directory does not exist: $SEARCH_ROOT" >&2
        exit 1
    fi
    while IFS= read -r found_file; do
        [[ -n "$found_file" ]] || continue
        TARGET_FILES+=("$found_file")
    done < <(find "$SEARCH_ROOT" -type f -name "*.meta.toml" | sort)
fi

TOTAL_FOUND="${#TARGET_FILES[@]}"

if [[ "$TOTAL_FOUND" -eq 0 ]]; then
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        jq -n --arg count "$GROUP_COUNT" '{
            total_citations: 0,
            group_count: ($count | tonumber),
            groups: [range($count | tonumber) | {group_id: (. + 1), count: 0, citations: []}]
        }'
    elif [[ "$OUTPUT_FORMAT" == "summary" ]]; then
        echo "No .meta.toml citation files discovered."
    fi
    exit 0
fi

# Parse all discovered files using yq into a single JSON stream
PARSED_STREAM=$(
    for target in "${TARGET_FILES[@]}"; do
        # Extract [meta] table and attach resolved file path
        yq -p=toml -o=json '.meta + {"file": filename}' "$target" 2>/dev/null || true
    done
)

if [[ -z "$PARSED_STREAM" ]]; then
    echo "Error: Failed to parse any valid .meta tables from discovered files." >&2
    exit 1
fi

case "$OUTPUT_FORMAT" in
    json)
        echo "$PARSED_STREAM" | jq -s --arg groups "$GROUP_COUNT" '
            ($groups | tonumber) as $num_groups |
            . as $all |
            {
                total_citations: ($all | length),
                group_count: $num_groups,
                groups: [
                    range($num_groups) as $idx |
                    {
                        group_id: ($idx + 1),
                        citations: [
                            $all[range($idx; ($all | length); $num_groups)]
                        ]
                    } | .count = (.citations | length)
                ]
            }
        '
        ;;
    summary)
        echo "$PARSED_STREAM" | jq -s -r --arg groups "$GROUP_COUNT" '
            ($groups | tonumber) as $num_groups |
            . as $all |
            "Discovered \($all | length) citation(s) across \($num_groups) partition group(s):\n\n" +
            (
                [
                    range($num_groups) as $idx |
                    [ $all[range($idx; ($all | length); $num_groups)] ] as $group_items |
                    "  [Group \($idx + 1)] (\($group_items | length) items):\n" +
                    (
                        $group_items | map(
                            "    - \(.file)\n      creator: \(.creator // "n/a")\n      source:  \(.source_location // .source_repository // .source // "n/a")"
                        ) | join("\n")
                    )
                ] | join("\n\n")
            )
        '
        ;;
    files)
        for f in "${TARGET_FILES[@]}"; do
            echo "$f"
        done
        ;;
    *)
        echo "Error: Invalid output format: $OUTPUT_FORMAT. Expected: json, summary, files" >&2
        exit 1
        ;;
esac
