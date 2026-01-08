# Telegram Notify Skill

Get notified on Telegram when Claude Code or Codex agents complete tasks, encounter errors, or need your input.

## Prerequisites

- **uv** installed and on PATH ([install guide](https://docs.astral.sh/uv/getting-started/installation/))
- Network access to `api.telegram.org`
- A Telegram account

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow the prompts to name your bot
4. Save the **bot token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 2. Get Your Chat ID

1. Send any message to your new bot (just say "hi")
2. Open this URL in your browser (replace `<TOKEN>` with your bot token):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Find `"chat":{"id":123456789}` in the response - that number is your chat ID

**For group chats:**
- Add the bot to your group
- Group chat IDs start with `-100` (e.g., `-1001234567890`)
- You may need to disable privacy mode: message @BotFather, send `/setprivacy`, select your bot, choose "Disable"

### 3. Set Environment Variables

Add to your shell profile (`~/.zshrc`, `~/.bashrc`, etc.):

```bash
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="987654321"
```

Then reload your shell:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### 4. Test the Setup

**Dry run (no message sent):**
```bash
uv run ~/.claude/skills/telegram-notify/telegram-notify.py \
  --status success \
  --summary "Test notification - dry run" \
  --dry-run
```

**Real notification:**
```bash
uv run ~/.claude/skills/telegram-notify/telegram-notify.py \
  --status success \
  --summary "Telegram notifications are working!" \
  --todo "Check your Telegram"
```

You should receive a message in your Telegram chat.

## Usage

The script is designed to be called by Claude Code or Codex agents. See `SKILL.md` for agent-specific usage instructions.

### Manual Usage

```bash
# Success notification
uv run ~/.claude/skills/telegram-notify/telegram-notify.py \
  --status success \
  --summary "Completed the task" \
  --todo "Review changes" \
  --todo "Run tests"

# Error notification
uv run ~/.claude/skills/telegram-notify/telegram-notify.py \
  --status error \
  --summary "Build failed with 3 errors"

# Blocked notification
uv run ~/.claude/skills/telegram-notify/telegram-notify.py \
  --status blocked \
  --summary "Need API credentials to continue"
```

### Options

| Option | Description |
|--------|-------------|
| `--status`, `-s` | Required. One of: `success`, `error`, `blocked` |
| `--summary`, `-m` | Required. What happened (max 500 chars) |
| `--todo`, `-t` | Optional. Repeatable. Action items (max 5) |
| `--dry-run`, `-n` | Print message without sending |
| `--pwd` | Override detected working directory |
| `--branch` | Override detected git branch |
| `--session` | Override detected session ID |

## Troubleshooting

### "Missing environment variables" error

Make sure both `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set:
```bash
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID
```

### Bot doesn't respond / no messages

1. Make sure you've messaged the bot at least once (send "hi")
2. Verify your chat ID is correct using the getUpdates API
3. For groups, check that the bot is a member and privacy mode is disabled

### Rate limiting

Telegram limits bots to ~30 messages per second. The script automatically handles rate limits by waiting and retrying.

### Network errors

Ensure you have internet access and can reach `api.telegram.org`:
```bash
curl https://api.telegram.org
```

## Message Format

Notifications include:

- Status icon and title
- Agent name (Claude Code / Codex)
- Working directory
- Git branch
- Session ID (first 8 chars)
- Your summary
- TODO items
- Timestamp

Example:
```
✅ Task Completed

🤖 Claude Code
📂 ~/projects/myapp
🌿 feature/auth
🆔 a1b2c3d4

━━━━━━━━━━━━━━━━━━━━

📋 Summary
Implemented JWT authentication with refresh tokens.

📝 Your TODOs
• Review src/auth/ changes
• Run test suite

━━━━━━━━━━━━━━━━━━━━
⏱️ 2026-01-08 12:34
```

## Known Limitations

- Codex session ID detection not yet implemented (shows as blank)
- Maximum message length is 4000 characters (truncated if longer)
- No inline keyboard buttons (planned for future)
- No file/image attachments (planned for future)
