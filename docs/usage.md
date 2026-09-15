# Usage

**Companion to**: the README [Quick start](https://github.com/Flux-Frontiers/quiltwright#quick-start), which
keeps one short example. This page holds the recipes for each backend, casting
to Looking Glass Bridge, and view sweeps for a hologram printer.

Shell targets and the CLI live in [shell.md](shell.md). Backend-specific depth
and camera detail lives in [povray.md](povray.md), [cycles.md](cycles.md), and
[lfd.md](lfd.md).

---

## From a PyVista scene

```python
import pyvista as pv
from quiltwright import QUILT_PRESETS, render_quilt, save_quilt

p = pv.Plotter(off_screen=True)
p.add_mesh(pv.ParametricTorus())

spec = QUILT_PRESETS["portrait"]
save_quilt(render_quilt(p, spec), "torus", spec)   # -> torus_qs8x6a0.75.png
```

---

## From a POV-Ray scene

The scene file is never modified -- each view wraps it with `#include` and
appends one camera.

```python
from quiltwright import QUILT_PRESETS, PovCamera, render_pov_quilt, save_quilt

camera = PovCamera(location=(15, 20, 6), look_at=(44, 19.2, 45.1), fov=53.13)
spec = QUILT_PRESETS["16-landscape"]
quilt = render_pov_quilt("pov-scenes/museum/museum.pov", spec, camera,
                         include_paths=["pov-scenes/myinclude", "pov-scenes"])
save_quilt(quilt, "museum", spec)
```

The museum scene ships in [pov-scenes/](https://github.com/Flux-Frontiers/quiltwright/tree/main/pov-scenes).
[scripts/render_museum_hologram.py](https://github.com/Flux-Frontiers/quiltwright/blob/main/scripts/render_museum_hologram.py)
renders it end-to-end; the worked case study is [povray.md](povray.md).

---

## From a Cycles scene

Same plotter, path-traced instead of rasterized -- Metal on Apple Silicon,
OptiX/HIP/oneAPI elsewhere, CPU as the fallback.
`render_cycles_quilt_from_plotter` reads the plotter and does not mutate it,
so it also runs where `render_quilt` cannot (no OpenGL stack).

```python
import pyvista as pv
from quiltwright import QUILT_PRESETS, render_cycles_quilt_from_plotter, save_quilt

p = pv.Plotter(off_screen=True)
p.add_mesh(pv.ParametricTorus())

spec = QUILT_PRESETS["portrait"]
quilt = render_cycles_quilt_from_plotter(p, spec, lighting="studio")
save_quilt(quilt, "torus_cycles", spec)
```

For a `.blend` file or a mesh already on disk (glTF, OBJ, STL, PLY, USD, FBX,
Alembic), call `render_cycles_quilt` with an explicit `CyclesCamera`:

```python
from quiltwright import CyclesCamera, QUILT_PRESETS, render_cycles_quilt, save_quilt

camera = CyclesCamera(location=(0, -35, 8), look_at=(0, 0, 5), fov=14)
spec = QUILT_PRESETS["portrait"]
quilt = render_cycles_quilt("protein.glb", spec, camera, samples=128)
save_quilt(quilt, "protein", spec)
```

Lighting rigs and two worked examples (DNA helix vs POV-Ray, PyMOL cartoon vs
Cycles) are in [cycles.md](cycles.md). Auto-framing any mesh file from its
bounds is covered in [mesh-import.md](mesh-import.md).

---

## From a ParaView state file

Nothing is exported. The `.pvsm` goes back to ParaView's own `pvpython` and the
render view's camera is swept in place, so the filter pipeline, color maps,
opacity transfer functions and volume rendering all survive -- the parts a
round trip through an exported mesh loses.

```python
from quiltwright import QUILT_PRESETS, save_quilt
from quiltwright.paraview import depth_report, probe_paraview_state, render_paraview_quilt

spec = QUILT_PRESETS["portrait"]

camera = probe_paraview_state("session.pvsm", spec, fov=14.0)
print(depth_report(camera, spec))       # the budget, before paying for the sweep

quilt = render_paraview_quilt("session.pvsm", spec, fov=14.0)
save_quilt(quilt, "session", spec)
```

`probe_paraview_state()` loads the state without rendering, so the depth budget
is known first. Frame the scene in ParaView the way you want it seen and save
state: its camera becomes the center view and its focal point the holographic
focal plane.

ParaView is a desktop application with its own interpreter, never a Python
dependency -- `quiltwright paraview --check` reports the `pvpython` it found.
The bundled Mount Hood example is one command:

```bash
quiltwright paraview paraview-scenes/mount-hood/mount-hood.pvsm --view-cone 20 --zoom 2.10
```

The two flags trade against each other. The default device is `16-landscape`,
whose native cone is capped at 35 degrees; a narrower cone leaves room for more
zoom at the same disparity, so the terrain fills the panel without ghosting.
`make quilt-mount-hood` runs exactly this.

Run it from the repository root: a `.pvsm` resolves its data paths against the
working directory, and a state that cannot find its data renders an empty scene
rather than failing. Full details in [paraview.md](paraview.md).

---

## Send it to the display

```python
from quiltwright import cast_quilt, save_and_cast_quilt

cast_quilt("museum_qs8x6a1.77778.png", spec)   # needs Looking Glass Bridge >= 2.2

path, error = save_and_cast_quilt(quilt, "museum", spec)
```

`save_quilt` takes the array and `cast_quilt` takes a path.
`save_and_cast_quilt` composes the two and returns a failed cast rather than
raising, so a Bridge that isn't running never costs you the render. Saved
filenames carry the `_qs<cols>x<rows>a<aspect>` suffix that Looking Glass Studio
and Bridge parse.

Several quilts play as one playlist that advances on a timer and loops. Each
entry carries its own spec, so grids can differ:

```python
from quiltwright import QUILT_PRESETS, cast_playlist

go = QUILT_PRESETS["go"]
cast_playlist(
    [("bdna-go_qs11x6a0.5625.png", go), ("bell-jar-portrait_qs11x6a0.5625.png", go)],
    duration_ms=10_000,
    head_index=1,
)
```

From the shell, `quiltwright playlist` does the same and reads each quilt's
tiling from its filename; see [cli.md](cli.md#playlist).

---

## Send it to a hologram printer (in development)

A printer wants the views as **separate frames**, not tiled, and LitiHolo's
published spec asks for 23 of them -- a prime count, so no quilt grid can
express it. `LITIHOLO_SWEEP` is that single-row spec. POV-Ray only for now;
no file has been through the printer's software.

```python
from quiltwright import LITIHOLO_SWEEP, format_depth_budget, render_pov_views

print(format_depth_budget(LITIHOLO_SWEEP, camera, {"near": 31, "far": 96}))
paths = render_pov_views("pov-scenes/museum/museum.pov", LITIHOLO_SWEEP,
                         camera, "sweep/",
                         include_paths=["pov-scenes/myinclude", "pov-scenes"])
```

23 views over 45° is 2.05° between adjacent views (a Portrait quilt is 0.74°),
so a sweep has *less* margin than a quilt, not more. Open questions are in
[lfd.md](lfd.md#what-this-does-and-does-not-establish).

---

## Check the depth budget

Whether a hologram fuses comes down to adjacent-view disparity. Quiltwright
gives you the arithmetic before the render:

```python
from quiltwright import QUILT_PRESETS, focal_distance_for_range, view_disparity

focal = focal_distance_for_range(near=31, far=96)       # harmonic mean, not midpoint
view_disparity(QUILT_PRESETS["16-landscape"], fov=53.13,
               focal_distance=focal, depth=31)          # -> px between adjacent views
```

The results worth knowing before you frame a shot are summarized in the README
[depth budget](https://github.com/Flux-Frontiers/quiltwright#the-depth-budget) section and derived in
[povray.md](povray.md).

---

## Device presets

`QUILT_PRESETS` carries the official quilt settings for Portrait, Go, and the
16"/27"/32"/65" panels in both orientations. The 16" Gen3 Landscape entry is
verified against what Bridge reports for real hardware.

```python
from quiltwright import QUILT_PRESETS
QUILT_PRESETS["16-landscape"]      # 8x6 views, 7680x4320, aspect 1.7778
```
