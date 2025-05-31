"""Tests for utility functions."""

import pytest

from aifleet.utils import (
    format_duration,
    generate_batch_id,
    parse_branch_prompt_pairs,
    safe_branch_name,
)


class TestUtils:
    """Test utility functions."""

    def test_generate_batch_id(self):
        """Test batch ID generation."""
        batch_id1 = generate_batch_id()
        batch_id2 = generate_batch_id()

        # Should be unique
        assert batch_id1 != batch_id2

        # Should have correct format
        assert len(batch_id1) == 11  # YYMMDD-XXXX
        assert batch_id1[6] == "-"
        assert batch_id1[:6].isdigit()
        assert all(c.isalnum() for c in batch_id1[7:])

    def test_parse_branch_prompt_pairs(self):
        """Test parsing branch:prompt pairs."""
        # Valid pairs
        args = [
            "fix-auth:Fix authentication bug",
            "add-tests:Add unit tests",
            "docs:Update documentation",
        ]

        pairs = parse_branch_prompt_pairs(args)
        assert len(pairs) == 3
        assert pairs[0] == ("fix-auth", "Fix authentication bug")
        assert pairs[1] == ("add-tests", "Add unit tests")
        assert pairs[2] == ("docs", "Update documentation")

        # With whitespace
        args_ws = ["branch : prompt with spaces"]
        pairs_ws = parse_branch_prompt_pairs(args_ws)
        assert pairs_ws[0] == ("branch", "prompt with spaces")

    def test_parse_branch_prompt_pairs_invalid(self):
        """Test parsing invalid branch:prompt pairs."""
        # Missing colon
        with pytest.raises(Exception) as exc_info:
            parse_branch_prompt_pairs(["no-colon"])
        assert "Invalid format" in str(exc_info.value)

        # Empty branch
        with pytest.raises(Exception) as exc_info:
            parse_branch_prompt_pairs([":prompt"])
        assert "Empty branch" in str(exc_info.value)

        # Empty prompt
        with pytest.raises(Exception) as exc_info:
            parse_branch_prompt_pairs(["branch:"])
        assert "Empty branch or prompt" in str(exc_info.value)

    def test_format_duration(self):
        """Test duration formatting."""
        # Seconds
        assert format_duration(45.5) == "45.5s"
        assert format_duration(59.9) == "59.9s"

        # Minutes
        assert format_duration(60) == "1.0m"
        assert format_duration(90) == "1.5m"
        assert format_duration(3599) == "60.0m"

        # Hours
        assert format_duration(3600) == "1.0h"
        assert format_duration(5400) == "1.5h"
        assert format_duration(7200) == "2.0h"

    def test_safe_branch_name(self):
        """Test safe branch name conversion."""
        # Basic conversion
        assert safe_branch_name("Fix Auth Bug") == "fix-auth-bug"
        assert safe_branch_name("Add-Unit-Tests") == "add-unit-tests"

        # Special characters
        assert safe_branch_name("Fix bug #123") == "fix-bug-123"
        assert safe_branch_name("feature/new@thing") == "feature-new-thing"

        # Multiple hyphens
        assert safe_branch_name("fix---bug") == "fix-bug"
        assert safe_branch_name("--leading-trailing--") == "leading-trailing"

        # Dots and underscores preserved
        assert safe_branch_name("v1.2.3_release") == "v1.2.3_release"
