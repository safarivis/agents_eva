"""Tests for tools module."""
import pytest

from src.tools import TOOLS


class TestToolsSchema:
    """Tests for TOOLS schema validation."""

    def test_tools_is_list(self):
        """TOOLS is a list."""
        assert isinstance(TOOLS, list)

    def test_tools_has_two_tools(self):
        """TOOLS contains exactly 2 tools."""
        assert len(TOOLS) == 2

    def test_read_memory_tool_exists(self):
        """read_memory tool exists with correct schema."""
        tool = next((t for t in TOOLS if t["name"] == "read_memory"), None)
        assert tool is not None
        assert "description" in tool
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"
        assert "name" in tool["input_schema"]["properties"]

    def test_update_context_tool_exists(self):
        """update_context tool exists with correct schema."""
        tool = next((t for t in TOOLS if t["name"] == "update_context"), None)
        assert tool is not None
        assert "description" in tool
        assert "input_schema" in tool
        assert "category" in tool["input_schema"]["properties"]
        assert "summary" in tool["input_schema"]["properties"]
        assert "details" in tool["input_schema"]["properties"]
