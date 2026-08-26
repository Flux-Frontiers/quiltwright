# Blender Cycles Holographic Output

**Module**: `quiltwright.cycles`
**Source**: `src/quiltwright/cycles.py`

> *POV-Ray will never see a ray-tracing core. Meshes don't have to care.*

Renders Blender scenes and mesh files as Looking Glass quilts with Cycles,
Blender's production path tracer. Companion to [povray.md](povray.md), which
covers the POV-Ray backend the same way; everything downstream of quilt
assembly -- filenames, casting, playback -- is shared with the rest of
quiltwright.

---

## Concept

The POV-Ray backend exists for scenes that *are* POV-Ray: CSG, isosurfaces,
thirty-year-old archives. Those stay where they are. But most of what a
scientific pipeline produces today is **meshes** -- PyVista/VTK geometry,
glTF exports, USD, molecular surfaces -- and meshes are exactly what
hardware ray tracing eats.

That is what this backend buys:

- **Apple's ray-tracing engine, where it exists.** Cycles' Metal device runs
  ray/triangle intersection on the dedicated ray-tracing hardware of M3-class
  and later Apple GPUs (earlier Apple Silicon runs the same Metal path in GPU
  software). The equivalent applies elsewhere: OptiX on NVIDIA RT cores, HIP
  on AMD, oneAPI on Intel. Device selection is automatic, in that order, with
  CPU as the always-works fallback.
- **One process per quilt, not one parse per view.** POV-Ray re-reads the
  scene and rebuilds its structures for every view -- 48 times for a Portrait
  quilt. Here the scene loads once, Cycles builds its BVH once
  (`use_persistent_data`), and only the camera moves between views. For
  mesh-heavy scenes the per-view cost collapses to actual ray tracing.
- **Production shading for free.** Denoising, area lights, HDRI worlds,
  subsurface scattering -- whatever the scene or its materials ask for,
  Cycles already does.

The off-axis geometry is identical to every other quiltwright backend: the
eye translates along the camera's right vector and the frustum shears back so
the look-at point stays pinned -- here via Blender's *camera shift*, with

```text
shift_x = -offset / (2 * Z * tan(fov/2) * aspect)
```

which is the same quantity VTK's `SetWindowCenter` receives in the PyVista
backend, in fractions of the frame width instead of half-widths. The
end-to-end tests render emissive markers at known depths and assert the
focal-plane marker does not move across the sweep -- the property that
distinguishes a correct off-axis shear from toe-in rotation.

## Mechanism

`render_cycles_quilt()` writes a **job description** (JSON) and a **driver
script**, then runs one headless Blender:

```text
blender --background --factory-startup --python driver.py -- job.json
```

The driver -- generated from `quiltwright/cycles.py`, dependency-free beyond
`bpy` -- loads the scene, configures Cycles, builds the camera, and renders
`view000.png ... viewNNN.png` in a single process. The parent streams
progress from `QW_`-prefixed stdout lines and tiles the frames with the same
`assemble_quilt()` every backend feeds. `render_cycles_views()` is the sweep
variant for hologram printers and lenticular interlacers, matching
`render_pov_views()`.

## Scene sources

| Input | Route |
|---|---|
| `.blend` | Opened natively: its materials, lights, world and (optionally) camera are used as-is |
| `.gltf` / `.glb`, `.obj`, `.stl`, `.ply`, `.usd*`, `.fbx`, `.abc` | Imported into an empty scene |

Imported meshes usually arrive without lights, and an unlit scene renders
*black* in a path tracer, so by default an import with no lights of its own
gets a neutral world plus a sun (`ensure_light=False` to opt out). A
`.blend` is never touched.

### PyVista, directly

A composed `pv.Plotter` needs no manual export step:

```python
quilt = render_cycles_quilt_from_plotter(plotter, spec)   # render_quilt, ray-traced
```

is the hardware-ray-traced sibling of `render_quilt()` -- same plotter in,
same quilt out, same FOV/dolly convention. Behind it,
`export_plotter_gltf()` writes the scene to glTF and
`cycles_camera_from_plotter()` translates the plotter's camera; both are
public for when you want the intermediate pieces (pass `gltf=` to keep the
exported scene for reuse).

The hop between VTK's world and Blender's is one deliberate contract: the
scene is exported **un-rotated** (`rotate_scene=False`, since the rotation
VTK otherwise bakes for glTF's Y-up convention has varied across versions),
and Blender's importer then applies its fixed Y-up-to-Z-up rotation, landing
a VTK point `(x, y, z)` at `(x, -z, y)`. The camera goes through the same
rotation, so scene and camera agree and the render matches what the plotter
framed -- an invariant the end-to-end tests pin with depth markers, because
a wrong hop renders perfectly plausible frames whose *sweep* is tilted.

Scalar-mapped colours survive: VTK bakes them into a glTF base-colour
texture that Blender wires into the material on import. Lights do not
exist in the export, which is what `ensure_light` is for. Notably, the
export works with no OpenGL stack at all -- the plotter is read and
exported, never rendered -- so this path runs on headless machines where
`render_quilt()` itself cannot.

## Cameras

Two modes:

**Explicit** -- a `CyclesCamera`, the right-handed Z-up twin of `PovCamera`:
`location`, `look_at` (the focal plane), `up`, vertical `fov`. It exposes the
same `fov`/`focal_distance` pair, so `format_depth_budget()` and the
`Clearance` arithmetic from the POV-Ray backend apply unchanged -- run the
depth budget before committing Cycles to a 48-view render, exactly as you
would for POV-Ray.

**The scene's own** -- pass `camera=None` with a `.blend`, and the file's
active camera becomes the centre view. The focal plane is taken from the
camera's depth-of-field **focus distance** (or focus object): that is
Blender's native "this distance matters" annotation, and setting it blurs
nothing unless DoF rendering is actually enabled. The camera's lens, sensor
and existing shift are preserved; only `shift_x` moves during the sweep.

A subtlety worth recording: Blender's shift units and effective field of view
both depend on the camera's *sensor fit*, and its `AUTO` fit sizes the sensor
off `sensor_width` even when it resolves to a vertical fit. The driver
mirrors `BKE_camera_params_compute_viewplane` exactly; the sensor-fit
branches are each pinned by rendered-marker tests, because this is precisely
the kind of arithmetic that looks right and ghosts on glass.

## Usage

```python
from quiltwright.lfd import QUILT_PRESETS, save_quilt
from quiltwright.cycles import CyclesCamera, render_cycles_quilt

camera = CyclesCamera(location=(0, -35, 8), look_at=(0, 0, 5), fov=14)
spec = QUILT_PRESETS["portrait"]
quilt = render_cycles_quilt("protein.glb", spec, camera, samples=128)
save_quilt(quilt, "protein", spec)      # -> protein_qs8x6a0.75.png
```

A `.blend` on its own camera:

```python
quilt = render_cycles_quilt("scene.blend", spec, None)   # DoF focus = focal plane
```

Knobs that matter:

- `samples` -- 64 previews cleanly with the denoiser on; 128-256 for finals.
- `device` -- `"auto"` (GPU first, Metal first), `"gpu"` (error if none),
  `"cpu"`.
- `threads` -- CPU renders get the same courtesy cap as the POV-Ray backend
  (`cpu_count - 2`, Blender's `-t`); `0` takes every core.
- `keep_views` -- retain the per-view PNGs and the job JSON for inspection.

**Requirements**: a `blender` binary -- `brew install --cask blender` on
macOS (the standard `/Applications` install is found automatically), or
`BLENDER_BINARY` pointing anywhere else. Blender 4.x or later.

## What stays with POV-Ray

Scenes written in POV-Ray's scene language. CSG, isosurfaces and blobs do
not map onto triangle acceleration structures, and the definitive answer to
"how do I hardware-ray-trace `museum.pov`" remains: you don't -- that scene's
value is that it renders *unmodified*, and [povray.md](povray.md) is its
path. The two backends produce interchangeable quilts on purpose; use
whichever the scene's format dictates.

## Testing

`tests/test_cycles.py` runs its geometry and orchestration tests on numpy
alone (a stub stands in for Blender). The end-to-end tests need a real
`bpy` and are found two ways: a `blender` binary, or `QW_BPY_PYTHON` naming
a Python interpreter with the [`bpy` wheel](https://pypi.org/project/bpy/)
installed -- the CI/container case. With neither, they skip cleanly.
