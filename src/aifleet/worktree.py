"""Git worktree operations for AI Fleet."""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


class WorktreeManager:
    """Manages git worktrees for AI agents."""

    def __init__(self, repo_root: Path, worktree_root: Path):
        """Initialize worktree manager.

        Args:
            repo_root: Main repository root
            worktree_root: Directory for worktrees
        """
        self.repo_root = repo_root
        self.worktree_root = worktree_root
        self.worktree_root.mkdir(parents=True, exist_ok=True)

    def _run_git(
        self, args: List[str], cwd: Optional[Path] = None
    ) -> Tuple[bool, str, str]:
        """Run a git command.

        Args:
            args: Git command arguments
            cwd: Working directory (defaults to repo_root)

        Returns:
            (success, stdout, stderr)
        """
        cwd = cwd or self.repo_root

        try:
            result = subprocess.run(
                ["git"] + args, cwd=cwd, capture_output=True, text=True
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)

    def create_worktree(
        self, branch: str, path: Optional[Path] = None
    ) -> Optional[Path]:
        """Create a new worktree.

        Args:
            branch: Branch name
            path: Worktree path (auto-generated if not provided)

        Returns:
            Path to created worktree or None if failed
        """
        if path is None:
            # Auto-generate path based on branch name
            safe_branch = branch.replace("/", "-")
            path = self.worktree_root / safe_branch

        # Check if worktree already exists
        if path.exists():
            print(f"Worktree already exists at {path}")
            return path

        # Check if branch exists
        success, stdout, _ = self._run_git(
            ["show-ref", "--verify", f"refs/heads/{branch}"]
        )
        branch_exists = success

        # Create worktree
        if branch_exists:
            # Use existing branch
            success, stdout, stderr = self._run_git(
                ["worktree", "add", str(path), branch]
            )
        else:
            # Create new branch
            success, stdout, stderr = self._run_git(
                ["worktree", "add", str(path), "-b", branch]
            )

        if not success:
            print(f"Failed to create worktree: {stderr}")
            return None

        return path

    def remove_worktree(self, path: Path, force: bool = False) -> bool:
        """Remove a worktree.

        Args:
            path: Worktree path
            force: Force removal even if there are changes

        Returns:
            True if successful
        """
        # Remove worktree from git
        args = ["worktree", "remove", str(path)]
        if force:
            args.append("--force")

        success, stdout, stderr = self._run_git(args)

        if not success:
            print(f"Failed to remove worktree: {stderr}")
            # Try to clean up directory anyway
            if path.exists() and force:
                try:
                    shutil.rmtree(path)
                    return True
                except Exception as e:
                    print(f"Failed to remove directory: {e}")
            return False

        return True

    def list_worktrees(self) -> List[Tuple[str, str]]:
        """List all worktrees.

        Returns:
            List of (path, branch) tuples
        """
        success, stdout, stderr = self._run_git(["worktree", "list", "--porcelain"])

        if not success:
            print(f"Failed to list worktrees: {stderr}")
            return []

        worktrees = []
        current_path = None

        for line in stdout.strip().split("\n"):
            if line.startswith("worktree "):
                current_path = line[9:]
            elif line.startswith("branch ") and current_path:
                branch = line[7:]
                worktrees.append((current_path, branch))
                current_path = None

        return worktrees

    def copy_credential_files(self, worktree_path: Path, files: List[str]) -> List[str]:
        """Copy credential files from main repo to worktree.

        Args:
            worktree_path: Destination worktree path
            files: List of files to copy (relative to repo root)

        Returns:
            List of successfully copied files
        """
        copied = []

        for file in files:
            src = self.repo_root / file
            dst = worktree_path / file

            if not src.exists():
                print(f"Source file not found: {file}")
                continue

            try:
                # Create parent directory if needed
                dst.parent.mkdir(parents=True, exist_ok=True)

                # Copy file
                shutil.copy2(src, dst)
                copied.append(file)
                print(f"Copied {file}")
            except Exception as e:
                print(f"Failed to copy {file}: {e}")

        return copied

    def run_setup_commands(self, worktree_path: Path, commands: List[str]) -> bool:
        """Run setup commands in worktree.

        Args:
            worktree_path: Worktree path
            commands: List of commands to run

        Returns:
            True if all commands succeeded
        """
        for command in commands:
            print(f"Running: {command}")

            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=worktree_path,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    print(f"Command failed: {result.stderr}")
                    return False

                if result.stdout:
                    print(result.stdout)

            except Exception as e:
                print(f"Failed to run command: {e}")
                return False

        return True

    def setup_worktree(
        self,
        branch: str,
        credential_files: List[str],
        setup_commands: List[str],
        quick_setup: bool = False,
    ) -> Optional[Path]:
        """Create and setup a worktree.

        Args:
            branch: Branch name
            credential_files: Files to copy
            setup_commands: Commands to run
            quick_setup: Skip setup commands if True

        Returns:
            Path to setup worktree or None if failed
        """
        # Create worktree
        worktree_path = self.create_worktree(branch)
        if not worktree_path:
            return None

        # Copy credential files
        if credential_files:
            copied = self.copy_credential_files(worktree_path, credential_files)
            print(f"Copied {len(copied)} credential files")

        # Run setup commands
        if setup_commands and not quick_setup:
            success = self.run_setup_commands(worktree_path, setup_commands)
            if not success:
                print("Setup commands failed")
                # Don't remove worktree - user might want to debug

        return worktree_path

    def get_worktree_info(self, path: Path) -> Optional[dict]:
        """Get information about a worktree.

        Args:
            path: Worktree path

        Returns:
            Info dict or None
        """
        if not path.exists():
            return None

        # Get git status
        success, stdout, stderr = self._run_git(["status", "--porcelain"], cwd=path)

        info = {
            "path": str(path),
            "exists": True,
            "clean": success and not stdout.strip(),
        }

        # Get current branch
        success, stdout, _ = self._run_git(["branch", "--show-current"], cwd=path)
        if success:
            info["branch"] = stdout.strip()

        return info
