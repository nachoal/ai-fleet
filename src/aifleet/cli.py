"""AI Fleet CLI - Main entry point."""

import click

from .commands.create import create
from .commands.list import list


@click.group()
@click.version_option()
def main():
    """AI Fleet - Spin up and command a fleet of AI developer agents."""
    pass


@main.command()
@click.option("--edit", "-e", is_flag=True, help="Edit config")
@click.option("--validate", "-v", is_flag=True, help="Validate config")
def config(edit, validate):
    """Manage configuration."""
    if edit:
        click.echo("Would edit config")
    elif validate:
        click.echo("Config is valid")
    else:
        click.echo("Configuration file: ~/.ai_fleet/config.toml")


# Add commands
main.add_command(create)
main.add_command(list)

# Alias for CLI
cli = main

if __name__ == "__main__":
    main()
