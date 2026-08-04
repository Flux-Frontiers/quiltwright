# Release Notes — v0.1.0

> Released: 2026-08-04

Quiltwright 0.1.0 is the first release: a Python library that turns rendered
scenes into **quilts** — the tiled multi-view images that Looking Glass
lenticular light-field displays fuse into real, glasses-free depth. It renders
from PyVista/VTK or POV-Ray, does the off-axis projection correctly in both
backends, and drives Looking Glass Bridge directly. The code was extracted
from [WaveRider](https://github.com/Flux-Frontiers/waverider) 0.12.0, where it
grew as `waverider.lfd` / `waverider.hld`; it now stands alone so that
manifold visualisation, molecular rendering, and scene archives can share it
without depending on each other.

## What's here

**Correct off-axis projection.** Each view slides the camera laterally while
continuing to face the same direction, with the image plane sheared back onto
the original view axis. The intuitive alternative — swivelling each camera to
keep the subject centred — introduces vertical parallax the display cannot
fuse, and is the single most common way light-field renders go wrong. Both
backends get this right, at full float64 precision, because the shear term is
a small correction to a large vector and single precision measurably moves
the focal plane in large scenes.

**A POV-Ray backend for ray-traced holograms.** `render_pov_quilt()` renders
quilts from existing `.pov` scenes without modifying them: each view wraps
the scene with `#include` and appends one off-axis camera, which POV-Ray
honours because it uses the last camera it parses. Thirty-year-old scenes
render as holograms unchanged — the repo ships a complete 1994 museum
interior under `pov-scenes/` as a worked example, with
`scripts/render_museum_hologram.py` driving it end-to-end from measured
depth and wall-clearance data.

**The depth-budget arithmetic.** Whether a hologram fuses or ghosts comes
down to adjacent-view disparity. `view_disparity()` predicts it to within 2%
of ray-traced ground truth, and `focal_distance_for_range()` places the focal
plane at the harmonic mean of the depth range, where near and far content
are equally penalised. You know before rendering whether a scene will fuse.

**Driving the glass.** `QUILT_PRESETS` carries verified quilt settings for
Portrait, Go, and the 16″/27″/32″/65″ panels; `cast_quilt()` and friends
speak Bridge's HTTP orchestration protocol directly, and saved filenames
carry the `_qs<cols>x<rows>a<aspect>` suffix that Studio and Bridge parse
automatically. The `quiltwright.hld` module targets the Hololuminescent
line, which plays ordinary video rather than quilts.

## Installing

`pip install quiltwright` for the core; add `[viz]` for the PyVista backend,
`[video]` for encoding. The POV-Ray backend needs a `povray` binary and
Bridge ≥ 2.2 drives the display — the full stack is covered in
[docs/install.md](docs/install.md).

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
