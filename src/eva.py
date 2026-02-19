"""Eva - Private optimization engine for Louis du Plessis."""
import argparse
import sys
from pathlib import Path

from .agent import run_agent


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Eva orchestrator")
    parser.add_argument("prompt", nargs="?", help="Prompt for Eva")
    parser.add_argument(
        "--memory-dir",
        type=Path,
        default=Path("memory"),
        help="Path to memory directory",
    )
    args = parser.parse_args()

    if not args.prompt:
        print("Usage: python -m src.eva 'Your prompt here'")
        sys.exit(1)

    try:
        response = run_agent(args.prompt, args.memory_dir)
        print(response)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
