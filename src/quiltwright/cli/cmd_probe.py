"""
CLI command: ``quiltwright probe`` -- measure a POV-Ray scene's depth range.

Every number in a depth budget except one comes from the display.  The
exception is the scene's own near and far depth, and getting those wrong is
what puts a subject behind the glass or ghosting in front of it -- so they
are measured here rather than guessed, by sliding an opaque plane along the
view axis and scoring each frame for how much geometry is still in front of
it (:func:`~quiltwright.povray.depth_sweep`).

The output is two numbers to hand to
:func:`~quiltwright.lfd.focal_distance_for_range`, plus the share of the
frame the sweep could never hide -- sky, or a sea running to the horizon.
That residual is not far content: it never occludes, it is low-contrast, and
paying disparity for it pushes the subject off the glass.  Leave it out of
the balance.

Two things this command cannot do for you:

*It probes the camera you give it.*  A hologram's eye is usually not the
scene's own, and a sweep through the wrong camera describes a scene nobody
is going to render.  ``--eye``/``--aim``/``--fov`` are how you say which.

*It cannot read a backdrop's knee.*  A room's walls close the sweep out, so
the 95% rule lands on real content.  A sea does not close -- it keeps taking
a little more of the frame at every distance -- and there the printed *far*
is the end of the sweep, not the subject.  Fit the far tail, subtract that
creep, and take 95% of what is left; ``--rows`` prints the curve to fit.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

from pathlib import Path

import click

from quiltwright.cli.main import cli


@cli.command("probe")
@click.argument("scene", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--eye",
    type=float,
    nargs=3,
    metavar="X Y Z",
    required=True,
    help="Camera position to probe through, in scene units.",
)
@click.option(
    "--aim",
    type=float,
    nargs=3,
    metavar="X Y Z",
    required=True,
    help="Camera look_at point.",
)
@click.option(
    "--fov",
    type=float,
    default=53.13,
    show_default=True,
    help="Vertical field of view in degrees. The default is POV-Ray's own "
    "unit direction/up lens, 2*atan(0.5).",
)
@click.option(
    "--min-distance",
    type=float,
    default=None,
    help="Near end of the sweep [default: 1% of --max-distance]. A scene "
    "composed far from its eye -- porin sits 1100 units out -- wants its "
    "probes where its content is, not 200 of them in front of it.",
)
@click.option(
    "--max-distance",
    type=float,
    default=400.0,
    show_default=True,
    help="Far end of the sweep, before the one at infinity.",
)
@click.option(
    "--probes",
    type=int,
    default=200,
    show_default=True,
    help="Number of planes between the two distances.",
)
@click.option(
    "--include-path",
    "include_paths",
    multiple=True,
    metavar="DIR",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Extra #include directory; repeatable. The scene's own is automatic.",
)
@click.option("--width", type=int, default=320, show_default=True, help="Probe frame width.")
@click.option("--height", type=int, default=180, show_default=True, help="Probe frame height.")
@click.option(
    "--quality",
    type=int,
    default=11,
    show_default=True,
    help="POV-Ray +Q. Below 8 it disables transparency and glass reads solid.",
)
@click.option(
    "--pov-arg",
    "pov_args",
    multiple=True,
    metavar="ARG",
    help="Extra POV-Ray argument, e.g. +MV3.1 for a scene with no #version "
    "pragma of its own; repeatable.",
)
@click.option("--rows", is_flag=True, help="Print the whole curve, one distance per line.")
def probe(
    scene: Path,
    eye: tuple[float, float, float],
    aim: tuple[float, float, float],
    fov: float,
    min_distance: float | None,
    max_distance: float,
    probes: int,
    include_paths: tuple[Path, ...],
    width: int,
    height: int,
    quality: int,
    pov_args: tuple[str, ...],
    rows: bool,
) -> None:
    """Measure SCENE's near and far depth by plane sweep.

    \b
    quiltwright probe pov-scenes/bell_jar/bj.pov --eye 0 35 -95 --aim 0 18 0
    quiltwright probe pov-scenes/porin/3porin.pov --eye 0 0 -1100 --aim 0 0 0 \\
        --include-path pov-scenes/myinclude --min-distance 700 \\
        --max-distance 1600 --pov-arg +MV3.1
    """
    import numpy as np

    from quiltwright.povray import PovCamera, depth_sweep, summarise_depth_sweep

    if quality < 8:
        click.echo(f"warning: +Q{quality} disables transparency; glass will read solid", err=True)
    near_end = max_distance * 0.01 if min_distance is None else min_distance
    if near_end >= max_distance:
        raise click.UsageError("--min-distance must be less than --max-distance")

    camera = PovCamera(location=eye, look_at=aim, fov=fov)
    # The trailing plane is effectively at infinity: what it fails to hide is
    # sky, and sky is what must stay out of the near/far balance.
    grid = [*np.linspace(near_end, max_distance, probes), 5000.0]

    click.echo(f"Sweeping {scene.name} through {len(grid)} planes at {width}x{height}")
    try:
        curve = depth_sweep(
            scene,
            camera,
            grid,
            include_paths=include_paths,
            width=width,
            height=height,
            quality=quality,
            extra_args=pov_args,
        )
    except (RuntimeError, FileNotFoundError) as exc:
        raise click.ClickException(str(exc)) from exc

    if rows:
        click.echo()
        for distance, fraction in curve:
            click.echo(f"  {distance:10.2f}  {fraction * 100:6.2f}%")

    found = summarise_depth_sweep(curve)
    if found["far"] >= max_distance:
        # The sea case: a backdrop that never closes takes the 95% rule with
        # it.  Say so here rather than let the number be copied into a scene.
        click.echo(
            "\nnote: far landed on the end of the sweep, so the backdrop never "
            "closed.\n  Re-read it as the knee: --rows, fit the far tail's "
            "linear creep, subtract it,\n  and take 95% of what is left."
        )
    click.echo(f"\n  nearest geometry   {found['near']:.0f} units")
    click.echo(f"  structured far     {found['far']:.0f} units (95% of occludable content)")
    click.echo(f"  sky at infinity    {found['sky_fraction'] * 100:.1f}% of frame")
    click.echo(f"\n  -> near = {found['near']:.1f}, far = {found['far']:.1f}")
