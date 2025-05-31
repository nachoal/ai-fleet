"""Configuration management for AI Fleet."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import toml


class ConfigManager:
    """Manages AI Fleet configuration."""

    DEFAULT_CONFIG = {
        "repo_root": str(Path.home() / "code" / "my-project"),
        "worktree_root": str(Path.home() / ".ai_fleet" / "worktrees"),
        "tmux_prefix": "ai_",
        "default_agent": "claude",
        "claude_flags": "--dangerously-skip-permissions",
        "credential_files": [],
        "setup_commands": [],
        "quick_setup": False,
    }

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config manager.

        Args:
            config_dir: Override config directory (mainly for testing)
        """
        self.config_dir = config_dir or Path.home() / ".ai_fleet"
        self.config_file = self.config_dir / "config.toml"
        self._config: Dict[str, Any] = {}
        self._ensure_config_dir()
        self.load()

    def _ensure_config_dir(self) -> None:
        """Ensure config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        """Load configuration from disk."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    self._config = toml.load(f)
            except Exception as e:
                print(f"Error loading config: {e}", file=sys.stderr)
                self._config = {}

        # Apply defaults for missing keys
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = value

    def save(self) -> None:
        """Save configuration to disk."""
        try:
            with open(self.config_file, "w") as f:
                toml.dump(self._config, f)
        except Exception as e:
            print(f"Error saving config: {e}", file=sys.stderr)
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        # Support dot notation (e.g., "linear.token")
        parts = key.split(".")
        value = self._config

        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        parts = key.split(".")
        config = self._config

        # Navigate to the parent dict
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]

        # Set the value
        config[parts[-1]] = value

    def validate(self) -> List[str]:
        """Validate configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check repo_root exists
        repo_root = Path(self.get("repo_root"))
        if not repo_root.exists():
            errors.append(f"repo_root does not exist: {repo_root}")
        elif not (repo_root / ".git").exists():
            errors.append(f"repo_root is not a git repository: {repo_root}")

        # Check credential files exist in repo_root
        for cred_file in self.get("credential_files", []):
            cred_path = repo_root / cred_file
            if not cred_path.exists():
                errors.append(f"Credential file not found: {cred_file}")

        return errors

    def create_default_config(self) -> None:
        """Create default configuration file."""
        if not self.config_file.exists():
            # Try to detect current git repo
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "rev-parse", "--show-toplevel"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                repo_root = result.stdout.strip()
                self.set("repo_root", repo_root)
            except Exception:
                pass  # Use default

            self.save()

    @property
    def repo_root(self) -> Path:
        """Get repository root path."""
        return Path(self.get("repo_root"))

    @property
    def worktree_root(self) -> Path:
        """Get worktree root path."""
        return Path(self.get("worktree_root"))

    @property
    def tmux_prefix(self) -> str:
        """Get tmux session prefix."""
        return str(self.get("tmux_prefix", "ai_"))

    @property
    def default_agent(self) -> str:
        """Get default agent."""
        return str(self.get("default_agent", "claude"))

    @property
    def claude_flags(self) -> str:
        """Get claude flags."""
        return str(self.get("claude_flags", ""))

    @property
    def credential_files(self) -> List[str]:
        """Get credential files to copy."""
        result = self.get("credential_files", [])
        return result if isinstance(result, list) else []

    @property
    def setup_commands(self) -> List[str]:
        """Get setup commands to run."""
        result = self.get("setup_commands", [])
        return result if isinstance(result, list) else []

    @property
    def quick_setup(self) -> bool:
        """Get quick setup mode."""
        return bool(self.get("quick_setup", False))
