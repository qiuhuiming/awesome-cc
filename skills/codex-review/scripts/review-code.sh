#!/bin/bash
# Review code changes using codex review.
# Usage:
#   review-code.sh [--uncommitted | --base <branch> | --commit <sha>] \
#                  [--prompt <text> | --prompt-file <file>] [--title <text>]
set -euo pipefail

usage() {
    cat <<'EOF'
Usage:
  review-code.sh [--uncommitted | --base <branch> | --commit <sha>] \
                 [--prompt <text> | --prompt-file <file>] [--title <text>]

Modes (mutually exclusive):
  --uncommitted         Review staged, unstaged, and untracked changes
  --base <branch>       Review changes against branch
  --commit <sha>        Review changes introduced by commit
  (default)             Auto-detect base branch

Options:
  --prompt <text>       Custom review instructions
  --prompt-file <file>  Read custom review instructions from file
  --title <text>        Optional title shown in review summary
  -h, --help            Show this message
EOF
}

require_cmd() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "Error: required command not found: $1" >&2
        exit 127
    fi
}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="auto"
BASE=""
COMMIT_SHA=""
PROMPT_TEXT=""
PROMPT_FILE=""
TITLE=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --uncommitted)
            [ "$MODE" = "auto" ] || { echo "Error: review mode flags are mutually exclusive." >&2; usage; exit 2; }
            MODE="uncommitted"
            shift
            ;;
        --base)
            [ "$MODE" = "auto" ] || { echo "Error: review mode flags are mutually exclusive." >&2; usage; exit 2; }
            [ "${2:-}" ] || { echo "Error: --base requires a branch." >&2; usage; exit 2; }
            MODE="base"
            BASE="$2"
            shift 2
            ;;
        --commit)
            [ "$MODE" = "auto" ] || { echo "Error: review mode flags are mutually exclusive." >&2; usage; exit 2; }
            [ "${2:-}" ] || { echo "Error: --commit requires a SHA." >&2; usage; exit 2; }
            MODE="commit"
            COMMIT_SHA="$2"
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
            PROMPT_FILE="$2"
            shift 2
            ;;
        --title)
            [ "${2:-}" ] || { echo "Error: --title requires text." >&2; usage; exit 2; }
            TITLE="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: unknown argument: $1" >&2
            usage
            exit 2
            ;;
    esac
done

require_cmd git
require_cmd codex

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "Error: Not a git repository. Use review-plan.sh for non-git content." >&2
    exit 1
fi

if [ -n "$PROMPT_FILE" ]; then
    [ -f "$PROMPT_FILE" ] || { echo "Error: prompt file not found: $PROMPT_FILE" >&2; exit 2; }
    PROMPT_TEXT="$(cat "$PROMPT_FILE")"
fi

if [ "$MODE" = "commit" ]; then
    if ! git rev-parse --verify "${COMMIT_SHA}^{commit}" >/dev/null 2>&1; then
        echo "Error: commit not found: $COMMIT_SHA" >&2
        exit 2
    fi
fi

# Auto-detect base branch if needed.
if [ "$MODE" = "auto" ]; then
    BASE="$("$SCRIPT_DIR/detect-base-branch.sh")"
fi

if [ -n "$PROMPT_TEXT" ]; then
    # codex review mode flags (--uncommitted, --base, --commit) cannot be
    # combined with a positional [PROMPT] argument.  Fall back to codex exec
    # with the diff embedded in the prompt.

    # Generate diff based on mode.
    case "$MODE" in
        uncommitted)
            DIFF="$(git diff HEAD; git diff --cached)"
            # Include untracked files.
            while IFS= read -r f; do
                [ -n "$f" ] || continue
                DIFF="$DIFF
--- /dev/null
+++ b/$f
$(sed 's/^/+/' "$f")"
            done < <(git ls-files --others --exclude-standard)
            ;;
        base|auto)
            DIFF="$(git diff "${BASE}...HEAD")"
            ;;
        commit)
            DIFF="$(git show "$COMMIT_SHA")"
            ;;
    esac

    # Compose the full prompt.
    FULL_PROMPT="Review the following code changes."
    if [ -n "$TITLE" ]; then
        FULL_PROMPT="$FULL_PROMPT

Title: $TITLE"
    fi
    FULL_PROMPT="$FULL_PROMPT

Instructions: $PROMPT_TEXT

Diff:
$DIFF"

    printf '%s\n' "$FULL_PROMPT" | codex exec -
else
    # No custom prompt — use codex review directly.
    declare -a args
    args=(review)

    case "$MODE" in
        uncommitted)
            args+=(--uncommitted)
            ;;
        base|auto)
            args+=(--base "$BASE")
            ;;
        commit)
            args+=(--commit "$COMMIT_SHA")
            ;;
    esac

    if [ -n "$TITLE" ]; then
        args+=(--title "$TITLE")
    fi

    codex "${args[@]}"
fi
