# Eva Phase 2: Agent Core Design

**Date:** 2026-02-19
**Status:** Approved
**Depends on:** Phase 1 Foundation (complete)

---

## Overview

Phase 2 implements the agent core - the agentic loop that loads memory, calls Claude with tools, and executes tool requests. This is the "brain" that makes Eva functional.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| SDK | Anthropic Python SDK only | Radical simplicity, no extra frameworks |
| Execution model | Fully autonomous | Red lines defined in soul.md, everything else executes freely |
| Trigger model | Single-shot per trigger | GitHub Actions designed for this, clean environments |
| Phase 2 tools | Memory-only | Verify core works before adding complexity |
| Entry point | CLI only | Testable locally, GitHub Actions calls same way |

## Architecture

```
src/
├── memory.py      # ✅ Phase 1 complete
├── tools.py       # Tool definitions + execute_tool()
├── agent.py       # run_agent() - agentic loop
├── eva.py         # CLI entry point
└── __main__.py    # Enable `python -m src.eva`
```

---

## Component Designs

### tools.py

Tool definitions in Anthropic SDK format:

```python
TOOLS = [
    {
        "name": "read_memory",
        "description": "Read a memory file (soul, user, telos, context, harness)",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "enum": ["soul", "user", "telos", "context", "harness"]}
            },
            "required": ["name"]
        }
    },
    {
        "name": "update_context",
        "description": "Add entry to context.md rolling log",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
                "summary": {"type": "string"},
                "details": {"type": "string"},
                "followup": {"type": "string"}
            },
            "required": ["category", "summary", "details"]
        }
    }
]

def execute_tool(name: str, args: dict, memory_dir: Path) -> str:
    """Execute a tool and return result as string."""
```

### agent.py

Single function for the agentic loop:

```python
def build_system_prompt(memory: dict[str, str]) -> str:
    """Combine memory files into system prompt."""

def run_agent(prompt: str, memory_dir: Path) -> str:
    """Run one agent loop cycle.

    1. Load memory into system prompt
    2. Call Claude with tools
    3. Execute any tool calls (loop until done)
    4. Return final response
    """
```

Key behaviors:
- Memory loaded once at start, injected into system prompt
- Loops until Claude stops requesting tools
- Returns final text response

### eva.py

CLI entry point:

```python
def main():
    parser = argparse.ArgumentParser(description="Eva orchestrator")
    parser.add_argument("prompt", nargs="?", help="Prompt for Eva")
    parser.add_argument("--memory-dir", type=Path, default=Path("memory"))
```

Usage:
```bash
python -m src.eva "What's in my soul.md?"
python -m src.eva "Summarize my recent context" --memory-dir ./memory
```

---

## Testing Strategy

### tests/test_tools.py
- `test_tools_schema_valid`: TOOLS list has correct structure
- `test_execute_read_memory`: returns file content
- `test_execute_update_context`: appends to context.md
- `test_execute_unknown_tool`: raises error

### tests/test_agent.py
- `test_build_system_prompt`: includes all 5 memory sections
- `test_run_agent_simple_response`: mocked Claude returns text (no tools)
- `test_run_agent_with_tool_call`: mocked Claude uses read_memory tool
- `test_run_agent_missing_memory`: raises FileNotFoundError

### tests/test_eva.py
- `test_main_with_prompt`: runs successfully
- `test_main_no_prompt`: exits with usage message
- `test_main_missing_memory_dir`: exits with error

Approach:
- Mock `anthropic.Anthropic()` to avoid real API calls
- Use `tmp_path` fixtures for memory directory
- TDD: write failing tests first, then implement

---

## Error Handling

| Error Type | Strategy |
|------------|----------|
| Tool execution error | Return error message to Claude, let it recover |
| Missing memory file | Fail fast with FileNotFoundError |
| API errors | Bubble up to eva.py, exit with error code |
| Unknown tool | Raise ToolExecutionError |

```python
class ToolExecutionError(Exception):
    """Raised when tool execution fails."""
    pass
```

---

## Red Lines (Future)

No red line checks needed for Phase 2 - `read_memory` and `update_context` are safe operations.

Will add `is_red_line_action()` check in Phase 3+ when we add:
- Email sending
- WhatsApp messaging
- File deletion
- Financial operations

---

## Success Criteria

1. `python -m src.eva "What is my purpose?"` returns response using memory
2. All tests pass with mocked API calls
3. Agent can use tools in a loop (e.g., read multiple memory files)
4. Context updates persist to context.md

---

## Next Phase

Phase 3: GitHub Actions workflows (heartbeat, morning-brief, wa-message)
