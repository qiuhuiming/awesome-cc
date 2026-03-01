---
name: codex-review
description: Use this skill only when the user explicitly asks to use Codex (for example mentions "codex", "codex review", or "use codex") to review implementation plans, code changes, commits, or specific files. Do not trigger for generic review requests that do not explicitly ask for Codex.
---

# Codex Review Skill

Use Codex CLI in non-interactive mode to review plans and code with clear scope and reproducible output.

## Trigger Policy (Strict)

Trigger this skill only when the user explicitly asks for Codex.

Trigger examples:
- "use codex to review this"
- "codex review my PR"
- "用 codex 看一下这个提交"

Do not trigger examples:
- "review my code"
- "帮我审一下这个方案"
- "can you do a quick PR review"

If the request is a review task but Codex is not explicitly requested, use normal review behavior instead of this skill.

## Invocation Guidelines

IMPORTANT: Never change to this skill's directory. Stay in the user's current working directory and invoke scripts using their absolute path:

```bash
"$HOME/.claude/skills/codex-review/scripts/<script-name>.sh" [args]
```

This ensures the scripts operate on files in the user's project, not the skill directory.

## Review Types

### 1. Plan Review (works outside git repos)

```bash
"$HOME/.claude/skills/codex-review/scripts/review-plan.sh" [--file <path> | --content <text>] [--prompt <text> | --prompt-file <file>]
cat plan.md | "$HOME/.claude/skills/codex-review/scripts/review-plan.sh" [--prompt <text> | --prompt-file <file>]
```

Examples:
```bash
"$HOME/.claude/skills/codex-review/scripts/review-plan.sh" --file /path/to/plan.md
"$HOME/.claude/skills/codex-review/scripts/review-plan.sh" --file /path/to/plan.md --prompt "Focus on security and rollout risks"
cat /path/to/plan.md | "$HOME/.claude/skills/codex-review/scripts/review-plan.sh" --prompt-file /path/to/focus.txt
```

### 2. Code Review (git repositories)

```bash
"$HOME/.claude/skills/codex-review/scripts/review-code.sh" [--uncommitted | --base <branch> | --commit <sha>] [--prompt <text> | --prompt-file <file>] [--title <text>]
```

Modes:
- `--uncommitted`: review staged, unstaged, and untracked changes
- `--base <branch>`: review changes against a branch
- `--commit <sha>`: review changes introduced by one commit
- default: auto-detect base branch and review against it

Examples:
```bash
"$HOME/.claude/skills/codex-review/scripts/review-code.sh" --uncommitted
"$HOME/.claude/skills/codex-review/scripts/review-code.sh"
"$HOME/.claude/skills/codex-review/scripts/review-code.sh" --base main --prompt "Focus on API compatibility"
"$HOME/.claude/skills/codex-review/scripts/review-code.sh" --commit abc1234 --title "Auth hotfix review"
```

### 3. Direct Codex Commands

Use direct commands when script behavior is insufficient.

Review selected files:
```bash
codex exec --skip-git-repo-check "Review these files for correctness, security, and maintainability.

$(cat path/to/file1 path/to/file2)"
```

Review a diff directly:
```bash
DIFF=$(git diff HEAD~1)
codex exec "Review this diff for regressions and missing tests.

$DIFF"
```

## Prompt Guidelines

Include:
1. Context: what is being reviewed and why
2. Focus: exact review dimensions (correctness, security, performance, etc.)
3. Scope: exact files / commit / diff range
4. Constraints: compatibility or rollout constraints

Prefer scoped prompts over whole-repo prompts to reduce noise.

## Review Report Structure

Always format the final review output with this structure:

```markdown
## Summary
- What was reviewed
- Overall risk level

## Findings
- [Severity] path/to/file:line - issue description, impact, why it matters

## Risks / Unknowns
- Missing context or checks required before merge

## Recommended Fixes
- Concrete, prioritized next steps
```

## Safety and Scope

- Review only requested scope; do not pull unrelated files.
- Avoid including secrets, env files, or large generated artifacts in prompts.
- If secret-like content is detected, warn and ask to sanitize scope.
- For large diffs, split review by area to keep findings precise.

## Notes

- Scripts handle git repo checks and base branch discovery.
- `codex review` mode flags (`--uncommitted`, `--base`, `--commit`) cannot be combined with custom prompts; the script falls back to `codex exec` when both are needed.
- For long prompts, scripts pass prompt content through stdin to avoid shell escaping and length issues.
