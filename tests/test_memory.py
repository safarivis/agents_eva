"""Tests for memory module."""
import pytest
from pathlib import Path

from src.memory import load_memory_file


class TestLoadMemoryFile:
    """Tests for load_memory_file function."""

    def test_load_soul_returns_content(self, tmp_path: Path):
        """load_memory_file returns content of soul.md."""
        # Arrange
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        soul_file = memory_dir / "soul.md"
        soul_file.write_text("# Eva - Soul\n\n## Identity\n\nEva is a test.")

        # Act
        result = load_memory_file(memory_dir, "soul")

        # Assert
        assert result is not None
        assert "Eva - Soul" in result
        assert "Identity" in result

    def test_load_nonexistent_file_raises(self, tmp_path: Path):
        """load_memory_file raises FileNotFoundError for missing file."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            load_memory_file(memory_dir, "nonexistent")

    def test_load_user_returns_content(self, tmp_path: Path):
        """load_memory_file returns content of user.md."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        user_file = memory_dir / "user.md"
        user_file.write_text("# Louis du Plessis\n\n## Identity\n\nLouis is a test.")

        result = load_memory_file(memory_dir, "user")

        assert "Louis du Plessis" in result
