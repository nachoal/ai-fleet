"""Initialize AI Fleet configuration in a project."""

from pathlib import Path

import click

from ..config import ConfigManager


def detect_project_type(project_root: Path) -> str:
    """Detect the type of project based on files present.

    Args:
        project_root: The project root directory

    Returns:
        Project type string (rails, node, python, etc.)
    """
    # Check for Rails
    if (project_root / "Gemfile").exists() and any(
        file.name in ["rails", "bin/rails"] for file in project_root.rglob("*")
    ):
        return "rails"

    # Check for Node.js
    if (project_root / "package.json").exists():
        return "node"

    # Check for Python
    if (project_root / "requirements.txt").exists() or (
        project_root / "pyproject.toml"
    ).exists():
        return "python"

    return "generic"


@click.command()
@click.option(
    "--type",
    "project_type",
    type=click.Choice(["rails", "node", "python", "generic", "minimal"]),
    help="Project type for configuration defaults",
)
@click.option(
    "--migrate-legacy", is_flag=True, help="Migrate from legacy global config"
)
def init(project_type: str, migrate_legacy: bool) -> None:
    """Initialize AI Fleet configuration for this project.

    This creates a .aifleet/config.toml file with sensible defaults
    based on your project type.
    """
    config = ConfigManager()

    # Check if we're in a git repository
    if not config.is_git_repository:
        click.echo("❌ Not in a git repository", err=True)
        click.echo("AI Fleet requires a git repository to manage worktrees.", err=True)
        raise SystemExit(1)

    # Check if already initialized
    if config.has_project_config and not migrate_legacy:
        click.echo("❌ Project already initialized", err=True)
        click.echo(f"Configuration exists at: {config.project_config_file}", err=True)
        click.echo("\nTo edit configuration, run: fleet config --edit", err=True)
        raise SystemExit(1)

    if not config.project_root:
        click.echo("❌ Unable to determine project root", err=True)
        raise SystemExit(1)

    project_name = config.project_root.name

    # Handle legacy migration
    if migrate_legacy and config.has_legacy_config():
        click.echo("Migrating from legacy global configuration...")
        config.migrate_legacy_config()
        click.echo("✅ Migration complete!")
        return

    # Auto-detect project type if not specified
    if not project_type:
        project_type = detect_project_type(config.project_root)
        if project_type != "generic":
            click.echo(f"Detected project type: {project_type}")

    # Get project type name for display
    project_type_names = {
        "rails": "Ruby on Rails",
        "node": "Node.js",
        "python": "Python",
        "generic": "Generic",
        "minimal": "Minimal",
    }

    click.echo(f"\nInitializing AI Fleet for project: {project_name}")
    click.echo(f"Project type: {project_type_names.get(project_type, project_type)}")

    # Show what will be created
    if project_type == "rails":
        click.echo("\nConfiguration will include:")
        click.echo("  • Credential files: config/master.key, .env, .env.local")
        click.echo("  • Setup commands: bundle install, yarn install, db:migrate")
    elif project_type == "node":
        click.echo("\nConfiguration will include:")
        click.echo("  • Credential files: .env, .env.local")
        click.echo("  • Setup commands: npm install")
    elif project_type == "python":
        click.echo("\nConfiguration will include:")
        click.echo("  • Credential files: .env")
        click.echo("  • Setup commands: pip install -r requirements.txt")
    elif project_type == "minimal":
        click.echo("\nMinimal configuration (no credential files or setup commands)")

    if not click.confirm("\nCreate configuration?"):
        click.echo("Cancelled.")
        return

    # Initialize the project
    try:
        config.initialize_project(project_type)
        click.echo(f"\n✅ Created {config.project_config_file}")

        # Add to .gitignore if needed
        gitignore_path = (
            config.project_root / ".gitignore"
            if config.project_root
            else Path(".gitignore")
        )
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                gitignore_content = f.read()

            if ".aifleet/worktrees/" not in gitignore_content:
                with open(gitignore_path, "a") as f:
                    if not gitignore_content.endswith("\n"):
                        f.write("\n")
                    f.write("\n# AI Fleet worktrees\n")
                    f.write(".aifleet/worktrees/\n")
                click.echo("✅ Added .aifleet/worktrees/ to .gitignore")

        click.echo("\nNext steps:")
        click.echo("  1. Review configuration: fleet config")
        click.echo("  2. Edit if needed: fleet config --edit")
        click.echo(
            "  3. Create your first agent: fleet create <branch> --prompt '<task>'"
        )

        # Check for legacy config
        if config.has_legacy_config():
            click.echo(
                "\n💡 Found legacy global config. "
                "Run 'fleet init --migrate-legacy' to import it."
            )

    except Exception as e:
        click.echo(f"❌ Error initializing project: {e}", err=True)
        raise SystemExit(1) from e
