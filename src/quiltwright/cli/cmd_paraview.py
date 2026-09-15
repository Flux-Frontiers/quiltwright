"""
CLI command: ``quiltwright paraview`` -- a ParaView state file, straight to a quilt.

The shell face of :mod:`quiltwright.paraview`.  Hand it the ``.pvsm`` a
ParaView session saved and it comes back a light-field quilt of that
session -- pipeline, colour maps, transfer functions and camera intact,
because the sweep runs inside ParaView's own ``pvpython`` rather than on an
export of the data.

The state's camera is the centre view and its focal point becomes the
holographic focal plane, so frame the scene in ParaView the way you want it
seen and save state.  The depth budget is printed before the sweep starts,
from a probe that loads the state without rendering; ParaView's startup is
a few seconds, and a 48-view sweep of a large dataset is the expensive part.

**ParaView is optional and this command is the place that says so.**  It is
a desktop application with its own interpreter, never a Python dependency.
``--check`` reports where ``pvpython`` was found before anything is loaded,
and a missing ParaView fails with install instructions rather than a
traceback.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import time
from pathlib import Path

import click

from quiltwright.cli.main import cli
from quiltwright.quilt import QUILT_PRESETS, STANDARD_VIEW_CONE, resolve_view_cone, save_quilt


@cli.command()
@click.argument(
    "state", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=False
)
@click.option(
    "--device",
    type=click.Choice(sorted(QUILT_PRESETS)),
    default="16-landscape",
    show_default=True,
    help="Target display, which sets the quilt grid, size and view cone.",
)
@click.option(
    "--fov",
    type=float,
    default=14.0,
    show_default=True,
    help="Vertical field of view in degrees; the camera is dollied back to keep "
    "the state's framing. 0 keeps the state's own FOV.",
)
@click.option(
    "--zoom",
    type=float,
    default=None,
    help="Dolly factor after framing; > 1 fills more of each tile, which is what "
    "drives perceived depth.",
)
@click.option(
    "--view-cone",
    type=float,
    default=None,
    help=f"View cone in degrees. Defaults to the device's own, capped at "
    f"{STANDARD_VIEW_CONE:g} so a wide panel does not overrun the disparity budget.",
)
@click.option(
    "--orientation-axes",
    is_flag=True,
    help="Keep ParaView's corner axes widget. Off by default: it is pinned to "
    "the screen, so it would sit on the glass in every view.",
)
@click.option("--preview", is_flag=True, help="Quarter-size quilt, for iterating on framing.")
@click.option(
    "--still",
    is_flag=True,
    help="One centre view as a flat image, at the device's aspect, instead of a quilt.",
)
@click.option(
    "--keep-views",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help="Directory to keep the per-view PNGs and camera probe in.",
)
@click.option(
    "--out",
    "out_stem",
    default=None,
    help="Output stem; defaults to the state name under renders/quilts/ "
    "(or gallery/ with --still).",
)
@click.option("--cast", "do_cast", is_flag=True, help="Send the result to Looking Glass Bridge.")
@click.option("--check", is_flag=True, help="Report where pvpython was found and exit.")
def paraview(
    state: Path | None,
    device: str,
    fov: float,
    zoom: float | None,
    view_cone: float | None,
    orientation_axes: bool,
    preview: bool,
    still: bool,
    keep_views: Path | None,
    out_stem: str | None,
    do_cast: bool,
    check: bool,
) -> None:
    """Render the ParaView state file STATE as a quilt.

    \b
    quiltwright paraview session.pvsm
    quiltwright paraview session.pvsm --still
    quiltwright paraview session.pvsm --device 27-portrait --zoom 1.4 --cast
    quiltwright paraview --check
    """
    from quiltwright.paraview import (
        ParaViewNotAvailable,
        available,
        depth_report,
        probe_paraview_state,
        render_paraview_quilt,
    )

    if check:
        found = available()
        if found is None:
            raise click.ClickException(
                "no pvpython found: brew install --cask paraview, or set PARAVIEW_BINARY"
            )
        click.echo(f"pvpython: {found}")
        return
    if state is None:
        raise click.UsageError("STATE is required unless --check is given.")

    spec, capped_from = resolve_view_cone(QUILT_PRESETS[device], view_cone)
    if capped_from is not None and not still:
        click.echo(
            f"  view cone        {capped_from:.0f} deg native -> {spec.view_cone:.0f} to keep "
            f"the budget in range (--view-cone {capped_from:.0f} to override)"
        )
    if preview:
        spec = spec.scaled(0.25)
    if still:
        spec = spec.still()
    fov_arg = None if fov == 0 else fov

    click.echo(f"paraview hologram <- {state.name}{' (preview)' if preview else ''}")
    try:
        camera = probe_paraview_state(state, spec, fov=fov_arg, zoom=zoom)
    except (ParaViewNotAvailable, RuntimeError, FileNotFoundError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(
        f"  view             {camera.view}, eye {tuple(round(c, 3) for c in camera.position)}, "
        f"focal {camera.focal_distance:.3f}, fov {camera.fov:.1f} deg"
    )
    click.echo(
        f"  quilt            {spec.quilt_width}x{spec.quilt_height}, "
        f"tiles {spec.tile_width}x{spec.tile_height}, cone {spec.view_cone:.0f} deg"
    )
    if not still:
        click.echo(depth_report(camera, spec))

    started = time.time()
    try:
        quilt = render_paraview_quilt(
            state,
            spec,
            fov=fov_arg,
            zoom=zoom,
            hide_orientation_axes=not orientation_axes,
            keep_views=keep_views,
        )
    except (ParaViewNotAvailable, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc
    elapsed = time.time() - started

    default_stem = f"gallery/{state.stem}" if still else f"renders/quilts/{state.stem}"
    stem = out_stem or default_stem
    out = save_quilt(quilt, f"{stem}-preview" if preview else stem, spec)
    click.echo(f"  wrote {out}  ({elapsed:.0f}s, {elapsed / spec.n_views:.1f}s/view)")

    if do_cast:
        from quiltwright.bridge import cast_quilt

        cast_quilt(out, spec)
        click.echo("  cast to Looking Glass Bridge")
