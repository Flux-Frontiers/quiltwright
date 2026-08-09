# Release Notes — v0.2.0

> Released: 2026-08-08

Quiltwright 0.2.0 widens the output side and hardens the render side. A scene
can now feed a hologram printer as well as a light-field panel, without being
rebuilt; and rendering a quilt no longer means handing the desktop over to
POV-Ray for several minutes.

## What changed

**Sweeps, for consumers that aren't a panel.** A quilt packs views into a
rectangular grid, which cannot express a prime view count — and the LitiHolo
desktop hologram printer's published specification asks for 23. `sweep_spec()`
builds a single-row layout instead, `LITIHOLO_SWEEP` presets it to the
printer's published field of view, and `render_pov_views()` writes the frames
out individually with the same off-axis camera geometry `render_pov_quilt()`
uses, minus the tiling. This is a narrower claim than compatibility — no file
has been through the printer's own software yet — and `docs/lfd.md` records
what's still open, including whether a hogel slicer wants the off-axis frusta
this renders or the toe-in arc an earlier hologram submission used.

**Scene-framing helpers, promoted out of a script.** `PovCamera.aimed()`,
`Clearance`, `sweep_extent()`, and `depth_budget()` / `format_depth_budget()`
now live in `quiltwright.povray` instead of being rewritten per scene. They
make adapting an existing POV-Ray scene to a sweep or quilt the same three
measurements every time: the camera's own eye/aim/lens, the lateral corridor
the room actually clears, and the disparity at labelled depths, including a
warning when a sweep would carry the camera through a wall.

**Rendering stops saturating the machine.** `make` used to pin every core for
the several minutes a quilt takes; `RENDER_THREADS` now defaults to `NCPU-2`
and `JOBS` defaults to 1 (POV-Ray threads a single render across all cores
itself, so extra processes were only adding contention). `make
quilts RENDER_THREADS=$(NCPU)` opts back into the full box when you want it.

**Test coverage for previously-untested paths.** The Looking Glass Bridge
transport layer (`cast_quilt`, `pause_quilt`, `resume_quilt`, `stop_quilt`)
had no tests at all, which left a prior fix — avoiding the `delete_playlist`
call that hung Bridge 2.6.3 twice in testing — resting on nothing but a commit
message; it's now pinned and verified by mutation. The Gen3 16″ Landscape
preset, the awkward one whose tiles are stored anamorphically, is pinned
against real Bridge output.

**Documentation and assets caught up to what the code does.** The README is
reframed around the two pipelines Quiltwright actually serves rather than a
generic projection-fixing pitch, and its hero caption now names the display
targets — Looking Glass light-field and hololuminescent panels, plus Litiholo
printers in development. The museum scene's depth range was re-measured
rather than estimated, correcting figures that had drifted since the original
render, and reference stills are now committed so what each scene looks like
is diffable without a local POV-Ray install.

## Upgrading

No breaking changes. If you render quilts locally, `make quilts` now runs
capped and single-threaded by default — pass `RENDER_THREADS=$(NCPU)` if you
want the old full-machine behaviour back. New code wanting a hologram-printer
sweep instead of a quilt should start from `quiltwright.lfd.sweep_spec()` or
`LITIHOLO_SWEEP`.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
