"""Update command for AI Fleet."""

import click

from ..updater import (
    UpdateChecker,
    get_installation_method,
    update_via_pip,
    update_via_pipx,
    update_via_uv,
)


@click.command()
@click.option("--check", is_flag=True, help="Only check for updates without installing")
@click.option("--force", is_flag=True, help="Force update check (bypass cache)")
def update(check: bool, force: bool) -> None:
    """Check for and install updates to AI Fleet."""
    from .. import __version__

    checker = UpdateChecker(__version__)
    update_available, latest_version = checker.check_for_updates(force=force)

    if not update_available:
        click.echo(f"✅ AI Fleet is up to date (v{__version__})")
        return

    click.echo(f"🆕 Update available: v{__version__} → v{latest_version}")

    if check:
        click.echo("\nRun 'fleet update' to install the latest version")
        return

    # Detect installation method
    install_method = get_installation_method()

    click.echo(f"\nDetected installation method: {install_method}")

    if install_method == "pipx":
        click.echo("Updating via pipx...")
        if update_via_pipx():
            click.echo("✅ Successfully updated AI Fleet")
            click.echo(
                "\n🔄 Please restart your terminal or run 'hash -r' "
                "to use the new version"
            )
        else:
            click.echo(
                "❌ Failed to update. Run manually: pipx upgrade ai-fleet", err=True
            )
            raise SystemExit(1)

    elif install_method == "pip":
        click.echo("Updating via pip...")
        if update_via_pip():
            click.echo("✅ Successfully updated AI Fleet")
            click.echo("\n🔄 Please restart your terminal to use the new version")
        else:
            click.echo(
                "❌ Failed to update. Run manually: pip install --upgrade ai-fleet",
                err=True,
            )
            raise SystemExit(1)

    elif install_method == "uv":
        click.echo("Updating via uv...")
        if update_via_uv():
            click.echo("✅ Successfully updated AI Fleet")
        else:
            click.echo(
                "❌ Failed to update. Run manually: uv pip install --upgrade ai-fleet",
                err=True,
            )
            raise SystemExit(1)

    elif install_method == "source":
        click.echo("\n📝 You're running from source. To update:")
        click.echo("   git pull origin main")
        click.echo("   uv pip install -e .")
        click.echo("\nOr if using pip:")
        click.echo("   git pull origin main")
        click.echo("   pip install -e .")
    else:
        click.echo("\n⚠️  Unable to detect installation method.")
        click.echo("Please update manually using your package manager:")
        click.echo("  - pipx: pipx upgrade ai-fleet")
        click.echo("  - pip: pip install --upgrade ai-fleet")
        click.echo("  - uv: uv pip install --upgrade ai-fleet")
