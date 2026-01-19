---
name: telegram-notify
description: Send Telegram notifications when tasks complete, fail, or need user input. Use after completing significant work, encountering errors, or when blocked waiting for user decisions.
---

# Telegram Notify Skill

Send notifications to the user's Telegram when tasks complete, fail, or need input.

## When to Use

| Trigger | Notify? | Example |
|---------|---------|---------|
| Task completed (significant work) | Yes | Multi-file refactor, feature implementation, PR created |
| Task failed with error | Yes | Build failure, test failure, unrecoverable error |
| Blocked on user decision | Yes | Need clarification, approval required, missing credentials |
| Quick task (<1 min) | No | Fixed typo, added comment, simple rename |
| Mid-task progress | No | "Step 2/5 done" - wait until fully complete |

## How to Notify

Claude Code:
```bash
uv run ~/.claude/skills/telegram-notify/telegram-notify.py \
  --status success \
  --summary "Implemented user authentication with JWT. Created PR #42." \
  --todo "Review src/auth/ changes" \
  --todo "Run tests locally" \
  --todo "Merge when ready"
```

Codex (default `CODEX_HOME=~/.codex`):
```bash
uv run ~/.codex/skills/telegram-notify/telegram-notify.py \
  --status success \
  --summary "Implemented user authentication with JWT. Created PR #42." \
  --todo "Review src/auth/ changes" \
  --todo "Run tests locally" \
  --todo "Merge when ready"
```

### Status Options

| Status | When to Use |
|--------|-------------|
| `--status success` | Task completed successfully |
| `--status error` | Task failed with an error |
| `--status blocked` | Waiting for user input or decision |

### Arguments

| Arg | Required | Description |
|-----|----------|-------------|
| `--status` | Yes | One of: `success`, `error`, `blocked` |
| `--summary` | Yes | 1-3 sentences describing what happened (max 500 chars) |
| `--todo` | No | Repeatable. Action items for the user (max 5) |
| `--dry-run` | No | Print message without sending (for testing) |

## Message Guidelines

### Summary (required)

- 1-3 sentences, max 500 characters
- Focus on WHAT was accomplished, not HOW
- Include key artifacts: PR numbers, file paths, endpoints, error messages

Good examples:
- "Implemented JWT authentication with refresh tokens. Created PR #42 with 15 files changed."
- "Build failed: TypeScript compilation error in src/auth/login.ts:42. Missing type for 'user' parameter."
- "Blocked: Need clarification on authentication method - should we use OAuth2 or API keys?"

Bad examples:
- "Done" (too vague)
- "I made changes to the authentication system by modifying several files including..." (too verbose)

### TODOs (optional)

- Max 5 items (additional items are truncated)
- Actionable, user-facing tasks only
- Be specific

Good examples:
- "Review changes in src/auth/"
- "Run `npm test` to verify"
- "Approve PR #42"
- "Provide API credentials for staging"

Bad examples:
- "Check the code" (too vague)
- "I need you to review the implementation details" (not concise)

## Anti-Spam Rules

- Only notify ONCE per logical task
- Never notify for trivial changes (typos, comments, formatting)
- Don't send progress updates - wait until the task is complete
- When in doubt, don't notify

## Context Auto-Detection

The script automatically detects and includes:

- **Agent**: Claude Code or Codex
- **Working directory**: Current project path
- **Git branch**: Current branch name
- **Session ID**: Claude Code session (first 8 chars); Codex not detected yet (use `--session`)

You can override these with `--pwd`, `--branch`, `--session` if needed.

## Error Scenarios

If notification fails, the script will:

1. Print an error message to stderr
2. Exit with code 1

Common issues:

- Missing `TELEGRAM_BOT_TOKEN` or `TELEGRAM_CHAT_ID` environment variables
- Network connectivity issues
- Rate limiting (script auto-retries with backoff)

## Examples

Note: Use `~/.claude/...` for Claude Code or `~/.codex/...` (or `$CODEX_HOME`) for Codex.

### Successful completion

```bash
uv run ~/.claude/skills/telegram-notify/telegram-notify.py \
  --status success \
  --summary "Refactored authentication module. Reduced code by 30% and added comprehensive tests." \
  --todo "Review src/auth/ changes" \
  --todo "Run the test suite"
```

### Error notification

```bash
uv run ~/.claude/skills/telegram-notify/telegram-notify.py \
  --status error \
  --summary "Build failed: 3 TypeScript errors in src/api/. See terminal for details." \
  --todo "Check terminal output" \
  --todo "Fix type errors in UserService"
```

### Blocked on input

```bash
uv run ~/.claude/skills/telegram-notify/telegram-notify.py \
  --status blocked \
  --summary "Need database credentials for staging environment to continue migration." \
  --todo "Provide STAGING_DB_URL" \
  --todo "Confirm migration strategy"
```
