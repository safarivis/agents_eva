"""Tools module for Eva - tool definitions and execution."""
from pathlib import Path

from .memory import load_memory_file, update_context
from .composio_tools import (
    github_get_repo,
    github_list_issues,
    github_create_issue,
    github_create_pull_request,
    github_get_file_contents,
)

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
    # GitHub Tools
    {
        "name": "github_get_repo",
        "description": "Get information about a GitHub repository (stars, forks, issues, description)",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner (username or org)"},
                "repo": {"type": "string", "description": "Repository name"},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "github_list_issues",
        "description": "List issues in a GitHub repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["owner", "repo"],
        },
    },
    {
        "name": "github_create_issue",
        "description": "Create a new issue in a GitHub repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Issue body/description"},
                "labels": {"type": "array", "items": {"type": "string"}, "description": "Label names"},
            },
            "required": ["owner", "repo", "title"],
        },
    },
    {
        "name": "github_create_pull_request",
        "description": "Create a pull request in a GitHub repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "title": {"type": "string", "description": "PR title"},
                "head": {"type": "string", "description": "Branch with changes"},
                "base": {"type": "string", "description": "Branch to merge into (usually main)"},
                "body": {"type": "string", "description": "PR description"},
            },
            "required": ["owner", "repo", "title", "head", "base"],
        },
    },
    {
        "name": "github_get_file_contents",
        "description": "Get contents of a file from a GitHub repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string", "description": "Repository owner"},
                "repo": {"type": "string", "description": "Repository name"},
                "path": {"type": "string", "description": "File path in repo (e.g., 'src/main.py')"},
                "ref": {"type": "string", "description": "Branch or commit (default: main)", "default": "main"},
            },
            "required": ["owner", "repo", "path"],
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

    # GitHub Tools
    elif name == "github_get_repo":
        try:
            result = github_get_repo(args["owner"], args["repo"])
            return f"📁 {result['full_name']}\n⭐ {result['stars']} | 🍴 {result['forks']} | 🐛 {result['open_issues']} open issues\n📝 {result['description'] or 'No description'}\n🔗 {result['html_url']}"
        except RuntimeError as e:
            return f"⚠️ {e}\nSet GITHUB_TOKEN env var: export GITHUB_TOKEN='ghp_xxx'"

    elif name == "github_list_issues":
        try:
            issues = github_list_issues(
                args["owner"],
                args["repo"],
                state=args.get("state", "open"),
                limit=args.get("limit", 10),
            )
            if not issues:
                return "No issues found."
            lines = [f"🐛 Issues in {args['owner']}/{args['repo']}:", ""]
            for i in issues:
                lines.append(f"#{i['number']}: {i['title']} ({i['state']}) - {i['author']}")
            return "\n".join(lines)
        except RuntimeError as e:
            return f"⚠️ {e}\nSet GITHUB_TOKEN env var: export GITHUB_TOKEN='ghp_xxx'"

    elif name == "github_create_issue":
        try:
            result = github_create_issue(
                args["owner"],
                args["repo"],
                args["title"],
                body=args.get("body", ""),
                labels=args.get("labels"),
            )
            return f"✅ Issue created: #{result['number']}\n🔗 {result['url']}"
        except RuntimeError as e:
            return f"⚠️ {e}\nSet GITHUB_TOKEN env var: export GITHUB_TOKEN='ghp_xxx'"

    elif name == "github_create_pull_request":
        try:
            result = github_create_pull_request(
                args["owner"],
                args["repo"],
                args["title"],
                args["head"],
                args["base"],
                body=args.get("body", ""),
            )
            return f"✅ Pull request created: #{result['number']}\n🔗 {result['url']}"
        except RuntimeError as e:
            return f"⚠️ {e}\nSet GITHUB_TOKEN env var: export GITHUB_TOKEN='ghp_xxx'"

    elif name == "github_get_file_contents":
        try:
            content = github_get_file_contents(
                args["owner"],
                args["repo"],
                args["path"],
                ref=args.get("ref", "main"),
            )
            return f"📄 {args['path']}:\n```\n{content[:2000]}\n```"
        except RuntimeError as e:
            return f"⚠️ {e}\nSet GITHUB_TOKEN env var: export GITHUB_TOKEN='ghp_xxx'"

    else:
        raise ToolExecutionError(f"Unknown tool: {name}")
