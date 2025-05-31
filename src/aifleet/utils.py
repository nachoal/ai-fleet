"""Utility functions placeholder."""

import random
import string
from datetime import datetime


def generate_batch_id():
    """Generate a batch ID."""
    date_part = datetime.now().strftime("%y%m%d")
    random_part = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{date_part}-{random_part}"


def parse_branch_prompt_pairs(args):
    """Parse branch:prompt pairs."""
    pairs = []
    for arg in args:
        if ":" not in arg:
            raise ValueError(f"Invalid format: {arg}")
        branch, prompt = arg.split(":", 1)
        if not branch or not prompt:
            raise ValueError(f"Empty branch or prompt in: {arg}")
        pairs.append((branch.strip(), prompt.strip()))
    return pairs


def format_duration(seconds):
    """Format duration."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds / 60:.1f}m"
    else:
        return f"{seconds / 3600:.1f}h"


def safe_branch_name(name):
    """Convert to safe branch name."""
    safe = name.lower().replace(" ", "-")
    safe = "".join(c if c.isalnum() or c in "-_." else "-" for c in safe)
    while "--" in safe:
        safe = safe.replace("--", "-")
    return safe.strip("-")
