#!/usr/bin/env python3
"""Interactive Barsoom novel explorer using Shesha."""

import argparse
import os
import sys
from pathlib import Path

from shesha import Shesha
from shesha.rlm.trace import TokenUsage, Trace

BOOKS = {
    "barsoom-1.txt": "A Princess of Mars",
    "barsoom-2.txt": "The Gods of Mars",
    "barsoom-3.txt": "The Warlord of Mars",
    "barsoom-4.txt": "Thuvia, Maid of Mars",
    "barsoom-5.txt": "The Chessmen of Mars",
    "barsoom-6.txt": "The Master Mind of Mars",
    "barsoom-7.txt": "A Fighting Man of Mars",
}


def is_exit_command(user_input: str) -> bool:
    """Check if user input is an exit command."""
    return user_input.lower() in ("quit", "exit")


def format_stats(execution_time: float, token_usage: TokenUsage, trace: Trace) -> str:
    """Format verbose stats for display after an answer."""
    prompt = token_usage.prompt_tokens
    completion = token_usage.completion_tokens
    total = token_usage.total_tokens
    lines = [
        "---",
        f"Execution time: {execution_time:.2f}s",
        f"Tokens: {total} (prompt: {prompt}, completion: {completion})",
        f"Trace steps: {len(trace.steps)}",
    ]
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Explore the Barsoom novels using Shesha RLM")
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Force re-upload of novels (even if project exists)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show execution stats after each answer",
    )
    return parser.parse_args(argv)


STORAGE_PATH = "./barsoom_data"
PROJECT_NAME = "barsoom"


def get_datasets_dir() -> Path:
    """Get the path to the barsoom test datasets directory."""
    return Path(__file__).parent.parent / "test-datasets" / "barsoom"


def setup_project(shesha: Shesha) -> None:
    """Set up the barsoom project by uploading novels."""
    print("Setting up Barsoom project...")
    project = shesha.create_project(PROJECT_NAME)
    datasets_dir = get_datasets_dir()

    for filename, title in BOOKS.items():
        filepath = datasets_dir / filename
        print(f"Uploading: {title} ({filename})")
        project.upload(filepath)

    print(f"Setup complete! {len(BOOKS)} novels loaded.")


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Check for API key
    if not os.environ.get("SHESHA_API_KEY"):
        print("Error: SHESHA_API_KEY environment variable not set.")
        print("Set it with: export SHESHA_API_KEY=your-api-key")
        sys.exit(1)

    # Initialize Shesha
    shesha = Shesha(storage_path=STORAGE_PATH)

    # Check if project exists
    project_exists = PROJECT_NAME in shesha.list_projects()

    # Setup if needed
    if args.setup or not project_exists:
        setup_project(shesha)

    # Get the project
    project = shesha.get_project(PROJECT_NAME)
    if project is None:
        print("Error: Failed to load barsoom project.")
        sys.exit(1)

    print()
    print('Ask questions about the Barsoom series. Type "quit" or "exit" to leave.')
    print()

    # Interactive loop
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if is_exit_command(user_input):
            print("Goodbye!")
            break

        try:
            result = project.query(user_input)
            print()
            print(result.answer)
            print()

            if args.verbose:
                print(format_stats(result.execution_time, result.token_usage, result.trace))
                print()

        except Exception as e:
            print(f"\nError: {e}")
            print('Try again or type "quit" to exit.')
            print()


if __name__ == "__main__":
    main()
