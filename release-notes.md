# Release Notes — v0.5.0

> Released: 2026-08-16

Quiltwright had two rendering backends that never met: `lfd` sweeps a live
`pv.Plotter`, `povray` sweeps a `.pov` file on disk. **`quiltwright.povgen`
produces the second from the first**, so a scene composed in Python — or grown
by a geometry engine such as `kg_utils.viz3d` — can be ray-traced instead of
rasterised by VTK.

## What changed

### Analytic, not a mesh dump

By the time geometry reaches a `pv.Plotter` it is already tessellated:
`pv.Sphere` is a triangulated ball. Dumping those triangles into a `mesh2`
keeps VTK's facets *and* costs a great deal of text, re-parsed once per view —
48 times for a Portrait quilt. `povgen` re-emits *intent* instead: a limb is a
`sphere_sweep`, a leaf is a `sphere`.

Measured on a 3000-leaf organic tree (192k triangles, 159k vertices once
tessellated):

| Form | Size |
|---|---|
| `mesh2` equivalent | ~12.5 MB |
| analytic, oriented leaf instances | 839 KB |
| analytic, plain spheres | 508 KB |

**15× to 25× smaller**, with exact silhouettes at any zoom — which is most of
the reason to leave VTK in the first place. `mesh2` stays unimplemented, as
the fallback for geometry with no analytic description.

### Verified by dual render

`tests/test_povgen_parity.py` renders the same scene through both backends at
a matched camera and compares silhouettes: **IoU ≈ 0.95 with identical
bounding boxes.** The fixture is deliberately asymmetric in depth, because a
scene straddling the focal plane renders almost identically whether or not `z`
was flipped — the first draft passed cleanly with the handedness conversion
removed entirely.

### Four decisions made for the caller

- **Handedness.** Scenes are authored right-handed and `z` is negated on
  emission. Box corners are re-sorted, and `Instance` rotations are conjugated
  by the reflection.
- **No camera is emitted.** `render_pov_quilt` appends one off-axis camera per
  view and POV-Ray honours the last it parses.
- **Opacity becomes `transmit`, not `filter`.** `filter` would tint everything
  seen through the surface.
- **`SphereSweep` defaults to `linear_spline`,** which interpolates its control
  points rather than pulling away from already-smoothed geometry.

## Three fixes from the first consumer

Building an analytic tree in `gutenberg_kg` on top of this surfaced three
things worth having before anyone else does the same:

- **`lights_from_bounds` takes `up`.** *Above* was hard-coded to `+y` — right
  for a VTK scene, wrong for the `+z`-up world `kg_utils.viz3d` builds, where
  the key light landed below the ground and lit the subject from underneath.
  The default is unchanged, so no existing caller moves.

- **`povgen` no longer drags in VTK.** It is NumPy-only by design but could not
  be imported without the rendering stack: the package `__init__` re-exported
  `lfd` eagerly, and `povgen` imported `povray` for `PovCamera`. Both are
  deferred now — the public API is identical.

- **`PovCamera` holds POV-Ray coordinates, and now says so.** Three places
  implied otherwise. A consumer framed a camera in the scene's right-handed
  world and got a flawless render of empty space, with every assertion passing
  because they compared right-handed against right-handed.

`PovScene.bounds()` also now documents what instancing costs it, and how to
work around it.

## Upgrading

Nothing breaks. `lights_from_bounds` keeps its `+y`-up default; pass
`up=(0, 0, 1)` for a `+z`-up scene. The lazy `__init__` leaves every name in
`__all__` reachable exactly as before.
