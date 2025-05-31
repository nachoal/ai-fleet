"""Tests for worktree operations."""

import subprocess

from aifleet.worktree import WorktreeManager


class TestWorktreeManager:
    """Test WorktreeManager functionality."""

    def test_create_worktree_new_branch(self, git_repo, temp_dir):
        """Test creating worktree with new branch."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create worktree with new branch
        path = worktree_mgr.create_worktree("feature/test-branch")

        assert path is not None
        assert path.exists()
        assert path.name == "feature-test-branch"

        # Verify branch exists
        result = subprocess.run(
            ["git", "branch", "--list", "feature/test-branch"],
            cwd=git_repo,
            capture_output=True,
            text=True,
        )
        assert "feature/test-branch" in result.stdout

    def test_create_worktree_existing_branch(self, git_repo, temp_dir):
        """Test creating worktree with existing branch."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create branch and immediately switch back to main
        subprocess.run(
            ["git", "branch", "existing-branch"],
            cwd=git_repo,
            capture_output=True,
        )

        # Create worktree with existing branch
        path = worktree_mgr.create_worktree("existing-branch")

        assert path is not None
        assert path.exists()

    def test_create_worktree_already_exists(self, git_repo, temp_dir):
        """Test creating worktree that already exists."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create worktree
        path1 = worktree_mgr.create_worktree("test-branch")

        # Try to create again
        path2 = worktree_mgr.create_worktree("test-branch")

        # Should return existing path
        assert path2 == path1

    def test_remove_worktree(self, git_repo, temp_dir):
        """Test removing worktree."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create worktree
        path = worktree_mgr.create_worktree("test-branch")
        assert path.exists()

        # Remove worktree
        removed = worktree_mgr.remove_worktree(path)
        assert removed is True
        assert not path.exists()

    def test_list_worktrees(self, git_repo, temp_dir):
        """Test listing worktrees."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create multiple worktrees
        worktree_mgr.create_worktree("branch1")
        worktree_mgr.create_worktree("branch2")

        # List worktrees
        worktrees = worktree_mgr.list_worktrees()

        # Should include main repo + 2 worktrees
        assert len(worktrees) >= 3

        # Check our worktrees are listed
        branches = [branch for _, branch in worktrees]
        # Handle both short and full branch names
        assert any("branch1" in b for b in branches)
        assert any("branch2" in b for b in branches)

    def test_copy_credential_files(self, git_repo, temp_dir):
        """Test copying credential files."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create credential files in main repo
        (git_repo / "config").mkdir()
        (git_repo / "config" / "master.key").write_text("secret-key")
        (git_repo / ".env").write_text("API_KEY=test")

        # Create worktree
        worktree_path = worktree_mgr.create_worktree("test-branch")

        # Copy credential files
        files_to_copy = ["config/master.key", ".env"]
        copied = worktree_mgr.copy_credential_files(worktree_path, files_to_copy)

        assert len(copied) == 2
        assert (worktree_path / "config" / "master.key").exists()
        assert (worktree_path / ".env").exists()
        assert (worktree_path / "config" / "master.key").read_text() == "secret-key"

    def test_copy_credential_files_missing(self, git_repo, temp_dir):
        """Test copying missing credential files."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create worktree
        worktree_path = worktree_mgr.create_worktree("test-branch")

        # Try to copy non-existent files
        files_to_copy = ["missing.key", "also-missing.env"]
        copied = worktree_mgr.copy_credential_files(worktree_path, files_to_copy)

        assert len(copied) == 0

    def test_run_setup_commands(self, git_repo, temp_dir):
        """Test running setup commands."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create worktree
        worktree_path = worktree_mgr.create_worktree("test-branch")

        # Run setup commands
        commands = ["echo 'Setup 1' > setup1.txt", "echo 'Setup 2' > setup2.txt"]

        success = worktree_mgr.run_setup_commands(worktree_path, commands)

        assert success is True
        assert (worktree_path / "setup1.txt").exists()
        assert (worktree_path / "setup2.txt").exists()

    def test_run_setup_commands_failure(self, git_repo, temp_dir):
        """Test running failing setup commands."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create worktree
        worktree_path = worktree_mgr.create_worktree("test-branch")

        # Run command that fails
        commands = ["false"]  # Unix command that always fails

        success = worktree_mgr.run_setup_commands(worktree_path, commands)
        assert success is False

    def test_setup_worktree_full(self, git_repo, temp_dir):
        """Test full worktree setup."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create credential file
        (git_repo / ".env").write_text("API_KEY=test")

        # Setup worktree
        path = worktree_mgr.setup_worktree(
            branch="test-setup",
            credential_files=[".env"],
            setup_commands=["echo 'Setup complete' > setup.log"],
            quick_setup=False,
        )

        assert path is not None
        assert (path / ".env").exists()
        assert (path / "setup.log").exists()

    def test_setup_worktree_quick(self, git_repo, temp_dir):
        """Test quick worktree setup (skip commands)."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Setup worktree with quick mode
        path = worktree_mgr.setup_worktree(
            branch="test-quick",
            credential_files=[],
            setup_commands=["echo 'Should not run' > setup.log"],
            quick_setup=True,
        )

        assert path is not None
        assert not (path / "setup.log").exists()  # Command should not run

    def test_get_worktree_info(self, git_repo, temp_dir):
        """Test getting worktree information."""
        worktree_mgr = WorktreeManager(git_repo, temp_dir / "worktrees")

        # Create worktree
        path = worktree_mgr.create_worktree("test-info")

        # Get info
        info = worktree_mgr.get_worktree_info(path)

        assert info is not None
        assert info["exists"] is True
        assert info["clean"] is True
        assert info["branch"] == "test-info"

        # Modify file
        (path / "test.txt").write_text("modified")

        info2 = worktree_mgr.get_worktree_info(path)
        assert info2["clean"] is False
