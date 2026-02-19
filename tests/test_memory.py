"""Tests for memory module."""
import pytest
from pathlib import Path

from src.memory import load_memory_file, load_all_memory, count_memory_tokens


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


class TestLoadAllMemory:
    """Tests for load_all_memory function."""

    def test_load_all_returns_dict(self, tmp_path: Path):
        """load_all_memory returns dict with all memory files."""
        # Arrange
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "soul.md").write_text("# Soul")
        (memory_dir / "user.md").write_text("# User")
        (memory_dir / "telos.md").write_text("# Telos")
        (memory_dir / "context.md").write_text("# Context")
        (memory_dir / "harness.md").write_text("# Harness")

        # Act
        result = load_all_memory(memory_dir)

        # Assert
        assert isinstance(result, dict)
        assert len(result) == 5
        assert "soul" in result
        assert "user" in result
        assert "telos" in result
        assert "context" in result
        assert "harness" in result

    def test_load_all_missing_file_raises(self, tmp_path: Path):
        """load_all_memory raises if any required file is missing."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "soul.md").write_text("# Soul")
        # Missing other files

        with pytest.raises(FileNotFoundError):
            load_all_memory(memory_dir)


class TestCountMemoryTokens:
    """Tests for count_memory_tokens function."""

    def test_count_returns_positive_int(self):
        """count_memory_tokens returns positive integer for non-empty text."""
        text = "Hello, this is a test."
        result = count_memory_tokens(text)
        assert isinstance(result, int)
        assert result > 0

    def test_count_empty_string_returns_zero(self):
        """count_memory_tokens returns 0 for empty string."""
        result = count_memory_tokens("")
        assert result == 0

    def test_count_known_text(self):
        """count_memory_tokens returns expected count for known text."""
        # "Hello world" is typically 2 tokens in cl100k_base
        text = "Hello world"
        result = count_memory_tokens(text)
        assert result == 2
