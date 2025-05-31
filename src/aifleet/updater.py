"""Update checker and installer for AI Fleet."""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Tuple

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from packaging import version

    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False


class UpdateChecker:
    """Check for AI Fleet updates."""

    GITHUB_API_URL = "https://api.github.com/repos/nachoal/ai-fleet/releases/latest"
    CACHE_FILE = Path.home() / ".config" / "ai-fleet" / "update_check.json"
    CACHE_DURATION = 86400  # 24 hours

    def __init__(self, current_version: str):
        self.current_version = current_version

    def check_for_updates(self, force: bool = False) -> Tuple[bool, str]:
        """Check if a new version is available."""
        if not HAS_REQUESTS:
            return False, self.current_version

        # Check cache first
        if not force and self._is_cache_valid():
            cached_data = self._load_cache()
            if cached_data:
                return self._compare_versions(cached_data.get("latest_version", ""))

        try:
            response = requests.get(self.GITHUB_API_URL, timeout=5)
            response.raise_for_status()

            data = response.json()
            latest_version = data.get("tag_name", "").lstrip("v")

            if not latest_version:
                return False, self.current_version

            # Cache the result
            self._save_cache(
                {"latest_version": latest_version, "timestamp": time.time()}
            )

            return self._compare_versions(latest_version)

        except Exception:
            # Silently fail - don't interrupt user's workflow
            return False, self.current_version

    def _compare_versions(self, latest_version: str) -> Tuple[bool, str]:
        """Compare current version with latest."""
        if not latest_version:
            return False, self.current_version

        if HAS_PACKAGING:
            try:
                is_newer = version.parse(latest_version) > version.parse(
                    self.current_version
                )
                return is_newer, latest_version
            except Exception:
                pass

        # Fallback to simple string comparison
        return latest_version != self.current_version, latest_version

    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid."""
        if not self.CACHE_FILE.exists():
            return False

        try:
            with open(self.CACHE_FILE, "r") as f:
                data = json.load(f)
                timestamp = data.get("timestamp", 0)
                return bool((time.time() - timestamp) < self.CACHE_DURATION)
        except Exception:
            return False

    def _load_cache(self) -> Optional[dict]:
        """Load cached update check data."""
        try:
            with open(self.CACHE_FILE, "r") as f:
                data: dict = json.load(f)
                return data
        except Exception:
            return None

    def _save_cache(self, data: dict) -> None:
        """Save update check data to cache."""
        try:
            self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CACHE_FILE, "w") as f:
                json.dump(data, f)
        except Exception:
            pass


def get_installation_method() -> str:
    """Detect how AI Fleet was installed."""
    # Check if running from source (development)
    if Path(__file__).parent.parent.parent.joinpath(".git").exists():
        return "source"

    # Check for pipx
    if "pipx" in sys.prefix or "pipx" in str(Path(sys.executable).parent):
        return "pipx"

    # Check for uv
    if "uv" in sys.prefix or ".venv" in sys.prefix:
        # Could be uv or regular venv, check for uv.lock
        project_root = Path(__file__).parent.parent.parent
        if project_root.joinpath("uv.lock").exists():
            return "uv"

    # Default to pip
    return "pip"


def update_via_pipx() -> bool:
    """Update using pipx."""
    try:
        subprocess.run(
            ["pipx", "upgrade", "ai-fleet"], check=True, capture_output=True, text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def update_via_pip() -> bool:
    """Update using pip."""
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "ai-fleet"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def update_via_uv() -> bool:
    """Update using uv."""
    try:
        subprocess.run(
            ["uv", "pip", "install", "--upgrade", "ai-fleet"],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False
