"""List command placeholder."""

import click


@click.command()
@click.option("--grouped", "-g", is_flag=True, help="Group by batch")
@click.option("--all", "-a", is_flag=True, help="Show all agents")
def list(grouped, all):
    """List all agents."""
    click.echo("No active agents")
