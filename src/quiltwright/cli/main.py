"""
Root Click group for the quiltwright CLI.

Stays core-only -- numpy, pillow and click, the same promise the package
makes for a ``pip install quiltwright`` with no extras -- so nothing here
drags in the PyVista/VTK rendering stack.  A subcommand that needs a heavier
dependency imports it inside its own callback.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import importlib.metadata

import click


@click.group()
@click.version_option(version=importlib.metadata.version("quiltwright"), prog_name="quiltwright")
def cli() -> None:
    """quiltwright -- holographic output for Looking Glass displays."""


# Import subcommands to register them
from quiltwright.cli import (  # noqa: E402, F401
    cmd_bridge,
    cmd_cartoon,
    cmd_cast,
    cmd_wallpaper,
    cmd_weave,
)
