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
