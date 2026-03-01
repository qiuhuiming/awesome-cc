#!/bin/bash
# Auto-detect the best base branch for review.
# Usage: detect-base-branch.sh
set -euo pipefail

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "main"
    exit 0
fi

is_resolvable_branch() {
    local branch="$1"
    [ -n "$branch" ] && git rev-parse --verify "$branch" >/dev/null 2>&1
}

# 1) origin/HEAD symbolic ref (most reliable when set)
origin_head="$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null || true)"
origin_head="${origin_head#origin/}"
if is_resolvable_branch "$origin_head"; then
    echo "$origin_head"
    exit 0
fi

# 2) Parse remote metadata fallback
remote_head="$(git remote show origin 2>/dev/null | sed -n 's/.*HEAD branch: //p' | head -n1 || true)"
if is_resolvable_branch "$remote_head"; then
    echo "$remote_head"
    exit 0
fi

# 3) Current branch upstream target
upstream_ref="$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || true)"
upstream_branch="${upstream_ref#origin/}"
if is_resolvable_branch "$upstream_branch"; then
    echo "$upstream_branch"
    exit 0
fi

# 4) Common defaults
for branch in main master develop trunk; do
    if is_resolvable_branch "$branch"; then
        echo "$branch"
        exit 0
    fi
done

echo "Warning: unable to detect base branch, falling back to main." >&2
echo "main"
