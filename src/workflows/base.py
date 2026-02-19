"""Base utilities for Eva workflows."""
import subprocess
from pathlib import Path


def sync_memory(repo_dir: Path) -> None:
    """Pull latest memory from git.

    Args:
        repo_dir: Path to repository root
    """
    subprocess.run(
        ["git", "pull", "--rebase"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )


def push_memory(repo_dir: Path, message: str) -> None:
    """Commit and push memory changes.

    Args:
        repo_dir: Path to repository root
        message: Commit message
    """
    subprocess.run(
        ["git", "add", "memory/context.md"],
        cwd=repo_dir,
        check=True,
        capture_output=True,
    )
    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=repo_dir,
        capture_output=True,
    )
    if result.returncode != 0:  # Changes exist
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
        )
