"""AI Fleet CLI entry point."""

import sys

import click

from .commands.attach import attach
from .commands.create import create
from .commands.fanout import fanout
from .commands.kill import kill
from .commands.list import list
from .commands.logs import logs
from .commands.multi import multi
from .commands.prompt import prompt
from .config import ConfigManager


@click.group()
@click.version_option(package_name="ai-fleet")
def cli():
    """AI Fleet - Manage AI coding agents in parallel.

    Spin up and command a fleet of AI developer agents from your terminal.
    Each agent runs in its own git worktree with an isolated tmux session.
    """
    # Ensure config exists
    config = ConfigManager()
    if not config.config_file.exists():
        click.echo("Creating default configuration...", err=True)
        config.create_default_config()


@cli.command()
@click.option("--edit", "-e", is_flag=True, help="Open config file in editor")
@click.option("--validate", "-v", is_flag=True, help="Validate configuration")
def config(edit: bool, validate: bool):
    """Manage AI Fleet configuration."""
    config_mgr = ConfigManager()

    if edit:
        import os
        import subprocess

        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, str(config_mgr.config_file)])
    elif validate:
        errors = config_mgr.validate()
        if errors:
            click.echo("Configuration errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        else:
            click.echo("✅ Configuration is valid")
    else:
        # Show current config
        click.echo(f"Configuration file: {config_mgr.config_file}")
        click.echo("\nCurrent settings:")
        with open(config_mgr.config_file, "r") as f:
            click.echo(f.read())


# Add commands to CLI
cli.add_command(create)
cli.add_command(list)
cli.add_command(prompt)
cli.add_command(attach)
cli.add_command(logs)
cli.add_command(kill)
cli.add_command(fanout)
cli.add_command(multi)


# Create flt alias
flt = cli

# Alias for CLI
main = cli

if __name__ == "__main__":
    cli()
