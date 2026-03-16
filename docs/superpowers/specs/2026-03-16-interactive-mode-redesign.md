# Interactive Mode Redesign & Commands Removal

**Date**: 2026-03-16
**Status**: Draft

## Problem

The current CLI has several pain points:

1. **Step-by-step interaction** — agent validation, commands checkbox, skills checkbox, confirmation prompt, overwrite prompt — up to 5 sequential interactions for a single install
2. **Commands are dead weight** — the project has zero command files; all content is skills. Yet the code fully supports commands discovery, installation, and uninstallation
3. **Single-agent limitation** — users who want the same skills in multiple agents must run the CLI multiple times
4. **Redundant parameters** — `--commands-only` and `--skills-only` exist solely to skip one of the two checkbox prompts

## Design

### 1. Remove Commands Support Entirely

Delete all commands-related code across every module:

- **`discovery.py`**: remove `discover_commands()`, `discover_installed_commands()`
- **`installer.py`**: remove `install_command()`, `uninstall_command()`, commands handling in `install_items()` / `uninstall_items()`. `get_target_dirs()` → `get_skills_dir(agent) -> Path`. Also simplify `ensure_target_dirs()` to accept a single skills dir
- **`ui.py`**: remove commands from `show_list()`, `show_installed_list()`, `show_summary()`, `show_uninstall_summary()`, `show_completion()`, `show_uninstall_completion()`. Remove `show_install_progress()` target parameter. Update `show_header()` to drop commands directory display
- **`cli.py`**: remove `--commands`, `--commands-only`, `--skills-only` parameters from both install and uninstall
- **`models.py`**: remove `"command"` from `ItemInfo.item_type` literal (or remove `item_type` entirely since only skills remain). Unify `InstallResult` and `UninstallResult` into a single `OperationResult` dataclass (no `operation` field needed — callers already know context)

### 2. Multi-Agent Support

**CLI parameter change**: `--agent` / `-a` becomes a repeatable `list[str]` option.

```
ace install --agent claude-code --agent codex --all
```

**Interactive mode**: `questionary.checkbox()` for agent selection (multi-select).

**Install logic**: loop over selected agents, install all selected skills into each agent's skills directory.

**`get_target_dirs()`** becomes `get_skills_dir(agent: str) -> Path` — returns a single Path.

### 3. Simplified Interactive Flow

Two prompts, no confirmation:

```
? Select target agents (Space to select, Enter to confirm):
❯ ☑ claude-code
  ☐ codex
  ☐ opencode

? Select skills to install (Space to select, Enter to confirm):
  ☑ [Select All]
  ☐ [Select None]
  ──────────────────────────────
  ☐ codex-exec       - Drive codex CLI in headless mode
  ☑ dao-mode         - Discovery and analysis mode
  ☐ notebooklm       - Google NotebookLM automation
  ☐ orchestrate      - Agent team orchestrator
  ☐ skill-creator    - Guide for creating effective skills
  ☐ telegram-notify  - Send Telegram notifications
  ☐ uv              - Modern Python package manager

Installing to claude-code...
  ✓ dao-mode
✨ 1 skill installed to 1 agent
```

- No separate "Proceed with installation?" confirmation — selecting items and pressing Enter is the confirmation
- Overwrite behavior: `--force` overwrites silently; without `--force`, prompt per conflict (unchanged)
- `--yes` auto-confirms overwrite prompts only (the confirmation step is already removed)

**Edge cases:**
- No agents selected → print "No agents selected." and exit
- No skills selected → print "Nothing to install." and exit
- Ctrl+C at any prompt → exit gracefully

### 4. Uninstall Follows the Same Pattern

```
? Select target agents:
  ☑ claude-code

? Select skills to uninstall:
  ☐ dao-mode
  ☑ skill-creator

Uninstalling from claude-code...
  ✓ skill-creator (removed)
Uninstall complete! 1 skill removed from 1 agent
```

For uninstall, the skills list shows the **union** of installed skills across all selected agents. Each skill is uninstalled from whichever selected agents have it installed.

**Edge cases:**
- No installed skills across any selected agent → print "No skills installed for selected agents." and exit
- `ace uninstall --list` requires `--agent` to know which directories to scan

### 5. CLI Parameters (Post-Redesign)

#### `ace install`

| Parameter | Type | Description |
|-----------|------|-------------|
| `--agent, -a` | `list[str]` | Target agents (repeatable). Required for non-list operations |
| `--skills, -s` | `list[str]` | Install specific skills by name (repeatable) |
| `--all` | `bool` | Install all skills |
| `--list, -l` | `bool` | List available skills (no agent required) |
| `--dry-run` | `bool` | Preview without copying |
| `--yes, -y` | `bool` | Auto-confirm all prompts |
| `--force, -f` | `bool` | Overwrite existing files |

**Removed**: `--commands / -c`, `--commands-only`, `--skills-only`

#### `ace uninstall`

Same as install but without `--force`. `--skills` uninstalls specific skills. `--all` uninstalls everything.

### 6. Non-Interactive Mode Behavior

When `--agent` and `--skills` (or `--all`) are provided, no prompts appear:

```bash
# Install specific skills to multiple agents
ace install -a claude-code -a codex -s dao-mode -s uv

# Install all skills to one agent, no prompts
ace install -a claude-code --all -y

# Dry run
ace install -a claude-code --all --dry-run
```

When `--agent` is provided but no skills specified, enter interactive mode for skill selection only (skip agent prompt).

When `--all` is provided without `--agent`, enter interactive mode for agent selection only (skip skills prompt).

When nothing is provided, full interactive mode (both prompts).

## Files to Modify

| File | Changes |
|------|---------|
| `src/awesome_cc/models.py` | Remove `"command"` from `ItemInfo.item_type`. Merge `InstallResult` + `UninstallResult` → `OperationResult` |
| `src/awesome_cc/discovery.py` | Delete `discover_commands()`, `discover_installed_commands()`. Keep `discover_skills()`, `discover_installed_skills()`, `validate_names()`, `get_item_by_name()` |
| `src/awesome_cc/installer.py` | Delete `install_command()`, `uninstall_command()`. `get_target_dirs()` → `get_skills_dir()`. Simplify `install_items()` / `uninstall_items()` to skills-only |
| `src/awesome_cc/ui.py` | Add `interactive_select_agents()`. Simplify all display functions to skills-only. Remove `confirm_install()` / `confirm_uninstall()`. Simplify summary/completion messages |
| `src/awesome_cc/cli.py` | Rewrite `install()` and `uninstall()` with new parameter set, multi-agent loop, simplified interactive flow |
| `pyproject.toml` | Remove any commands-related data-files entries (if present) |
| `scripts/sync_pyproject.py` | Remove commands directory handling |

## Verification

```bash
# List available skills
uv run ace install --list

# Full interactive mode (both prompts)
uv run ace install

# Interactive skill selection only (agent pre-selected)
uv run ace install -a claude-code

# Direct install, multiple agents
uv run ace install -a claude-code -a codex -s dao-mode --dry-run

# Install all to one agent
uv run ace install -a claude-code --all --dry-run -y

# Uninstall interactive
uv run ace uninstall

# Uninstall direct
uv run ace uninstall -a claude-code -s dao-mode --dry-run

# Run tests
uv run pytest tests/ -v
```
