"""Utility functions for AI Fleet."""

import random
import string
from datetime import datetime
from typing import List, Tuple

import click


def generate_batch_id() -> str:
    """Generate a unique batch ID."""
    # Use format: YYMMDD-XXXX (date + random chars)
    date_part = datetime.now().strftime("%y%m%d")
    random_part = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{date_part}-{random_part}"


def parse_branch_prompt_pairs(args: List[str]) -> List[Tuple[str, str]]:
    """Parse branch:prompt pairs from command arguments.

    Args:
        args: List of "branch:prompt" strings

    Returns:
        List of (branch, prompt) tuples
    """
    pairs = []

    for arg in args:
        if ":" not in arg:
            raise click.BadParameter(f"Invalid format: {arg}. Expected 'branch:prompt'")

        branch, prompt = arg.split(":", 1)
        if not branch or not prompt:
            raise click.BadParameter(f"Empty branch or prompt in: {arg}")

        pairs.append((branch.strip(), prompt.strip()))

    return pairs


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def safe_branch_name(name: str) -> str:
    """Convert a string to a safe git branch name."""
    # Replace spaces and special chars with hyphens
    safe = name.lower()
    safe = safe.replace(" ", "-")
    safe = "".join(c if c.isalnum() or c in "-_." else "-" for c in safe)
    # Remove multiple consecutive hyphens
    while "--" in safe:
        safe = safe.replace("--", "-")
    # Remove leading/trailing hyphens
    safe = safe.strip("-")
    return safe
