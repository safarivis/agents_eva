"""Tests for agent module."""
import pytest
from pathlib import Path

from src.agent import build_system_prompt


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
