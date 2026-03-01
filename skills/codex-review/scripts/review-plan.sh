#!/bin/bash
# Review plans/content using codex exec (works outside git repos).
# Usage:
#   review-plan.sh [--file <path> | --content <text>] [--prompt <text> | --prompt-file <file>]
#   cat plan.md | review-plan.sh [--prompt <text> | --prompt-file <file>]
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  review-plan.sh [--file <path> | --content <text>] [--prompt <text> | --prompt-file <file>]
  cat plan.md | review-plan.sh [--prompt <text> | --prompt-file <file>]

Backward compatible usage:
  review-plan.sh <plan-file-or-content> [custom-prompt]
EOF
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Error: required command not found: $1" >&2
        exit 127
    fi
}

PLAN_CONTENT=""
PROMPT_TEXT=""
PROMPT_FILE=""
POSITIONAL=()

while [ "$#" -gt 0 ]; do
    case "$1" in
        --file)
            [ -z "$PLAN_CONTENT" ] || { echo "Error: only one of --file/--content/input is allowed." >&2; usage; exit 2; }
            [ "${2:-}" ] || { echo "Error: --file requires a path." >&2; usage; exit 2; }
            [ -f "$2" ] || { echo "Error: plan file not found: $2" >&2; exit 2; }
            PLAN_CONTENT="$(cat "$2")"
            shift 2
            ;;
        --content)
            [ -z "$PLAN_CONTENT" ] || { echo "Error: only one of --file/--content/input is allowed." >&2; usage; exit 2; }
            [ "${2:-}" ] || { echo "Error: --content requires text." >&2; usage; exit 2; }
            PLAN_CONTENT="$2"
            shift 2
            ;;
        --prompt)
            [ -z "$PROMPT_FILE" ] || { echo "Error: --prompt and --prompt-file are mutually exclusive." >&2; usage; exit 2; }
            [ "${2:-}" ] || { echo "Error: --prompt requires text." >&2; usage; exit 2; }
            PROMPT_TEXT="$2"
            shift 2
            ;;
        --prompt-file)
            [ -z "$PROMPT_TEXT" ] || { echo "Error: --prompt and --prompt-file are mutually exclusive." >&2; usage; exit 2; }
            [ "${2:-}" ] || { echo "Error: --prompt-file requires a file path." >&2; usage; exit 2; }
            [ -f "$2" ] || { echo "Error: prompt file not found: $2" >&2; exit 2; }
            PROMPT_FILE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

require_cmd codex

# Backward-compatible positional mode: review-plan.sh <plan-file-or-content> [custom-prompt]
if [ "${#POSITIONAL[@]}" -gt 0 ]; then
    if [ -z "$PLAN_CONTENT" ]; then
        if [ -f "${POSITIONAL[0]}" ]; then
            PLAN_CONTENT="$(cat "${POSITIONAL[0]}")"
        else
            PLAN_CONTENT="${POSITIONAL[0]}"
        fi
    fi
    if [ "${#POSITIONAL[@]}" -gt 1 ] && [ -z "$PROMPT_TEXT" ] && [ -z "$PROMPT_FILE" ]; then
        PROMPT_TEXT="${POSITIONAL[1]}"
    fi
fi

if [ -z "$PLAN_CONTENT" ] && [ ! -t 0 ]; then
    PLAN_CONTENT="$(cat)"
fi

if [ -n "$PROMPT_FILE" ]; then
    PROMPT_TEXT="$(cat "$PROMPT_FILE")"
fi

DEFAULT_PROMPT="Provide feedback on: completeness, potential issues, missing edge cases, and suggestions for improvement."
if [ -z "$PROMPT_TEXT" ]; then
    PROMPT_TEXT="$DEFAULT_PROMPT"
fi

if [ -z "$PLAN_CONTENT" ]; then
    echo "Error: no plan content provided." >&2
    usage
    exit 2
fi

FINAL_PROMPT=$(cat <<EOF
Review the following implementation plan.

Focus:
$PROMPT_TEXT

Plan content:
$PLAN_CONTENT
EOF
)

# Pass prompt through stdin to avoid command-line escaping/length issues.
printf '%s\n' "$FINAL_PROMPT" | codex exec --skip-git-repo-check -
