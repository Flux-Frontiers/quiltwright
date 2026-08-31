# Architecture

Quiltwright turns a scene into holographic output: an off-axis multi-view
*quilt* (or, for Hololuminescent Displays, ordinary 2-D video). Three
rendering backends converge on one assembler, and a numpy-only geometry
core keeps a machine that only casts a finished quilt from having to
install a GPU rendering stack to do it.

```
scene sources                  backends                    shared middle              outputs
PyVista plotter   ----+                                     QuiltSpec / presets
POV-Ray .pov      ----+--->   off-axis views  ------------> assemble_quilt  --------->  quilt PNG
Blender / mesh    ----+       (per-backend camera math)      view_offsets              HLD video
arrays (povgen)   ----+                                      save_quilt                 weave (no Bridge)
PyMOL cartoons    ----+                                                                  LitiHolo sweep
TVB brains        ----+
```

## Module map

| Module | Owns | Depends on |
|---|---|---|
| `quiltwright.quilt` | `QuiltSpec`, `QUILT_PRESETS`, `QuiltCamera` protocol, `window_shear`, `view_offsets`, `view_disparity`, `focal_distance_for_range`, `sweep_extent`, `assemble_quilt`, `save_quilt` | numpy, pillow |
| `quiltwright.bridge` | `BRIDGE_URL`, `cast_quilt`, `save_and_cast_quilt`, `pause_quilt`, `resume_quilt`, `stop_quilt` | `quilt` |
| `quiltwright.runtime` | `find_ffmpeg`, `COURTESY_CORES_HELD_BACK` | stdlib |
| `quiltwright.lfd` | PyVista backend: `render_quilt`, `render_quilt_video`, `scene_depths`, `frame_and_focus`, `depth_report`, `camera_frame` | `quilt`, `bridge`, `runtime`, `[viz]` |
| `quiltwright.povray` | POV-Ray backend: `PovCamera`, `camera_block`, `render_pov_quilt`, `Clearance`, `depth_budget`, `depth_sweep` | `quilt`, `runtime`, `povray` binary |
| `quiltwright.cycles` | Blender Cycles backend: `CyclesCamera`, `view_shift_x`, `render_cycles_quilt`, mesh import and auto-framing | `quilt`, `runtime`, `blender` binary |
| `quiltwright.povgen` | Analytic `.pov` scene composer (primitives, no VTK) | numpy only |
| `quiltwright.hld` | Hololuminescent Display video (2-D, not a quilt) | `runtime`, `[viz]` |
| `quiltwright.weave` | CPU port of Bridge's lenticular shader -- pre-lensed native frames with no Bridge process | `quilt` |
| `quiltwright.tvb_data` | The Virtual Brain dataset downloader (cortical surfaces, connectomes) | `cache` |
| `quiltwright.pymol` | Headless-PyMOL cartoon/surface geometry as a `.pov` include | PyMOL (optional) |
| `quiltwright.cache` | Platform-correct download cache directory, shared by every downloader | stdlib |
| `quiltwright.runreport` | Markdown provenance report written beside a render | stdlib |
| `quiltwright.cli` | The `quiltwright` console script | click |

The dependency graph is acyclic and one-directional: `quilt` and `runtime`
import nothing from this package; `bridge` and `weave` import only `quilt`;
each backend (`lfd`, `povray`, `cycles`) imports `quilt` and `runtime` but
never each other. Nothing outside `quilt.py` needs to know that another
backend exists.

## Why the geometry core is separate from every backend

Before this split, quilt geometry, the assembler, and the Bridge HTTP
client all lived inside `quiltwright.lfd`, the PyVista backend -- because
that backend shipped first. The other two backends and the CLI imported
the shared pieces *from the PyVista module*, including two of its private
names, and `lfd.depth_report` imported back from `povray` to format a
report, which made the dependency graph briefly cyclic.

`quiltwright.quilt` and `quiltwright.bridge` now hold that shared middle
instead, and neither imports VTK, PyVista, POV-Ray, or Blender. That
matters because of `quiltwright`'s own `__init__.py`: every name in
`__all__` is a **lazy** re-export (PEP 562, via `__getattr__`), bound to
its owning submodule on first access rather than at import time. A script
that only calls `cast_quilt()` against an already-rendered PNG imports
`quiltwright.bridge`, not `quiltwright.lfd` -- so it never pays for VTK.
`pip install quiltwright` (no extras) gets exactly this: `numpy`, `pillow`,
`click`, and nothing that renders anything. `poetry install --with viz`
adds PyVista; `--with video` adds ffmpeg; `--with molecules` adds
`pypdb2pov`. CI's `core-install` job (`tests.yml`) asserts this holds by
installing the bare package and checking PyVista never lands in the
environment.

## The off-axis invariant

Every backend produces its views the same way conceptually -- shift the
camera sideways from a shared look-at point, one shift per view -- but each
renderer expresses that shift in its own units, because each has a
different camera model:

| Backend | Function | What it mutates |
|---|---|---|
| PyVista / VTK | `lfd._apply_off_axis_view` | `SetWindowCenter(-offset / half_width, 0)` |
| POV-Ray | `povray.camera_block` | shears `direction` by `offset * D / Z` |
| Blender Cycles | `cycles.view_shift_x` | `-offset / (2 * Z * tan(fov/2) * aspect)` |

`quilt.window_shear()` is the one dimensionless formula underneath all
three: a horizontal window shift, in half-widths, that pins the look-at
point regardless of which renderer receives it. Each backend's function
converts that shared value into its own convention rather than
reimplementing the geometry independently. `PovCamera` and `CyclesCamera`
both satisfy the `QuiltCamera` protocol (`location`, `look_at`, `fov`,
`focal_distance`, `basis()`) up to handedness -- POV-Ray is left-handed,
Blender and VTK are right-handed -- so `depth_budget()` and
`format_depth_budget()` in `quiltwright.povray` accept either camera
without caring which renderer produced it.

## Scene sources

A backend never modifies the scene it is handed. What varies is where the
scene comes from:

- **PyVista plotter** -- built in memory, fed straight to `lfd.render_quilt`.
- **`.pov` file** -- written by hand, decades ago, or generated. `povgen`
  composes one from analytic primitives (spheres, cylinders, swept paths)
  entirely in numpy, so geometry from `kg_utils.viz3d` or similar can reach
  POV-Ray without a mesh tessellation pass.
- **Mesh / `.blend`** -- glTF, OBJ, STL, PLY, USD, FBX, or a native Blend
  file, auto-framed from its bounding box and rendered by `cycles`.
- **PyMOL cartoons** -- `quiltwright.pymol` generates the ribbon/surface
  geometry `pdb2pov` never could, as an `.inc` a POV-Ray scene includes.
- **TVB brain data** -- `tvb_data` downloads cortical surfaces and
  connectomes from The Virtual Brain on demand, through the shared cache
  in `quiltwright.cache`.

See [docs/lfd.md](lfd.md), [docs/povray.md](povray.md),
[docs/cycles.md](cycles.md), [docs/povgen.md](povgen.md),
[docs/pdb2pov.md](pdb2pov.md), and [docs/tvb-data.md](tvb-data.md) for each
source and backend in full.

## CLI versus scripts

The `quiltwright` console script (`quiltwright.cli`) covers hardware and
tooling that takes arbitrary input: `mesh`, `cartoon`, and `probe` accept
any file or scene; `cast`, `weave`, `wallpaper`, and `bridge` drive a
connected panel. There is no generic `quiltwright render` -- a *composed*
exhibit (the museum, the vitrine, the PyVista brain demo) is a
`scripts/render_*.py` script, not a subcommand, because each one wires up
scene-specific choices (camera framing, lighting, which molecules) that
have no arbitrary-input form. `docs/shell.md` documents both halves make
target by make target.

## What this document is not

It is a map, not the manual -- the backend-specific pages linked above cover
each renderer's setup, camera derivation, and worked examples in full. The
[API reference](api/quilt.md) is generated from the same docstrings the
code ships with, so it can't drift from what is actually there.
