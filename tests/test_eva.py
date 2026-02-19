"""Tests for eva CLI module."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.eva import main


class TestMain:
    """Tests for main CLI function."""

    def test_no_prompt_exits_with_error(self, capsys):
        """main exits with error when no prompt provided."""
        with patch("sys.argv", ["eva"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Usage" in captured.out or "usage" in captured.out.lower()

    def test_with_prompt_calls_run_agent(self, tmp_path: Path):
        """main calls run_agent with prompt."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "soul.md").write_text("# Soul")
        (memory_dir / "user.md").write_text("# User")
        (memory_dir / "telos.md").write_text("# Telos")
        (memory_dir / "context.md").write_text("# Context")
        (memory_dir / "harness.md").write_text("# Harness")

        with patch("sys.argv", ["eva", "Hello Eva", "--memory-dir", str(memory_dir)]):
            with patch("src.eva.run_agent") as mock_run:
                mock_run.return_value = "Hello!"
                main()
                mock_run.assert_called_once_with("Hello Eva", memory_dir)

    def test_missing_memory_dir_exits_with_error(self, tmp_path: Path, capsys):
        """main exits with error when memory dir doesn't exist."""
        fake_dir = tmp_path / "nonexistent"

        with patch("sys.argv", ["eva", "Hello", "--memory-dir", str(fake_dir)]):
            with patch("src.eva.run_agent") as mock_run:
                mock_run.side_effect = FileNotFoundError("Memory not found")
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err
