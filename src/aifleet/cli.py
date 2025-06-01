"""AI Fleet CLI entry point."""

import sys

import click

from .commands.attach import attach
from .commands.create import create
from .commands.fanout import fanout
from .commands.init import init
from .commands.kill import kill
from .commands.list import list
from .commands.logs import logs
from .commands.multi import multi
from .commands.prompt import prompt
from .commands.update import update
from .config import ConfigManager


@click.group()
@click.version_option(package_name="ai-fleet")
def cli():
    """AI Fleet - Manage AI coding agents in parallel.

    Spin up and command a fleet of AI developer agents from your terminal.
    Each agent runs in its own git worktree with an isolated tmux session.
    """
    pass


@cli.command()
@click.option("--edit", "-e", is_flag=True, help="Open config file in editor")
@click.option("--validate", "-v", is_flag=True, help="Validate configuration")
@click.option("--show-origin", is_flag=True, help="Show where each setting comes from")
def config(edit: bool, validate: bool, show_origin: bool):
    """Manage AI Fleet configuration."""
    config_mgr = ConfigManager()

    if edit:
        import os
        import subprocess

        if not config_mgr.has_project_config:
            click.echo("❌ No project configuration found.", err=True)
            click.echo("Run 'fleet init' to initialize this project.", err=True)
            sys.exit(1)

        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, str(config_mgr.project_config_file)])
    elif validate:
        errors = config_mgr.validate()
        if errors:
            click.echo("Configuration errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        else:
            click.echo("✅ Configuration is valid")
    elif show_origin:
        # Show config with sources
        info = config_mgr.get_config_info()
        click.echo("Configuration sources:")
        click.echo(f"  Project root: {info['project_root'] or 'Not in git repository'}")
        click.echo(f"  Project config: {info['project_config'] or 'None'}")
        click.echo(f"  User config: {info['user_config']}")
        click.echo(f"  Using defaults: {info['using_defaults']}")
    else:
        # Show current config
        if not config_mgr.is_git_repository:
            click.echo("❌ Not in a git repository", err=True)
            sys.exit(1)

        if not config_mgr.has_project_config:
            click.echo("❌ No project configuration found.", err=True)
            click.echo("\nRun 'fleet init' to initialize this project.", err=True)
            sys.exit(1)

        if config_mgr.project_root:
            click.echo(f"Project: {config_mgr.project_root.name}")
        click.echo(f"Configuration file: {config_mgr.project_config_file}")
        click.echo("\nCurrent settings:")
        if config_mgr.project_config_file:
            with open(config_mgr.project_config_file, "r") as f:
                click.echo(f.read())


# Add commands to CLI
cli.add_command(init)
cli.add_command(create)
cli.add_command(list)
cli.add_command(prompt)
cli.add_command(attach)
cli.add_command(logs)
cli.add_command(kill)
cli.add_command(fanout)
cli.add_command(multi)
cli.add_command(update)


# Create flt alias
flt = cli

# Alias for CLI
main = cli

if __name__ == "__main__":
    cli()
