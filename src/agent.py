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
