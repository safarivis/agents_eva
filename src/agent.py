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
