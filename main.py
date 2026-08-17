"""Compatibility entry point for running the project from a checkout.

Install the project first with `pip install -e .`, then either run this file or
use the `downloads-organizer` command exposed by the package.
"""

from downloads_organizer.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
