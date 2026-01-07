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
- `uv` - Python package manager guidance

## Quick Install

One-liner (clone + install commands and skills):
```bash
git clone https://github.com/qiuhuiming/awesome-cc.git /tmp/awesome-cc && cp /tmp/awesome-cc/commands/*.md ~/.claude/commands/ && cp -r /tmp/awesome-cc/skills/* ~/.claude/skills/ && rm -rf /tmp/awesome-cc
```

## Interactive Install

Use the CLI installer to selectively install commands and skills:

```bash
# List available commands and skills
uvx --from git+https://github.com/qiuhuiming/awesome-cc acc-install install --list

# Interactive mode - select what to install
uvx --from git+https://github.com/qiuhuiming/awesome-cc acc-install install --agent claude-code

# Install specific items
uvx --from git+https://github.com/qiuhuiming/awesome-cc acc-install install \
    --agent claude-code --commands commit --commands code-review --skills uv

# Install all
uvx --from git+https://github.com/qiuhuiming/awesome-cc acc-install install --agent claude-code --all

# For Codex users
uvx --from git+https://github.com/qiuhuiming/awesome-cc acc-install install --agent codex --all
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

## Development

Run from source:

```bash
git clone https://github.com/qiuhuiming/awesome-cc.git
cd awesome-cc

# List available items
uv run acc-install install --list

# Install interactively
uv run acc-install install --agent claude-code

# Install all
uv run acc-install install --agent claude-code --all --yes
```
