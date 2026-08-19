"""
CLI command: ``quiltwright weave`` -- interleave a quilt for one panel.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

from pathlib import Path

import click
import numpy as np

from quiltwright.cli.main import cli
from quiltwright.cli.options import resolve_grid
from quiltwright.lfd import QUILT_PRESETS, QuiltSpec
from quiltwright.weave import Calibration, weave_quilt


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

    columns, rows = resolve_grid(preset, grid_str, quilt.stem)

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
