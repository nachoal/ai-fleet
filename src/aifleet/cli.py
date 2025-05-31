"""AI Fleet CLI - Main entry point."""

import click


@click.group()
@click.version_option()
def main():
    """AI Fleet - Spin up and command a fleet of AI developer agents from your terminal."""
    pass


@main.command()
def list():
    """List all running agents."""
    click.echo("No agents running yet. This is a placeholder command.")


if __name__ == "__main__":
    main()