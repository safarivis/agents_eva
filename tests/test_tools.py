"""Tests for tools module."""
import pytest
from pathlib import Path

from src.tools import TOOLS, execute_tool, ToolExecutionError


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


class TestExecuteTool:
    """Tests for execute_tool function."""

    def test_execute_read_memory(self, tmp_path: Path):
        """execute_tool reads memory file content."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "soul.md").write_text("# Eva Soul\n\nTest content.")

        result = execute_tool("read_memory", {"name": "soul"}, memory_dir)

        assert "Eva Soul" in result
        assert "Test content" in result

    def test_execute_update_context(self, tmp_path: Path):
        """execute_tool updates context.md."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "context.md").write_text("# Context\n\n")

        result = execute_tool(
            "update_context",
            {"category": "Test", "summary": "Test summary", "details": "Test details"},
            memory_dir,
        )

        assert "success" in result.lower()
        content = (memory_dir / "context.md").read_text()
        assert "Test summary" in content

    def test_execute_unknown_tool_raises(self, tmp_path: Path):
        """execute_tool raises ToolExecutionError for unknown tool."""
        with pytest.raises(ToolExecutionError):
            execute_tool("unknown_tool", {}, tmp_path)

    def test_execute_read_memory_missing_file(self, tmp_path: Path):
        """execute_tool returns error message for missing file."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()

        result = execute_tool("read_memory", {"name": "soul"}, memory_dir)

        assert "error" in result.lower()
