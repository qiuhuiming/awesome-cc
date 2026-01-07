"""Data models for the installer."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class ItemInfo:
    """Information about a command or skill."""

    name: str
    description: str
    path: Path
    item_type: Literal["command", "skill"]

    def __str__(self) -> str:
        return f"{self.name} - {self.description}"


@dataclass
class InstallResult:
    """Result of an installation operation."""

    name: str
    success: bool
    skipped: bool = False
    error: str | None = None
