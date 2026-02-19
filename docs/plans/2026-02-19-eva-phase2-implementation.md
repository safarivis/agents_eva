# Eva Phase 2: Agent Core Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the agent core - agentic loop that loads memory, calls Claude with tools, and executes tool requests.

**Architecture:** Three new files: `tools.py` (tool definitions + executor), `agent.py` (agentic loop), `eva.py` (CLI entry). Uses Anthropic SDK directly with tool calling. Single-shot execution model.

**Tech Stack:** Python 3.11+, anthropic SDK, pytest, pytest-mock

---

## Task 1: Add pytest-mock dependency

**Files:**
- Modify: `requirements.txt`
- Modify: `pyproject.toml`

**Step 1: Update requirements.txt**

Add to `requirements.txt`:
```
pytest-mock>=3.12.0
```

**Step 2: Update pyproject.toml**

Add to `[project.optional-dependencies]` dev list:
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.12.0",
]
```

**Step 3: Install updated dependencies**

Run: `pip install -e ".[dev]"`
Expected: Successfully installed pytest-mock

**Step 4: Commit**

```bash
git add requirements.txt pyproject.toml
git commit -m "chore: add pytest-mock dependency"
```

---

## Task 2: Write failing tests for TOOLS schema

**Files:**
- Create: `tests/test_tools.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.tools'"

**Step 3: Commit failing test**

```bash
git add tests/test_tools.py
git commit -m "test: add failing tests for TOOLS schema"
```

---

## Task 3: Implement TOOLS constant

**Files:**
- Create: `src/tools.py`

**Step 1: Write minimal implementation**

```python
"""Tools module for Eva - tool definitions and execution."""
from pathlib import Path

from .memory import load_memory_file, update_context

# Tool definitions in Anthropic SDK format
TOOLS = [
    {
        "name": "read_memory",
        "description": "Read a memory file (soul, user, telos, context, harness)",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "enum": ["soul", "user", "telos", "context", "harness"],
                    "description": "Name of memory file to read",
                }
            },
            "required": ["name"],
        },
    },
    {
        "name": "update_context",
        "description": "Add entry to context.md rolling log",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Entry category (Decision, Learning, Commitment, etc.)",
                },
                "summary": {
                    "type": "string",
                    "description": "One-line summary",
                },
                "details": {
                    "type": "string",
                    "description": "Full details of the entry",
                },
                "followup": {
                    "type": "string",
                    "description": "Optional follow-up action",
                },
            },
            "required": ["category", "summary", "details"],
        },
    },
]
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_tools.py -v`
Expected: PASS (4 passed)

**Step 3: Commit**

```bash
git add src/tools.py
git commit -m "feat: add TOOLS constant with tool definitions"
```

---

## Task 4: Write failing tests for execute_tool

**Files:**
- Modify: `tests/test_tools.py`

**Step 1: Add failing tests**

```python
from pathlib import Path

from src.tools import TOOLS, execute_tool, ToolExecutionError


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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_tools.py::TestExecuteTool -v`
Expected: FAIL with "ImportError: cannot import name 'execute_tool'"

**Step 3: Commit failing test**

```bash
git add tests/test_tools.py
git commit -m "test: add failing tests for execute_tool"
```

---

## Task 5: Implement execute_tool

**Files:**
- Modify: `src/tools.py`

**Step 1: Add implementation**

Add to `src/tools.py` after TOOLS:

```python
class ToolExecutionError(Exception):
    """Raised when tool execution fails."""

    pass


def execute_tool(name: str, args: dict, memory_dir: Path) -> str:
    """Execute a tool and return result as string.

    Args:
        name: Tool name
        args: Tool arguments
        memory_dir: Path to memory directory

    Returns:
        Tool execution result as string

    Raises:
        ToolExecutionError: If tool is unknown
    """
    if name == "read_memory":
        try:
            return load_memory_file(memory_dir, args["name"])
        except FileNotFoundError as e:
            return f"Error: {e}"

    elif name == "update_context":
        update_context(
            memory_dir,
            category=args["category"],
            summary=args["summary"],
            details=args["details"],
            followup=args.get("followup"),
        )
        return "Context updated successfully."

    else:
        raise ToolExecutionError(f"Unknown tool: {name}")
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_tools.py -v`
Expected: PASS (8 passed)

**Step 3: Commit**

```bash
git add src/tools.py
git commit -m "feat: implement execute_tool function"
```

---

## Task 6: Write failing tests for build_system_prompt

**Files:**
- Create: `tests/test_agent.py`

**Step 1: Write the failing test**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.agent'"

**Step 3: Commit failing test**

```bash
git add tests/test_agent.py
git commit -m "test: add failing tests for build_system_prompt"
```

---

## Task 7: Implement build_system_prompt

**Files:**
- Create: `src/agent.py`

**Step 1: Write minimal implementation**

```python
"""Agent module for Eva - agentic loop implementation."""
import anthropic
from pathlib import Path

from .memory import load_all_memory
from .tools import TOOLS, execute_tool


def build_system_prompt(memory: dict[str, str]) -> str:
    """Combine memory files into system prompt.

    Args:
        memory: Dict mapping memory name to content

    Returns:
        Combined system prompt string
    """
    return f"""You are Eva, Louis's private optimization engine.

## Your Identity
{memory['soul']}

## Your User
{memory['user']}

## Your Purpose
{memory['telos']}

## Recent Context
{memory['context']}

## Your Architecture (Self-Awareness)
{memory['harness']}
"""
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_agent.py -v`
Expected: PASS (2 passed)

**Step 3: Commit**

```bash
git add src/agent.py
git commit -m "feat: implement build_system_prompt function"
```

---

## Task 8: Write failing tests for run_agent (simple response)

**Files:**
- Modify: `tests/test_agent.py`

**Step 1: Add failing test**

```python
from unittest.mock import MagicMock, patch

from src.agent import build_system_prompt, run_agent


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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_agent.py::TestRunAgent::test_simple_response_no_tools -v`
Expected: FAIL with "ImportError: cannot import name 'run_agent'"

**Step 3: Commit failing test**

```bash
git add tests/test_agent.py
git commit -m "test: add failing test for run_agent simple response"
```

---

## Task 9: Implement run_agent

**Files:**
- Modify: `src/agent.py`

**Step 1: Add implementation**

Add to `src/agent.py` after build_system_prompt:

```python
def run_agent(prompt: str, memory_dir: Path) -> str:
    """Run one agent loop cycle.

    1. Load memory into system prompt
    2. Call Claude with tools
    3. Execute any tool calls (loop until done)
    4. Return final response

    Args:
        prompt: User prompt
        memory_dir: Path to memory directory

    Returns:
        Final text response from Claude
    """
    client = anthropic.Anthropic()
    memory = load_all_memory(memory_dir)
    system = build_system_prompt(memory)

    messages = [{"role": "user", "content": prompt}]

    # Agentic loop - keep going until no more tool calls
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        # Check for tool use
        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            # No tools, return text response
            return "".join(b.text for b in response.content if hasattr(b, "text"))

        # Execute tools and continue loop
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tool in tool_uses:
            result = execute_tool(tool.name, tool.input, memory_dir)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": tool.id, "content": result}
            )
        messages.append({"role": "user", "content": tool_results})
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_agent.py -v`
Expected: PASS (3 passed)

**Step 3: Commit**

```bash
git add src/agent.py
git commit -m "feat: implement run_agent agentic loop"
```

---

## Task 10: Write failing test for run_agent with tool call

**Files:**
- Modify: `tests/test_agent.py`

**Step 1: Add failing test**

```python
    def test_with_tool_call(self, tmp_path: Path):
        """run_agent executes tool and returns final response."""
        # Arrange - create memory files
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        (memory_dir / "soul.md").write_text("# Eva Soul\nI am Eva.")
        (memory_dir / "user.md").write_text("# User")
        (memory_dir / "telos.md").write_text("# Telos")
        (memory_dir / "context.md").write_text("# Context")
        (memory_dir / "harness.md").write_text("# Harness")

        # First response: tool use
        mock_tool_block = MagicMock()
        mock_tool_block.type = "tool_use"
        mock_tool_block.id = "tool_123"
        mock_tool_block.name = "read_memory"
        mock_tool_block.input = {"name": "soul"}

        mock_response_1 = MagicMock()
        mock_response_1.content = [mock_tool_block]
        mock_response_1.stop_reason = "tool_use"

        # Second response: text
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Your soul says: I am Eva."

        mock_response_2 = MagicMock()
        mock_response_2.content = [mock_text_block]
        mock_response_2.stop_reason = "end_turn"

        with patch("src.agent.anthropic.Anthropic") as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_client.messages.create.side_effect = [mock_response_1, mock_response_2]

            # Act
            result = run_agent("What's in my soul?", memory_dir)

            # Assert
            assert "I am Eva" in result
            assert mock_client.messages.create.call_count == 2
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_agent.py::TestRunAgent::test_with_tool_call -v`
Expected: PASS (implementation already handles this)

**Step 3: Commit**

```bash
git add tests/test_agent.py
git commit -m "test: add test for run_agent with tool call"
```

---

## Task 11: Write failing test for run_agent missing memory

**Files:**
- Modify: `tests/test_agent.py`

**Step 1: Add failing test**

```python
    def test_missing_memory_raises(self, tmp_path: Path):
        """run_agent raises FileNotFoundError for missing memory."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir()
        # No memory files created

        with pytest.raises(FileNotFoundError):
            run_agent("Hello", memory_dir)
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/test_agent.py::TestRunAgent::test_missing_memory_raises -v`
Expected: PASS (implementation already raises FileNotFoundError from load_all_memory)

**Step 3: Commit**

```bash
git add tests/test_agent.py
git commit -m "test: add test for run_agent missing memory"
```

---

## Task 12: Write failing tests for eva.py CLI

**Files:**
- Create: `tests/test_eva.py`

**Step 1: Write the failing tests**

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_eva.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.eva'"

**Step 3: Commit failing test**

```bash
git add tests/test_eva.py
git commit -m "test: add failing tests for eva CLI"
```

---

## Task 13: Implement eva.py CLI

**Files:**
- Create: `src/eva.py`
- Create: `src/__main__.py`

**Step 1: Create eva.py**

```python
"""Eva - Private optimization engine for Louis du Plessis."""
import argparse
import sys
from pathlib import Path

from .agent import run_agent


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Eva orchestrator")
    parser.add_argument("prompt", nargs="?", help="Prompt for Eva")
    parser.add_argument(
        "--memory-dir",
        type=Path,
        default=Path("memory"),
        help="Path to memory directory",
    )
    args = parser.parse_args()

    if not args.prompt:
        print("Usage: python -m src.eva 'Your prompt here'")
        sys.exit(1)

    try:
        response = run_agent(args.prompt, args.memory_dir)
        print(response)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 2: Create __main__.py**

```python
"""Enable `python -m src.eva` invocation."""
from .eva import main

main()
```

**Step 3: Run test to verify it passes**

Run: `pytest tests/test_eva.py -v`
Expected: PASS (3 passed)

**Step 4: Commit**

```bash
git add src/eva.py src/__main__.py
git commit -m "feat: implement eva CLI entry point"
```

---

## Task 14: Run all tests and verify coverage

**Step 1: Run all tests with coverage**

Run: `pytest tests/ -v --cov=src --cov-report=term-missing`
Expected: All tests pass, coverage shows good coverage for all modules

**Step 2: Verify test count**

Expected: ~20 tests total (12 memory + 8 tools + agent + eva)

---

## Task 15: Integration test - manual verification

**Step 1: Test CLI locally (requires ANTHROPIC_API_KEY)**

Run: `python -m src.eva "What is my purpose?" --memory-dir memory`
Expected: Eva responds using memory context

**Step 2: Test with tool use**

Run: `python -m src.eva "Read my soul.md and tell me who you are" --memory-dir memory`
Expected: Eva uses read_memory tool and responds

---

## Task 16: Final commit and push

**Step 1: Commit any remaining changes**

```bash
git add -A
git status
```

**Step 2: Push to remote**

Run: `git push origin main`
Expected: Successfully pushed

---

## Summary

Phase 2 creates:
- `src/tools.py` - TOOLS constant + execute_tool()
- `src/agent.py` - build_system_prompt() + run_agent()
- `src/eva.py` - CLI entry point
- `src/__main__.py` - Module invocation support
- `tests/test_tools.py` - 8 tests
- `tests/test_agent.py` - 5 tests
- `tests/test_eva.py` - 3 tests

**Next:** Phase 3 - GitHub Actions workflows (heartbeat, morning-brief, wa-message)
