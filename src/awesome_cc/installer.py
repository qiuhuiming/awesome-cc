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
