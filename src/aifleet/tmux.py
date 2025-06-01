"""Tmux session management for AI Fleet."""

import subprocess
from typing import List, Optional, Tuple

import libtmux


class TmuxManager:
    """Manages tmux sessions for AI agents."""

    def __init__(self, prefix: str = "ai_"):
        """Initialize tmux manager.

        Args:
            prefix: Prefix for session names
        """
        self.prefix = prefix
        self.server = libtmux.Server()

    def _session_name(self, branch: str) -> str:
        """Generate session name from branch."""
        # Replace problematic characters for tmux
        safe_branch = branch.replace("/", "-").replace(":", "-")
        return f"{self.prefix}{safe_branch}"

    def create_session(
        self, branch: str, working_dir: str
    ) -> Optional[libtmux.Session]:
        """Create a new tmux session.

        Args:
            branch: Branch name
            working_dir: Working directory for the session

        Returns:
            Created session or None if failed
        """
        session_name = self._session_name(branch)

        # Check if session already exists
        try:
            existing = self.server.find_where({"session_name": session_name})
            if existing:
                print(f"Session {session_name} already exists")
                return existing
        except Exception:
            pass

        # Create new session
        try:
            session = self.server.new_session(
                session_name=session_name, start_directory=working_dir, detach=True
            )
            return session
        except Exception as e:
            print(f"Failed to create session: {e}")
            return None

    def send_command(self, branch: str, command: str) -> bool:
        """Send a command to a session.

        Args:
            branch: Branch name
            command: Command to send

        Returns:
            True if successful
        """
        session_name = self._session_name(branch)

        try:
            session = self.server.find_where({"session_name": session_name})
            if not session:
                print(f"Session {session_name} not found")
                return False

            # Get the first window and pane
            window = session.list_windows()[0]
            pane = window.list_panes()[0]

            # Send the command
            pane.send_keys(command, enter=True)
            return True
        except Exception as e:
            print(f"Failed to send command: {e}")
            return False

    def get_session_output(self, branch: str, lines: int = 100) -> Optional[str]:
        """Get recent output from a session.

        Args:
            branch: Branch name
            lines: Number of lines to retrieve

        Returns:
            Output text or None if failed
        """
        session_name = self._session_name(branch)

        try:
            # Use tmux capture-pane command
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", session_name, "-p", "-S", f"-{lines}"],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return result.stdout
            else:
                print(f"Failed to capture output: {result.stderr}")
                return None
        except Exception as e:
            print(f"Failed to get output: {e}")
            return None

    def attach_session(self, branch: str) -> None:
        """Attach to a tmux session interactively.

        Args:
            branch: Branch name
        """
        session_name = self._session_name(branch)

        try:
            # Check if we're inside tmux
            in_tmux = (
                subprocess.run(["printenv", "TMUX"], capture_output=True).returncode
                == 0
            )

            if in_tmux:
                # Switch to the session
                subprocess.run(["tmux", "switch-client", "-t", session_name])
            else:
                # Attach to the session
                subprocess.run(["tmux", "attach", "-t", session_name])
        except Exception as e:
            print(f"Failed to attach: {e}")

    def kill_session(self, branch: str) -> bool:
        """Kill a tmux session.

        Args:
            branch: Branch name

        Returns:
            True if successful
        """
        session_name = self._session_name(branch)

        try:
            session = self.server.find_where({"session_name": session_name})
            if session:
                session.kill_session()
                return True
            else:
                print(f"Session {session_name} not found")
                return False
        except Exception as e:
            print(f"Failed to kill session: {e}")
            return False

    def list_sessions(self) -> List[Tuple[str, Optional[int]]]:
        """List all AI Fleet tmux sessions.

        Returns:
            List of (session_name, pid) tuples
        """
        sessions = []

        try:
            for session in self.server.list_sessions():
                name = session.get("session_name", "")
                if name.startswith(self.prefix):
                    # Try to get PID of the main process
                    pid = None
                    try:
                        # Get the first pane's PID
                        window = session.list_windows()[0]
                        pane = window.list_panes()[0]
                        pid_result = pane.cmd("display-message", "-p", "#{pane_pid}")
                        if pid_result and pid_result.stdout:
                            pid = int(pid_result.stdout[0].strip())
                    except Exception:
                        pass

                    sessions.append((name, pid))
        except Exception as e:
            print(f"Failed to list sessions: {e}")

        return sessions

    def session_exists(self, branch: str) -> bool:
        """Check if a session exists.

        Args:
            branch: Branch name

        Returns:
            True if session exists
        """
        session_name = self._session_name(branch)

        try:
            session = self.server.find_where({"session_name": session_name})
            return session is not None
        except Exception:
            return False

    def get_pane_content(self, branch: str) -> Optional[str]:
        """Capture current pane content for status detection.

        Args:
            branch: Branch name

        Returns:
            Pane content or None if failed
        """
        session_name = self._session_name(branch)
        try:
            result = subprocess.run(
                ["tmux", "capture-pane", "-t", session_name, "-p"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout
            return None
        except Exception:
            return None

    def get_agent_status(self, branch: str) -> str:
        """Detect current agent status from pane content.

        Args:
            branch: Branch name

        Returns:
            Status string: ready, running, idle, dead, or unknown
        """
        if not self.session_exists(branch):
            return "dead"

        content = self.get_pane_content(branch)
        if content is None:
            return "unknown"

        # Check for Claude-specific patterns
        running_patterns = [
            "esc to interrupt",
            "Thinking",
            "I'll help",
            "Let me",
            "I'll ",
            "I'm going to",
            "I need to",
            "I can see",
            "Looking at",
            "Searching for",
            "Processing",
            "Analyzing",
        ]

        if any(pattern.lower() in content.lower() for pattern in running_patterns):
            return "running"

        # Check if waiting for input
        content_lines = content.strip().split("\n")
        if content_lines:
            last_line = content_lines[-1].strip()
            # Check for common prompts
            if last_line.endswith(("$", ">", ":", "?")) or "Human:" in content:
                return "ready"

        # Check for recent activity (if there's meaningful content)
        if len(content.strip()) > 50:  # Some meaningful content
            return "idle"

        return "idle"

    def get_session_info(self, branch: str) -> Optional[dict]:
        """Get detailed session information.

        Args:
            branch: Branch name

        Returns:
            Session info dict or None
        """
        session_name = self._session_name(branch)

        try:
            session = self.server.find_where({"session_name": session_name})
            if not session:
                return None

            # Get basic info
            info = {
                "name": session_name,
                "created": session.get("session_created", ""),
                "attached": int(session.get("session_attached", "0")) > 0,
                "windows": len(session.list_windows()),
            }

            # Try to get PID
            try:
                window = session.list_windows()[0]
                pane = window.list_panes()[0]
                pid_result = pane.cmd("display-message", "-p", "#{pane_pid}")
                if pid_result and pid_result.stdout:
                    info["pid"] = int(pid_result.stdout[0].strip())
            except Exception:
                info["pid"] = None

            return info
        except Exception as e:
            print(f"Failed to get session info: {e}")
            return None
