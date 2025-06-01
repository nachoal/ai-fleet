"""Base utilities for commands."""

import click

from ..config import ConfigManager


def ensure_project_config() -> ConfigManager:
    """Ensure we have a valid project configuration.

    Returns:
        ConfigManager instance

    Raises:
        SystemExit: If not in a git repo or no project config
    """
    config = ConfigManager()

    if not config.is_git_repository:
        click.echo("❌ Not in a git repository", err=True)
        click.echo(
            "\nAI Fleet requires a git repository to manage worktrees.", err=True
        )
        click.echo("Initialize a git repository first:", err=True)
        click.echo("  git init", err=True)
        raise SystemExit(1)

    if not config.has_project_config:
        click.echo("❌ No AI Fleet configuration found in this project", err=True)
        click.echo(f"\nProject root: {config.project_root}", err=True)
        click.echo("\nTo use AI Fleet in this project, run:", err=True)
        click.echo("  fleet init", err=True)
        click.echo(
            "\nThis will create a .aifleet/config.toml file with "
            "project-specific settings.",
            err=True,
        )

        if config.has_legacy_config():
            click.echo(
                "\n💡 Found legacy global config. You can import it with:", err=True
            )
            click.echo("  fleet init --migrate-legacy", err=True)

        raise SystemExit(1)

    return config
