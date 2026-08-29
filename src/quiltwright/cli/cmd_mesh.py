"""
CLI command: ``quiltwright mesh`` -- any 3D object file, straight to a quilt.

The general-purpose front door to the Cycles backend.  Hand it a mesh in any
format Blender can import -- glTF/GLB, OBJ, STL, PLY, USD, FBX, Alembic --
and it comes back a light-field quilt, with whatever textures and PBR
materials the file carries rendered as-is.

The other worked examples in ``scripts/`` *build* their geometry, so they
already know where the camera goes.  This command is handed a finished object
from somewhere else -- a modelling tool, a scanner, an asset library, an AI
generator such as Meshy -- whose scale, origin and up-axis after import are
all unknown, which makes a hand-picked ``CyclesCamera`` guesswork.
:func:`~quiltwright.cycles.mesh_bounds` measures the imported object through
the same importer the render uses, and
:func:`~quiltwright.cycles.frame_camera` puts the eye at the distance that
fills the view, aimed at the bounds centre -- which becomes the holographic
focal plane.  Both numbers are printed before the render starts, because
framing is the one thing a still cannot tell you after the fact.

Two things about an imported mesh are worth knowing before the first run:

*An unlit import renders black.*  A mesh file rarely carries lights, and a
path tracer obliges.  ``--lighting`` picks a rig -- ``studio`` floats the
object in the dark for a hero-object look, ``sky`` drops it into daylight, an
``.hdr``/``.exr`` path lights it from an environment map.

*A ``.blend`` is not a mesh file here.*  It carries its own camera, so it is
rendered by :func:`~quiltwright.cycles.render_cycles_quilt` with
``camera=None`` rather than auto-framed; this command rejects it and says so.

**Requires** a ``blender`` binary (macOS: ``brew install --cask blender``) or
``BLENDER_BINARY`` pointing at one.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import time
from pathlib import Path

import click

from quiltwright.cli.main import cli
from quiltwright.cycles import LIGHTING_RIGS, frame_camera, mesh_bounds, render_cycles_quilt
from quiltwright.quilt import QUILT_PRESETS, save_quilt


@cli.command("mesh")
@click.argument("source", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--device",
    type=click.Choice(sorted(QUILT_PRESETS)),
    default="portrait",
    show_default=True,
    help="Target display, which sets the quilt grid, size and view cone.",
)
@click.option(
    "--lighting",
    default="studio",
    show_default=True,
    help=f"Light rig for a mesh that carries none: one of {', '.join(LIGHTING_RIGS)}, "
    "or a path to an .hdr/.exr environment map.",
)
@click.option(
    "--fov",
    type=float,
    default=14.0,
    show_default=True,
    help="Vertical field of view in degrees. Object-centric, so narrow.",
)
@click.option(
    "--view-direction",
    type=float,
    nargs=3,
    metavar="X Y Z",
    default=(0.0, -1.0, 0.0),
    show_default=True,
    help="Direction from the object's centre to the eye (+z is up).",
)
@click.option(
    "--margin",
    type=float,
    default=1.2,
    show_default=True,
    help="Framing headroom beyond a tight fit; 1.0 is exactly tight.",
)
@click.option(
    "--samples", type=int, default=128, show_default=True, help="Cycles samples per pixel."
)
@click.option(
    "--view-transform",
    default="Standard",
    show_default=True,
    help='OCIO view transform ("Standard", "AgX", "Filmic", ...); see docs/cycles.md.',
)
@click.option(
    "--compute",
    type=click.Choice(["auto", "gpu", "cpu"]),
    default="auto",
    show_default=True,
    help="Cycles compute device. auto prefers a GPU, Metal first.",
)
@click.option("--preview", is_flag=True, help="Quarter-size quilt, for iterating on framing.")
@click.option(
    "--still",
    is_flag=True,
    help="One centre view as a flat image, at the device's aspect, instead of a quilt.",
)
@click.option(
    "--out",
    "out_stem",
    default=None,
    help="Output stem; defaults to the source name under renders/quilts/ "
    "(or gallery/ with --still).",
)
@click.option("--cast", "do_cast", is_flag=True, help="Send the result to Looking Glass Bridge.")
def mesh(
    source: Path,
    device: str,
    lighting: str,
    fov: float,
    view_direction: tuple[float, float, float],
    margin: float,
    samples: int,
    view_transform: str,
    compute: str,
    preview: bool,
    still: bool,
    out_stem: str | None,
    do_cast: bool,
) -> None:
    """Auto-frame the mesh file SOURCE and render it as a quilt.

    \b
    quiltwright mesh model.glb
    quiltwright mesh scan.fbx --lighting sky --still
    quiltwright mesh asset.obj --device 27-portrait --samples 256 --cast
    quiltwright mesh statue.ply --view-direction 0.5 -1 0.3 --fov 20
    """
    if source.suffix.lower() == ".blend":
        raise click.UsageError(
            "a .blend carries its own camera, so there is nothing to auto-frame here.\n"
            "Render it through quiltwright.cycles.render_cycles_quilt(scene, spec, None)."
        )

    spec = QUILT_PRESETS[device]
    if preview:
        spec = spec.scaled(0.25)
    if still:
        spec = spec.still()

    click.echo(f"mesh hologram <- {source.name}{' (preview)' if preview else ''}")

    try:
        lo, hi = mesh_bounds(source)
    except (RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"  bounds           {lo.round(3)} .. {hi.round(3)}  (size {(hi - lo).round(3)})")

    camera = frame_camera(lo, hi, fov=fov, view_direction=view_direction, margin=margin)
    click.echo(
        f"  camera           eye {tuple(round(c, 3) for c in camera.location)}, "
        f"focal {camera.focal_distance:.3f}, fov {fov:.0f} deg"
    )
    click.echo(
        f"  quilt            {spec.quilt_width}x{spec.quilt_height}, "
        f"tiles {spec.tile_width}x{spec.tile_height}, cone {spec.view_cone:.0f} deg"
    )
    click.echo(f"  lighting         {lighting}")

    # A rig name is one of the three; anything else is an HDRI path.
    rig: str | Path = lighting if lighting in LIGHTING_RIGS else Path(lighting)

    started = time.time()
    try:
        quilt = render_cycles_quilt(
            source,
            spec,
            camera,
            samples=samples,
            lighting=rig,
            device=compute,
            view_transform=view_transform,
            denoise=True,
        )
    except (RuntimeError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    elapsed = time.time() - started

    default_stem = f"gallery/{source.stem}" if still else f"renders/quilts/{source.stem}"
    stem = out_stem or default_stem
    out = save_quilt(quilt, f"{stem}-preview" if preview else stem, spec)
    click.echo(f"  wrote {out}  ({elapsed:.0f}s, {elapsed / spec.n_views:.1f}s/view)")

    if do_cast:
        from quiltwright.bridge import cast_quilt

        cast_quilt(out, spec)
        click.echo("  cast to Looking Glass Bridge")
