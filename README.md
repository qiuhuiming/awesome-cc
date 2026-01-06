# Awesome Claude Code

A collection of slash commands for Claude Code.

## Commands

- `/ask-mode` - Read-only conversational exploration mode
- `/code-review` - Review code changes with severity categorization
- `/commit` - Generate conventional commit messages
- `/make-command` - Generate or improve Claude Code commands
- `/prompt-engineer` - Analyze and improve prompts
- `/proactive-ask` - Structured requirement gathering before coding

## Quick Install

One-liner (clone + install):
```bash
git clone https://github.com/qiuhuiming/awesome-cc.git /tmp/awesome-cc && cp /tmp/awesome-cc/commands/*.md ~/.claude/commands/ && rm -rf /tmp/awesome-cc
```

## Manual Install

Copy all commands:
```bash
cp commands/*.md ~/.claude/commands/
```

Or copy individual commands:
```bash
cp commands/ask-mode.md ~/.claude/commands/
```

## Usage

After installation, use commands in Claude Code:
```
/ask-mode
/commit
/code-review
```
