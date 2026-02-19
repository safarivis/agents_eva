"""Memory module for Eva - load and save memory files."""
from datetime import datetime
from pathlib import Path

import tiktoken

# Required memory files for Eva's identity and context
MEMORY_FILES = ["soul", "user", "telos", "context", "harness"]


def load_memory_file(memory_dir: Path, name: str) -> str:
    """Load a memory file by name.

    Args:
        memory_dir: Path to memory directory
        name: Name of memory file (without .md extension)

    Returns:
        Content of the memory file as string

    Raises:
        FileNotFoundError: If memory file does not exist
    """
    file_path = memory_dir / f"{name}.md"
    if not file_path.exists():
        raise FileNotFoundError(f"Memory file not found: {file_path}")
    return file_path.read_text()


def load_all_memory(memory_dir: Path) -> dict[str, str]:
    """Load all required memory files.

    Args:
        memory_dir: Path to memory directory

    Returns:
        Dict mapping memory name to content

    Raises:
        FileNotFoundError: If any required memory file is missing
    """
    return {name: load_memory_file(memory_dir, name) for name in MEMORY_FILES}


# Initialize encoder once for efficiency
_encoder = tiktoken.get_encoding("cl100k_base")


def count_memory_tokens(text: str) -> int:
    """Count tokens in text using cl100k_base encoding.

    Args:
        text: Text to count tokens in

    Returns:
        Number of tokens
    """
    return len(_encoder.encode(text))


def update_context(
    memory_dir: Path,
    category: str,
    summary: str,
    details: str,
    followup: str | None = None,
) -> None:
    """Append a new entry to context.md.

    Args:
        memory_dir: Path to memory directory
        category: Entry category (Decision, Learning, Commitment, etc.)
        summary: One-line summary
        details: Full details of the entry
        followup: Optional follow-up action
    """
    context_file = memory_dir / "context.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    entry = f"\n### {timestamp} - [{category}]\n"
    entry += f"**Summary:** {summary}\n"
    entry += f"**Details:** {details}\n"
    if followup:
        entry += f"**Follow-up:** {followup}\n"

    with context_file.open("a") as f:
        f.write(entry)
