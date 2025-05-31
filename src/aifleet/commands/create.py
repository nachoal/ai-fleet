"""Create command placeholder."""

import click


@click.command()
@click.argument("branch")
@click.option("--prompt", "-p", help="Initial prompt")
def create(branch, prompt):
    """Create a new agent."""
    click.echo(f"Would create agent on branch {branch}")