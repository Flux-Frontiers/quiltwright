# Changelog

All notable changes to Quiltwright are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

## [0.3.1] — 2026-08-10

### Changed

- **The README documents the LitiHolo sweep as a third output, marked in
  development.** The pipeline diagram gained a branch for it and a `view
  sweeps` line in the middle box; the column header reads "outputs" rather
  than "displays", since one target is not a display. A new *Send it to a
  hologram printer* section in the quick start runs `LITIHOLO_SWEEP` through
  `render_pov_views()` end to end, with `format_depth_budget()` printed first
  and what the museum actually reports at a 45° cone — ~43 px of adjacent-view
  disparity against an ~8 px ghosting threshold, which is the report doing its
  job rather than an example worth copying unchanged.

  The narrow claim travels with it: what quiltwright emits is a sweep matching
  the published specification, not a verified printer input, and this path is
  POV-Ray only. Both links now point into the relevant sections of
  `docs/lfd.md` rather than at the top of the file.

- **README housekeeping the 0.3.0 release left behind.** The scene-source
  paragraph mentions `quiltwright.tvb_data` and the PyVista example datasets,
  which 0.3.0 added while the README still described only the two upstream
  pipelines. `docs/gallery.md` joins the documentation table — nothing in the
  repository linked to it — and the `docs/lfd.md` row names the view sweeps it
  covers.

### Fixed

- **The vendor's name is spelled LitiHolo throughout.** It appeared both ways
  across the README, `docs/brand.md` and this changelog; the company styles it
  with the capital H.

- **The coarse-sampling figure is 2.75×, not 2.7×.** 45° over 22 intervals
  against 35° over 47 is 2.747. The inputs — 2.05° and 0.74° — were already
  consistent in all four places that quote them; only the ratio was rounded
  down.

- **`render_pov_views()` no longer overstates what is known about hogels.** Its
  docstring asserted that a hologram's hogels are "no more forgiving than a lens
  sheet", while `docs/lfd.md`, `docs/povray.md` and `docs/pov-workflow.md` all
  hold that question open. The docstring now hedges the way the documentation
  does.

## [0.3.0] — 2026-08-10

### Added

- **`quiltwright.tvb_data` — brain geometry from The Virtual Brain as a scene
  source.** Cortical surfaces, structural connectomes, parcellations and
  sensor positions, downloaded on demand and returned as NumPy arrays or
  PyVista meshes ready for the LFD and HLD backends.

  This sits alongside POV-Ray scenes and the PyVista example datasets as a
  *source* of geometry, not an output backend. It arrives here rather than in
  a consumer because the package already reaches for real subjects to put on
  a display — `scripts/render_pyvista_hologram.py` downloads the Allen
  Institute mouse brain atlas, and `docs/pyvista-datasets.md` is already
  where "what is worth rendering" gets reasoned about.

  `tvb-root` ships no data of its own; the datasets live in `tvb-data`, a
  337 MB archive on Zenodo ([doi:10.5281/zenodo.10128131][tvb-doi],
  GPL-3.0). It is fetched on first use, MD5-verified, and cached in the
  platform's native per-user cache directory
  (`~/Library/Caches/quiltwright/tvb` on macOS,
  `$XDG_CACHE_HOME/quiltwright/tvb` on Linux,
  `%LOCALAPPDATA%\quiltwright\Cache\tvb` on Windows), overridable with
  `$QUILTWRIGHT_TVB_CACHE`. Individual files are read straight from the zip;
  the archive is never expanded on disk.

  **Nothing is vendored, and no new dependency is added.** Loading needs only
  the standard library and NumPy; the PyVista bridge needs the existing `viz`
  extra. Nothing in the module encodes video, so the GPL-3 `imageio-ffmpeg`
  build stays exactly where it was — in the optional `video` group, out of
  the default install. Downloading GPL data at runtime rather than shipping
  it is the same line this package already draws around ffmpeg.

  Covers 11 surfaces, 8 connectomes, 4 parcellations and 9 sensor sets:
  `load_surface`, `load_connectivity`, `load_region_mapping`, `load_sensors`,
  plus `surface_polydata` / `connectome_polydata`.

  The archive is not uniformly formatted, and each quirk is handled and
  tested. Most consequential: `cortex_2x120k` indexes triangles from 1 while
  every other surface indexes from 0, so loading it naively yields an index
  one past the last vertex — a silently corrupt mesh rather than an error.
  Also absorbed: split hemispheres, folder-nested members, float-encoded
  indices, bz2-compressed members, and an empty vertex-normals stub.

  Full reference in [docs/tvb-data.md](docs/tvb-data.md).

  [tvb-doi]: https://doi.org/10.5281/zenodo.10128131

- **`quiltwright.cache`** — one answer to "where do runtime downloads go",
  shared by every downloader. `cache_root()` gives the platform's own
  per-user cache directory; `dataset_cache_dir(name, env_var=...)` places one
  dataset under it, with a per-dataset environment override so a large
  download can be relocated without moving the rest.

### Changed

- **The Allen mouse atlas now caches in the platform-native location.**
  `scripts/render_pyvista_hologram.py` hard-coded
  `~/.cache/quiltwright/allen_ccf`, which is only native on Linux; on macOS
  these volumes belong in `~/Library/Caches`, next to where PyVista already
  puts its own downloads. It now goes through `quiltwright.cache` like the
  TVB archive, and honours `$QUILTWRIGHT_ALLEN_CACHE`.

  An existing download at the old path is adopted rather than silently
  re-fetched — the 10 µm template is well over a gigabyte, and this script
  has not been in a release, so anyone holding one has it from a local run.

## [0.2.0] — 2026-08-08

### Added

- **View sweeps, for consumers that are not a light-field panel**
  (`sweep_spec()`, `LITIHOLO_SWEEP`, `render_pov_views()`). A quilt's view count
  is `columns × rows`, so a rectangular grid cannot express a prime one — and
  the LitiHolo desktop hologram printer's published input specification asks for
  23 viewzone images per hogel. A single row expresses any count at all:
  - `quiltwright.lfd.sweep_spec(n_views, view_cone, tile_width, tile_height)`
    builds a single-row `QuiltSpec`. The camera sweep is identical to a quilt's;
    only the packing differs. Raises `ValueError` below 2 views.
  - `quiltwright.lfd.LITIHOLO_SWEEP` — 23 views across a 45° lateral field,
    horizontal parallax only, matching the printer's published specification.
    The per-view pixel size is *not* published, so 1600×2000 errs high
    deliberately: it comfortably exceeds the ~102×127 hogel grid of a 4×5-inch
    plate at 1 mm hogels, and downsampling is cheap where re-rendering is not.
    Aspect 0.8 is that plate in portrait; transpose for landscape.
  - `quiltwright.povray.render_pov_views()` writes `view000.png … viewNNN.png`
    into a directory, view 0 leftmost, and returns the paths in view order.
    Identical camera geometry to `render_pov_quilt()` — the same off-axis
    sheared frustum, the same focal plane on `look_at` — minus the quilt
    assembly.

  What this establishes is that quiltwright **emits a sweep matching the
  published specification**, which is a narrower claim than compatibility: no
  file has been through the printer's software. Two questions stand between the
  two. Whether a hogel slicer expects the off-axis sheared frusta quiltwright
  renders — unambiguously correct for a lenticular panel — or the toe-in
  circular arc a 2003 hologram submission of the same scene used; these are not
  interchangeable. And whether 23 views over 45° is too coarse: at 2.05° between
  adjacent views against a Looking Glass Portrait quilt's 0.74°, it samples
  about 2.75× coarser, which on a lenticular panel would step visibly rather than
  glide. Whether a hogel-based recording is more forgiving is unknown. Both are
  documented in `docs/lfd.md` rather than settled.
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
- **`Makefile` for the renders.** `make stills` regenerates every reference
  still at its scene's declared aspect, `make quilt-<subject>` / `make quilts`
  drive the hologram scripts, `preview-*` targets render quarter-size quilts
  for iterating, and `make release-assets TAG=...` attaches finished quilts to
  a GitHub release. `make help` lists everything.
- **`make quilt-lambda` / `make preview-lambda`**, and lambda joins `make
  quilts` — now four rather than three. The scene was already a registered
  subject in `render_still_life_hologram.py` and `still-lambda_main` already
  rendered its still; only the quilt targets were missing. Unlike the other two
  still lifes it was composed 16:9 in 1998 (`right <HDTV>`), so its framing is
  native on a landscape panel and it needs no `--fov` correction.
- **CI quilt rendering** (`.github/workflows/release.yml`). Publishing a
  release renders the three quilts in parallel, one runner each, and attaches
  them as release assets, so no one's laptop has to. The museum's full
  recursive supersample does not fit the 6-hour job limit on a standard
  runner, so CI renders it at `+A0.1`; the full-quality version renders
  locally and attaches with `make release-assets`.
- **The reference stills are now committed** (`renders/stills/`, 13 PNGs,
  ~14 MB). They are the diffable record of what each scene looks like, and
  regenerating them needs a POV-Ray install and patience. Quilts stay out of
  git — 25–40 MB each — and become release assets instead; `.gitignore` now
  ignores everything under `renders/` except the README and the stills.
- **`pov-scenes/lambda/`** — the 1998 "Lambda Repressor" poster scene from the
  archive: the 1LMB PDB file, the mesh converted from it
  (`lambda_complex2.inc`), the main scene with its sea, sky and chrome
  titling, and the original render `.ini` files.
- **Test coverage for the Looking Glass Bridge transport layer**
  (`cast_quilt`, `pause_quilt`, `resume_quilt`, `stop_quilt`, `_bridge_post`,
  `_enter_orchestration`), previously untested. A `FakeBridge` stands in for
  `urllib.request.urlopen` and pins the endpoint sequence — including that
  `stop_quilt` never calls `delete_playlist`, which hung Bridge 2.6.3 twice in
  testing and needed a `kill -9` to recover; that fix had rested on a commit
  message alone until now. Verified by mutation: reintroducing
  `delete_playlist` fails two tests with a legible diff. `lfd.py` coverage
  83% → 94%.

### Changed

- **Rendering no longer takes the whole machine.** `make` left every core
  saturated, which makes the desktop unusable for the several minutes a quilt
  takes. `RENDER_THREADS` now defaults to `NCPU - 2` (floor 1) and
  `make quilts RENDER_THREADS=$(NCPU)` opts back into the full box.

  Capping it needs two different levers, because there are two paths. The still
  targets invoke `povray` directly and simply gain `+WT`. The quilt scripts
  invoke it themselves, out of reach of the Makefile's argv, so those go through
  an INI file named by `POVINI`.

  Two traps came out of doing this, both worth writing down. `POVINI`
  *replaces* the INI POV-Ray would otherwise have read rather than adding to
  it — and that default is what carries the `Library_Path` entries for the
  standard includes, so an INI containing only `Work_Threads` makes
  `colors.inc` unfindable and every stock scene fails to parse. The generated
  file is therefore a copy of the discovered default with the cap appended.
  And a command-line `+WT` overrides the INI, which `quiltwright.povray`
  derives whenever `jobs > 1` — so raising `JOBS` silently defeats the cap.
- **`JOBS` now defaults to 1 rather than the core count.** That is the render
  scripts' own default and what `povray.md § 6` already recommended: POV-Ray
  threads a single render across all cores, so extra processes buy nothing and
  the old default was 18 single-threaded processes contending. It is also what
  keeps `RENDER_THREADS` effective, per the note above.
- **Makefile render timings corrected.** The help text advertised ~9 min for
  the bell jar and ~18 min for porin against measured 171 s and 120 s; porin
  was also labelled the slower of the two and is in fact the faster. Figures
  are now measured, and each says whether it was taken capped or uncapped
  rather than implying one condition for all four.
- **The quilt path and the sweep path now share one implementation.** `_sweep()`
  (the per-view render loop) and `_copy_views()` (retrieving frames from the
  temporary working directory) were extracted so `render_pov_quilt()` and
  `render_pov_views()` cannot drift apart in the geometry that matters.
  `render_pov_quilt`'s `keep_views=` argument routes through `_copy_views`; its
  behaviour is unchanged.
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
- **Quilts land in `renders/quilts/` instead of `out/`.** Both render scripts'
  `--out` defaults, the `save_quilt()` docstring example and the docs moved
  together.
- **`3porin.pov` now declares `#version 3.6;` and terminates its
  `#declare`s** (two there, ten in `myinclude/rainbow.inc`), so it renders
  as-is and the `+MV3.1` pin is gone from `render_still_life_hologram.py` and
  the docs. 3.6 rather than 3.7 is deliberate: under 3.7's rewritten gamma
  pipeline the scene's `assumed_gamma 2.2` renders 36% darker. Line endings
  normalised CRLF → LF while every line was being touched anyway.
- **`3porin.pov` and `museum.pov` reframed at 16:9** (1920×1080), matching the
  16" landscape panel the holograms target. The porin's extra width over the
  old 3/4 portrait frame is sea and sky. The museum camera is dollied 5 units
  toward the aim point to bring the near jar out toward the left frame edge,
  and `render_museum_hologram.py`'s `EYE`, `NEAR_DEPTH` (31 → 26) and
  `FAR_DEPTH` (96 → 91) follow the dolly. Aspect tables in
  `docs/pov-workflow.md` and `renders/README.md` updated.
- **README hero caption names its display targets.** The museum quilt is now
  described as output for Looking Glass light-field and hololuminescent
  displays, plus LitiHolo holographic printers (in development), rather than
  just "a 48-view light-field quilt".

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
