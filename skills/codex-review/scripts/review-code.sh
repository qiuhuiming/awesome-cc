#!/bin/bash
# Review code changes using codex review
# Usage: review-code.sh [--uncommitted|--base <branch>|--commit <sha>]
# Note: Custom prompts are NOT supported with these flags (codex CLI limitation)
set -e

IS_GIT_REPO=$(git rev-parse --git-dir 2>/dev/null && echo "yes" || echo "no")
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ "$IS_GIT_REPO" = "no" ]; then
    echo "Error: Not a git repository. Use review-plan.sh for non-git content."
    exit 1
fi

MODE="$1"
shift || true

# Note: codex review CLI does NOT support custom prompts with --uncommitted/--base/--commit flags.
# Custom prompts only work with bare "codex review" (no flags).

case "$MODE" in
    --uncommitted)
        codex review --uncommitted
        ;;
    --base)
        BASE="${1:-$("$SCRIPT_DIR/detect-base-branch.sh")}"
        shift || true
        codex review --base "$BASE"
        ;;
    --commit)
        SHA="$1"
        shift || true
        codex review --commit "$SHA"
        ;;
    *)
        # Default: auto-detect base branch
        BASE=$("$SCRIPT_DIR/detect-base-branch.sh")
        codex review --base "$BASE"
        ;;
esac
