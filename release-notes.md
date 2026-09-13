# Release Notes -- v0.13.0

> Released: 2026-09-13

This release adds a fourth scene source: ParaView. A `.pvsm` state file --
the filter pipeline, the color maps, the opacity transfer functions, the
camera, everything a session accumulates -- goes straight to a quilt,
because the sweep runs inside ParaView's own `pvpython` rather than on an
export of the data. The obvious route, saving the geometry out and reading
it back into PyVista, throws away everything that made the session worth
having; this one doesn't.

## What changed

**`quiltwright.paraview` and `quiltwright paraview`.**
`render_paraview_quilt("session.pvsm", spec)` hands the state file to
`pvpython` and sweeps the render view's camera in place with the same
off-axis recipe every other backend uses -- translate along the right
vector, shear with `vtkCamera.SetWindowCenter` -- then tiles the frames with
`assemble_quilt()`. Nothing is exported, so the session's pipeline, color
maps, transfer functions and camera all come across. `probe_paraview_state()`
reads the framed camera and visible bounds without rendering, so
`depth_report()` prints the disparity budget before the sweep is paid for;
`render_paraview_views()` keeps the per-view frames for inspection or a
hologram printer's sweep.

ParaView stays an external binary, never a dependency -- a 500 MB desktop
application with its own Python is not something a virtualenv can import.
`pvpython` is found via `PARAVIEW_BINARY`, then `PATH`, then the macOS
application bundle, so `brew install --cask paraview` needs no further
setup; `quiltwright paraview --check` reports what was found.

**What's verified, and what isn't.** `SetWindowCenter` survives ParaView's
`Render()` both in the default builtin-server mode and over a genuine
single-process client-server connection -- a separate `pvserver` reached
with `Connect()`, confirmed against real ParaView 6.1.1 with pixels that
actually moved, not just a property that read back unchanged. IceT
compositing across multiple MPI ranks is untested; a distributed-render
sweep may come back un-sheared, and the docs say so.

## Upgrading

No breaking changes -- `pip install -U quiltwright` is enough. The ParaView
backend needs no new extra; it only needs a `pvpython` reachable on the
machine, per [docs/paraview.md](docs/paraview.md).

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
