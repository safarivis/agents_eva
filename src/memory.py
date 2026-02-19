"""Memory module for Eva - load and save memory files."""
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
