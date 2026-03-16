# Interactive Mode Redesign Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify the CLI by removing dead commands support, adding multi-agent install, and consolidating the interactive flow into two quick checkbox prompts.

**Architecture:** Bottom-up rewrite: models → discovery → installer → ui → cli. Each layer is simplified to skills-only, then cli.py is rewritten with the new interactive flow and multi-agent support.

**Tech Stack:** Python, Typer, questionary, Rich

**Spec:** `docs/superpowers/specs/2026-03-16-interactive-mode-redesign.md`

---

## Chunk 1: Models & Discovery (bottom layers)

### Task 1: Simplify models.py

**Files:**
- Modify: `src/awesome_cc/models.py`

- [ ] **Step 1: Rewrite models.py**

Replace the entire file. Remove `item_type` from `ItemInfo` (only skills remain). Merge `InstallResult` + `UninstallResult` into `OperationResult`.

```python
"""Data models for the installer."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ItemInfo:
    """Information about a skill."""

    name: str
    description: str
    path: Path

    def __str__(self) -> str:
        return f"{self.name} - {self.description}"


@dataclass
class OperationResult:
    """Result of an install or uninstall operation."""

    name: str
    success: bool
    skipped: bool = False
    error: str | None = None
```

- [ ] **Step 2: Commit**

```bash
git add src/awesome_cc/models.py
git commit -m "refactor: simplify models — remove item_type, unify result classes"
```

### Task 2: Simplify discovery.py

**Files:**
- Modify: `src/awesome_cc/discovery.py`

- [ ] **Step 1: Rewrite discovery.py**

Remove `discover_commands()`, `discover_installed_commands()`. Remove `"commands"` check from `get_data_paths()`. Remove `item_type` from `ItemInfo` construction. Keep `discover_skills()`, `discover_installed_skills()`, `get_item_by_name()`, `validate_names()`, `parse_frontmatter()`, `get_package_root()`.

```python
"""Discovery module for scanning skills."""

import re
import sys
from pathlib import Path

import yaml

from .models import ItemInfo


def get_data_paths() -> list[Path]:
    """
    Get possible paths where the skills/ directory might be located.

    Returns paths in order of priority:
    1. Development mode: relative to package source (../../../)
    2. Installed mode: sys.prefix/share/awesome-cc/
    3. User install: ~/.local/share/awesome-cc/
    """
    paths = []

    dev_path = Path(__file__).parent.parent.parent
    if (dev_path / "skills").exists():
        paths.append(dev_path)

    installed_path = Path(sys.prefix) / "share" / "awesome-cc"
    if installed_path.exists():
        paths.append(installed_path)

    user_path = Path.home() / ".local" / "share" / "awesome-cc"
    if user_path.exists():
        paths.append(user_path)

    if not paths:
        paths.append(dev_path)

    return paths


def get_package_root() -> Path:
    """Get the root directory of the package (where skills/ lives)."""
    paths = get_data_paths()
    return paths[0] if paths else Path(__file__).parent.parent.parent


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if match:
        try:
            return yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            return {}
    return {}


def discover_skills(base_path: Path | None = None) -> list[ItemInfo]:
    """Discover all available skills."""
    if base_path is None:
        base_path = get_package_root()

    skills_dir = base_path / "skills"
    if not skills_dir.exists():
        return []

    items = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        try:
            content = skill_md.read_text(encoding="utf-8")
            frontmatter = parse_frontmatter(content)
            name = frontmatter.get("name", skill_dir.name)
            description = frontmatter.get("description", "No description available")
            items.append(ItemInfo(name=name, description=description, path=skill_dir))
        except Exception:
            continue

    return items


def discover_installed_skills(skills_dir: Path) -> list[ItemInfo]:
    """Discover installed skills in the target directory."""
    if not skills_dir.exists():
        return []

    items = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue

        try:
            content = skill_md.read_text(encoding="utf-8")
            frontmatter = parse_frontmatter(content)
            name = frontmatter.get("name", skill_dir.name)
            description = frontmatter.get("description", "No description available")
            items.append(ItemInfo(name=name, description=description, path=skill_dir))
        except Exception:
            continue

    return items


def get_item_by_name(items: list[ItemInfo], name: str) -> ItemInfo | None:
    """Find an item by name."""
    for item in items:
        if item.name == name:
            return item
    return None


def validate_names(
    requested: list[str], available: list[ItemInfo]
) -> tuple[list[str], list[str]]:
    """Validate requested names against available items."""
    available_names = {item.name for item in available}
    valid = [n for n in requested if n in available_names]
    invalid = [n for n in requested if n not in available_names]
    return valid, invalid
```

- [ ] **Step 2: Commit**

```bash
git add src/awesome_cc/discovery.py
git commit -m "refactor: remove commands from discovery, skills-only"
```

### Task 3: Simplify installer.py

**Files:**
- Modify: `src/awesome_cc/installer.py`

- [ ] **Step 1: Rewrite installer.py**

Remove `install_command()`, `uninstall_command()`. Rename `get_target_dirs()` → `get_skills_dir()` returning single Path. Simplify `ensure_target_dirs()` → `ensure_dir()`. Simplify `install_items()` / `uninstall_items()` to skills-only, returning `list[OperationResult]` (not tuples). Keep `install_skill()` and `uninstall_skill()`.

```python
"""Installer module for skill copy operations."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from .models import ItemInfo, OperationResult

VALID_AGENTS = ("claude-code", "codex", "opencode")


def get_skills_dir(agent: str) -> Path:
    """Get the skills directory for the given agent."""
    home = Path.home()
    dirs = {
        "claude-code": home / ".claude" / "skills",
        "codex": home / ".codex" / "skills",
        "opencode": home / ".config" / "opencode" / "skill",
    }
    if agent not in dirs:
        raise ValueError(f"Unknown agent: {agent}. Must be one of: {', '.join(VALID_AGENTS)}")
    return dirs[agent]


def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def install_skill(
    item: ItemInfo,
    target_dir: Path,
    force: bool = False,
    dry_run: bool = False,
    confirm_callback: Callable | None = None,
) -> OperationResult:
    """Install a single skill (entire directory)."""
    if dry_run:
        return OperationResult(name=item.name, success=True)

    target_path = target_dir / item.path.name

    if target_path.exists() and not force:
        if confirm_callback and not confirm_callback(item.name):
            return OperationResult(name=item.name, success=True, skipped=True)

    try:
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.copytree(item.path, target_path, symlinks=False, copy_function=shutil.copy2)
        return OperationResult(name=item.name, success=True)
    except PermissionError:
        return OperationResult(name=item.name, success=False, error=f"Permission denied: {target_path}")
    except Exception as e:
        return OperationResult(name=item.name, success=False, error=str(e))


def uninstall_skill(
    item: ItemInfo,
    dry_run: bool = False,
) -> OperationResult:
    """Uninstall a single skill (entire directory)."""
    if dry_run:
        return OperationResult(name=item.name, success=True)

    try:
        shutil.rmtree(item.path)
        return OperationResult(name=item.name, success=True)
    except FileNotFoundError:
        return OperationResult(name=item.name, success=False, error=f"Not found: {item.path}")
    except PermissionError:
        return OperationResult(name=item.name, success=False, error=f"Permission denied: {item.path}")
    except Exception as e:
        return OperationResult(name=item.name, success=False, error=str(e))


def install_skills(
    skills: list[ItemInfo],
    skills_dir: Path,
    force: bool = False,
    dry_run: bool = False,
    confirm_callback: Callable | None = None,
    progress_callback: Callable | None = None,
) -> list[OperationResult]:
    """Install multiple skills to a single agent directory."""
    if not dry_run:
        ensure_dir(skills_dir)

    results = []
    for skill in skills:
        result = install_skill(skill, skills_dir, force, dry_run, confirm_callback)
        results.append(result)
        if progress_callback:
            progress_callback(result)

    return results


def uninstall_skills(
    skills: list[ItemInfo],
    dry_run: bool = False,
    progress_callback: Callable | None = None,
) -> list[OperationResult]:
    """Uninstall multiple skills."""
    results = []
    for skill in skills:
        result = uninstall_skill(skill, dry_run)
        results.append(result)
        if progress_callback:
            progress_callback(result)

    return results
```

- [ ] **Step 2: Commit**

```bash
git add src/awesome_cc/installer.py
git commit -m "refactor: remove commands from installer, simplify to skills-only"
```

## Chunk 2: UI layer

### Task 4: Rewrite ui.py

**Files:**
- Modify: `src/awesome_cc/ui.py`

- [ ] **Step 1: Rewrite ui.py**

Add `interactive_select_agents()`. Simplify all display functions to skills-only. Remove `confirm_install()`, `confirm_uninstall()`. Remove commands from summary/completion/list. Update `show_header()` to accept list of agents and only show skills dirs.

```python
"""UI module for interactive selection and display."""

from pathlib import Path

import questionary
from rich.console import Console
from rich.table import Table

from .models import ItemInfo, OperationResult
from .installer import VALID_AGENTS

console = Console()

SELECT_ALL = "[Select All]"
SELECT_NONE = "[Select None]"


def interactive_select_agents() -> list[str]:
    """Interactive multi-select for agents."""
    choices = [
        questionary.Choice(title=agent, value=agent)
        for agent in VALID_AGENTS
    ]
    selected = questionary.checkbox(
        "Select target agents:",
        choices=choices,
        instruction="(Space to select, Enter to confirm)",
    ).ask()

    if selected is None:
        return []
    return selected


def interactive_select_skills(items: list[ItemInfo], action: str = "install") -> list[str]:
    """Interactive multi-select for skills."""
    if not items:
        console.print(f"[yellow]No skills available to {action}.[/yellow]")
        return []

    choices = [
        questionary.Choice(title=SELECT_ALL, value=SELECT_ALL),
        questionary.Choice(title=SELECT_NONE, value=SELECT_NONE),
        questionary.Separator("─" * 40),
    ]

    for item in items:
        desc = item.description[:60] + "..." if len(item.description) > 60 else item.description
        choices.append(
            questionary.Choice(
                title=f"{item.name:<20} - {desc}",
                value=item.name,
            )
        )

    selected = questionary.checkbox(
        f"Select skills to {action}:",
        choices=choices,
        instruction="(Space to select, Enter to confirm)",
    ).ask()

    if selected is None:
        return []
    if SELECT_ALL in selected:
        return [item.name for item in items]
    if SELECT_NONE in selected:
        return []
    return [s for s in selected if s not in (SELECT_ALL, SELECT_NONE)]


def confirm_overwrite(name: str, force: bool = False) -> bool:
    """Ask user to confirm overwriting an existing skill."""
    if force:
        return True
    return questionary.confirm(
        f"'{name}' already exists. Overwrite?",
        default=False,
    ).ask() or False


def show_list(skills: list[ItemInfo]) -> None:
    """Display available skills."""
    console.print()
    if skills:
        console.print("[bold cyan]Available Skills:[/bold cyan]")
        for skill in skills:
            desc = skill.description[:70] + "..." if len(skill.description) > 70 else skill.description
            console.print(f"  [green]{skill.name:<20}[/green] {desc}")
        console.print()
    console.print(f"[dim]Total: {len(skills)} skills[/dim]")


def show_installed_list(skills: list[ItemInfo]) -> None:
    """Display installed skills."""
    console.print()
    if skills:
        console.print("[bold cyan]Installed Skills:[/bold cyan]")
        for skill in skills:
            desc = skill.description[:70] + "..." if len(skill.description) > 70 else skill.description
            console.print(f"  [green]{skill.name:<20}[/green] {desc}")
        console.print()
        console.print(f"[dim]Total: {len(skills)} skills[/dim]")
    else:
        console.print("[yellow]No skills installed.[/yellow]")


def show_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def show_invalid_names(invalid: list[str], valid_names: list[str]) -> None:
    """Show error for invalid skill names with suggestions."""
    show_error(f"Unknown skills: {', '.join(invalid)}")
    console.print(f"[dim]Available skills: {', '.join(valid_names)}[/dim]")
    console.print("[dim]Use --list to see all available items.[/dim]")


def show_progress(result: OperationResult, action: str = "installed") -> None:
    """Display progress for a single operation."""
    if result.skipped:
        console.print(f"  [yellow]- {result.name} (skipped)[/yellow]")
    elif result.success:
        if action == "removed":
            console.print(f"  [green]✓ {result.name} ({action})[/green]")
        else:
            console.print(f"  [green]✓ {result.name}[/green]")
    else:
        console.print(f"  [red]✗ {result.name} (failed)[/red]")


def show_completion(installed: int, agents: list[str], action: str = "installed") -> None:
    """Display completion message."""
    console.print()
    agent_str = ", ".join(agents)
    if action == "installed":
        console.print(f"[bold green]✨ {installed} skill(s) {action} to {len(agents)} agent(s) ({agent_str})[/bold green]")
    else:
        console.print(f"[bold green]✨ {installed} skill(s) {action} from {len(agents)} agent(s) ({agent_str})[/bold green]")
```

- [ ] **Step 2: Commit**

```bash
git add src/awesome_cc/ui.py
git commit -m "refactor: rewrite UI for skills-only with multi-agent support"
```

## Chunk 3: CLI rewrite & cleanup

### Task 5: Rewrite cli.py

**Files:**
- Modify: `src/awesome_cc/cli.py`

- [ ] **Step 1: Rewrite cli.py**

New install/uninstall commands with: multi-agent `--agent` list, no commands params, no `commands_only`/`skills_only`, no confirmation step. Multi-agent loop for install/uninstall.

```python
"""CLI module for the installer."""

from typing import Annotated, Optional

import typer
from rich.console import Console

from . import __version__
from .discovery import (
    discover_installed_skills,
    discover_skills,
    get_item_by_name,
    validate_names,
)
from .installer import VALID_AGENTS, get_skills_dir, install_skills, uninstall_skills
from .models import OperationResult
from .ui import (
    confirm_overwrite,
    interactive_select_agents,
    interactive_select_skills,
    show_completion,
    show_error,
    show_installed_list,
    show_invalid_names,
    show_list,
    show_progress,
)

app = typer.Typer(
    name="ace",
    help="Awesome Claude Extensions - CLI installer for Claude Code skills.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"awesome-cc version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
) -> None:
    """Awesome Claude Code Installer."""
    pass


def validate_agents(agents: list[str]) -> None:
    """Validate agent names, exit on invalid."""
    for agent in agents:
        if agent not in VALID_AGENTS:
            show_error(f"Unknown agent: {agent}. Must be one of: {', '.join(VALID_AGENTS)}")
            raise typer.Exit(1)


def resolve_skills(names: list[str], available: list) -> list:
    """Convert skill names to ItemInfo objects."""
    items_by_name = {item.name: item for item in available}
    return [items_by_name[n] for n in names if n in items_by_name]


@app.command()
def install(
    agent: Annotated[
        Optional[list[str]],
        typer.Option(
            "--agent",
            "-a",
            help="Target agent (repeatable): claude-code, codex, or opencode",
        ),
    ] = None,
    skills: Annotated[
        Optional[list[str]],
        typer.Option(
            "--skills",
            "-s",
            help="Install specific skills by name",
        ),
    ] = None,
    all_items: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Install all skills",
        ),
    ] = False,
    list_items: Annotated[
        bool,
        typer.Option(
            "--list",
            "-l",
            help="List available skills",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would be installed without copying",
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Auto-confirm overwrite prompts",
        ),
    ] = False,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Overwrite existing files without prompting",
        ),
    ] = False,
) -> None:
    """Install skills for Claude Code, Codex, or OpenCode."""
    available_skills = discover_skills()

    # --list: no agent required
    if list_items:
        show_list(available_skills)
        raise typer.Exit()

    # Resolve agents
    agents = list(agent) if agent else []
    if agents:
        validate_agents(agents)

    # Determine what needs interactive prompts
    need_agent_prompt = not agents
    need_skills_prompt = not skills and not all_items

    # Interactive agent selection
    if need_agent_prompt:
        agents = interactive_select_agents()
        if not agents:
            console.print("[yellow]No agents selected.[/yellow]")
            raise typer.Exit()

    # Determine selected skills
    if all_items:
        selected_names = [s.name for s in available_skills]
    elif skills:
        valid, invalid = validate_names(skills, available_skills)
        if invalid:
            show_invalid_names(invalid, [s.name for s in available_skills])
            raise typer.Exit(1)
        selected_names = valid
    elif need_skills_prompt:
        selected_names = interactive_select_skills(available_skills, action="install")
    else:
        selected_names = []

    if not selected_names:
        console.print("[yellow]Nothing to install.[/yellow]")
        raise typer.Exit()

    skills_to_install = resolve_skills(selected_names, available_skills)

    if dry_run:
        console.print("[cyan]Dry run - no files will be copied:[/cyan]")

    # Overwrite callback
    def overwrite_cb(name: str) -> bool:
        if yes:
            return True
        return confirm_overwrite(name)

    # Install to each agent
    total_installed = 0
    for ag in agents:
        skills_dir = get_skills_dir(ag)
        console.print(f"\nInstalling to [bold]{ag}[/bold] ({skills_dir})...")

        results = install_skills(
            skills=skills_to_install,
            skills_dir=skills_dir,
            force=force,
            dry_run=dry_run,
            confirm_callback=overwrite_cb if not (force or yes) else None,
            progress_callback=lambda r: show_progress(r),
        )
        total_installed += sum(1 for r in results if r.success and not r.skipped)

    show_completion(total_installed, agents, action="installed")


@app.command()
def uninstall(
    agent: Annotated[
        Optional[list[str]],
        typer.Option(
            "--agent",
            "-a",
            help="Target agent (repeatable): claude-code, codex, or opencode",
        ),
    ] = None,
    skills: Annotated[
        Optional[list[str]],
        typer.Option(
            "--skills",
            "-s",
            help="Uninstall specific skills by name",
        ),
    ] = None,
    all_items: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Uninstall all skills",
        ),
    ] = False,
    list_items: Annotated[
        bool,
        typer.Option(
            "--list",
            "-l",
            help="List installed skills",
        ),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would be uninstalled without deleting",
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Auto-confirm all prompts",
        ),
    ] = False,
) -> None:
    """Uninstall skills from Claude Code, Codex, or OpenCode."""
    # Resolve agents
    agents = list(agent) if agent else []
    if agents:
        validate_agents(agents)

    # Agent is required for all uninstall operations
    if not agents:
        agents = interactive_select_agents()
        if not agents:
            console.print("[yellow]No agents selected.[/yellow]")
            raise typer.Exit()

    # Discover installed skills (union across selected agents)
    all_installed: dict[str, ItemInfo] = {}
    for ag in agents:
        skills_dir = get_skills_dir(ag)
        for item in discover_installed_skills(skills_dir):
            if item.name not in all_installed:
                all_installed[item.name] = item

    installed_skills = sorted(all_installed.values(), key=lambda x: x.name)

    # --list
    if list_items:
        show_installed_list(installed_skills)
        raise typer.Exit()

    # Determine selected skills
    if all_items:
        selected_names = [s.name for s in installed_skills]
    elif skills:
        valid, invalid = validate_names(skills, installed_skills)
        if invalid:
            show_invalid_names(invalid, [s.name for s in installed_skills])
            raise typer.Exit(1)
        selected_names = valid
    else:
        if not installed_skills:
            console.print("[yellow]No skills installed for selected agents.[/yellow]")
            raise typer.Exit()
        selected_names = interactive_select_skills(installed_skills, action="uninstall")

    if not selected_names:
        console.print("[yellow]Nothing to uninstall.[/yellow]")
        raise typer.Exit()

    if dry_run:
        console.print("[cyan]Dry run - no files will be deleted:[/cyan]")

    # Uninstall from each agent
    total_removed = 0
    selected_set = set(selected_names)
    for ag in agents:
        skills_dir = get_skills_dir(ag)
        agent_installed = discover_installed_skills(skills_dir)
        to_remove = [s for s in agent_installed if s.name in selected_set]

        if not to_remove:
            continue

        console.print(f"\nUninstalling from [bold]{ag}[/bold] ({skills_dir})...")

        results = uninstall_skills(
            skills=to_remove,
            dry_run=dry_run,
            progress_callback=lambda r: show_progress(r, action="removed"),
        )
        total_removed += sum(1 for r in results if r.success and not r.skipped)

    show_completion(total_removed, agents, action="removed")


if __name__ == "__main__":
    app()
```

- [ ] **Step 2: Commit**

```bash
git add src/awesome_cc/cli.py
git commit -m "refactor: rewrite CLI with multi-agent support, skills-only, simplified interactive flow"
```

### Task 6: Update sync_pyproject.py

**Files:**
- Modify: `scripts/sync_pyproject.py`

- [ ] **Step 1: Remove commands from sync script**

In `generate_data_files_section()` line 44, change `for dirname in ("commands", "skills"):` to `for dirname in ("skills",):`.

In `main()` line 92, same change: `for dirname in ("commands", "skills"):` → `for dirname in ("skills",):`.

Update the module docstring on line 2: remove "commands/" reference.

- [ ] **Step 2: Run the sync script to verify**

```bash
cd /Users/huiming.qiu/code/awesome-cc && python scripts/sync_pyproject.py
```

Expected: "Synced N entries (M files) to pyproject.toml" with no errors.

- [ ] **Step 3: Commit**

```bash
git add scripts/sync_pyproject.py pyproject.toml
git commit -m "refactor: remove commands from pyproject sync script"
```

### Task 7: Smoke test the full CLI

- [ ] **Step 1: Verify --list**

```bash
uv run ace install --list
```

Expected: Lists available skills (7 skills), no mention of commands.

- [ ] **Step 2: Verify --dry-run install**

```bash
uv run ace install -a claude-code --all --dry-run -y
```

Expected: Shows dry run output for all skills to claude-code.

- [ ] **Step 3: Verify multi-agent dry-run**

```bash
uv run ace install -a claude-code -a codex -s dao-mode --dry-run
```

Expected: Shows dry run for dao-mode to both agents.

- [ ] **Step 4: Verify uninstall --list**

```bash
uv run ace uninstall -a claude-code --list
```

Expected: Lists installed skills for claude-code.

- [ ] **Step 5: Verify --help output**

```bash
uv run ace install --help
uv run ace uninstall --help
```

Expected: No mention of `--commands`, `--commands-only`, `--skills-only`. Shows `--agent` as repeatable.

- [ ] **Step 6: Verify error handling**

```bash
uv run ace install -a invalid-agent --all
```

Expected: Error message about unknown agent.

- [ ] **Step 7: Final commit if any fixes needed**

```bash
git add -u && git commit -m "fix: address issues found in smoke testing"
```
