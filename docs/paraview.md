# A ParaView session -> a hologram

**Command**: `quiltwright paraview`
**Module**: `quiltwright.paraview` (`render_paraview_quilt`, `probe_paraview_state`, `depth_report`)

> *If you have a ParaView state file, you have a hologram. The pipeline,
> the color maps and the camera all come with it, because the sweep runs
> inside ParaView.*

[ParaView](https://www.paraview.org/) is where a great deal of simulation
output gets looked at: CFD, climate, astrophysics, finite-element results.
A session there is a filter pipeline (slice, contour, clip, streamlines), a
set of color maps and opacity transfer functions, representation settings,
and a camera, all of which ParaView saves as a `.pvsm` state file. None of
that survives the obvious route of exporting the data and reading it into
PyVista: the geometry comes across, and everything the user spent the
afternoon on does not.

Quiltwright takes the other route. It hands the state file back to
ParaView's own Python interpreter, `pvpython`, and sweeps the render view's
camera *in place*. The frames are of the session the user actually built.

---

## The one command

```bash
quiltwright paraview session.pvsm
```

That probes the state for its camera and depth range, prints the depth
budget, sweeps the camera across the device's view cone, and writes a quilt
under `renders/quilts/`. Common variations:

```bash
# Fast single-view still, to check what the state looks like at the device's aspect
quiltwright paraview session.pvsm --still

# A finished portrait quilt, pulled in a little, cast straight to the display
quiltwright paraview session.pvsm --device 27-portrait --zoom 1.4 --cast

# Keep the per-view frames and the camera probe for inspection
quiltwright paraview session.pvsm --keep-views renders/views/session

# Is ParaView reachable at all?
quiltwright paraview --check
```

| Flag | What it does |
|---|---|
| `--device` | Target display preset (`16-landscape` default; `portrait`, `27-portrait`, `go`, ...) |
| `--fov` | Vertical field of view (14 default). The camera is dollied back so the state's framing is kept; `0` keeps the state's own FOV and distance |
| `--zoom` | Dolly factor after framing. Values above 1 fill more of each tile, which is what drives perceived depth |
| `--view-cone` | View cone in degrees. Defaults to the device's own, capped at 35: `16-landscape` declares 50, which overruns the disparity budget. Narrowing it lets `--zoom` go higher at the same depth |
| `--orientation-axes` | Keep ParaView's corner axes widget. Hidden by default: it is pinned to the screen, so it would sit on the glass in every view |
| `--still` | One center view as a flat image at the device's aspect, instead of a quilt |
| `--preview` | Quarter-size quilt, for iterating |
| `--keep-views DIR` | Keep the per-view PNGs and `camera.json` |
| `--out STEM` | Output stem; defaults to the state's name under `renders/quilts/` (or `gallery/` with `--still`) |
| `--cast` | Send the finished quilt to Looking Glass Bridge |
| `--check` | Report where `pvpython` was found and exit |

## What comes across

Everything in the state, because nothing is converted. Sources, filters,
color maps, opacity transfer functions, representations (surface, wireframe,
points, volume rendering), scalar bars, lights, background: whatever the
render view showed when the state was saved is what each view of the quilt
shows. Volume rendering works because `WindowCenter` is a property of the
VTK camera, not of any particular mapper.

Two things about a state file are worth knowing before the first run:

*The camera is the one you saved.* The state's camera is the center view and
its focal point becomes the holographic focal plane, exactly as
`render_quilt()` treats a PyVista plotter. Frame the scene in ParaView the way
you want it seen, put the focal point on the thing that should sit at the
glass (`Adjust Camera` in the toolbar sets it directly), and save state. A
state with several render views is swept on the active one if it is a render
view, otherwise the first.

*Screen-pinned things sit on the glass.* Scalar bars, text annotations and
the orientation axes are 2-D widgets at fixed screen positions. Across a
sweep they land at the same tile position in every view, so the display puts
them exactly at the focal plane. That is harmless for a scalar bar; it is
noise for the orientation axes, which is why those are hidden by default.

## How the sweep works

It is the same sweep every Quiltwright backend makes, applied to the
vtkCamera ParaView owns rather than the one PyVista owns. For each view the
camera position and focal point translate together along the camera's right
vector, no rotation, and `vtkCamera.SetWindowCenter` shears the frustum back
so the original focal point stays centered. That is an off-axis projection,
never a toe-in; see [lfd.md](lfd.md) for why the distinction is what makes a
display fuse the views. The frames are tiled by `assemble_quilt()`, as the
POV-Ray and Cycles frames are.

The whole sweep runs in one `pvpython` process, so the state is loaded once.
The command runs `pvpython` twice: a probe that loads the state without
rendering, so the depth budget can be printed before committing, and then
the sweep. ParaView's startup is about three seconds on an M3 Max; the
sweep's cost is whatever your dataset costs to render, times the view count.

The script that runs inside ParaView cannot import Quiltwright (ParaView
bundles its own Python), so it carries its own copy of the offset and shear
arithmetic. A test execs that copy and checks it against `view_offsets()` and
`window_shear()`, which every other backend uses, so the two cannot drift.

### Verified, and not

`SetWindowCenter` survives ParaView's `Render()` in the default *builtin*
server mode, which is what `pvpython` runs on its own -- a laptop session --
and it survives over a genuine client-server connection too: a separate
`pvserver` process reached with `Connect()`, which is the shape this module
actually asks for. The sheared frame differs from the unsheared one by the
same shift either way.

What is still untested is IceT compositing across multiple MPI ranks
(`mpiexec -n N pvserver`), the mode a cluster uses to split one frame's
rendering across processes. ParaView syncs camera position, focal point,
view-up and view angle to each rank's remote server through named proxy
properties, and `WindowCenter` is not among them, so a distributed-render
sweep may come back un-sheared. If you run one, look at the outer views: an
un-sheared sweep has the subject drifting toward the tile edge rather than
staying centered on the focal plane.

## In Python

```python
from quiltwright import QUILT_PRESETS, save_quilt
from quiltwright.paraview import depth_report, probe_paraview_state, render_paraview_quilt

spec = QUILT_PRESETS["portrait"]

camera = probe_paraview_state("session.pvsm", spec, fov=14.0)
print(depth_report(camera, spec))          # near / focal / far disparity, before rendering

quilt = render_paraview_quilt("session.pvsm", spec, fov=14.0)
save_quilt(quilt, "session", spec)         # -> session_qs8x6a0.75.png
```

`render_paraview_views()` writes the per-view PNGs to a directory instead of
tiling them, for a hologram printer's sweep or for inspection. Pass the same
`fov` and `zoom` to the probe and the render, so the budget describes the
render you are about to make.

## Installing ParaView

ParaView is a desktop application with its own Python, never a Python
dependency of Quiltwright. `pvpython` is found through `PARAVIEW_BINARY`,
then `PATH`, then the macOS application bundle
(`/Applications/ParaView-*.app/Contents/bin/pvpython`), so the cask install
works with no further setup:

```bash
brew install --cask paraview       # macOS
quiltwright paraview --check       # reports the pvpython it will use
```

Binaries for every platform are at
[paraview.org/download](https://www.paraview.org/download/). The
`[openvkl]` initialization errors ParaView prints at startup on macOS are its
OSPRay module failing to load, which the sweep never uses; they are filtered
out of Quiltwright's error output.

## Slicer, and other VTK applications

The same argument applies to any application built on VTK, since the sweep
is twenty lines against `vtkCamera`. Nothing here drives
[3D Slicer](https://www.slicer.org/) yet, but Slicer's native `.nrrd`
volumes read straight into PyVista with `pv.read()`, so a Slicer volume
already reaches the display through the [PyVista backend](lfd.md) with no
conversion.
