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
    """quiltwright -- holographic output for Looking Glass displays.

    Hardware and tooling on a finished quilt (cast, weave, wallpaper,
    bridge), plus mesh / cartoon / probe for arbitrary input. Composed
    exhibits for the bundled scenes live in scripts/, not here.
    """


# Import subcommands to register them
from quiltwright.cli import (  # noqa: E402, F401
    cmd_bridge,
    cmd_cartoon,
    cmd_cast,
    cmd_mesh,
    cmd_probe,
    cmd_wallpaper,
    cmd_weave,
)
