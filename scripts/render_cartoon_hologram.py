#!/usr/bin/env python
"""
Render a real PyMOL cartoon as a Looking Glass hologram -- two backends, one mesh.

The mesh-heavy companion to ``render_dna_helix_hologram.py``.  That script's
subject (161 analytic spheres and cylinders) is exactly the case where
POV-Ray's analytic intersectors win outright; a Richardson cartoon -- tens of
thousands of real triangles, the same shape ``quiltwright cartoon`` produces
-- is the case this package's Cycles backend exists for.

Both backends render **the same PyMOL triangulation**, not two independently
modelled scenes:

* **``--backend povray``** calls :func:`~quiltwright.pymol.cartoon_inc`,
  mounts the resulting ``.inc`` with an
  :class:`~quiltwright.povgen.Instance`, and lights it with
  :func:`~quiltwright.povgen.lights_from_bounds` -- the same pipeline
  ``quiltwright cartoon`` and the vitrine scripts use.
* **``--backend cycles``** calls :func:`~quiltwright.pymol.cartoon_obj`,
  the mesh twin added alongside it: identical PyMOL export, coalesced the
  same way, written as a plain OBJ instead of a POV-Ray include (geometry
  only -- no per-vertex colour, since OBJ carries none reliably), then
  path-traced with :func:`~quiltwright.cycles.render_cycles_quilt`.

**Requires PyMOL** (see ``quiltwright cartoon --check`` for install routes)
and either a ``povray`` or ``blender`` binary depending on ``--backend``.
Not exercised end to end in this development environment -- no PyMOL here --
so treat first real output with the usual scrutiny that comes with
unverified code, most of all the coordinate flip
:func:`~quiltwright.pymol.cartoon_obj` documents.

Usage::

    python scripts/render_cartoon_hologram.py molecules/2omf.cif.gz --still
    python scripts/render_cartoon_hologram.py molecules/2omf.cif.gz --backend povray --still
    python scripts/render_cartoon_hologram.py molecules/1gfl.pdb --rep surface --backend cycles --still
    python scripts/render_cartoon_hologram.py 2omf.cif.gz --device portrait --cast

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import math
import tempfile
import time
from pathlib import Path

import numpy as np

from quiltwright.lfd import QUILT_PRESETS, QuiltSpec, save_quilt
from quiltwright.pymol import REPRESENTATIONS

#: A fixed 3/4-elevated viewing direction, in the right-handed convention
#: this script frames both cameras from.  Arbitrary but consistent -- the
#: same direction feeds both backends (see the module docstring on how the
#: POV-Ray camera reaches the same view of the mirror-image geometry
#: cartoon_inc() mounts).
VIEW_DIRECTION = np.array([0.55, -1.0, 0.4])
VIEW_DIRECTION = VIEW_DIRECTION / np.linalg.norm(VIEW_DIRECTION)

#: Margin beyond the tight framing distance, so the enclosing sphere does not
#: touch the frame edges.
FRAME_MARGIN = 1.2


def framing_distance(radius: float, fov: float) -> float:
    """Distance at which a sphere of *radius* exactly fills a *fov*-degree cone.

    ``sin(fov/2) = radius / distance`` is exact for a sphere, unlike the
    small-angle tangent approximation -- worth it here since object-centric
    FOVs (~14-30 deg) are not small angles.

    :param radius: Enclosing radius of the subject.
    :param fov: Vertical field of view in degrees.
    :return: Camera distance, with :data:`FRAME_MARGIN` applied.
    """
    return radius / math.sin(math.radians(fov) / 2.0) * FRAME_MARGIN


def render_povray(
    source: Path,
    work: Path,
    spec: QuiltSpec,
    fov: float,
    rep: str,
    color: str,
    finish: str,
    selection: str,
    assembly: str,
    surface_quality: int | None,
    antialias: float,
):
    """Export via :func:`~quiltwright.pymol.cartoon_inc` and ray-trace it.

    :return: The rendered quilt.
    """
    from quiltwright.povgen import Instance, PovScene, lights_from_bounds, to_pov
    from quiltwright.povray import PovCamera, render_pov_quilt
    from quiltwright.pymol import cartoon_inc

    inc_path = work / "cartoon.inc"
    result = cartoon_inc(
        source,
        inc_path,
        rep=rep,
        color=color,
        finish=finish,
        selection=selection,
        assembly=assembly,
        surface_quality=surface_quality,
    )
    print(
        f"  pymol ({result.backend}): {result.vertices} vertices, "
        f"{result.faces} faces, radius {result.enclosing_radius:.1f} A"
    )

    radius = result.enclosing_radius
    scene = PovScene(background="#1a1a1e", includes=[inc_path.name])
    scene.add(Instance(name=result.identifier))
    for light in lights_from_bounds(
        (-radius, -radius, -radius),
        (radius, radius, radius),
        up=(0.0, 0.0, 1.0),
        key_side=tuple(VIEW_DIRECTION),
        fill=True,
        rim=True,
    ):
        scene.add_light(light)

    scene_path = work / "wrapper.pov"
    scene.write(scene_path)

    distance = framing_distance(radius, fov)
    eye = tuple((VIEW_DIRECTION * distance).tolist())
    camera = PovCamera(
        location=to_pov(eye), look_at=to_pov((0.0, 0.0, 0.0)), sky=to_pov((0.0, 0.0, 1.0)), fov=fov
    )
    return render_pov_quilt(scene_path, spec, camera, antialias=antialias)


def render_cycles(
    source: Path,
    work: Path,
    spec: QuiltSpec,
    fov: float,
    rep: str,
    color: str,
    roughness: float,
    selection: str,
    assembly: str,
    surface_quality: int | None,
    lighting: str,
    samples: int,
):
    """Export via :func:`~quiltwright.pymol.cartoon_obj` and path-trace it.

    :return: The rendered quilt.
    """
    from quiltwright.cycles import CyclesCamera, render_cycles_quilt
    from quiltwright.pymol import cartoon_obj

    obj_path = work / "cartoon.obj"
    result = cartoon_obj(
        source,
        obj_path,
        rep=rep,
        color=color,
        roughness=roughness,
        selection=selection,
        assembly=assembly,
        surface_quality=surface_quality,
    )
    print(
        f"  pymol ({result.backend}): {result.vertices} vertices, "
        f"{result.faces} faces, radius {result.enclosing_radius:.1f} A"
    )

    distance = framing_distance(result.enclosing_radius, fov)
    eye = tuple((VIEW_DIRECTION * distance).tolist())
    camera = CyclesCamera(location=eye, look_at=(0.0, 0.0, 0.0), up=(0.0, 0.0, 1.0), fov=fov)
    return render_cycles_quilt(
        obj_path,
        spec,
        camera,
        lighting=lighting,
        samples=samples,
        denoise=True,
        view_transform="Standard",
    )


def main() -> int:
    """Render (and optionally cast) the cartoon hologram.

    :return: Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="structure PyMOL can load -- .pdb, .cif, .cif.gz")
    parser.add_argument(
        "--backend", default="cycles", choices=("cycles", "povray"), help="which ray tracer"
    )
    parser.add_argument(
        "--rep", default="cartoon", choices=REPRESENTATIONS, help="PyMOL representation"
    )
    parser.add_argument(
        "--color",
        default="ss",
        help='"ss" for helix/strand/loop (default), "spectrum" for a rainbow '
        "ramp (POV-Ray only -- OBJ has no reasonable way to carry one colour "
        "per residue), or any flat PyMOL colour name / #rrggbb",
    )
    parser.add_argument(
        "--roughness",
        type=float,
        default=0.3,
        help="Cycles only: material roughness for --color, lower is glossier",
    )
    parser.add_argument(
        "--finish",
        default="normal",
        choices=("normal", "metallic"),
        help="POV-Ray only: finish applied to each baked colour",
    )
    parser.add_argument("--selection", default="polymer", help="PyMOL selection")
    parser.add_argument(
        "--assembly", default="1", help='biological assembly; "" for asymmetric unit'
    )
    parser.add_argument(
        "--surface-quality", type=int, default=None, help="PyMOL surface_quality (--rep surface)"
    )
    parser.add_argument(
        "--lighting",
        default="studio",
        choices=("soft", "studio", "sky"),
        help="Cycles only; see docs/cycles.md",
    )
    parser.add_argument(
        "--device", default="portrait", choices=sorted(QUILT_PRESETS), help="target display"
    )
    parser.add_argument("--fov", type=float, default=20.0, help="vertical field of view, degrees")
    parser.add_argument("--samples", type=int, default=128, help="Cycles only: samples per pixel")
    parser.add_argument("--antialias", type=float, default=0.1, help="POV-Ray only: +A threshold")
    parser.add_argument("--preview", action="store_true", help="quarter-size quilt, for iterating")
    parser.add_argument(
        "--still",
        action="store_true",
        help="single centre-view render instead of a quilt, saved to gallery/",
    )
    parser.add_argument(
        "--out", default=None, help="output stem; defaults to renders/quilts/cartoon_<backend>"
    )
    parser.add_argument("--cast", action="store_true", help="send to Looking Glass Bridge")
    args = parser.parse_args()

    source = Path(args.source)
    spec: QuiltSpec = QUILT_PRESETS[args.device]
    if args.preview:
        spec = spec.scaled(0.25)
    if args.still:
        spec = spec.still()

    print(f"cartoon hologram -> {args.backend}{' (preview)' if args.preview else ''}")
    print(
        f"  quilt            {spec.quilt_width}x{spec.quilt_height}, "
        f"tiles {spec.tile_width}x{spec.tile_height}, cone {spec.view_cone:.0f} deg"
    )

    started = time.time()
    with tempfile.TemporaryDirectory(prefix="cartoon_hologram_") as tmp:
        work = Path(tmp)
        if args.backend == "cycles":
            print(f"  lighting         {args.lighting}")
            quilt = render_cycles(
                source,
                work,
                spec,
                args.fov,
                args.rep,
                args.color,
                args.roughness,
                args.selection,
                args.assembly,
                args.surface_quality,
                args.lighting,
                args.samples,
            )
        else:
            quilt = render_povray(
                source,
                work,
                spec,
                args.fov,
                args.rep,
                args.color,
                args.finish,
                args.selection,
                args.assembly,
                args.surface_quality,
                args.antialias,
            )
    elapsed = time.time() - started

    stem = args.out or f"renders/quilts/cartoon_{args.backend}"
    if args.still:
        stem = args.out or f"gallery/cartoon_{args.backend}"
    out = save_quilt(quilt, f"{stem}-preview" if args.preview else stem, spec)
    print(f"  wrote {out}  ({elapsed:.0f}s, {elapsed / spec.n_views:.1f}s/view)")

    if args.cast:
        from quiltwright.lfd import cast_quilt

        cast_quilt(out, spec)
        print("  cast to Looking Glass Bridge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
