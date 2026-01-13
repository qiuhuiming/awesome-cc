# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Awesome Claude Code (awesome-cc) is a collection of slash commands and skills for Claude Code and Codex. It provides an interactive CLI installer (`ace`) that allows developers to selectively install and manage custom commands and skills.

## Development Commands

```bash
# Run CLI in development mode
uv run ace install --list                    # List available items
uv run ace install --agent claude-code       # Interactive install
uv run ace install --agent claude-code --all # Install all items
uv run ace uninstall --agent claude-code     # Interactive uninstall
uv run ace install --agent opencode --all    # Install all items for OpenCode
```

## Architecture

### Directory Structure
- `commands/` - Slash commands as `.md` files with YAML frontmatter
- `skills/` - Skills as subdirectories, each containing a `SKILL.md` file
- `src/awesome_cc/` - Python CLI implementation

### CLI Modules (src/awesome_cc/)
- `cli.py` - Main entry point (Typer app with install/uninstall commands)
- `models.py` - Data models (`ItemInfo`, `InstallResult`, `UninstallResult`)
- `discovery.py` - File discovery and frontmatter parsing
- `installer.py` - File installation/uninstallation logic
- `ui.py` - Rich UI components and prompts

### Key Patterns

**Multi-path discovery** - Searches for commands/skills in priority order:
1. Development mode: relative to package source
2. System-wide: `sys.prefix/share/awesome-cc/`
3. User install: `~/.local/share/awesome-cc/`

**Dual-agent support** - Installs to either:
- Claude Code: `~/.claude/commands/` and `~/.claude/skills/`
- Codex: `~/.codex/commands/` and `~/.codex/skills/`
- OpenCode: `~/.opencode/commands/` and `~/.opencode/skills/`

**Frontmatter format** for commands and skills:
```yaml
---
name: command-name
description: Brief description
---
```

### Adding New Commands/Skills

**Commands**: Add a new `.md` file in `commands/` with YAML frontmatter containing `name` and `description`.

**Skills**: Create a new subdirectory in `skills/` with a `SKILL.md` file. Include any supporting scripts or resources in the same directory.

**Important**: After adding new commands or skills, update `pyproject.toml` under `[tool.setuptools.data-files]` to include the new files. This ensures they are included when the package is installed via `uvx` or `pip`.
