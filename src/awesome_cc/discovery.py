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
