"""Eva - Private optimization engine for Louis du Plessis."""
import argparse
import sys
from pathlib import Path

from .agent import run_agent


def interactive_mode(memory_dir: Path):
    """Run Eva in interactive REPL mode."""
    print("Eva - Private optimization engine")
    print("Type 'exit' or 'quit' to leave, Ctrl+C to interrupt\n")

    while True:
        try:
            prompt = input("You: ").strip()
            if not prompt:
                continue
            if prompt.lower() in ("exit", "quit", "q"):
                print("— Eva")
                break

            import sys
            print("Thinking...", flush=True)
            response = run_agent(prompt, memory_dir)
            sys.stdout.write(f"\nEva: {response}\n\n")
            sys.stdout.flush()
        except KeyboardInterrupt:
            print("\n— Eva")
            break
        except EOFError:
            print("\n— Eva")
            break
        except Exception as e:
            import traceback
            print(f"Error: {e}")
            traceback.print_exc()
            print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Eva orchestrator")
    parser.add_argument("prompt", nargs="*", help="Prompt for Eva")
    parser.add_argument(
        "--memory-dir",
        type=Path,
        default=Path("memory"),
        help="Path to memory directory",
    )
    args = parser.parse_args()

    # Join all args as prompt (allows: eva what should I do today)
    prompt = " ".join(args.prompt).strip() if args.prompt else ""

    if not prompt:
        # No prompt = interactive mode
        interactive_mode(args.memory_dir)
        return

    try:
        response = run_agent(prompt, args.memory_dir)
        print(response)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
