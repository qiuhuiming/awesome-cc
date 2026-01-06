# Awesome Claude Code

A collection of slash commands and skills for Claude Code.

## Commands

- `/ask-mode` - Read-only conversational exploration mode
- `/code-review` - Review code changes with severity categorization
- `/commit` - Generate conventional commit messages
- `/make-command` - Generate or improve Claude Code commands
- `/prompt-engineer` - Analyze and improve prompts
- `/proactive-ask` - Structured requirement gathering before coding

## Skills

- `codex-review` - Review plans/code using Codex CLI
- `skill-creator` - Guide for creating Claude skills
- `skill-share` - Create and share skills on Slack
- `template-skill` - Template for new skills

## Quick Install

One-liner (clone + install commands and skills):
```bash
git clone https://github.com/qiuhuiming/awesome-cc.git /tmp/awesome-cc && cp /tmp/awesome-cc/commands/*.md ~/.claude/commands/ && cp -r /tmp/awesome-cc/skills/* ~/.claude/skills/ && rm -rf /tmp/awesome-cc
```

## Manual Install

Copy commands:
```bash
cp commands/*.md ~/.claude/commands/
```

Copy skills:
```bash
cp -r skills/* ~/.claude/skills/
```

## Usage

After installation, use commands in Claude Code:
```
/ask-mode
/commit
/code-review
```
