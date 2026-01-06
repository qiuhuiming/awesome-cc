#!/bin/bash
# Auto-detect the default branch (main/master/develop/etc.)
# Usage: detect-base-branch.sh

if git rev-parse --git-dir > /dev/null 2>&1; then
    # Try to get default branch from remote
    DEFAULT=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
    if [ -z "$DEFAULT" ]; then
        # Fallback: check for common branch names
        for branch in main master develop; do
            if git show-ref --verify --quiet refs/heads/$branch; then
                DEFAULT=$branch
                break
            fi
        done
    fi
    echo "${DEFAULT:-main}"
else
    echo "main"  # Default fallback
fi
