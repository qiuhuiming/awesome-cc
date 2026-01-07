"""UI module for interactive selection and display."""

from pathlib import Path

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .models import ItemInfo

console = Console()

# Special option markers
SELECT_ALL = "[Select All]"
SELECT_NONE = "[Select None]"


def show_header(agent: str, commands_dir: Path, skills_dir: Path) -> None:
    """Display the installer header with target directories."""
    header_text = (
        f"[bold cyan]Awesome Claude Code Installer[/bold cyan]\n"
        f"Agent: [green]{agent}[/green]\n"
        f"Commands: [dim]{commands_dir}[/dim]\n"
        f"Skills:   [dim]{skills_dir}[/dim]"
    )
    console.print(Panel(header_text, expand=False))
    console.print()


def interactive_select(items: list[ItemInfo], item_type: str) -> list[str]:
    """
    Interactive multi-select for items.

    Args:
        items: List of items to choose from.
        item_type: Type of items ("commands" or "skills").

    Returns:
        List of selected item names.
    """
    if not items:
        console.print(f"[yellow]No {item_type} available.[/yellow]")
        return []

    # Build choices with Select All/None options
    choices = [
        questionary.Choice(title=SELECT_ALL, value=SELECT_ALL),
        questionary.Choice(title=SELECT_NONE, value=SELECT_NONE),
        questionary.Separator("─" * 40),
    ]

    for item in items:
        # Truncate description if too long
        desc = item.description[:60] + "..." if len(item.description) > 60 else item.description
        choices.append(
            questionary.Choice(
                title=f"{item.name:<20} - {desc}",
                value=item.name,
            )
        )

    while True:
        selected = questionary.checkbox(
            f"Select {item_type} to install:",
            choices=choices,
            instruction="(Space to select, Enter to confirm)",
        ).ask()

        if selected is None:
            # User cancelled (Ctrl+C)
            return []

        # Handle special options
        if SELECT_ALL in selected:
            return [item.name for item in items]
        if SELECT_NONE in selected:
            return []

        # Filter out any special options that might have been selected
        return [s for s in selected if s not in (SELECT_ALL, SELECT_NONE)]


def show_summary(
    commands: list[str],
    skills: list[str],
    commands_dir: Path,
    skills_dir: Path,
) -> None:
    """Display a summary of what will be installed."""
    if not commands and not skills:
        console.print("[yellow]Nothing selected for installation.[/yellow]")
        return

    table = Table(title="Installation Summary", expand=False)
    table.add_column("Type", style="cyan")
    table.add_column("Items", style="green")
    table.add_column("Target", style="dim")

    if commands:
        table.add_row(
            f"Commands ({len(commands)})",
            ", ".join(commands),
            str(commands_dir),
        )

    if skills:
        table.add_row(
            f"Skills ({len(skills)})",
            ", ".join(skills),
            str(skills_dir),
        )

    console.print()
    console.print(table)
    console.print()


def confirm_install(auto_yes: bool = False) -> bool:
    """Ask user to confirm installation."""
    if auto_yes:
        return True

    return questionary.confirm(
        "Proceed with installation?",
        default=True,
    ).ask() or False


def confirm_overwrite(name: str, force: bool = False) -> bool:
    """Ask user to confirm overwriting an existing file."""
    if force:
        return True

    return questionary.confirm(
        f"'{name}' already exists. Overwrite?",
        default=False,
    ).ask() or False


def show_install_progress(name: str, target: Path, success: bool, skipped: bool = False) -> None:
    """Display installation progress for a single item."""
    if skipped:
        console.print(f"  [yellow]- {name} (skipped)[/yellow]")
    elif success:
        console.print(f"  [green]\u2713 {name}[/green] -> {target}")
    else:
        console.print(f"  [red]\u2717 {name} (failed)[/red]")


def show_completion(commands_installed: int, skills_installed: int) -> None:
    """Display completion message."""
    console.print()
    console.print("[bold green]\u2728 Installation complete![/bold green]")
    if commands_installed > 0:
        console.print(f"   Commands: {commands_installed} installed")
    if skills_installed > 0:
        console.print(f"   Skills: {skills_installed} installed")


def show_list(commands: list[ItemInfo], skills: list[ItemInfo]) -> None:
    """Display available commands and skills."""
    console.print()

    if commands:
        console.print("[bold cyan]Available Commands:[/bold cyan]")
        for cmd in commands:
            desc = cmd.description[:70] + "..." if len(cmd.description) > 70 else cmd.description
            console.print(f"  [green]{cmd.name:<20}[/green] {desc}")
        console.print()

    if skills:
        console.print("[bold cyan]Available Skills:[/bold cyan]")
        for skill in skills:
            desc = skill.description[:70] + "..." if len(skill.description) > 70 else skill.description
            console.print(f"  [green]{skill.name:<20}[/green] {desc}")
        console.print()

    console.print(f"[dim]Total: {len(commands)} commands, {len(skills)} skills[/dim]")


def show_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[bold red]Error:[/bold red] {message}")


def show_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def show_invalid_names(invalid: list[str], item_type: str, valid_names: list[str]) -> None:
    """Show error for invalid names with suggestions."""
    show_error(f"Unknown {item_type}: {', '.join(invalid)}")
    console.print(f"[dim]Available {item_type}: {', '.join(valid_names)}[/dim]")
    console.print("[dim]Use --list to see all available items.[/dim]")
