"""CLI module for the installer."""

from typing import Annotated, Optional

import typer
from rich.console import Console

from . import __version__
from .discovery import (
    discover_installed_skills,
    discover_skills,
    validate_names,
)
from .installer import VALID_AGENTS, get_skills_dir, install_skills, uninstall_skills
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
