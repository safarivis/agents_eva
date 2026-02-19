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
