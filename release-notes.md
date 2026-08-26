# Release Notes -- v0.9.0

> Released: 2026-08-26

Quiltwright had two backends that could never be honestly compared -- POV-Ray's
analytic primitives and PyVista's rasteriser render different geometry by
construction. This release adds a third: Blender Cycles, with hardware ray
tracing where the GPU offers it, including Apple Silicon's Metal ray-tracing
cores. Alongside it come two worked examples built specifically to put
backends head to head on identical geometry, and running the more demanding of
the two against a real PyMOL install and real molecules caught three
pre-existing bugs along the way.

## What changed

**A third rendering backend: Blender Cycles.** `quiltwright.cycles` renders
`.blend` files and common mesh formats (glTF/GLB, OBJ, STL, PLY, USD, FBX,
Alembic) into quilts and view sweeps, mirroring the POV-Ray backend's own API
-- `CyclesCamera` is the right-handed Z-up twin of `PovCamera`, so
`format_depth_budget` and `Clearance` apply unchanged. On Apple Silicon (M3+),
Cycles' Metal device runs ray/triangle intersection on the GPU's ray-tracing
cores, with OptiX/CUDA/HIP/oneAPI tried in turn elsewhere and CPU as the
fallback. Getting the off-axis shear right meant mirroring Blender's own
`BKE_camera_params_compute_viewplane` sensor-fit rules exactly rather than
trusting the documented behaviour, because AUTO sensor fit sizes off
`sensor_width` even when it resolves vertically against a portrait frame --
every branch is guarded by end-to-end tests that render emissive markers at
known depths and assert the focal plane stays put across a sweep.

**A PyVista bridge, so the two backends can render the same scene.**
`render_cycles_quilt_from_plotter()` takes the same composed `pv.Plotter`
that `render_quilt()` already accepts and produces the same quilt, but
path-traced by Cycles instead of rasterised by VTK -- the plotter is read,
never mutated or rendered, so it runs on headless machines with no GL stack
at all. The coordinate hop underneath (`export_plotter_gltf()`'s
`rotate_scene=False`, plus Blender's own fixed Y-up-to-Z-up import remap) was
verified against actual imported geometry rather than assumed, since the
rotation glTF exporters bake has drifted across PyVista versions before.

**Lighting rigs, for imports that arrive with no lights of their own.** A
`lighting` parameter on `render_cycles_quilt()` / `render_cycles_views()`
adds `"soft"` (a neutral world plus a sun), `"studio"` (a camera-relative
three-point rig over a near-black world), `"sky"` (Blender's physical Nishita
sky), or an HDRI path -- scaled by focal distance so apparent brightness holds
regardless of scene scale. The sky rig's sun azimuth was set empirically:
four candidate rotations were rendered and compared side by side rather than
reasoned about from the physics.

**Two worked examples built to make the comparison fair.**
`scripts/render_dna_helix_hologram.py` composes a B-DNA double helix once as
a `pv.Plotter` and renders it through both backends off the same camera and
lighting. `scripts/render_cartoon_hologram.py` goes further, sharing the
*exact* PyMOL triangulation between backends via `cartoon_obj()`, the mesh
twin of the existing `cartoon_inc()`. Running the cartoon comparison against a
real PyMOL install and real structures (`molecules/` now carries
`2omf.cif.gz` and `1gfl.pdb` as fetchable examples) is what surfaced two of
the three fixes below -- the coordinate-flip math `cartoon_obj()` originally
shipped as algebraically-derived-but-unverified turned out to be correct, but
the geometry still arrived rotated, for an unrelated reason.

**Secondary-structure colouring and material control for the cartoon
comparison.** `color="ss"` on both `cartoon_inc()` and `cartoon_obj()` runs
`cmd.dss()` and colours helix, strand, and loop with three flat colours; for
the OBJ path, which has no way to carry a rainbow ramp, the colours are read
back out of PyMOL's own texture list and written as a companion `.mtl` with
only the materials a given structure actually uses. A `roughness` parameter
and a `finish="metallic"` option (tinted per baked colour rather than one
shared brass) round out material parity with POV-Ray's finish system; a
`"glass"` finish was tried and dropped, since a cartoon's 20-plus crossing
ribbons per view ray compound tint multiplicatively into black well before
added transparency could compensate.

**Documentation caught up to both new backends.** A Prerequisites table in
the README, and matching Blender/PyMOL sections in `docs/install.md`, cover
install requirements for backends that had grown core to the package with
zero coverage in either doc. A "From a Cycles scene" quick-start section
fills the one place -- Quick start itself -- where a reader working top to
bottom would never learn that `render_cycles_quilt` or
`render_cycles_quilt_from_plotter()` existed at all.

## Fixed

**Every POV-Ray colour in the package rendered 2-3x too bright.** No scene
ever declared `assumed_gamma`, so POV-Ray 3.7 treated colours as
already-linear light and gamma-encoded them again on output. `PovScene` now
declares `assumed_gamma srgb`, verified by round-tripping a known colour back
out of a rendered pixel.

**The Cycles backend's OBJ import turned meshes 90 degrees against their own
camera.** Blender's `wm.obj_import` remaps Wavefront's Y-up convention onto
its own Z-up world by default; every OBJ this package writes is already
Z-up, so the remap turned it sideways. Fixed by importing with an explicit
identity transform (`forward_axis="Y", up_axis="Z"`).

**A failed PyMOL export surfaced as a bare `FileNotFoundError`, frames away
from the real cause.** PyMOL's batch mode logs a bad load or selection and
keeps going rather than raising, so a bad path or selection used to exit `0`
having written nothing. Export now checks that PyMOL actually wrote its
expected output and raises with PyMOL's own traceback attached when it
didn't.

**Run reports recorded a startup warning where the POV-Ray build should
be.** The version probe read the first line of `povray --version`, which on
a machine with no user config file is a harmless "cannot open the user
configuration file" warning rather than the banner behind it. The banner is
now matched by its prefix instead of its position.

## Upgrading

Nothing to migrate. `pip install -U quiltwright` gets the new backend; it
needs a `blender` binary on `PATH` (or `QW_BPY_PYTHON` pointing at a
`bpy`-wheel interpreter), the same way the POV-Ray backend needs `povray`.
See `docs/cycles.md` for the lighting rig reference and both worked examples.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
