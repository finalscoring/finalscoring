"""``fs`` command-line entry point.

Wired up as a console script in ``pyproject.toml``. After installation:

    $ fs --help

Sub-commands cover the full development and operational loop: schema
initialization, scraping, building, and a placeholder serve command.
"""

from final_scoring.cli.app import app

__all__ = ["app"]
