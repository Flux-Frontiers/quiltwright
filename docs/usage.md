# Usage

**Companion to**: the README [Quick start](../README.md#quick-start), which
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

The museum scene ships in [pov-scenes/](../pov-scenes/).
[scripts/render_museum_hologram.py](../scripts/render_museum_hologram.py)
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
[depth budget](../README.md#the-depth-budget) section and derived in
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
