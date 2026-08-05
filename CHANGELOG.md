# Changelog

All notable changes to Quiltwright are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **Scene framing helpers** in `quiltwright.povray`, promoted from
  `scripts/render_museum_hologram.py` where they were written for one scene.
  Adapting an existing scene to a sweep is the same three measurements every
  time, and none of them belonged in a script:
  - `PovCamera.aimed()` — adopts a scene's own eye, aim and lens, then moves
    the focal plane along the original aim ray and slides the eye laterally
    with the look-at point riding along, so the view direction is untouched.
  - `Clearance` — the measured lateral corridor of an enclosed scene, with the
    recentring offset (`centre`), the widest cone that still clears the walls
    (`cone()`), and the check that a given quilt fits (`fits()`).
  - `sweep_extent()` — half-width of the lateral eye travel a quilt needs, in
    closed form.
  - `depth_budget()` / `format_depth_budget()` — adjacent-view disparity at
    labelled depths, as data and as a pre-render report that flags soft depths
    and warns when the sweep would leave the room.
- **Test suite for the Gen3 16" Landscape** (`TestSixteenLandscape`), the
  device these renders target. Pins the preset against the defaultQuilt Bridge
  reports, and covers the property that makes it the awkward one: its tiles are
  stored *anamorphically*, 960x720 holding a 16:9 view rendered 1280x720, so
  tile pixel aspect deliberately disagrees with view aspect. Also anchors the
  published museum depth budget (3.58 px near/far, 6.95 px sky) to this
  device's real 720 px tiles, and pins the cost of its native 50-degree cone.
- `docs/about-the-image.md` — what the museum scene is, what is on display in
  it, and the pipeline behind it: the B-DNA under the left bell jar is pdb2pov
  output from 14 Mar 1997, and pdb2pov still builds. The narrative moved here
  out of the `render_museum_hologram.py` docstring, which is now four sentences
  about the camera, and out of `povray.md § 4`, which is now only the numbers.
- `scripts/measure_depth_range.py` — measures a scene's depth range instead of
  estimating it. Slides an opaque plane along the view axis and scores how much
  of the frame stays in front of it, giving a cumulative depth histogram, and
  reports the near distance, the far distance covering 95% of occludable
  content, and the sky fraction that never occludes at all. Two traps are
  handled and documented: POV-Ray disables transparency below `+Q8`, so a cheap
  probe reports a room with no windows and no sky, and the measurement has to
  be taken through the camera that will render, not the scene's own.

### Changed

- `scripts/render_museum_hologram.py` now holds only the museum's measured
  constants and calls the module. Camera, cone and reported disparities are
  unchanged.
- **Poetry groups now mirror the PEP 621 extras one-for-one.** The `viz` group
  pulled in `imageio-ffmpeg` while the `[viz]` extra did not, so
  `poetry install --with viz` and `pip install ".[viz]"` produced different
  environments. ffmpeg now lives in its own `video` group, matching the
  `[video]` extra.
- `imageio-ffmpeg` added to the `dev` group. Without it the video tests skip,
  and a skipped test reports success while asserting nothing. It is the only
  skip condition a Python dependency can lift — the PyVista tests also need a
  system GL stack and an X server.
- `docs/install.md` records why ffmpeg stays an extra rather than a core
  dependency: the binary `imageio-ffmpeg` bundles is a GPLv3 build
  (`--enable-gpl --enable-version3`), which a BSD-3 project should hand people
  on request rather than by default. Also notes that encoding needs `libx264`
  and `libx265`, which a minimal or LGPL-only ffmpeg may lack — a failure that
  surfaces at encode time, not install time.
- `poetry.lock` regenerated for the group changes.
- **README reframed around the pipelines it actually serves.** It read as a
  solution to a projection problem; the purpose is holographic output for two
  scientific rendering pipelines — PyVista/VTK scenes from WaveRider and
  POV-Ray scenes from pdb2pov — onto two display technologies, light-field
  (quilts) and hololuminescent (2-D video). The off-axis projection note stays,
  subordinated to what it is in service of.
- **Re-measured the museum's depth range, and everything derived from it.**
  `NEAR_DEPTH` moves 32 → 31 and `FAR_DEPTH` 100 → 96, which moves the focal
  plane 48.5 → 46.9, the clearance-limited cone 25.6° → 26.4°, and the
  near/far disparity 3.58 → 3.68 px. Figures updated in `povray.md § 3-4`,
  the README, `about-the-image.md`, and the tests that pin them.

  Two corrections came out of measuring rather than estimating. The nearest
  geometry is the near pedestal's *tabletop*, not the bell jar it carries, so
  drawing the pedestals inward moved the near bound far less than the jar
  itself moved. And the sky is 6.1% of the frame, not the ~10% previously
  recorded. Re-measuring the *previous* layout with the same probe gives 26
  units, not the 32 documented for it, so the original figure was optimistic —
  the depth budget it produced was slightly tighter than believed, never
  looser.
- **Regenerated `museum_centre_view.png` and `museum_parallax.png`**, which
  still showed the old pedestal placement. The parallax figure is now views 0
  and 47 of the near pedestal against the painting behind it.
- The finished-quilt verification table in `povray.md § 4` is re-measured by
  cross-correlating feature crops between views 11 gaps apart, and now records
  the method's two failure modes: crops spanning a range of depths return a
  number belonging to no feature, and crops must be chosen on a view between
  the two being compared. It gains a row for a painting that sits within a unit
  of the focal plane and therefore does not move at all.
- **Corrected the museum scene's provenance.** It was described as "a 1994
  Michael Mittelstadt interior, later extended with molecular exhibits", which
  inverts the authorship: the scene is "Eric's Science Museum" (begun 10 Jun
  1995, revised 14 Mar 1997), and what it borrows from Mittelstadt's 1994 work
  is the room — walls, columns, window, frames, pedestals — while every exhibit
  in it is the author's own. Dates in `povray.md` and `install.md` fixed to
  match the scene headers.

## [0.1.0] — 2026-08-04

Initial release. Extracted from
[WaveRider](https://github.com/Flux-Frontiers/waverider) 0.12.0, where this
code grew as `waverider.lfd` / `waverider.hld`; git history for those files is
preserved. Split out because three unrelated consumers now depend on it —
manifold visualisation, molecular rendering, and a POV-Ray scene archive — and
none of them should have to depend on the others.

### Added

- **POV-Ray backend** (`quiltwright.povray`). Renders quilts from existing
  `.pov` scenes without modifying them: each view wraps the scene with
  `#include` and appends an off-axis camera, which POV-Ray honours because it
  uses the last camera it parses.
  - `PovCamera` — camera in `look_at` form, where the aim point becomes the
    holographic focal plane.
  - `camera_block()` — emits the sheared camera for one view. Never emits
    `angle`, which would override `|direction|` and silently destroy the
    shear.
  - `render_pov_quilt()` — sweeps the cone, ray-traces each view, assembles.
- **Depth budget tools** in `quiltwright.lfd`:
  - `view_disparity()` — adjacent-view pixel shift for content at a given
    depth. Verified against ray-traced renders to within 2%.
  - `focal_distance_for_range()` — harmonic-mean focal distance, which
    equalises the disparity penalty between near and far content.
- `assemble_quilt()` — renderer-agnostic tiling, extracted from
  `render_quilt()` so both backends share it. Consumes views lazily and
  validates the count.
- `docs/povray.md` and `docs/pdb2pov.md`.
- `scripts/render_museum_hologram.py` — worked example driving a 1994 POV-Ray
  interior, including the depth and clearance measurements it needs.

### Changed

- `find_ffmpeg()` is now public. It was `_find_ffmpeg`, imported across module
  boundaries by `hld`, which is not appropriate for a private helper.
- POV-Ray camera vectors are emitted at full float64 precision. At 10
  significant figures the shear term — a small correction to a large
  `direction` vector — lost enough accuracy to move the focal plane
  measurably in large scenes.
- The default Bridge playlist name is now `"quiltwright"`.
