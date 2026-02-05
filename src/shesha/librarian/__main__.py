"""Module entrypoint for the Librarian CLI.

Usage:
    python -m shesha.librarian ...
"""

import sys

from shesha.librarian.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

