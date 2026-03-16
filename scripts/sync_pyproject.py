#!/usr/bin/env python3
"""Scan skills/ directory and sync [tool.setuptools.data-files] in pyproject.toml."""

import re
from collections import defaultdict
from pathlib import Path

IGNORE_PATTERNS = {"__pycache__", ".pyc", ".pyo", ".DS_Store"}

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def should_ignore(path: Path) -> bool:
    return any(part in IGNORE_PATTERNS or part.startswith(".") for part in path.parts)


def scan_directory(base_dir: Path, prefix: str) -> dict[str, list[str]]:
    """Scan a directory and group files by their parent directory.

    Returns a dict mapping destination paths to lists of source file paths.
    e.g. "share/awesome-cc/skills/uv/references" -> ["skills/uv/references/cli_reference.md", ...]
    """
    groups: dict[str, list[str]] = defaultdict(list)
    if not base_dir.exists():
        return groups

    for file_path in sorted(base_dir.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(PROJECT_ROOT)
        if should_ignore(rel):
            continue
        parent_rel = rel.parent
        dest_key = f"share/awesome-cc/{parent_rel}"
        groups[dest_key].append(str(rel))

    return dict(sorted(groups.items()))


def generate_data_files_section() -> str:
    """Generate the [tool.setuptools.data-files] TOML section content."""
    all_groups: dict[str, list[str]] = {}

    for dirname in ("skills",):
        dir_path = PROJECT_ROOT / dirname
        all_groups.update(scan_directory(dir_path, dirname))

    if not all_groups:
        return "[tool.setuptools.data-files]\n"

    lines = ["[tool.setuptools.data-files]"]
    for dest, files in all_groups.items():
        if len(files) == 1:
            lines.append(f'"{dest}" = ["{files[0]}"]')
        else:
            lines.append(f'"{dest}" = [')
            for f in files:
                lines.append(f'    "{f}",')
            lines.append("]")

    return "\n".join(lines) + "\n"


def update_pyproject(pyproject_path: Path) -> None:
    content = pyproject_path.read_text(encoding="utf-8")

    new_section = generate_data_files_section()

    # Match the existing [tool.setuptools.data-files] section up to the next top-level section or EOF
    pattern = r"\[tool\.setuptools\.data-files\]\n(?:.*\n)*?(?=\n\[|\Z)"
    match = re.search(pattern, content)

    if match:
        content = content[: match.start()] + new_section + content[match.end() :]
    else:
        # Append if section doesn't exist
        content = content.rstrip() + "\n\n" + new_section

    pyproject_path.write_text(content, encoding="utf-8")


def main() -> None:
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"Error: {pyproject_path} not found")
        return

    update_pyproject(pyproject_path)

    # Print summary
    groups = {}
    for dirname in ("skills",):
        dir_path = PROJECT_ROOT / dirname
        groups.update(scan_directory(dir_path, dirname))

    total_files = sum(len(v) for v in groups.values())
    print(f"Synced {len(groups)} entries ({total_files} files) to pyproject.toml")


if __name__ == "__main__":
    main()
