"""Configuration management for AI Fleet."""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml


class ConfigManager:
    """Manages AI Fleet configuration with project-based support."""

    PROJECT_CONFIG_DIR = ".aifleet"
    PROJECT_CONFIG_FILE = "config.toml"
    USER_CONFIG_FILE = "config.toml"

    DEFAULT_PROJECT_CONFIG = {
        "project": {
            "name": None,  # Will be set from directory name
            "worktree_root": None,  # Will be set to ~/.aifleet/worktrees/<project-name>
        },
        "agent": {
            "default": "claude",
            "claude_flags": "--dangerously-skip-permissions",
        },
        "setup": {
            "credential_files": [],
            "commands": [],
            "quick": False,
        },
        "tmux": {
            "prefix": "ai_",
        },
    }

    DEFAULT_USER_CONFIG = {
        "defaults": {
            "agent": "claude",
            "worktree_base": str(Path.home() / ".aifleet" / "worktrees"),
        },
        "ui": {
            "color": True,
            "log_lines": 50,
        },
        "updates": {
            "check_on_startup": True,
            "check_interval_hours": 24,
        },
    }

    def __init__(self, project_root: Optional[Path] = None):
        """Initialize config manager.

        Args:
            project_root: Override project root (mainly for testing)
        """
        self._project_root = project_root
        self._project_config: Dict[str, Any] = {}
        self._user_config: Dict[str, Any] = {}
        self._using_defaults = False
        self.load()

    @property
    def project_root(self) -> Optional[Path]:
        """Get the project root directory."""
        if self._project_root:
            return self._project_root

        # Search upward from current directory for .git
        current = Path.cwd()
        while current != current.parent:
            if (current / ".git").exists():
                self._project_root = current
                return current
            current = current.parent

        return None

    @property
    def project_config_file(self) -> Optional[Path]:
        """Get the project configuration file path."""
        if not self.project_root:
            return None
        return self.project_root / self.PROJECT_CONFIG_DIR / self.PROJECT_CONFIG_FILE

    @property
    def user_config_dir(self) -> Path:
        """Get user configuration directory following XDG spec."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "aifleet"
        return Path.home() / ".config" / "aifleet"

    @property
    def user_config_file(self) -> Path:
        """Get user configuration file path."""
        return self.user_config_dir / self.USER_CONFIG_FILE

    @property
    def is_git_repository(self) -> bool:
        """Check if we're in a git repository."""
        return self.project_root is not None

    @property
    def has_project_config(self) -> bool:
        """Check if project has AI Fleet configuration."""
        return (
            self.project_config_file is not None and self.project_config_file.exists()
        )

    def load(self) -> None:
        """Load configuration from disk."""
        # Load user config
        if self.user_config_file.exists():
            try:
                with open(self.user_config_file, "r") as f:
                    self._user_config = toml.load(f)
            except Exception as e:
                print(f"Error loading user config: {e}", file=sys.stderr)
                self._user_config = {}

        # Load project config
        if self.project_config_file and self.project_config_file.exists():
            try:
                with open(self.project_config_file, "r") as f:
                    self._project_config = toml.load(f)
            except Exception as e:
                print(f"Error loading project config: {e}", file=sys.stderr)
                self._project_config = {}
        else:
            self._using_defaults = True

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with hierarchy: project > user > defaults.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        # Try project config first
        value = self._get_from_dict(self._project_config, key)
        if value is not None:
            return value

        # Try user config
        value = self._get_from_dict(self._user_config, key)
        if value is not None:
            return value

        # Try defaults
        if (
            key.startswith("project.")
            or key.startswith("agent.")
            or key.startswith("setup.")
            or key.startswith("tmux.")
        ):
            value = self._get_from_dict(self.DEFAULT_PROJECT_CONFIG, key)
        else:
            value = self._get_from_dict(self.DEFAULT_USER_CONFIG, key)

        if value is not None:
            return value

        return default

    def _get_from_dict(self, config: Dict[str, Any], key: str) -> Any:
        """Get value from dictionary using dot notation."""
        parts = key.split(".")
        value = config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        return value

    def set(self, key: str, value: Any, target: str = "project") -> None:
        """Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
            target: Where to save ("project" or "user")
        """
        if target == "project" and not self.has_project_config:
            raise ValueError("No project configuration found. Run 'fleet init' first.")

        config = self._project_config if target == "project" else self._user_config
        parts = key.split(".")

        # Navigate to the parent dict
        current = config
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set the value
        current[parts[-1]] = value

    def save(self, target: str = "project") -> None:
        """Save configuration to disk.

        Args:
            target: Which config to save ("project" or "user")
        """
        if target == "project":
            if not self.project_config_file:
                raise ValueError("Not in a git repository")

            self.project_config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.project_config_file, "w") as f:
                toml.dump(self._project_config, f)
        else:
            self.user_config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.user_config_file, "w") as f:
                toml.dump(self._user_config, f)

    def initialize_project(self, project_type: Optional[str] = None) -> None:
        """Initialize project configuration.

        Args:
            project_type: Type of project (rails, node, python, etc.)
        """
        if not self.project_root:
            raise ValueError("Not in a git repository")

        if self.has_project_config:
            raise ValueError("Project already initialized")

        # Create default config
        project_name = self.project_root.name
        # Deep copy the default config to avoid modifying the class attribute
        import copy

        config: Dict[str, Any] = copy.deepcopy(self.DEFAULT_PROJECT_CONFIG)
        config["project"]["name"] = project_name

        # Set worktree root based on project name
        worktree_base = self.get(
            "defaults.worktree_base", str(Path.home() / ".aifleet" / "worktrees")
        )
        config["project"]["worktree_root"] = str(Path(worktree_base) / project_name)

        # Apply project type specific defaults
        if project_type == "rails":
            config["setup"]["credential_files"] = [
                "config/master.key",
                ".env",
                ".env.local",
            ]
            config["setup"]["commands"] = [
                "bundle install",
                "yarn install",
                "bundle exec rails db:migrate",
            ]
        elif project_type == "node":
            config["setup"]["credential_files"] = [".env", ".env.local"]
            config["setup"]["commands"] = ["npm install"]
        elif project_type == "python":
            config["setup"]["credential_files"] = [".env"]
            config["setup"]["commands"] = ["pip install -r requirements.txt"]

        self._project_config = config
        self.save("project")

    def validate(self) -> List[str]:
        """Validate configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if not self.is_git_repository:
            errors.append("Not in a git repository")
            return errors

        if not self.has_project_config:
            errors.append(
                "No project configuration found. Run 'fleet init' to initialize."
            )
            return errors

        # Check credential files exist
        for cred_file in self.credential_files:
            cred_path = self.repo_root / cred_file
            if not cred_path.exists():
                errors.append(f"Credential file not found: {cred_file}")

        return errors

    def get_config_info(self) -> Dict[str, Any]:
        """Get information about configuration sources."""
        info = {
            "project_root": str(self.project_root) if self.project_root else None,
            "project_config": str(self.project_config_file)
            if self.project_config_file
            else None,
            "project_config_exists": self.has_project_config,
            "user_config": str(self.user_config_file),
            "user_config_exists": self.user_config_file.exists(),
            "using_defaults": self._using_defaults,
        }
        return info

    # Convenience properties for backward compatibility
    @property
    def repo_root(self) -> Path:
        """Get repository root path."""
        if not self.project_root:
            raise ValueError("Not in a git repository")
        return self.project_root

    @property
    def worktree_root(self) -> Path:
        """Get worktree root path."""
        default_path = str(Path.home() / ".aifleet" / "worktrees" / "default")
        return Path(self.get("project.worktree_root", default_path))

    @property
    def tmux_prefix(self) -> str:
        """Get tmux session prefix."""
        return str(self.get("tmux.prefix", "ai_"))

    @property
    def default_agent(self) -> str:
        """Get default agent."""
        return str(self.get("agent.default", "claude"))

    @property
    def claude_flags(self) -> str:
        """Get claude flags."""
        return str(self.get("agent.claude_flags", ""))

    @property
    def credential_files(self) -> List[str]:
        """Get credential files to copy."""
        result = self.get("setup.credential_files", [])
        return result if isinstance(result, list) else []

    @property
    def setup_commands(self) -> List[str]:
        """Get setup commands to run."""
        result = self.get("setup.commands", [])
        return result if isinstance(result, list) else []

    @property
    def quick_setup(self) -> bool:
        """Get quick setup mode."""
        return bool(self.get("setup.quick", False))

    # Legacy config file support for migration
    @property
    def legacy_config_file(self) -> Path:
        """Get legacy global config file path."""
        return Path.home() / ".ai_fleet" / "config.toml"

    def has_legacy_config(self) -> bool:
        """Check if legacy global config exists."""
        return self.legacy_config_file.exists()

    def migrate_legacy_config(self) -> None:
        """Migrate from legacy global config to project config."""
        if not self.has_legacy_config():
            return

        try:
            with open(self.legacy_config_file, "r") as f:
                legacy = toml.load(f)

            # Map old keys to new structure
            self._project_config = {
                "project": {
                    "name": self.project_root.name if self.project_root else "default",
                    "worktree_root": legacy.get("worktree_root"),
                },
                "agent": {
                    "default": legacy.get("default_agent", "claude"),
                    "claude_flags": legacy.get("claude_flags", ""),
                },
                "setup": {
                    "credential_files": legacy.get("credential_files", []),
                    "commands": legacy.get("setup_commands", []),
                    "quick": legacy.get("quick_setup", False),
                },
                "tmux": {
                    "prefix": legacy.get("tmux_prefix", "ai_"),
                },
            }

            # Save and backup
            self.save("project")
            backup_path = self.legacy_config_file.with_suffix(".toml.backup")
            self.legacy_config_file.rename(backup_path)
            print("Migrated legacy config to project config.")
            print(f"Backup saved at: {backup_path}")

        except Exception as e:
            print(f"Error migrating legacy config: {e}", file=sys.stderr)
