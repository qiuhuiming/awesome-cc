"""UI module for interactive selection and display."""

import questionary
from rich.console import Console

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
