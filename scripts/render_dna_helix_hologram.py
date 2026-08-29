#!/usr/bin/env python
"""
Render a B-DNA double helix as a Looking Glass hologram -- two backends, one scene.

A worked side-by-side for ``docs/cycles.md`` and ``docs/povray.md``: the same
helix geometry (backbones as sphere glyphs, base-pair rungs coloured A/T/G/C,
one strand rotated for the minor-groove asymmetry a real helix has) feeds
either renderer from one ``pv.Plotter``, so the comparison is honest -- same
camera, same colours, same subject.

* **``--backend cycles``** (default) exports the plotter to glTF and
  path-traces it with :func:`~quiltwright.cycles.render_cycles_quilt_from_plotter`
  -- GPU ray tracing where the hardware offers it (Metal on Apple Silicon).
  ``--lighting`` picks the rig; see ``docs/cycles.md``.
* **``--backend povray``** re-expresses the same points as analytic POV-Ray
  primitives (:class:`~quiltwright.povgen.Sphere` /
  :class:`~quiltwright.povgen.Cylinder`) and ray-traces with
  :func:`~quiltwright.povray.render_pov_quilt`.  The camera comes from
  :func:`~quiltwright.povgen.pov_camera_from_plotter`, so both backends frame
  the subject identically, and the light rig from
  :func:`~quiltwright.povgen.lights_from_bounds`.

On a molecule this size (161 primitives, no mesh data), POV-Ray's analytic
intersectors are hard to beat -- seconds, not minutes, on a single core. The
Cycles backend earns its keep on mesh-heavy scenes (Richardson cartoons,
scanned surfaces, anything with real triangle counts) and on Apple Silicon,
where the same call runs on the GPU's ray-tracing cores instead.

Usage::

    python scripts/render_dna_helix_hologram.py --still
    python scripts/render_dna_helix_hologram.py --backend cycles --lighting studio --still
    python scripts/render_dna_helix_hologram.py --backend povray --still
    python scripts/render_dna_helix_hologram.py --device portrait --preview
    python scripts/render_dna_helix_hologram.py --device portrait --cast

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from quiltwright.lfd import QUILT_PRESETS, QuiltSpec, save_quilt

# --- Geometry ----------------------------------------------------------------
# Right-handed, +z up -- the convention both quiltwright.povgen and pyvista
# share, so the same arrays feed either backend with no coordinate juggling.

TURNS = 2.5
POINTS_PER_TURN = 24
RADIUS = 1.0
RISE_PER_TURN = 1.7
MINOR_GROOVE = 2.2  # radians: strand B's phase offset from strand A
BACKBONE_RADIUS = 0.17
RUNG_RADIUS = 0.075
SEED = 1953  # the year the structure was published

BASE_COLOURS = {"A": "#2e9e46", "T": "#f2b705", "G": "#1c6fd4", "C": "#d43a2f"}
PAIR = {"A": "T", "T": "A", "G": "C", "C": "G"}


def helix_strands() -> tuple[np.ndarray, np.ndarray]:
    """The two backbone point arrays, each ``(n, 3)``."""
    n = int(TURNS * POINTS_PER_TURN)
    t = np.linspace(0.0, TURNS * 2.0 * np.pi, n)
    z = t / (2.0 * np.pi) * RISE_PER_TURN
    strand_a = np.column_stack([RADIUS * np.cos(t), RADIUS * np.sin(t), z])
    strand_b = np.column_stack(
        [RADIUS * np.cos(t + MINOR_GROOVE), RADIUS * np.sin(t + MINOR_GROOVE), z]
    )
    return strand_a, strand_b


def base_pairs(strand_a: np.ndarray, strand_b: np.ndarray, *, stride: int = 3):
    """Yield ``(start, end, base)`` half-rungs, both halves of every pair.

    Every third rung is drawn (``stride``) so individual base pairs read
    clearly rather than fusing into a solid ladder; each rung is split at the
    helix axis into two half-cylinders, one per paired base, coloured
    independently.
    """
    rng = np.random.default_rng(SEED)
    for i in range(0, len(strand_a), stride):
        a, b = strand_a[i], strand_b[i]
        mid = (a + b) / 2.0
        base = rng.choice(list(BASE_COLOURS))
        yield a, mid, base
        yield mid, b, PAIR[base]


def build_plotter():
    """Compose the helix as a PyVista plotter: geometry and camera, no lights.

    Shared by both backends -- the Cycles path renders this plotter directly
    (via glTF), the POV-Ray path only borrows its camera
    (:func:`~quiltwright.povgen.pov_camera_from_plotter`) and rebuilds the
    same points as analytic primitives.
    """
    import pyvista as pv

    strand_a, strand_b = helix_strands()

    def strand_mesh(points):
        return pv.PolyData(points).glyph(
            geom=pv.Sphere(radius=BACKBONE_RADIUS, theta_resolution=24, phi_resolution=24),
            scale=False,
            orient=False,
        )

    rungs = {k: [] for k in BASE_COLOURS}
    for start, end, base in base_pairs(strand_a, strand_b):
        rungs[base].append(
            pv.Cylinder(
                center=(start + end) / 2.0,
                direction=end - start,
                radius=RUNG_RADIUS,
                height=float(np.linalg.norm(end - start)),
            )
        )

    p = pv.Plotter(off_screen=True)
    p.add_mesh(strand_mesh(strand_a), color="#f4f0e6")
    p.add_mesh(strand_mesh(strand_b), color="#f4f0e6")
    for base, cyls in rungs.items():
        if cyls:
            p.add_mesh(pv.merge(cyls), color=BASE_COLOURS[base])
    p.add_mesh(
        pv.Plane(center=(0, 0, -BACKBONE_RADIUS), direction=(0, 0, 1), i_size=40, j_size=40),
        color="#565a63",
    )

    height = float(strand_a[-1, 2])
    p.camera_position = [(5.6, -7.8, 2.1), (0.0, 0.0, height / 2.0), (0.0, 0.0, 1.0)]
    return p


def build_pov_scene(path: Path):
    """The same helix as analytic POV-Ray primitives, written to *path*.

    Mirrors :func:`build_plotter`'s geometry exactly (same points, same
    stride, same seed) so the two backends differ only in how they ray-trace,
    not in what they ray-trace. The light rig comes from
    :func:`~quiltwright.povgen.lights_from_bounds`, sized to the helix's own
    bounds -- the floor slab is deliberately excluded from that measurement,
    or the rig would place lights sized to the 40-unit floor instead of the
    ~4-unit helix.

    :return: The written scene path.
    """
    from quiltwright.povgen import (
        Cylinder,
        Finish,
        PovScene,
        Sphere,
        Texture,
        ground_slab,
        lights_from_bounds,
    )

    strand_a, strand_b = helix_strands()
    matte = Finish(ambient=0.02, diffuse=0.9, phong=0.15, phong_size=40)
    ivory = Texture(color="#f4f0e6", finish=matte)
    base_tex = {k: Texture(color=c, finish=matte) for k, c in BASE_COLOURS.items()}
    floor_tex = Texture(color="#565a63", finish=Finish(ambient=0.02, diffuse=0.9))

    lo = np.minimum(strand_a.min(axis=0), strand_b.min(axis=0)) - BACKBONE_RADIUS
    hi = np.maximum(strand_a.max(axis=0), strand_b.max(axis=0)) + BACKBONE_RADIUS

    scene = PovScene(background="#1a1a1e")
    for strand in (strand_a, strand_b):
        scene.add([Sphere(p, BACKBONE_RADIUS, texture=ivory) for p in strand])
    for start, end, base in base_pairs(strand_a, strand_b):
        scene.add(Cylinder(start, end, RUNG_RADIUS, texture=base_tex[base]))
    scene.add(ground_slab(lo, hi, up=(0.0, 0.0, 1.0), size=15.0, texture=floor_tex))

    for light in lights_from_bounds(
        lo, hi, up=(0.0, 0.0, 1.0), key_side=(1.0, -1.0, 0.3), fill=True, rim=True
    ):
        scene.add_light(light)

    return scene.write(path)


def main() -> int:
    """Render (and optionally cast) the DNA helix hologram.

    :return: Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--backend", default="cycles", choices=("cycles", "povray"), help="which ray tracer"
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
    parser.add_argument("--fov", type=float, default=32.0, help="vertical field of view, degrees")
    parser.add_argument("--samples", type=int, default=128, help="Cycles only: samples per pixel")
    parser.add_argument("--preview", action="store_true", help="quarter-size quilt, for iterating")
    parser.add_argument(
        "--still",
        action="store_true",
        help="single centre-view render instead of a quilt, saved to gallery/",
    )
    parser.add_argument(
        "--out", default=None, help="output stem; defaults to renders/quilts/dna_helix_<backend>"
    )
    parser.add_argument("--cast", action="store_true", help="send to Looking Glass Bridge")
    args = parser.parse_args()

    spec: QuiltSpec = QUILT_PRESETS[args.device]
    if args.preview:
        spec = spec.scaled(0.25)
    if args.still:
        spec = spec.still()

    print(f"dna helix hologram -> {args.backend}{' (preview)' if args.preview else ''}")
    print(
        f"  quilt            {spec.quilt_width}x{spec.quilt_height}, "
        f"tiles {spec.tile_width}x{spec.tile_height}, cone {spec.view_cone:.0f} deg"
    )

    plotter = build_plotter()
    started = time.time()

    if args.backend == "cycles":
        from quiltwright.cycles import render_cycles_quilt_from_plotter

        print(f"  lighting         {args.lighting}")
        quilt = render_cycles_quilt_from_plotter(
            plotter,
            spec,
            fov=args.fov,
            lighting=args.lighting,
            samples=args.samples,
            denoise=True,
        )
    else:
        import tempfile

        from quiltwright.povgen import pov_camera_from_plotter
        from quiltwright.povray import render_pov_quilt

        camera = pov_camera_from_plotter(plotter, fov=args.fov)
        with tempfile.TemporaryDirectory(prefix="dna_helix_pov_") as tmp:
            scene_path = build_pov_scene(Path(tmp) / "helix.pov")
            quilt = render_pov_quilt(scene_path, spec, camera, antialias=0.1)
    plotter.close()

    elapsed = time.time() - started
    stem = args.out or f"renders/quilts/dna_helix_{args.backend}"
    if args.still:
        stem = args.out or f"gallery/dna_helix_{args.backend}"
    out = save_quilt(quilt, f"{stem}-preview" if args.preview else stem, spec)
    print(f"  wrote {out}  ({elapsed:.0f}s, {elapsed / spec.n_views:.1f}s/view)")

    if args.cast:
        from quiltwright.lfd import cast_quilt

        cast_quilt(out, spec)
        print("  cast to Looking Glass Bridge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
