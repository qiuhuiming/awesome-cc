"""CLI module for the installer."""

from typing import Annotated, Optional

import typer
from rich.console import Console

from . import __version__
from .discovery import (
    discover_commands,
    discover_skills,
    get_item_by_name,
    validate_names,
)
from .installer import get_target_dirs, install_items
from .models import InstallResult
from .ui import (
    confirm_install,
    confirm_overwrite,
    interactive_select,
    show_completion,
    show_error,
    show_header,
    show_install_progress,
    show_invalid_names,
    show_list,
    show_summary,
)

app = typer.Typer(
    name="acc-install",
    help="Interactive CLI installer for Claude Code skills and commands.",
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


@app.command()
def install(
    agent: Annotated[
        Optional[str],
        typer.Option(
            "--agent",
            "-a",
            help="Target agent: claude-code or codex",
        ),
    ] = None,
    commands: Annotated[
        Optional[list[str]],
        typer.Option(
            "--commands",
            "-c",
            help="Install specific commands by name",
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
    commands_only: Annotated[
        bool,
        typer.Option(
            "--commands-only",
            help="Interactive mode: only prompt for commands",
        ),
    ] = False,
    skills_only: Annotated[
        bool,
        typer.Option(
            "--skills-only",
            help="Interactive mode: only prompt for skills",
        ),
    ] = False,
    all_items: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Install all commands and skills",
        ),
    ] = False,
    list_items: Annotated[
        bool,
        typer.Option(
            "--list",
            "-l",
            help="List available commands and skills",
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
            help="Auto-confirm all prompts",
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
    """Install commands and skills for Claude Code or Codex."""
    # Discover available items
    available_commands = discover_commands()
    available_skills = discover_skills()

    # Handle --list (doesn't require --agent)
    if list_items:
        show_list(available_commands, available_skills)
        raise typer.Exit()

    # Validate agent is provided for install operations
    if not agent:
        show_error("--agent is required for installation. Use 'claude-code' or 'codex'.")
        raise typer.Exit(1)

    # Validate agent name
    if agent not in ("claude-code", "codex"):
        show_error(f"Unknown agent: {agent}. Must be 'claude-code' or 'codex'.")
        raise typer.Exit(1)

    # Get target directories
    commands_dir, skills_dir = get_target_dirs(agent)

    # Validate mutually exclusive options
    selector_count = sum([
        bool(commands),
        bool(skills),
        commands_only,
        skills_only,
        all_items,
    ])
    if all_items and selector_count > 1:
        show_error("--all cannot be combined with --commands, --skills, --commands-only, or --skills-only")
        raise typer.Exit(1)

    # Determine which items to install
    selected_commands: list[str] = []
    selected_skills: list[str] = []

    if all_items:
        # Install all
        selected_commands = [c.name for c in available_commands]
        selected_skills = [s.name for s in available_skills]
    elif commands or skills:
        # Direct specification mode
        if commands:
            valid, invalid = validate_names(commands, available_commands)
            if invalid:
                show_invalid_names(invalid, "commands", [c.name for c in available_commands])
                raise typer.Exit(1)
            selected_commands = valid

        if skills:
            valid, invalid = validate_names(skills, available_skills)
            if invalid:
                show_invalid_names(invalid, "skills", [s.name for s in available_skills])
                raise typer.Exit(1)
            selected_skills = valid
    else:
        # Interactive mode
        show_header(agent, commands_dir, skills_dir)

        if not skills_only:
            selected_commands = interactive_select(available_commands, "commands")

        if not commands_only:
            selected_skills = interactive_select(available_skills, "skills")

    # Nothing to install?
    if not selected_commands and not selected_skills:
        console.print("[yellow]Nothing to install.[/yellow]")
        raise typer.Exit()

    # Show summary
    show_summary(selected_commands, selected_skills, commands_dir, skills_dir)

    # Confirm installation
    if not confirm_install(auto_yes=yes):
        console.print("[yellow]Installation cancelled.[/yellow]")
        raise typer.Exit()

    # Get item objects
    commands_to_install = [
        get_item_by_name(available_commands, name)
        for name in selected_commands
    ]
    commands_to_install = [c for c in commands_to_install if c is not None]

    skills_to_install = [
        get_item_by_name(available_skills, name)
        for name in selected_skills
    ]
    skills_to_install = [s for s in skills_to_install if s is not None]

    # Install
    if dry_run:
        console.print("[cyan]Dry run - no files will be copied:[/cyan]")

    console.print("\nInstalling...")

    def progress_callback(result: InstallResult, target: str) -> None:
        show_install_progress(result.name, target, result.success, result.skipped)

    def overwrite_callback(name: str) -> bool:
        # If --yes is passed, auto-confirm overwrites
        if yes:
            return True
        return confirm_overwrite(name, force=False)

    command_results, skill_results = install_items(
        commands=commands_to_install,
        skills=skills_to_install,
        commands_dir=commands_dir,
        skills_dir=skills_dir,
        force=force,
        dry_run=dry_run,
        confirm_callback=overwrite_callback if not (force or yes) else None,
        progress_callback=progress_callback,
    )

    # Count results
    commands_installed = sum(1 for r in command_results if r.success and not r.skipped)
    skills_installed = sum(1 for r in skill_results if r.success and not r.skipped)

    # Show completion
    show_completion(commands_installed, skills_installed)


if __name__ == "__main__":
    app()
