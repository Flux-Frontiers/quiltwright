"""
Command-line entry point for ``quiltwright``.

Stays core-only -- numpy, pillow and click, the same promise the package makes
for a ``pip install quiltwright`` with no extras -- so weaving a wallpaper
never needs the PyVista/VTK rendering stack.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import importlib.metadata
import re
from pathlib import Path

import click
import numpy as np

from quiltwright.lfd import QUILT_PRESETS, QuiltSpec
from quiltwright.weave import Calibration, weave_quilt

#: Looking Glass filename convention: ``stem_qs<cols>x<rows>a<aspect>.ext``
#: (see :meth:`~quiltwright.lfd.QuiltSpec.filename`).  Recovers the tiling
#: grid from a quilt saved by :func:`~quiltwright.lfd.save_quilt` when
#: neither ``--preset`` nor ``--grid`` is given.
_QS_SUFFIX = re.compile(r"_qs(\d+)x(\d+)a[\d.]+$")


def _grid_from_filename(stem: str) -> tuple[int, int] | None:
    """Recover ``(columns, rows)`` from a Looking Glass quilt filename.

    :param stem: Filename without its extension.
    :return: ``(columns, rows)``, or ``None`` if the suffix is absent.
    """
    m = _QS_SUFFIX.search(stem)
    return (int(m.group(1)), int(m.group(2))) if m else None


def _resolve_grid(preset: str | None, grid: str | None, stem: str) -> tuple[int, int]:
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
    found = _grid_from_filename(stem)
    if found is not None:
        return found
    raise click.UsageError(
        f"cannot determine the quilt's tiling grid from {stem!r}: "
        "pass --preset or --grid, or use a filename ending in "
        "_qs<cols>x<rows>a<aspect> (the save_quilt() convention)"
    )


@click.group()
@click.version_option(version=importlib.metadata.version("quiltwright"), prog_name="quiltwright")
def cli() -> None:
    """quiltwright -- holographic output for Looking Glass displays."""


@cli.command("weave")
@click.argument("quilt", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--cal",
    "cal_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the panel's visual.json calibration file.",
)
@click.option(
    "--preset",
    type=click.Choice(sorted(QUILT_PRESETS)),
    default=None,
    help="Quilt tiling grid, by device preset name.",
)
@click.option(
    "--grid",
    "grid_str",
    metavar="COLSxROWS",
    default=None,
    help="Quilt tiling grid, explicit (e.g. 8x6); defaults to parsing the "
    "_qs<cols>x<rows> filename suffix.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output path (default: <quilt stem>_native_<serial>.png).",
)
@click.option(
    "--invert",
    is_flag=True,
    default=False,
    help="Reverse the view order if the fused result reads inside-out.",
)
def weave_cmd(
    quilt: Path,
    cal_path: Path,
    preset: str | None,
    grid_str: str | None,
    output: Path | None,
    invert: bool,
) -> None:
    """Weave a quilt into a native pre-lensed frame for one panel.

    Interleaves QUILT into a native-resolution frame, ready to display 1:1 on
    the panel -- most usefully as its desktop wallpaper, with no Bridge
    process required. See quiltwright.weave for the math.
    """
    from PIL import Image

    columns, rows = _resolve_grid(preset, grid_str, quilt.stem)

    array = np.asarray(Image.open(quilt).convert("RGB"))
    q_h, q_w = array.shape[:2]
    # weave_quilt() reads columns/rows/pixel-dims off *spec*, not aspect --
    # but a spec should still describe the quilt it names, not a placeholder.
    aspect = (q_w / columns) / (q_h / rows)
    spec = QuiltSpec(columns=columns, rows=rows, quilt_width=q_w, quilt_height=q_h, aspect=aspect)

    cal = Calibration.load(cal_path)
    native = weave_quilt(array, spec, cal, invert=invert)

    if output is not None:
        out_path = output
    else:
        suffix = f"_native_{cal.serial}" if cal.serial else "_native"
        out_path = quilt.with_name(quilt.stem.split("_qs")[0] + suffix + ".png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(native).save(out_path)

    click.echo(
        f"{quilt.name}  ({columns}x{rows} views, {q_w}x{q_h})  ->  "
        f"{out_path}  ({cal.screen_w}x{cal.screen_h}"
        f"{', ' + cal.serial if cal.serial else ''})"
    )


def main() -> None:
    """The ``quiltwright`` console script entry point."""
    cli()


if __name__ == "__main__":
    main()
