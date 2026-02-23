# Tool Calling 2.0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade Eva to use Anthropic's Programmatic Tool Calling (PTC) and Dynamic Filtering, with multi-model peer review.

**Architecture:** Provider Strategy Pattern isolates PTC to Anthropic provider while maintaining NVIDIA/Grok support. Tools define `allowed_callers` for PTC-enabled operations. Peer review runs as GitHub Action with GPT-4o + Gemini consensus.

**Tech Stack:** Python 3.11+, Anthropic SDK, OpenAI SDK, Google Generative AI, pytest

**Design Document:** `docs/plans/2026-02-23-tool-calling-2.0-design.md`

---

## Phase 1: Provider Infrastructure

### Task 1: Create Provider Protocol

**Files:**
- Create: `src/providers/__init__.py`
- Test: `tests/test_providers/__init__.py`

**Step 1: Create providers directory**

```bash
mkdir -p src/providers tests/test_providers
touch src/providers/__init__.py tests/test_providers/__init__.py
```

**Step 2: Write the failing test for ProviderStrategy protocol**

Create `tests/test_providers/test_protocol.py`:

```python
"""Test provider protocol definition."""
import pytest
from typing import Protocol, runtime_checkable


def test_provider_strategy_is_protocol():
    """ProviderStrategy should be a runtime-checkable Protocol."""
    from src.providers import ProviderStrategy

    assert hasattr(ProviderStrategy, '__protocol_attrs__') or isinstance(ProviderStrategy, type)


def test_provider_strategy_requires_run_method():
    """ProviderStrategy must define run() method signature."""
    from src.providers import ProviderStrategy

    # Check run is defined
    assert hasattr(ProviderStrategy, 'run')


def test_provider_strategy_requires_supports_ptc():
    """ProviderStrategy must define supports_ptc property."""
    from src.providers import ProviderStrategy

    assert 'supports_ptc' in dir(ProviderStrategy)


def test_get_provider_strategy_returns_strategy():
    """get_provider_strategy() returns appropriate strategy for provider name."""
    from src.providers import get_provider_strategy, ProviderStrategy

    strategy = get_provider_strategy("anthropic")
    assert hasattr(strategy, 'run')
    assert hasattr(strategy, 'supports_ptc')
```

**Step 3: Run test to verify it fails**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_providers/test_protocol.py -v`
Expected: FAIL with "ModuleNotFoundError" or "ImportError"

**Step 4: Write minimal implementation**

Update `src/providers/__init__.py`:

```python
"""Provider strategy pattern for multi-provider support."""
from typing import Protocol, runtime_checkable
from pathlib import Path


@runtime_checkable
class ProviderStrategy(Protocol):
    """Protocol for LLM provider strategies."""

    supports_ptc: bool
    supports_code_execution: bool

    def run(self, prompt: str, system: str, tools: list, memory_dir: Path) -> str:
        """Run the agent loop with the given prompt and tools."""
        ...


def get_provider_strategy(provider: str) -> ProviderStrategy:
    """Get the appropriate strategy for the given provider.

    Args:
        provider: Provider name ("anthropic", "nvidia", or "grok")

    Returns:
        ProviderStrategy instance

    Raises:
        ValueError: If provider is unknown
    """
    if provider == "anthropic":
        from .anthropic import AnthropicStrategy
        return AnthropicStrategy()
    elif provider == "nvidia":
        from .nvidia import NvidiaStrategy
        return NvidiaStrategy()
    elif provider == "grok":
        from .grok import GrokStrategy
        return GrokStrategy()
    else:
        raise ValueError(f"Unknown provider: {provider}")
```

**Step 5: Run test to verify it passes (will still fail - need provider implementations)**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_providers/test_protocol.py::test_provider_strategy_is_protocol -v`
Expected: PASS for protocol test, others will fail until providers implemented

**Step 6: Commit**

```bash
git add src/providers/__init__.py tests/test_providers/__init__.py tests/test_providers/test_protocol.py
git commit -m "feat(providers): add ProviderStrategy protocol and factory"
```

---

### Task 2: Extract Anthropic Provider (Classic Loop First)

**Files:**
- Create: `src/providers/anthropic.py`
- Create: `tests/test_providers/test_anthropic.py`
- Modify: `src/agent.py`

**Step 1: Write the failing test for AnthropicStrategy**

Create `tests/test_providers/test_anthropic.py`:

```python
"""Test Anthropic provider strategy."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestAnthropicStrategyBasic:
    """Test basic AnthropicStrategy functionality."""

    @pytest.fixture
    def strategy(self):
        """Create strategy with mocked client."""
        with patch("src.providers.anthropic.anthropic.Anthropic"):
            from src.providers.anthropic import AnthropicStrategy
            return AnthropicStrategy()

    def test_supports_ptc_is_true(self, strategy):
        """Anthropic provider supports PTC."""
        assert strategy.supports_ptc is True

    def test_supports_code_execution_is_true(self, strategy):
        """Anthropic provider supports code execution."""
        assert strategy.supports_code_execution is True

    def test_simple_response_no_tools(self, strategy):
        """Direct response without tool use."""
        mock_response = Mock(
            stop_reason="end_turn",
            content=[Mock(type="text", text="Hello!")],
        )
        # Remove container attribute for basic test
        mock_response.container = None
        strategy.client.messages.create = Mock(return_value=mock_response)

        result = strategy.run("Hi", "system prompt", [], Path("/tmp"))

        assert result == "Hello!"
```

**Step 2: Run test to verify it fails**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_providers/test_anthropic.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/providers/anthropic.py`:

```python
"""Anthropic provider with PTC and code execution support."""
import anthropic
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..tools import execute_tool


@dataclass
class ContainerState:
    """Track code execution container state."""
    id: Optional[str] = None
    expires_at: Optional[str] = None


class AnthropicStrategy:
    """Anthropic provider strategy with PTC support."""

    supports_ptc: bool = True
    supports_code_execution: bool = True

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic()
        self.container = ContainerState()
        self.model = model

    def run(self, prompt: str, system: str, tools: list, memory_dir: Path) -> str:
        """Run agent loop with PTC support.

        Args:
            prompt: User prompt
            system: System prompt
            tools: List of tool definitions
            memory_dir: Path to memory directory

        Returns:
            Final text response
        """
        messages = [{"role": "user", "content": prompt}]

        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system,
                tools=tools if tools else None,
                messages=messages,
                **({"container": self.container.id} if self.container.id else {}),
            )

            # Track container for reuse
            if hasattr(response, "container") and response.container:
                self.container.id = response.container.id
                self.container.expires_at = getattr(response.container, "expires_at", None)

            # Check stop reason
            if response.stop_reason == "end_turn":
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                messages.append({"role": "assistant", "content": response.content})
                tool_results = self._execute_tools(response.content, memory_dir)
                messages.append({"role": "user", "content": tool_results})
                continue

            # pause_turn = long-running code execution, continue
            if response.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": response.content})
                continue

            # Unknown stop reason, return what we have
            return self._extract_text(response)

    def _extract_text(self, response) -> str:
        """Extract text content from response."""
        return "".join(
            b.text for b in response.content
            if hasattr(b, "text")
        )

    def _execute_tools(self, content: list, memory_dir: Path) -> list:
        """Execute tool calls from response content.

        Args:
            content: Response content blocks
            memory_dir: Path to memory directory

        Returns:
            List of tool result blocks
        """
        results = []
        for block in content:
            if getattr(block, "type", None) == "tool_use":
                try:
                    result = execute_tool(block.name, block.input, memory_dir)
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
                except Exception as e:
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"Error executing {block.name}: {str(e)}",
                        "is_error": True,
                    })
        return results
```

**Step 4: Run test to verify it passes**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_providers/test_anthropic.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/providers/anthropic.py tests/test_providers/test_anthropic.py
git commit -m "feat(providers): add AnthropicStrategy with basic loop"
```

---

### Task 3: Extract NVIDIA Provider

**Files:**
- Create: `src/providers/nvidia.py`
- Create: `tests/test_providers/test_nvidia.py`

**Step 1: Write the failing test**

Create `tests/test_providers/test_nvidia.py`:

```python
"""Test NVIDIA/Kimi provider strategy."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path


class TestNvidiaStrategy:
    """Test NvidiaStrategy functionality."""

    @pytest.fixture
    def strategy(self):
        """Create strategy with mocked client."""
        with patch("src.providers.nvidia.OpenAI"):
            from src.providers.nvidia import NvidiaStrategy
            return NvidiaStrategy()

    def test_supports_ptc_is_false(self, strategy):
        """NVIDIA provider does not support PTC."""
        assert strategy.supports_ptc is False

    def test_supports_code_execution_is_false(self, strategy):
        """NVIDIA provider does not support code execution."""
        assert strategy.supports_code_execution is False

    def test_simple_response_no_tools(self, strategy):
        """Direct response without tool use."""
        mock_message = Mock(
            content="Hello from Kimi!",
            tool_calls=None,
        )
        mock_response = Mock(
            choices=[Mock(message=mock_message)],
        )
        strategy.client.chat.completions.create = Mock(return_value=mock_response)

        result = strategy.run("Hi", "system prompt", [], Path("/tmp"))

        assert result == "Hello from Kimi!"
```

**Step 2: Run test to verify it fails**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_providers/test_nvidia.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/providers/nvidia.py`:

```python
"""NVIDIA provider using Kimi K2.5 via OpenAI-compatible API."""
import os
import json
from pathlib import Path

from openai import OpenAI

from ..tools import execute_tool


NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "moonshotai/kimi-k2.5"


def _convert_tools_to_openai_format(tools: list) -> list:
    """Convert Anthropic tool format to OpenAI function format."""
    result = []
    for tool in tools:
        # Skip Anthropic-specific tools (code_execution, web_fetch, etc.)
        if "type" in tool and tool["type"].startswith(("code_execution", "web_fetch", "web_search")):
            continue
        result.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {}),
            },
        })
    return result


class NvidiaStrategy:
    """NVIDIA provider strategy using Kimi K2.5."""

    supports_ptc: bool = False
    supports_code_execution: bool = False

    def __init__(self):
        self.client = OpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=os.environ.get("NVIDIA_API_KEY"),
        )
        self.model = NVIDIA_MODEL

    def run(self, prompt: str, system: str, tools: list, memory_dir: Path) -> str:
        """Run agent loop with classic tool calling.

        Args:
            prompt: User prompt
            system: System prompt
            tools: List of tool definitions
            memory_dir: Path to memory directory

        Returns:
            Final text response
        """
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        openai_tools = _convert_tools_to_openai_format(tools) if tools else None

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=8192,  # Kimi is a reasoning model, needs more tokens
                messages=messages,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto" if openai_tools else None,
            )

            message = response.choices[0].message

            # Check for tool calls
            if not message.tool_calls:
                content = message.content
                # Kimi K2.5 reasoning model - content may be in reasoning_content
                if not content and hasattr(message, "reasoning_content"):
                    content = message.reasoning_content
                return content or ""

            # Execute tools and continue loop
            messages.append(message)
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = execute_tool(tool_call.function.name, args, memory_dir)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
```

**Step 4: Run test to verify it passes**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_providers/test_nvidia.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/providers/nvidia.py tests/test_providers/test_nvidia.py
git commit -m "feat(providers): add NvidiaStrategy with classic loop"
```

---

### Task 4: Extract Grok Provider

**Files:**
- Create: `src/providers/grok.py`
- Create: `tests/test_providers/test_grok.py`

**Step 1: Write the failing test**

Create `tests/test_providers/test_grok.py`:

```python
"""Test Grok provider strategy."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path


class TestGrokStrategy:
    """Test GrokStrategy functionality."""

    @pytest.fixture
    def strategy(self):
        """Create strategy with mocked client."""
        with patch("src.providers.grok.OpenAI"):
            from src.providers.grok import GrokStrategy
            return GrokStrategy()

    def test_supports_ptc_is_false(self, strategy):
        """Grok provider does not support PTC."""
        assert strategy.supports_ptc is False

    def test_supports_code_execution_is_false(self, strategy):
        """Grok provider does not support code execution."""
        assert strategy.supports_code_execution is False

    def test_simple_response_no_tools(self, strategy):
        """Direct response without tool use."""
        mock_message = Mock(
            content="Hello from Grok!",
            tool_calls=None,
        )
        mock_response = Mock(
            choices=[Mock(message=mock_message)],
        )
        strategy.client.chat.completions.create = Mock(return_value=mock_response)

        result = strategy.run("Hi", "system prompt", [], Path("/tmp"))

        assert result == "Hello from Grok!"
```

**Step 2: Run test to verify it fails**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_providers/test_grok.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 3: Write minimal implementation**

Create `src/providers/grok.py`:

```python
"""Grok provider using xAI API."""
import os
import json
from pathlib import Path

from openai import OpenAI

from ..tools import execute_tool


GROK_BASE_URL = "https://api.x.ai/v1"
GROK_MODEL = "grok-3-fast"


def _convert_tools_to_openai_format(tools: list) -> list:
    """Convert Anthropic tool format to OpenAI function format."""
    result = []
    for tool in tools:
        # Skip Anthropic-specific tools
        if "type" in tool and tool["type"].startswith(("code_execution", "web_fetch", "web_search")):
            continue
        result.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {}),
            },
        })
    return result


class GrokStrategy:
    """Grok provider strategy using xAI API."""

    supports_ptc: bool = False
    supports_code_execution: bool = False

    def __init__(self):
        self.client = OpenAI(
            base_url=GROK_BASE_URL,
            api_key=os.environ.get("GROK_API_KEY"),
        )
        self.model = GROK_MODEL

    def run(self, prompt: str, system: str, tools: list, memory_dir: Path) -> str:
        """Run agent loop with classic tool calling.

        Args:
            prompt: User prompt
            system: System prompt
            tools: List of tool definitions
            memory_dir: Path to memory directory

        Returns:
            Final text response
        """
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        openai_tools = _convert_tools_to_openai_format(tools) if tools else None

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=4096,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto" if openai_tools else None,
            )

            message = response.choices[0].message

            # Check for tool calls
            if not message.tool_calls:
                return message.content or ""

            # Execute tools and continue loop
            messages.append(message)
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = execute_tool(tool_call.function.name, args, memory_dir)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
```

**Step 4: Run test to verify it passes**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_providers/test_grok.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/providers/grok.py tests/test_providers/test_grok.py
git commit -m "feat(providers): add GrokStrategy with classic loop"
```

---

### Task 5: Refactor agent.py to Use Providers

**Files:**
- Modify: `src/agent.py`
- Modify: `tests/test_agent.py` (if exists)

**Step 1: Read current agent.py**

Run: `cat src/agent.py` to understand current structure

**Step 2: Write test for refactored agent**

Update or create `tests/test_agent.py`:

```python
"""Test agent module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path


class TestRunAgent:
    """Test run_agent function."""

    @pytest.fixture
    def memory_dir(self, tmp_path):
        """Create temporary memory directory with required files."""
        mem = tmp_path / "memory"
        mem.mkdir()
        (mem / "soul.md").write_text("I am Eva.")
        (mem / "user.md").write_text("Louis prefers concise responses.")
        (mem / "telos.md").write_text("Help Louis be productive.")
        (mem / "context.md").write_text("# Context Log")
        (mem / "harness.md").write_text("Eva architecture docs.")
        return mem

    @patch("src.agent.get_provider_strategy")
    def test_run_agent_uses_provider_strategy(self, mock_get_strategy, memory_dir):
        """run_agent delegates to provider strategy."""
        from src.agent import run_agent

        mock_strategy = Mock()
        mock_strategy.run.return_value = "Response from provider"
        mock_get_strategy.return_value = mock_strategy

        result = run_agent("Hello", memory_dir)

        mock_strategy.run.assert_called_once()
        assert result == "Response from provider"

    @patch("src.agent.get_provider_strategy")
    @patch.dict("os.environ", {"EVA_PROVIDER": "nvidia"})
    def test_run_agent_respects_provider_env(self, mock_get_strategy, memory_dir):
        """run_agent uses EVA_PROVIDER environment variable."""
        from src.agent import run_agent

        mock_strategy = Mock()
        mock_strategy.run.return_value = "Response"
        mock_get_strategy.return_value = mock_strategy

        run_agent("Hello", memory_dir)

        mock_get_strategy.assert_called_with("nvidia")
```

**Step 3: Run test to verify it fails**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_agent.py -v`
Expected: FAIL (agent.py still uses old structure)

**Step 4: Refactor agent.py**

Replace `src/agent.py`:

```python
"""Agent module for Eva - agentic loop implementation."""
import os
from pathlib import Path

from .memory import load_all_memory
from .tools import get_tools_for_provider
from .providers import get_provider_strategy

# Provider configuration
PROVIDER = os.environ.get("EVA_PROVIDER", "anthropic")


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


def run_agent(prompt: str, memory_dir: Path) -> str:
    """Run one agent loop cycle.

    1. Load memory into system prompt
    2. Get provider strategy
    3. Get tools for provider
    4. Delegate to strategy

    Args:
        prompt: User prompt
        memory_dir: Path to memory directory

    Returns:
        Final text response from LLM
    """
    provider = os.environ.get("EVA_PROVIDER", "anthropic")

    memory = load_all_memory(memory_dir)
    system = build_system_prompt(memory)
    tools = get_tools_for_provider(provider)

    strategy = get_provider_strategy(provider)
    return strategy.run(prompt, system, tools, memory_dir)
```

**Step 5: Run test to verify it passes**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_agent.py -v`
Expected: PASS

**Step 6: Run all provider tests**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_providers/ -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add src/agent.py tests/test_agent.py
git commit -m "refactor(agent): delegate to provider strategies"
```

---

## Phase 2: Tool Definitions with PTC Support

### Task 6: Reorganize tools.py with allowed_callers

**Files:**
- Modify: `src/tools.py`
- Modify: `tests/test_tools.py`

**Step 1: Write test for new tool structure**

Update `tests/test_tools.py`:

```python
"""Test tools module."""
import pytest
from pathlib import Path


class TestToolDefinitions:
    """Test tool definitions."""

    def test_core_tools_have_no_allowed_callers(self):
        """Core tools (memory ops) should not have allowed_callers."""
        from src.tools import CORE_TOOLS

        for tool in CORE_TOOLS:
            assert "allowed_callers" not in tool, f"{tool['name']} should not have allowed_callers"

    def test_composio_tools_have_allowed_callers(self):
        """Composio tools should have allowed_callers for PTC."""
        from src.tools import COMPOSIO_TOOLS

        for tool in COMPOSIO_TOOLS:
            assert "allowed_callers" in tool, f"{tool['name']} should have allowed_callers"
            assert "code_execution_20260120" in tool["allowed_callers"]

    def test_get_tools_for_anthropic_includes_code_execution(self):
        """Anthropic provider gets code execution tool."""
        from src.tools import get_tools_for_provider

        tools = get_tools_for_provider("anthropic")
        tool_types = [t.get("type", "") for t in tools]

        assert any("code_execution" in t for t in tool_types)

    def test_get_tools_for_nvidia_strips_allowed_callers(self):
        """NVIDIA provider tools should not have allowed_callers."""
        from src.tools import get_tools_for_provider

        tools = get_tools_for_provider("nvidia")

        for tool in tools:
            assert "allowed_callers" not in tool


class TestExecuteTool:
    """Test tool execution."""

    @pytest.fixture
    def memory_dir(self, tmp_path):
        """Create temporary memory directory."""
        mem = tmp_path / "memory"
        mem.mkdir()
        (mem / "soul.md").write_text("I am Eva.")
        (mem / "context.md").write_text("# Context")
        return mem

    def test_execute_read_memory(self, memory_dir):
        """read_memory tool returns file content."""
        from src.tools import execute_tool

        result = execute_tool("read_memory", {"name": "soul"}, memory_dir)

        assert "I am Eva" in result

    def test_execute_unknown_tool_returns_error(self, memory_dir):
        """Unknown tool returns error string."""
        from src.tools import execute_tool

        result = execute_tool("unknown_tool", {}, memory_dir)

        assert "Error" in result or "Unknown" in result
```

**Step 2: Run test to verify some fail**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_tools.py -v`
Expected: Some FAIL (new structure not implemented)

**Step 3: Rewrite tools.py**

Replace `src/tools.py`:

```python
"""Tools module for Eva - tool definitions and execution."""
import json
from pathlib import Path
from typing import Literal

from .memory import load_memory_file, update_context
from .composio_tools import fetch_emails, fetch_calendar_events, send_email

# Type alias for caller types
CallerType = Literal["direct", "code_execution_20260120"]

# Core Eva tools - always direct (simple, low-latency)
CORE_TOOLS = [
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

# Composio tools - PTC-enabled for batching and filtering
COMPOSIO_TOOLS = [
    {
        "name": "fetch_emails",
        "description": "Fetch emails from Gmail. Returns JSON list of {id, subject, from, snippet, date}.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum emails to fetch",
                    "default": 10,
                },
                "query": {
                    "type": "string",
                    "description": "Gmail search query",
                    "default": "is:unread",
                },
            },
        },
        "allowed_callers": ["code_execution_20260120"],
    },
    {
        "name": "fetch_calendar_events",
        "description": "Fetch upcoming calendar events. Returns JSON list of {id, summary, start, end}.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hours_ahead": {
                    "type": "integer",
                    "description": "How many hours ahead to look",
                    "default": 24,
                },
            },
        },
        "allowed_callers": ["code_execution_20260120"],
    },
    {
        "name": "send_email",
        "description": "Send an email via Gmail.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to_email": {
                    "type": "string",
                    "description": "Recipient email address",
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject line",
                },
                "body": {
                    "type": "string",
                    "description": "Email body text",
                },
            },
            "required": ["to_email", "subject", "body"],
        },
        "allowed_callers": ["code_execution_20260120"],
    },
]

# Web tools - dynamic filtering version
WEB_TOOLS = [
    {
        "type": "web_fetch_20260209",
        "name": "web_fetch",
        "max_uses": 10,
        "max_content_tokens": 50000,
    },
]

# Code execution tool (required for PTC)
CODE_EXECUTION_TOOL = {
    "type": "code_execution_20260120",
    "name": "code_execution",
}

# Legacy TOOLS export for backward compatibility
TOOLS = CORE_TOOLS + COMPOSIO_TOOLS


def get_tools_for_provider(provider: str) -> list:
    """Return tools formatted for the given provider.

    Args:
        provider: Provider name ("anthropic", "nvidia", or "grok")

    Returns:
        List of tool definitions appropriate for the provider
    """
    if provider == "anthropic":
        # Full toolset with PTC support
        return CORE_TOOLS + COMPOSIO_TOOLS + WEB_TOOLS + [CODE_EXECUTION_TOOL]
    else:
        # Strip allowed_callers and Anthropic-specific tools for non-PTC providers
        tools = []
        for tool in CORE_TOOLS + COMPOSIO_TOOLS:
            clean_tool = {k: v for k, v in tool.items() if k != "allowed_callers"}
            tools.append(clean_tool)
        return tools


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
        Tool execution result as string (JSON for structured data)
    """
    try:
        if name == "read_memory":
            return load_memory_file(memory_dir, args["name"])

        elif name == "update_context":
            update_context(
                memory_dir,
                category=args["category"],
                summary=args["summary"],
                details=args["details"],
                followup=args.get("followup"),
            )
            return "Context updated successfully."

        elif name == "fetch_emails":
            emails = fetch_emails(
                max_results=args.get("max_results", 10),
                query=args.get("query", "is:unread"),
            )
            return json.dumps(emails)

        elif name == "fetch_calendar_events":
            events = fetch_calendar_events(
                hours_ahead=args.get("hours_ahead", 24),
            )
            return json.dumps(events)

        elif name == "send_email":
            success = send_email(
                to_email=args["to_email"],
                subject=args["subject"],
                body=args["body"],
            )
            return json.dumps({"success": success})

        else:
            return f"Error: Unknown tool '{name}'"

    except FileNotFoundError as e:
        return f"Error: File not found - {e}"
    except KeyError as e:
        return f"Error: Missing required argument - {e}"
    except Exception as e:
        import logging
        logging.exception(f"Tool {name} failed")
        return f"Error: {type(e).__name__} - {str(e)}"
```

**Step 4: Run test to verify it passes**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_tools.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/tools.py tests/test_tools.py
git commit -m "feat(tools): add PTC support with allowed_callers"
```

---

## Phase 3: Peer Review System

### Task 7: Add Peer Review Module

**Files:**
- Create: `src/review/__init__.py`
- Create: `src/review/peer_review.py`
- Create: `tests/test_review/__init__.py`
- Create: `tests/test_review/test_peer_review.py`

**Step 1: Create directories**

```bash
mkdir -p src/review tests/test_review
touch src/review/__init__.py tests/test_review/__init__.py
```

**Step 2: Write failing test for consensus logic**

Create `tests/test_review/test_peer_review.py`:

```python
"""Test peer review module."""
import pytest
from unittest.mock import Mock, patch


class TestReviewVerdict:
    """Test ReviewVerdict enum."""

    def test_verdict_values(self):
        """ReviewVerdict has expected values."""
        from src.review.peer_review import ReviewVerdict

        assert ReviewVerdict.APPROVE.value == "approve"
        assert ReviewVerdict.REQUEST_CHANGES.value == "request_changes"
        assert ReviewVerdict.COMMENT.value == "comment"


class TestConsensus:
    """Test peer review consensus logic."""

    def test_two_approvals_passes(self):
        """Two approvals should pass consensus."""
        from src.review.peer_review import ReviewResult, ReviewVerdict, get_consensus

        reviews = [
            ReviewResult("GPT-4o", ReviewVerdict.APPROVE, [], []),
            ReviewResult("Gemini", ReviewVerdict.APPROVE, [], []),
        ]

        passed, reason = get_consensus(reviews)

        assert passed is True
        assert "2/3" in reason or "approved" in reason.lower()

    def test_one_approval_fails(self):
        """One approval should fail consensus."""
        from src.review.peer_review import ReviewResult, ReviewVerdict, get_consensus

        reviews = [
            ReviewResult("GPT-4o", ReviewVerdict.APPROVE, [], []),
            ReviewResult("Gemini", ReviewVerdict.REQUEST_CHANGES, ["Fix X"], []),
        ]

        passed, reason = get_consensus(reviews)

        assert passed is False

    def test_security_concern_blocks_even_with_approvals(self):
        """Security concerns should block regardless of approvals."""
        from src.review.peer_review import ReviewResult, ReviewVerdict, get_consensus

        reviews = [
            ReviewResult("GPT-4o", ReviewVerdict.APPROVE, [], ["SQL injection risk"]),
            ReviewResult("Gemini", ReviewVerdict.APPROVE, [], []),
        ]

        passed, reason = get_consensus(reviews)

        assert passed is False
        assert "security" in reason.lower()
```

**Step 3: Run test to verify it fails**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_review/test_peer_review.py -v`
Expected: FAIL with "ModuleNotFoundError"

**Step 4: Write implementation**

Create `src/review/peer_review.py`:

```python
"""Multi-model peer review system."""
import json
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from openai import OpenAI


class ReviewVerdict(Enum):
    """Possible review verdicts."""
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    COMMENT = "comment"


@dataclass
class ReviewResult:
    """Result from a single reviewer."""
    reviewer: str
    verdict: ReviewVerdict
    comments: list[str]
    security_concerns: list[str]


REVIEW_PROMPT = """You are a senior code reviewer. Review this PR diff for:

1. **Code Quality**: Readability, maintainability, best practices
2. **Security**: Injection risks, credential exposure, OWASP Top 10
3. **Edge Cases**: Error handling, null checks, boundary conditions
4. **Performance**: Obvious inefficiencies, N+1 queries, memory leaks

PR Title: {title}
PR Description: {description}

Diff:
```
{diff}
```

Respond in JSON format only:
{{
  "verdict": "approve" | "request_changes" | "comment",
  "comments": ["comment1", "comment2"],
  "security_concerns": []
}}
"""


def get_consensus(reviews: list[ReviewResult]) -> tuple[bool, str]:
    """Determine consensus from review results.

    Rules:
    - Any security concern = block
    - 2/3 approval = pass

    Args:
        reviews: List of review results

    Returns:
        Tuple of (passed, reason)
    """
    # Security concerns block regardless of approval
    all_security = []
    for r in reviews:
        all_security.extend(r.security_concerns)
    if all_security:
        return False, f"Security concerns found: {all_security}"

    # Count approvals
    approvals = sum(1 for r in reviews if r.verdict == ReviewVerdict.APPROVE)
    if approvals >= 2:
        return True, "Consensus reached: 2/3 approved"

    return False, "Consensus not reached: changes requested"


class PeerReviewer:
    """Multi-model peer review system."""

    def __init__(self):
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self._gemini = None  # Lazy load

    @property
    def gemini(self):
        """Lazy-load Gemini client."""
        if self._gemini is None:
            import google.generativeai as genai
            genai.configure(api_key=os.environ.get("GOOGLE_AI_API_KEY"))
            self._gemini = genai.GenerativeModel("gemini-2.0-flash")
        return self._gemini

    def review_with_gpt4o(
        self, title: str, description: str, diff: str
    ) -> ReviewResult:
        """Get review from GPT-4o.

        Args:
            title: PR title
            description: PR description
            diff: Code diff

        Returns:
            ReviewResult from GPT-4o
        """
        response = self.openai.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": REVIEW_PROMPT.format(
                    title=title, description=description, diff=diff
                )
            }],
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        return ReviewResult(
            reviewer="GPT-4o",
            verdict=ReviewVerdict(data["verdict"]),
            comments=data.get("comments", []),
            security_concerns=data.get("security_concerns", []),
        )

    def review_with_gemini(
        self, title: str, description: str, diff: str
    ) -> ReviewResult:
        """Get review from Gemini.

        Args:
            title: PR title
            description: PR description
            diff: Code diff

        Returns:
            ReviewResult from Gemini
        """
        response = self.gemini.generate_content(
            REVIEW_PROMPT.format(title=title, description=description, diff=diff)
        )
        # Parse JSON from response
        text = response.text
        # Handle potential markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        data = json.loads(text.strip())
        return ReviewResult(
            reviewer="Gemini 2.0",
            verdict=ReviewVerdict(data["verdict"]),
            comments=data.get("comments", []),
            security_concerns=data.get("security_concerns", []),
        )

    def run_review(
        self, title: str, description: str, diff: str
    ) -> tuple[bool, str, list[ReviewResult]]:
        """Run full peer review with both models.

        Args:
            title: PR title
            description: PR description
            diff: Code diff

        Returns:
            Tuple of (passed, reason, reviews)
        """
        reviews = []

        # Get reviews from both models
        try:
            reviews.append(self.review_with_gpt4o(title, description, diff))
        except Exception as e:
            reviews.append(ReviewResult(
                reviewer="GPT-4o",
                verdict=ReviewVerdict.COMMENT,
                comments=[f"Review failed: {e}"],
                security_concerns=[],
            ))

        try:
            reviews.append(self.review_with_gemini(title, description, diff))
        except Exception as e:
            reviews.append(ReviewResult(
                reviewer="Gemini 2.0",
                verdict=ReviewVerdict.COMMENT,
                comments=[f"Review failed: {e}"],
                security_concerns=[],
            ))

        passed, reason = get_consensus(reviews)
        return passed, reason, reviews
```

Update `src/review/__init__.py`:

```python
"""Peer review module."""
from .peer_review import (
    ReviewVerdict,
    ReviewResult,
    PeerReviewer,
    get_consensus,
)

__all__ = ["ReviewVerdict", "ReviewResult", "PeerReviewer", "get_consensus"]
```

**Step 5: Run test to verify it passes**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_review/test_peer_review.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/review/ tests/test_review/
git commit -m "feat(review): add multi-model peer review system"
```

---

### Task 8: Add Peer Review CLI Runner

**Files:**
- Create: `src/review/run_review.py`

**Step 1: Write the CLI runner**

Create `src/review/run_review.py`:

```python
#!/usr/bin/env python3
"""CLI runner for peer review - used by GitHub Action."""
import argparse
import json
import os
import sys
from pathlib import Path

from .peer_review import PeerReviewer


def format_review_comment(passed: bool, reason: str, reviews: list) -> str:
    """Format review results as GitHub comment markdown.

    Args:
        passed: Whether consensus was reached
        reason: Consensus reason
        reviews: List of ReviewResult objects

    Returns:
        Markdown formatted comment
    """
    status = "Approved" if passed else "Changes Requested"
    emoji = "white_check_mark" if passed else "x"

    lines = [
        f"## Peer Review: {status} :{emoji}:",
        "",
        f"**Consensus:** {reason}",
        "",
        "---",
        "",
    ]

    for review in reviews:
        verdict_emoji = {
            "approve": "white_check_mark",
            "request_changes": "x",
            "comment": "speech_balloon",
        }.get(review.verdict.value, "grey_question")

        lines.append(f"### {review.reviewer} :{verdict_emoji}:")
        lines.append("")

        if review.comments:
            lines.append("**Comments:**")
            for comment in review.comments:
                lines.append(f"- {comment}")
            lines.append("")

        if review.security_concerns:
            lines.append("**Security Concerns:**")
            for concern in review.security_concerns:
                lines.append(f"- :warning: {concern}")
            lines.append("")

    lines.append("---")
    lines.append("*Automated review by Eva Peer Review System*")

    return "\n".join(lines)


def post_github_comment(pr_number: int, comment: str) -> None:
    """Post comment to GitHub PR using gh CLI.

    Args:
        pr_number: PR number
        comment: Comment body
    """
    import subprocess

    subprocess.run(
        ["gh", "pr", "comment", str(pr_number), "--body", comment],
        check=True,
    )


def add_github_label(pr_number: int, label: str) -> None:
    """Add label to GitHub PR.

    Args:
        pr_number: PR number
        label: Label name
    """
    import subprocess

    subprocess.run(
        ["gh", "pr", "edit", str(pr_number), "--add-label", label],
        check=True,
    )


def main():
    """Run peer review CLI."""
    parser = argparse.ArgumentParser(description="Run peer review on PR")
    parser.add_argument("--pr-number", type=int, required=True, help="PR number")
    parser.add_argument("--diff-file", type=Path, required=True, help="Path to diff file")
    parser.add_argument("--title", default="", help="PR title")
    parser.add_argument("--description", default="", help="PR description")
    parser.add_argument("--dry-run", action="store_true", help="Don't post to GitHub")
    args = parser.parse_args()

    # Read diff
    diff = args.diff_file.read_text()

    # Get PR info if not provided
    title = args.title
    description = args.description
    if not title:
        import subprocess
        result = subprocess.run(
            ["gh", "pr", "view", str(args.pr_number), "--json", "title,body"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            title = data.get("title", "")
            description = data.get("body", "")

    # Run review
    print(f"Running peer review on PR #{args.pr_number}...")
    reviewer = PeerReviewer()
    passed, reason, reviews = reviewer.run_review(title, description, diff)

    # Format comment
    comment = format_review_comment(passed, reason, reviews)

    if args.dry_run:
        print("\n--- DRY RUN ---")
        print(comment)
        print(f"\nPassed: {passed}")
    else:
        # Post comment
        post_github_comment(args.pr_number, comment)

        # Add label
        label = "peer-review-approved" if passed else "peer-review-changes-requested"
        try:
            add_github_label(args.pr_number, label)
        except Exception as e:
            print(f"Warning: Could not add label: {e}")

    # Exit with appropriate code
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
```

**Step 2: Commit**

```bash
git add src/review/run_review.py
git commit -m "feat(review): add CLI runner for GitHub Action"
```

---

### Task 9: Add Peer Review GitHub Action

**Files:**
- Create: `.github/workflows/peer-review.yml`

**Step 1: Write the GitHub Action**

Create `.github/workflows/peer-review.yml`:

```yaml
name: Peer Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install openai google-generativeai
          pip install -e .

      - name: Get PR diff
        run: |
          git diff origin/${{ github.base_ref }}...HEAD > diff.txt

      - name: Run peer review
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GOOGLE_AI_API_KEY: ${{ secrets.GOOGLE_AI_API_KEY }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python -m src.review.run_review \
            --pr-number ${{ github.event.pull_request.number }} \
            --diff-file diff.txt
```

**Step 2: Commit**

```bash
git add .github/workflows/peer-review.yml
git commit -m "ci: add peer review GitHub Action"
```

---

### Task 10: Update Dependencies

**Files:**
- Modify: `requirements.txt`

**Step 1: Read current requirements**

Run: `cat requirements.txt`

**Step 2: Add google-generativeai**

Update `requirements.txt` to add:

```txt
google-generativeai>=0.5.0
```

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add google-generativeai for Gemini peer review"
```

---

## Phase 4: Integration Testing

### Task 11: Add Integration Tests

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write integration test**

Create `tests/test_integration.py`:

```python
"""Integration tests for Eva agent."""
import pytest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path


class TestAgentIntegration:
    """Test full agent flow with mocked external services."""

    @pytest.fixture
    def memory_dir(self, tmp_path):
        """Create temporary memory files."""
        mem = tmp_path / "memory"
        mem.mkdir()
        (mem / "soul.md").write_text("I am Eva, Louis's optimization engine.")
        (mem / "user.md").write_text("Louis prefers concise responses.")
        (mem / "telos.md").write_text("Help Louis be productive.")
        (mem / "context.md").write_text("# Context Log\n\nNo recent activity.")
        (mem / "harness.md").write_text("Eva runs on Claude with PTC support.")
        return mem

    @patch("src.providers.anthropic.anthropic.Anthropic")
    def test_anthropic_simple_response(self, mock_anthropic_cls, memory_dir):
        """Test simple response flow with Anthropic provider."""
        from src.agent import run_agent

        # Setup mock
        mock_client = Mock()
        mock_anthropic_cls.return_value = mock_client

        mock_response = Mock(
            stop_reason="end_turn",
            content=[Mock(type="text", text="Hello, Louis!")],
            container=None,
        )
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"EVA_PROVIDER": "anthropic"}):
            result = run_agent("Hello Eva", memory_dir)

        assert result == "Hello, Louis!"
        mock_client.messages.create.assert_called_once()

    @patch("src.providers.anthropic.anthropic.Anthropic")
    @patch("src.composio_tools._get_toolset")
    def test_anthropic_with_tool_call(self, mock_toolset, mock_anthropic_cls, memory_dir):
        """Test tool calling flow with Anthropic provider."""
        from src.agent import run_agent

        # Setup Anthropic mock
        mock_client = Mock()
        mock_anthropic_cls.return_value = mock_client

        # First response: tool call
        tool_call_response = Mock(
            stop_reason="tool_use",
            content=[
                Mock(type="text", text="Let me check your emails."),
                Mock(
                    type="tool_use",
                    id="tool_123",
                    name="fetch_emails",
                    input={"query": "is:unread", "max_results": 5},
                ),
            ],
            container=Mock(id="ctr_abc", expires_at="2026-02-23T12:00:00Z"),
        )

        # Second response: final answer
        final_response = Mock(
            stop_reason="end_turn",
            content=[Mock(type="text", text="You have 3 unread emails.")],
            container=Mock(id="ctr_abc", expires_at="2026-02-23T12:00:00Z"),
        )

        mock_client.messages.create.side_effect = [tool_call_response, final_response]

        # Setup Composio mock
        mock_ts = Mock()
        mock_toolset.return_value = mock_ts
        mock_ts.execute_action.return_value = {
            "data": {
                "messages": [
                    {"id": "1", "subject": "Test 1"},
                    {"id": "2", "subject": "Test 2"},
                    {"id": "3", "subject": "Test 3"},
                ]
            }
        }

        with patch.dict("os.environ", {"EVA_PROVIDER": "anthropic"}):
            result = run_agent("Check my emails", memory_dir)

        assert "3 unread emails" in result
        assert mock_client.messages.create.call_count == 2


class TestProviderSwitch:
    """Test switching between providers."""

    @pytest.fixture
    def memory_dir(self, tmp_path):
        """Create temporary memory files."""
        mem = tmp_path / "memory"
        mem.mkdir()
        (mem / "soul.md").write_text("I am Eva.")
        (mem / "user.md").write_text("Louis.")
        (mem / "telos.md").write_text("Help.")
        (mem / "context.md").write_text("# Context")
        (mem / "harness.md").write_text("Architecture.")
        return mem

    @patch("src.providers.nvidia.OpenAI")
    def test_nvidia_provider(self, mock_openai_cls, memory_dir):
        """Test NVIDIA provider is used when configured."""
        from src.agent import run_agent

        mock_client = Mock()
        mock_openai_cls.return_value = mock_client

        mock_message = Mock(content="Hello from Kimi!", tool_calls=None)
        mock_response = Mock(choices=[Mock(message=mock_message)])
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("os.environ", {"EVA_PROVIDER": "nvidia", "NVIDIA_API_KEY": "test"}):
            result = run_agent("Hello", memory_dir)

        assert result == "Hello from Kimi!"
        mock_openai_cls.assert_called_once()
```

**Step 2: Run integration tests**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/test_integration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add integration tests for agent flow"
```

---

### Task 12: Run Full Test Suite

**Step 1: Run all tests**

Run: `cd /home/louisdup/Agents/eva && python -m pytest tests/ -v --tb=short`
Expected: All PASS

**Step 2: If any failures, fix and re-run**

**Step 3: Final commit if needed**

```bash
git add -A
git commit -m "fix: resolve test failures" --allow-empty
```

---

## Summary

**Total Tasks:** 12
**Estimated Commits:** 12

**Phase 1: Provider Infrastructure** (Tasks 1-5)
- ProviderStrategy protocol
- Anthropic, NVIDIA, Grok strategies
- Refactored agent.py

**Phase 2: Tool Definitions** (Task 6)
- PTC-enabled tools with allowed_callers
- Provider-specific tool loading

**Phase 3: Peer Review** (Tasks 7-10)
- Multi-model review logic
- CLI runner
- GitHub Action
- Dependencies

**Phase 4: Integration** (Tasks 11-12)
- Integration tests
- Full test suite validation

**Required Secrets (to add to GitHub):**
- `OPENAI_API_KEY` - For GPT-4o peer review
- `GOOGLE_AI_API_KEY` - For Gemini peer review
