#!/bin/bash
# Review plans or content using codex exec (works outside git repos)
# Usage: review-plan.sh <plan-file-or-content> [custom-prompt]
set -e

CONTENT="$1"
CUSTOM_PROMPT="${2:-Provide feedback on: completeness, potential issues, missing edge cases, and suggestions for improvement.}"

if [ -z "$CONTENT" ]; then
    echo "Usage: review-plan.sh <plan-file-or-content> [custom-prompt]"
    exit 1
fi

# Check if it's a file path or direct content
if [ -f "$CONTENT" ]; then
    PLAN_CONTENT=$(cat "$CONTENT")
else
    PLAN_CONTENT="$CONTENT"
fi

codex exec --skip-git-repo-check "Review the following implementation plan. $CUSTOM_PROMPT

$PLAN_CONTENT"
