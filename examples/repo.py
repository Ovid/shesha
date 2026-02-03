#!/usr/bin/env python3
"""Interactive git repository explorer using Shesha."""

import argparse


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Explore git repositories using Shesha RLM"
    )
    parser.add_argument(
        "repo",
        nargs="?",
        help="Git repository URL or local path (shows picker if omitted)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Auto-apply updates without prompting",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show execution stats after each answer",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    pass
