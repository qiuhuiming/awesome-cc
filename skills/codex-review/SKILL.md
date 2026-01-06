---
name: codex-review
description: This skill should be used when the user explicitly wants to review plans, implemented code, or other content using Codex. It invokes the codex CLI in non-interactive mode with solid prompts containing clear background and context.
---

# Codex Review Skill

This skill leverages the Codex CLI to perform reviews of plans, code changes, or other content in non-interactive mode.

## When to Use

Use this skill when:
- User explicitly requests a review using codex (e.g., "use codex to review this", "codex review my code")
- Reviewing implementation plans before execution
- Reviewing code changes (uncommitted, against base branch, or specific commits)
- Reviewing specific files for quality, security, or other criteria

## Review Types

### 1. Plan Review

To review an implementation plan or any content (works outside git repos):

```bash
./scripts/review-plan.sh <plan-file-or-content> [custom-prompt]
```

**Examples:**
```bash
# Review a plan file
./scripts/review-plan.sh /path/to/plan.md

# Review with custom focus
./scripts/review-plan.sh /path/to/plan.md "Focus on security implications and scalability"

# Review inline content
./scripts/review-plan.sh "$(cat <<'EOF'
# My Plan
1. Step one
2. Step two
EOF
)"
```

### 2. Code Review

To review code changes in a git repository:

```bash
./scripts/review-code.sh [mode] [options] [prompt]
```

**Modes:**

| Mode | Description |
|------|-------------|
| `--uncommitted` | Review staged, unstaged, and untracked changes |
| `--base <branch>` | Review changes against a specific base branch |
| `--commit <sha>` | Review changes from a specific commit |
| *(default)* | Auto-detect base branch and review against it |

**Examples:**
```bash
# Review uncommitted changes
./scripts/review-code.sh --uncommitted

# Review against auto-detected base branch
./scripts/review-code.sh

# Review against specific branch
./scripts/review-code.sh --base main

# Review a specific commit
./scripts/review-code.sh --commit abc1234
```

> **Note:** Custom prompts are not supported with `--uncommitted`, `--base`, or `--commit` flags.
> This is a limitation of the `codex review` CLI. Use `codex review "custom prompt"` (no flags) for custom prompts.

### 3. Direct Codex Commands

For more control, invoke codex directly:

**Review specific files:**
```bash
codex exec --skip-git-repo-check "Review the following files for [CRITERIA]:

Files: [FILE_PATHS]

Context: [BACKGROUND]

$(cat file1.py file2.py)"
```

**Review git diff directly:**
```bash
codex exec "Review this diff for potential issues:

$(git diff HEAD~1)"
```

## Prompt Construction Guidelines

When constructing prompts for codex, always include:

1. **Clear background context** - What is being reviewed and why
2. **Specific focus areas** - What aspects to analyze (security, performance, correctness, etc.)
3. **Full content** - For plans, include the entire plan content
4. **Relevant code** - For code reviews, specify files or use appropriate flags

**Example prompt structure:**
```
Review the following [TYPE] for [PROJECT/CONTEXT].

Focus on:
- [Aspect 1]
- [Aspect 2]
- [Aspect 3]

[CONTENT]
```

## Notes

- Scripts automatically handle git repo detection and base branch discovery
- Non-git directories are supported for plan reviews via `--skip-git-repo-check`
- Default prompts are provided but can be customized for specific needs
- Output is displayed directly in terminal (no file saving)
