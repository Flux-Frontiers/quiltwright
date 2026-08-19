"""
Shared option handling for the quiltwright CLI.

The one thing every command has to agree on is how a quilt's tiling grid is
determined, because a quilt PNG does not carry it: the grid lives in the
Looking Glass filename suffix, and getting it wrong silently shuffles the
views rather than failing.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import re

import click

from quiltwright.lfd import QUILT_PRESETS

#: Looking Glass filename convention: ``stem_qs<cols>x<rows>a<aspect>.ext``
#: (see :meth:`~quiltwright.lfd.QuiltSpec.filename`).  Recovers the tiling
#: grid from a quilt saved by :func:`~quiltwright.lfd.save_quilt` when
#: neither ``--preset`` nor ``--grid`` is given.
QS_SUFFIX = re.compile(r"_qs(\d+)x(\d+)a([\d.]+)$")


def grid_from_filename(stem: str) -> tuple[int, int] | None:
    """Recover ``(columns, rows)`` from a Looking Glass quilt filename.

    :param stem: Filename without its extension.
    :return: ``(columns, rows)``, or ``None`` if the suffix is absent.
    """
    m = QS_SUFFIX.search(stem)
    return (int(m.group(1)), int(m.group(2))) if m else None


def aspect_from_filename(stem: str) -> float | None:
    """Recover the tile aspect from a Looking Glass quilt filename.

    :param stem: Filename without its extension.
    :return: The aspect, or ``None`` if the suffix is absent.
    """
    m = QS_SUFFIX.search(stem)
    return float(m.group(3)) if m else None


def resolve_grid(preset: str | None, grid: str | None, stem: str) -> tuple[int, int]:
    """Determine the quilt's tiling grid from ``--preset``, ``--grid``, or the
    filename, in that order.

    :param preset: ``--preset`` value, or ``None``.
    :param grid: ``--grid`` value (``"COLSxROWS"``), or ``None``.
    :param stem: Quilt filename without its extension, for the fallback.
    :return: ``(columns, rows)``.
    :raises click.UsageError: If both ``--preset`` and ``--grid`` are given,
        or if none of the three sources yields a grid.
    """
    if preset is not None and grid is not None:
        raise click.UsageError("--preset and --grid are mutually exclusive")
    if preset is not None:
        spec = QUILT_PRESETS[preset]
        return spec.columns, spec.rows
    if grid is not None:
        cols, rows = grid.lower().split("x")
        return int(cols), int(rows)
    found = grid_from_filename(stem)
    if found is not None:
        return found
    raise click.UsageError(
        f"cannot determine the quilt's tiling grid from {stem!r}: "
        "pass --preset or --grid, or use a filename ending in "
        "_qs<cols>x<rows>a<aspect> (the save_quilt() convention)"
    )
