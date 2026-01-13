"""Installer module for file copy operations."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from .models import InstallResult, ItemInfo, UninstallResult


def get_target_dirs(agent: str) -> tuple[Path, Path]:
    """
    Get target directories for the given agent.

    Args:
        agent: Agent name ('claude-code', 'codex', or 'opencode').

    Returns:
        Tuple of (commands_dir, skills_dir).
    """
    home = Path.home()

    if agent == "claude-code":
        base = home / ".claude"
    elif agent == "codex":
        base = home / ".codex"
    elif agent == "opencode":
        base = home / ".opencode"
    else:
        raise ValueError(
            f"Unknown agent: {agent}. Must be 'claude-code', 'codex', or 'opencode'."
        )

    return base / "commands", base / "skills"


def ensure_target_dirs(commands_dir: Path, skills_dir: Path) -> None:
    """Create target directories if they don't exist."""
    commands_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)


def install_command(
    item: ItemInfo,
    target_dir: Path,
    force: bool = False,
    dry_run: bool = False,
    confirm_callback: Callable | None = None,
) -> InstallResult:
    """
    Install a single command.

    Args:
        item: Command to install.
        target_dir: Target directory.
        force: Overwrite without prompting.
        dry_run: Don't actually copy files.
        confirm_callback: Function to call to confirm overwrite.

    Returns:
        InstallResult with operation status.
    """
    if dry_run:
        return InstallResult(name=item.name, success=True)

    target_file = target_dir / item.path.name

    # Check if file exists
    if target_file.exists() and not force:
        if confirm_callback and not confirm_callback(item.name):
            return InstallResult(name=item.name, success=True, skipped=True)

    try:
        shutil.copy2(item.path, target_file)
        return InstallResult(name=item.name, success=True)
    except PermissionError:
        return InstallResult(
            name=item.name,
            success=False,
            error=f"Permission denied: {target_file}",
        )
    except Exception as e:
        return InstallResult(name=item.name, success=False, error=str(e))


def install_skill(
    item: ItemInfo,
    target_dir: Path,
    force: bool = False,
    dry_run: bool = False,
    confirm_callback: Callable | None = None,
) -> InstallResult:
    """
    Install a single skill (entire directory).

    Args:
        item: Skill to install.
        target_dir: Target directory.
        force: Overwrite without prompting.
        dry_run: Don't actually copy files.
        confirm_callback: Function to call to confirm overwrite.

    Returns:
        InstallResult with operation status.
    """
    if dry_run:
        return InstallResult(name=item.name, success=True)

    target_path = target_dir / item.path.name

    # Check if directory exists
    if target_path.exists() and not force:
        if confirm_callback and not confirm_callback(item.name):
            return InstallResult(name=item.name, success=True, skipped=True)

    try:
        # Remove existing directory if force or confirmed
        if target_path.exists():
            shutil.rmtree(target_path)

        # Copy the entire skill directory
        shutil.copytree(
            item.path,
            target_path,
            symlinks=False,  # Follow symlinks, copy as regular files
            copy_function=shutil.copy2,  # Preserve metadata including permissions
        )
        return InstallResult(name=item.name, success=True)
    except PermissionError:
        return InstallResult(
            name=item.name,
            success=False,
            error=f"Permission denied: {target_path}",
        )
    except Exception as e:
        return InstallResult(name=item.name, success=False, error=str(e))


def install_items(
    commands: list[ItemInfo],
    skills: list[ItemInfo],
    commands_dir: Path,
    skills_dir: Path,
    force: bool = False,
    dry_run: bool = False,
    confirm_callback: Callable | None = None,
    progress_callback: Callable | None = None,
) -> tuple[list[InstallResult], list[InstallResult]]:
    """
    Install multiple commands and skills.

    Args:
        commands: List of commands to install.
        skills: List of skills to install.
        commands_dir: Target directory for commands.
        skills_dir: Target directory for skills.
        force: Overwrite without prompting.
        dry_run: Don't actually copy files.
        confirm_callback: Function to call to confirm overwrite.
        progress_callback: Function to call after each item.

    Returns:
        Tuple of (command_results, skill_results).
    """
    if not dry_run:
        ensure_target_dirs(commands_dir, skills_dir)

    command_results = []
    for cmd in commands:
        result = install_command(cmd, commands_dir, force, dry_run, confirm_callback)
        command_results.append(result)
        if progress_callback:
            progress_callback(result, commands_dir / cmd.path.name)

    skill_results = []
    for skill in skills:
        result = install_skill(skill, skills_dir, force, dry_run, confirm_callback)
        skill_results.append(result)
        if progress_callback:
            progress_callback(result, skills_dir / skill.path.name)

    return command_results, skill_results


def uninstall_command(
    item: ItemInfo,
    dry_run: bool = False,
) -> UninstallResult:
    """
    Uninstall a single command.

    Args:
        item: Command to uninstall (path points to the installed file).
        dry_run: Don't actually delete files.

    Returns:
        UninstallResult with operation status.
    """
    if dry_run:
        return UninstallResult(name=item.name, success=True)

    try:
        item.path.unlink()
        return UninstallResult(name=item.name, success=True)
    except FileNotFoundError:
        return UninstallResult(
            name=item.name,
            success=False,
            error=f"File not found: {item.path}",
        )
    except PermissionError:
        return UninstallResult(
            name=item.name,
            success=False,
            error=f"Permission denied: {item.path}",
        )
    except Exception as e:
        return UninstallResult(name=item.name, success=False, error=str(e))


def uninstall_skill(
    item: ItemInfo,
    dry_run: bool = False,
) -> UninstallResult:
    """
    Uninstall a single skill (entire directory).

    Args:
        item: Skill to uninstall (path points to the installed directory).
        dry_run: Don't actually delete files.

    Returns:
        UninstallResult with operation status.
    """
    if dry_run:
        return UninstallResult(name=item.name, success=True)

    try:
        shutil.rmtree(item.path)
        return UninstallResult(name=item.name, success=True)
    except FileNotFoundError:
        return UninstallResult(
            name=item.name,
            success=False,
            error=f"Directory not found: {item.path}",
        )
    except PermissionError:
        return UninstallResult(
            name=item.name,
            success=False,
            error=f"Permission denied: {item.path}",
        )
    except Exception as e:
        return UninstallResult(name=item.name, success=False, error=str(e))


def uninstall_items(
    commands: list[ItemInfo],
    skills: list[ItemInfo],
    dry_run: bool = False,
    progress_callback: Callable | None = None,
) -> tuple[list[UninstallResult], list[UninstallResult]]:
    """
    Uninstall multiple commands and skills.

    Args:
        commands: List of commands to uninstall.
        skills: List of skills to uninstall.
        dry_run: Don't actually delete files.
        progress_callback: Function to call after each item.

    Returns:
        Tuple of (command_results, skill_results).
    """
    command_results = []
    for cmd in commands:
        result = uninstall_command(cmd, dry_run)
        command_results.append(result)
        if progress_callback:
            progress_callback(result)

    skill_results = []
    for skill in skills:
        result = uninstall_skill(skill, dry_run)
        skill_results.append(result)
        if progress_callback:
            progress_callback(result)

    return command_results, skill_results
