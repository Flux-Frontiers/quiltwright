# Release Notes -- v0.10.0

> Released: 2026-08-30

Nothing in this release changes what comes out of the renderer. It changes the
shape of what produces it. Three backends had accumulated inside a package
whose geometry, device presets, Bridge client and PyVista rendering all lived
in one module, `lfd.py`, which meant that casting a finished quilt to a panel
imported VTK, and that the same off-axis window shift was derived
independently in three places. This release splits that module along the lines
it had already grown, and promotes the last few things that were reachable
only by copying code out of a script in a checkout.

The other half of the release is about arbitrary input. Until now every worked
example built its own geometry and therefore already knew where the camera
went. A mesh that arrives from somewhere else -- a modeling tool, a scan, an
asset library, a generator -- carries no camera and no known scale, and a
scene whose depth range has never been measured cannot have its budget
computed. Two new CLI commands close both gaps.

## What changed

**Quilt geometry and the Bridge client left the PyVista backend.**
`QuiltSpec`, the device presets, `assemble_quilt`, `save_quilt`,
`view_offsets`, `view_disparity`, `focal_distance_for_range` and
`sweep_extent` now live in `quiltwright.quilt`, which needs only numpy and
pillow; `cast_quilt` and the transport controls live in `quiltwright.bridge`,
which is stdlib alone. `quiltwright.lfd` is what its name always implied -- the
PyVista backend -- and re-exports every moved name, so `from quiltwright.lfd
import QuiltSpec` still works and nothing downstream has to move. Package-level
lazy imports resolve `QuiltSpec` without loading VTK at all, which is the point:
a core install can now compute a quilt's geometry and drive a panel without a
rendering stack anywhere on the machine. `find_ffmpeg` moved to
`quiltwright.runtime` for the same reason, since importing it used to drag
PyVista in behind it.

**`QuiltCamera` and `window_shear()` state the off-axis shift once.** VTK's
`SetWindowCenter`, Blender's `shift_x` and POV-Ray's `direction` shear are
three unit conversions of a single dimensionless number, and each backend used
to arrive at it separately. The shared form lives in `quiltwright.quilt`, with
the per-backend conversion left where it belongs. The protocol is named
`QuiltCamera` rather than `Camera` so it does not collide with layer 1's
`CameraFrame`, and `lfd.camera_frame` is now the public name for the vtkCamera
decomposition it was doing privately.

**`quiltwright mesh` renders any 3D object file, with the camera derived from
the geometry.** The Cycles backend could already import glTF/GLB, OBJ, STL,
PLY, USD, FBX and Alembic, but choosing a `CyclesCamera` for an unfamiliar
mesh was guesswork about scale, origin and post-import up-axis. `mesh_bounds()`
imports the file once, through the same importer the render uses, and reports
its world-space bounding box; `frame_camera()` turns that box into a camera
that fills the field of view via the exact spherical relation
`sin(fov/2) = r/d` and aims at the bounds center, which becomes the focal
plane; `autoframe_camera()` composes the two. `frame_camera()` is pure
arithmetic and unit-tested directly, and the end-to-end path is covered against
a real Blender import. The CLI command wraps all of it with `--lighting`,
`--view-direction`, `--fov`, `--margin`, `--device`, `--samples`, `--still`
and the rest. A `.blend` is refused with its reason, since it carries its own
camera and there is nothing to auto-frame.

**`quiltwright probe` promotes the plane sweep into the package.**
`depth_sweep()` and `summarise_depth_sweep()` are the measurement every near
and far figure in this repository was taken with, and until now they were
reachable only by running a script out of a checkout. They live in
`quiltwright.povray` beside the budget they feed, both tested -- the marker
plane's arithmetic and the summary thresholds directly, the sweep end to end
against a scene with known depths -- and both now take the same courtesy thread
cap the quilt renderers do, rather than every core for the length of a few
hundred frames. The command adds one thing the script never did: when a sweep
never closes, because the scene runs to a sea or a sky or any backdrop at the
horizon, the reported far value is the end of the sweep rather than a
measurement, and it now says so instead of letting that number be copied into
a scene.

**Three smaller promotions out of the scripts.** `frame_and_focus()` in
`quiltwright.lfd` is the PyVista counterpart to `frame_camera()`: it re-fits
the camera at the final view direction by projecting the bounding box's corners
onto the camera's own axes, so an obliquely viewed flat subject is no longer
held at its bounding *sphere's* distance, which is what used to make mountains
read as specks. `fov_vertical_to_horizontal()` in `quiltwright.povgen` is the
inverse of a conversion that was already public in one direction only.
`QuiltSpec.still()` gives a one-tile spec at the device's own aspect, replacing
the hard-coded `880x1100` literal each worked example carried, which ignored
`--device` and framed a landscape panel's still in portrait.

**The CLI is hardware and tooling; `scripts/` is the gallery.** There is
deliberately no generic `quiltwright render`. `cast`, `weave`, `wallpaper` and
`bridge` operate on a finished quilt; `mesh`, `cartoon` and `probe` take
arbitrary input. The composed exhibits for the scenes this repository ships --
museum, vitrine, still-life, DNA helix, cartoon comparison -- stay in
`scripts/`, where they are the presented work rather than unfinished CLI. Two
private cross-module imports that this boundary exposed are now public
(`bridge_post`, `enter_orchestration`), which a fan-in of six and five had
already made them in practice.

**`git push` no longer waits on the ray tracer.** The pre-push pytest hook runs
`-m "not slow"`, taking the local gate from 96 s to 16 s while still running
557 of 588 tests. The marker existed but carried only 13 tests: the three
classes in `tests/test_povray.py` that shell out to a real `povray` binary were
the bulk of the cost and were unmarked. They are marked now. Separately,
`TestDepthSweep` ray-traced its scene once per test because its fixtures were
function-scoped; class-scoping them takes 12 s off every full run, CI included.
Nothing is skipped rather than deferred -- CI runs the suite unfiltered on both
interpreters, and now runs on `develop` as well as `main`, which previously got
no CI at all.

**Knowledge-graph tooling, pinned to the repository rather than the machine.**
An optional `kg` Poetry group installs `pycode-kg` and `doc-kg` into
`.venv/bin`, and `.grok/config.toml` points both MCP servers at those paths, so
an agent working here talks to the pinned versions instead of whatever a global
install has drifted to. A group and not an extra on purpose: an extra reaches
the published wheel metadata and would hand every `pip install quiltwright` a
torch and sentence-transformers install for tooling the package never runs.

**The docs document the Poetry path, and use US spellings.** `README.md` and
`docs/install.md` now give the Poetry commands beside the pip ones -- every
extra has a dependency group of the same name -- and the `pyproject.toml`
header lists every working combination, including the comma-with-no-space form
Poetry requires. British spellings are gone from the prose across `docs/` and
the READMEs; identifiers keep theirs, since they name real code.

## Upgrading

Nothing to migrate. Every name that moved is re-exported from where it used to
live, so existing imports keep working; the only reason to update them is to
avoid loading PyVista for geometry that no longer needs it. `pip install -U
quiltwright` is enough. The two new CLI commands need the backends they drive:
`quiltwright mesh` needs a `blender` binary, `quiltwright probe` a `povray`
one, the same as the libraries behind them.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
