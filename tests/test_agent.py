"""Tests for agent module."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.agent import build_system_prompt, run_agent


class TestBuildSystemPrompt:
    """Tests for build_system_prompt function."""

    def test_includes_all_memory_sections(self):
        """build_system_prompt includes all 5 memory sections."""
        memory = {
            "soul": "# Soul content",
            "user": "# User content",
            "telos": "# Telos content",
            "context": "# Context content",
            "harness": "# Harness content",
        }

        result = build_system_prompt(memory)

        assert "Soul content" in result
        assert "User content" in result
        assert "Telos content" in result
        assert "Context content" in result
        assert "Harness content" in result

    def test_includes_eva_identity(self):
        """build_system_prompt mentions Eva identity."""
        memory = {
            "soul": "# Soul",
            "user": "# User",
            "telos": "# Telos",
            "context": "# Context",
            "harness": "# Harness",
        }

        result = build_system_prompt(memory)

        assert "Eva" in result


class TestRunAgent:
    """Tests for run_agent function."""

    def test_simple_response_no_tools(self, tmp_path: Path):
        """run_agent returns text when Claude doesn't use tools."""
        # Arrange - create memory files
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "soul.md").write_text("# Soul")
        (memory_dir / "user.md").write_text("# User")
        (memory_dir / "telos.md").write_text("# Telos")
        (memory_dir / "context.md").write_text("# Context")
        (memory_dir / "harness.md").write_text("# Harness")

        # Mock Claude response
        mock_response = MagicMock()
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Hello, I am Eva."
        mock_response.content = [mock_text_block]
        mock_response.stop_reason = "end_turn"

        with patch("src.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            # Act
            result = run_agent("Hello", memory_dir)

            # Assert
            assert result == "Hello, I am Eva."
            mock_client.messages.create.assert_called_once()
