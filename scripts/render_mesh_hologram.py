#!/usr/bin/env python
"""
Render any 3D object file as a Looking Glass hologram -- mesh in, quilt out.

The general-purpose front door to the Cycles backend: hand it a mesh file in
any format Blender can import -- glTF/GLB, OBJ, STL, PLY, USD, FBX, Alembic --
and it comes back a light-field quilt, with the textures and PBR materials the
file carries rendered as-is.  Where the other worked examples build their
geometry (a DNA helix, a PyMOL cartoon) and so already know where the camera
goes, this one is handed a finished object from somewhere else -- a modelling
tool, a scanner, an asset library, an AI generator such as Meshy -- and has to
work out the framing itself.

That framing is the whole point.  A ``.blend`` can carry its own camera; an
imported mesh cannot, and its scale, origin and up-axis after import are all
unknown, so a hand-picked ``CyclesCamera`` is guesswork.
:func:`~quiltwright.cycles.autoframe_camera` removes the guess: it imports the
mesh once to measure its world-space bounds, then places a front-on camera at
the distance that fills the view, aimed at the bounds centre -- which becomes
the holographic focal plane.  Everything after that is the ordinary Cycles
sweep.

An imported mesh usually arrives with no lights of its own, and a path tracer
renders an unlit scene *black*, so ``--lighting`` picks a rig (see
``docs/cycles.md``); ``studio`` floats the object in the dark for a hero-object
look, ``sky`` drops it into daylight, an ``.hdr``/``.exr`` path lights it from
an environment map.

**Requires** a ``blender`` binary (``brew install --cask blender``) or
``BLENDER_BINARY`` pointing at one, and pillow.

Usage::

    python scripts/render_mesh_hologram.py model.glb
    python scripts/render_mesh_hologram.py scan.fbx --lighting sky --still
    python scripts/render_mesh_hologram.py asset.obj --device 27-portrait --samples 256 --cast
    python scripts/render_mesh_hologram.py statue.ply --view-direction 0.5 -1 0.3 --fov 20

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from quiltwright.cycles import frame_camera, mesh_bounds, render_cycles_quilt
from quiltwright.lfd import QUILT_PRESETS, QuiltSpec, save_quilt


def main() -> int:
    """Auto-frame a mesh file and render (optionally cast) its hologram.

    :return: Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="mesh file: .glb/.gltf, .obj, .stl, .ply, .usd*, .fbx, .abc")
    parser.add_argument(
        "--device", default="portrait", choices=sorted(QUILT_PRESETS), help="target display"
    )
    parser.add_argument(
        "--lighting",
        default="studio",
        help='"studio" (default), "soft", "sky", or a path to an .hdr/.exr environment map',
    )
    parser.add_argument("--fov", type=float, default=14.0, help="vertical field of view, degrees")
    parser.add_argument(
        "--view-direction",
        type=float,
        nargs=3,
        metavar=("X", "Y", "Z"),
        default=(0.0, -1.0, 0.0),
        help="direction from the object centre to the eye (default: front, 0 -1 0)",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=1.2,
        help="framing headroom beyond a tight fit (1.0 is exactly tight)",
    )
    parser.add_argument("--samples", type=int, default=128, help="Cycles samples per pixel")
    parser.add_argument(
        "--view-transform",
        default="Standard",
        help='OCIO view transform ("Standard", "AgX", "Filmic", ...); see docs/cycles.md',
    )
    parser.add_argument(
        "--device-compute",
        dest="compute",
        default="auto",
        choices=("auto", "gpu", "cpu"),
        help="Cycles compute device (auto prefers GPU, Metal first)",
    )
    parser.add_argument("--preview", action="store_true", help="quarter-size quilt, for iterating")
    parser.add_argument(
        "--still",
        action="store_true",
        help="single centre-view render instead of a quilt, saved to gallery/",
    )
    parser.add_argument("--out", default=None, help="output stem; defaults from the source name")
    parser.add_argument("--cast", action="store_true", help="send to Looking Glass Bridge")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_file():
        parser.error(f"source not found: {source}")

    spec: QuiltSpec = QUILT_PRESETS[args.device]
    if args.preview:
        spec = spec.scaled(0.25)
    if args.still:
        spec = QuiltSpec(columns=1, rows=1, quilt_width=880, quilt_height=1100, aspect=0.8)

    print(f"mesh hologram <- {source.name}{' (preview)' if args.preview else ''}")

    lo, hi = mesh_bounds(source)
    size = hi - lo
    print(f"  bounds           {lo.round(3)} .. {hi.round(3)}  (size {size.round(3)})")
    camera = frame_camera(
        lo, hi, fov=args.fov, view_direction=tuple(args.view_direction), margin=args.margin
    )
    print(
        f"  camera           eye {tuple(round(c, 3) for c in camera.location)}, "
        f"focal {camera.focal_distance:.3f}, fov {args.fov:.0f} deg"
    )
    print(
        f"  quilt            {spec.quilt_width}x{spec.quilt_height}, "
        f"tiles {spec.tile_width}x{spec.tile_height}, cone {spec.view_cone:.0f} deg"
    )
    print(f"  lighting         {args.lighting}")

    # "studio"/"soft"/"sky" are rig names; anything else is an HDRI path.
    lighting: str | Path = args.lighting
    if args.lighting not in ("studio", "soft", "sky"):
        lighting = Path(args.lighting)

    started = time.time()
    quilt = render_cycles_quilt(
        source,
        spec,
        camera,
        samples=args.samples,
        lighting=lighting,
        device=args.compute,
        view_transform=args.view_transform,
        denoise=True,
    )
    elapsed = time.time() - started

    default_stem = f"gallery/{source.stem}" if args.still else f"renders/quilts/{source.stem}"
    stem = args.out or default_stem
    out = save_quilt(quilt, f"{stem}-preview" if args.preview else stem, spec)
    print(f"  wrote {out}  ({elapsed:.0f}s, {elapsed / spec.n_views:.1f}s/view)")

    if args.cast:
        from quiltwright.lfd import cast_quilt

        cast_quilt(out, spec)
        print("  cast to Looking Glass Bridge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
