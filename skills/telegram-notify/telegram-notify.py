#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx>=0.27", "typer>=0.12"]
# ///
"""
Telegram notification script for Claude Code and Codex agents.

Sends formatted notifications to a Telegram chat when tasks complete,
fail, or need user input.

Environment variables:
    TELEGRAM_BOT_TOKEN: Bot token from @BotFather
    TELEGRAM_CHAT_ID: Your personal/group chat ID
"""

from __future__ import annotations

import html
import os
import subprocess
import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated

import httpx
import typer

app = typer.Typer(add_completion=False)


class Status(str, Enum):
    success = "success"
    error = "error"
    blocked = "blocked"


STATUS_CONFIG = {
    Status.success: {"icon": "\u2705", "title": "Task Completed"},
    Status.error: {"icon": "\u274c", "title": "Task Failed"},
    Status.blocked: {"icon": "\u23f8\ufe0f", "title": "Waiting for Input"},
}


def html_escape(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    return html.escape(text)


def truncate(text: str, max_len: int = 4000) -> str:
    """Truncate text to fit Telegram's 4096 char limit."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def detect_agent() -> str:
    """Detect which agent is running."""
    if os.getenv("CLAUDECODE") == "1":
        return "Claude Code"
    elif Path.home().joinpath(".codex").exists():
        return "Codex"
    return "Unknown"


def get_claude_session_id() -> str | None:
    """Get Claude Code session ID from most recent session-env dir."""
    session_dir = Path.home() / ".claude" / "session-env"
    if not session_dir.exists():
        return None
    try:
        sessions = sorted(
            [p for p in session_dir.iterdir() if p.is_dir()],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return sessions[0].name[:8] if sessions else None
    except (OSError, IndexError):
        return None


def get_git_branch() -> str:
    """Get current git branch."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        branch = result.stdout.strip()
        return branch if branch else "detached"
    except Exception:
        return "N/A"


def shorten_path(path: str) -> str:
    """Replace home dir with ~."""
    home = str(Path.home())
    if path.startswith(home):
        return "~" + path[len(home) :]
    return path


def get_context(
    pwd_override: str | None = None,
    branch_override: str | None = None,
    session_override: str | None = None,
) -> dict:
    """Gather context with optional overrides."""
    agent = detect_agent()
    session_id = session_override
    if session_id is None and agent == "Claude Code":
        session_id = get_claude_session_id()
    # TODO: Add Codex session ID detection

    return {
        "agent": agent,
        "pwd": shorten_path(pwd_override or os.getcwd()),
        "git_branch": branch_override or get_git_branch(),
        "session_id": session_id,
    }


def format_message(
    status: Status,
    summary: str,
    todos: list[str],
    ctx: dict,
) -> str:
    """Format message with HTML escaping and truncation."""
    config = STATUS_CONFIG[status]
    icon = config["icon"]
    title = config["title"]

    # Escape all user inputs
    summary_escaped = html_escape(summary)
    todos_escaped = [html_escape(t) for t in todos]
    pwd_escaped = html_escape(ctx["pwd"])
    branch_escaped = html_escape(ctx["git_branch"])
    agent_escaped = html_escape(ctx["agent"])

    # Build message
    lines = [
        f'{icon} <b>{title}</b>',
        "",
        f'\U0001f916 {agent_escaped}',
        f'\U0001f4c2 <code>{pwd_escaped}</code>',
        f'\U0001f33f <code>{branch_escaped}</code>',
    ]

    if ctx["session_id"]:
        session_escaped = html_escape(ctx["session_id"])
        lines.append(f'\U0001f194 <code>{session_escaped}</code>')

    lines.extend([
        "",
        "\u2501" * 20,
        "",
        "<b>\U0001f4cb Summary</b>",
        summary_escaped,
    ])

    if todos_escaped:
        lines.extend([
            "",
            "<b>\U0001f4dd Your TODOs</b>",
        ])
        for todo in todos_escaped[:5]:  # Max 5 TODOs
            lines.append(f"\u2022 {todo}")

    lines.extend([
        "",
        "\u2501" * 20,
        f'\u23f1\ufe0f {datetime.now().strftime("%Y-%m-%d %H:%M")}',
    ])

    message = "\n".join(lines)
    return truncate(message)


def send_telegram_message(text: str, dry_run: bool = False) -> bool:
    """Send message via Telegram Bot API with retry logic."""
    if dry_run:
        print("=== DRY RUN - Message not sent ===")
        print(text)
        print("=== END DRY RUN ===")
        return True

    # Get env vars
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    missing = []
    if not token:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not chat_id:
        missing.append("TELEGRAM_CHAT_ID")

    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        print("\nSet them in your shell:", file=sys.stderr)
        print("  export TELEGRAM_BOT_TOKEN='your-bot-token'", file=sys.stderr)
        print("  export TELEGRAM_CHAT_ID='your-chat-id'", file=sys.stderr)
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
    }

    max_retries = 2
    for attempt in range(max_retries):
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=payload)

                if response.status_code == 200:
                    print("Notification sent successfully!")
                    return True

                # Handle rate limiting
                if response.status_code == 429:
                    try:
                        data = response.json()
                        retry_after = data.get("parameters", {}).get("retry_after", 5)
                        print(f"Rate limited. Waiting {retry_after}s before retry...", file=sys.stderr)
                        time.sleep(retry_after)
                        continue
                    except Exception:
                        time.sleep(5)
                        continue

                # Log error and retry on server errors
                if response.status_code >= 500 and attempt < max_retries - 1:
                    print(f"Server error {response.status_code}. Retrying...", file=sys.stderr)
                    time.sleep(2)
                    continue

                # Non-retryable error
                print(f"Error: Telegram API returned {response.status_code}", file=sys.stderr)
                try:
                    error_body = response.json()
                    print(f"Response: {error_body}", file=sys.stderr)
                except Exception:
                    print(f"Response: {response.text}", file=sys.stderr)
                return False

        except httpx.TimeoutException:
            if attempt < max_retries - 1:
                print("Request timed out. Retrying...", file=sys.stderr)
                continue
            print("Error: Request timed out after retries", file=sys.stderr)
            return False
        except httpx.RequestError as e:
            print(f"Error: Network error - {e}", file=sys.stderr)
            return False

    return False


@app.command()
def main(
    status: Annotated[Status, typer.Option("--status", "-s", help="Task status")] = Status.success,
    summary: Annotated[str, typer.Option("--summary", "-m", help="Summary of what was done (max 500 chars)")] = "",
    todo: Annotated[list[str] | None, typer.Option("--todo", "-t", help="Action item for user (repeatable)")] = None,
    pwd: Annotated[str | None, typer.Option("--pwd", help="Override working directory")] = None,
    branch: Annotated[str | None, typer.Option("--branch", help="Override git branch")] = None,
    session: Annotated[str | None, typer.Option("--session", help="Override session ID")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Print message without sending")] = False,
) -> None:
    """
    Send a Telegram notification about task completion.

    Example:
        uv run telegram-notify.py --status success --summary "Built the project" --todo "Review changes"
    """
    if not summary:
        print("Error: --summary is required", file=sys.stderr)
        raise typer.Exit(1)

    # Enforce limits
    if len(summary) > 500:
        summary = summary[:497] + "..."

    todos = todo or []
    if len(todos) > 5:
        todos = todos[:5]

    # Gather context
    ctx = get_context(pwd, branch, session)

    # Format and send
    message = format_message(status, summary, todos, ctx)
    success = send_telegram_message(message, dry_run=dry_run)

    if not success:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
