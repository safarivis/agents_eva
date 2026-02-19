"""Agent module for Eva - agentic loop implementation."""
import os
import json
import anthropic
from openai import OpenAI
from pathlib import Path

from .memory import load_all_memory
from .tools import TOOLS, execute_tool

# Provider configuration
PROVIDER = os.environ.get("EVA_PROVIDER", "anthropic")  # "anthropic" or "nvidia"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "moonshotai/kimi-k2.5"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"


def _convert_tools_to_openai_format(tools: list) -> list:
    """Convert Anthropic tool format to OpenAI function format."""
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        }
        for tool in tools
    ]


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
    2. Call LLM with tools
    3. Execute any tool calls (loop until done)
    4. Return final response

    Args:
        prompt: User prompt
        memory_dir: Path to memory directory

    Returns:
        Final text response from LLM
    """
    memory = load_all_memory(memory_dir)
    system = build_system_prompt(memory)

    if PROVIDER == "nvidia":
        return _run_agent_nvidia(prompt, system, memory_dir)
    else:
        return _run_agent_anthropic(prompt, system, memory_dir)


def _run_agent_anthropic(prompt: str, system: str, memory_dir: Path) -> str:
    """Run agent using Anthropic Claude."""
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": prompt}]

    while True:
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=4096,
            system=system,
            tools=TOOLS,
            messages=messages,
        )

        tool_uses = [b for b in response.content if b.type == "tool_use"]
        if not tool_uses:
            return "".join(b.text for b in response.content if hasattr(b, "text"))

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tool in tool_uses:
            result = execute_tool(tool.name, tool.input, memory_dir)
            tool_results.append(
                {"type": "tool_result", "tool_use_id": tool.id, "content": result}
            )
        messages.append({"role": "user", "content": tool_results})


def _run_agent_nvidia(prompt: str, system: str, memory_dir: Path) -> str:
    """Run agent using NVIDIA API (Kimi K2.5)."""
    client = OpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=os.environ.get("NVIDIA_API_KEY"),
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    tools = _convert_tools_to_openai_format(TOOLS)

    while True:
        response = client.chat.completions.create(
            model=NVIDIA_MODEL,
            max_tokens=4096,
            messages=messages,
            tools=tools,
            tool_choice="auto",
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
