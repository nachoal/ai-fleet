"""Configuration management placeholder."""

from pathlib import Path


class ConfigManager:
    """Placeholder ConfigManager."""

    def __init__(self, config_dir=None):
        self.config_dir = config_dir or Path.home() / ".ai_fleet"
        self.config_file = self.config_dir / "config.toml"

    def validate(self):
        return []