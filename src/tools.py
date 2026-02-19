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
