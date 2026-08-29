# Changelog

All notable changes to Quiltwright are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **`sweep_extent()` lives next to `QuiltSpec`.** The closed-form half-width
  of a view sweep is quilt geometry, not POV-Ray-specific; `povray` re-exports
  it. `depth_budget` / `format_depth_budget` take any camera with `fov` and
  `focal_distance` (`QuiltCamera`, `CyclesCamera`, or a two-field lens), so
  `lfd.depth_report` no longer builds a throwaway `PovCamera`.

- **`QuiltCamera` protocol and `window_shear()`.** The three backends
  (VTK `SetWindowCenter`, Blender `shift_x`, POV-Ray `direction` shear)
  are unit conversions of one dimensionless window shift, now in
  `quiltwright.quilt`. Named `QuiltCamera` so it does not collide with
  layer 1's `CameraFrame`. `lfd.camera_frame` is the public name for the
  vtkCamera decomposition (the private `_camera_frame` remains as an
  alias). The courtesy core cap lives in `quiltwright.runtime` so Cycles
  no longer imports it from the POV-Ray module.

- **A general-purpose "any 3D object file → quilt" path, with the camera
  auto-framed from the mesh.** The Cycles backend already imported glTF/GLB,
  OBJ, STL, PLY, USD, FBX and Alembic, but every worked example so far
  *built* its own geometry and so already knew where the camera went. A
  finished mesh that arrives from elsewhere — a modelling tool, a scan, an
  asset library, an AI generator such as Meshy — carries no camera, and its
  scale, origin and post-import up-axis are unknown, so a hand-picked
  `CyclesCamera` was guesswork. Three new functions in `quiltwright.cycles`
  remove the guess: `mesh_bounds()` imports the file once (through the same
  importer the render uses) and reports its world-space bounding box,
  `frame_camera()` turns a box into a `CyclesCamera` that fills the field of
  view via the exact spherical relation `sin(fov/2) = r/d` and aims at the
  bounds centre (the focal plane), and `autoframe_camera()` composes the two.
  `frame_camera()` is pure arithmetic and unit-tested directly; `mesh_bounds()`
  and the end-to-end path are covered against a real Blender import.

- **`quiltwright mesh`** — the model-agnostic front door to the above, and the
  first CLI command that is a render rather than a step downstream of one.
  `quiltwright mesh model.glb` probes, frames, renders and writes a quilt in
  one command, with `--lighting` (`studio`/`soft`/`sky`/an HDRI),
  `--view-direction`, `--fov`, `--margin`, `--device`, `--samples`,
  `--compute`, `--view-transform`, `--still`, `--preview`, `--out` and
  `--cast`. A `.blend` is refused with the reason (it carries its own camera,
  so there is nothing to auto-frame). Documented in
  [docs/mesh-import.md](docs/mesh-import.md), now linked from the README
  documentation table.

- **`quiltwright probe`, and the plane sweep behind it, promoted into the
  package.** `depth_sweep()` and `summarise_depth_sweep()` now live in
  `quiltwright.povray` alongside the budget they feed, having previously been
  reachable only by running a script out of a checkout -- and they are the
  measurement every near/far figure in this repo was taken with. Both are
  tested: the marker plane's arithmetic and the summary thresholds directly,
  the sweep end to end against a scene with known depths. The sweep now takes
  the same courtesy thread cap the quilt renderers do, rather than every core
  for the length of a few hundred frames. The command adds one thing the
  script did not: when the sweep never closed -- a sea, a sky, any backdrop
  running to the horizon -- the reported *far* is the end of the sweep rather
  than a measurement, and it now says so instead of letting the number be
  copied into a scene.

- **`frame_and_focus()`** in `quiltwright.lfd` -- the PyVista counterpart to
  `frame_camera()`, promoted out of `scripts/render_pyvista_hologram.py`,
  where a tight fit for a tilted view was reachable only by copying forty
  lines. It re-fits the camera at the final view direction by projecting the
  bounding box's corners onto the camera's own axes (so an obliquely viewed
  flat subject is not held at its bounding *sphere*'s distance, which is what
  made mountains read as specks) and places the focal plane at the harmonic
  mean of the resulting depths. Documented in
  [docs/lfd.md](docs/lfd.md#framing-a-tilted-view).

- **`fov_vertical_to_horizontal()`** in `quiltwright.povgen`, the inverse of
  the `fov_horizontal_to_vertical()` that was already public. A scene composed
  from `right`/`up` vectors states its lens vertically while `PovCamera` wants
  the horizontal angle, so the conversion was being done in a script.

- **`QuiltSpec.still()`** — a one-tile spec at the device's own aspect, for
  the single centre view that checks framing before a sweep is paid for. The
  worked-example scripts each carried their own hard-coded `880x1100`
  literal, which ignored `--device` and framed a landscape panel's still in
  portrait.

### Changed

- **Quilt geometry and Bridge HTTP no longer live inside the PyVista
  backend.** `QuiltSpec`, presets, `assemble_quilt`, `save_quilt` and the
  view-offset arithmetic moved to `quiltwright.quilt` (numpy + pillow).
  `cast_quilt` and the transport controls moved to `quiltwright.bridge`
  (stdlib). `quiltwright.lfd` re-exports every moved name, so
  `from quiltwright.lfd import QuiltSpec` is unchanged. Package-level lazy
  imports now resolve `QuiltSpec` without loading VTK. Plan:
  [docs/architecture-plan.md](docs/architecture-plan.md).

## [0.9.0] - 2026-08-26

### Added

- **A "From a Cycles scene" quick-start section in the README.** The Cycles
  backend was already documented in Install prerequisites, the
  architecture overview, the Documentation table and Testing -- but Quick
  start itself only walked through PyVista and POV-Ray, so a reader going
  top-to-bottom would never learn how to call `render_cycles_quilt` or
  `render_cycles_quilt_from_plotter()`. Both entry points are now shown
  alongside their POV-Ray/PyVista siblings, with pointers to both worked
  examples and `docs/cycles.md`.

- **`quiltwright.pymol.cartoon_obj()` and `scripts/render_cartoon_hologram.py`**
  -- the mesh-heavy comparison the DNA helix example deliberately isn't.
  `cartoon_obj()` is the mesh twin of `cartoon_inc()`: the identical PyMOL
  export and coalescing, written as a plain OBJ instead of a POV-Ray
  include, so `render_cartoon_hologram.py --backend cycles` and
  `--backend povray` render **the same PyMOL triangulation** through both
  backends rather than two independently modelled scenes. Carries the same
  POV-Ray-native-to-right-handed coordinate flip as the rest of the
  package (negate *z*, reverse face winding to compensate) -- derived
  algebraically and checked against a synthetic mesh2 fixture, and now
  exercised against a real PyMOL install and real structures (`molecules/`
  carries `2omf.cif.gz` and `1gfl.pdb` as fetchable examples). That exercise
  found the coordinate flip itself was fine but the geometry still arrived
  turned 90 degrees against its camera -- see Fixed, below -- exactly the
  failure mode this entry originally flagged as unverified.

- **`color="ss"` on both `cartoon_inc()` and `cartoon_obj()`.** Runs
  `cmd.dss()` then colours helix, strand and everything else (loops, turns)
  with the three flat colours in `SS_COLORS` -- the conventional
  three-colour cartoon, as an alternative to a `"spectrum"` rainbow or a
  single flat colour. For `cartoon_obj()`, whose OBJ has no way to carry a
  rainbow ramp (`color="spectrum"` now raises there, with a pointer to
  `cartoon_inc()`/POV-Ray instead), the three baked colours are read back
  out of PyMOL's own `texture_list` rather than recomputed, matched to
  `SS_COLORS` by nearest RGB, and written as a companion `.mtl` with one
  material per colour actually used -- so a structure with no helices
  writes no unused `helix` material. `render_cartoon_hologram.py --color`
  defaults to `"ss"` on both backends now, in place of the old
  Cycles-has-no-colour-at-all default.

- **A `roughness` parameter on `cartoon_obj()`**, written into the `.mtl` as
  Wavefront's `Pr` extension. Blender's own default (`0.5`) reads as flat
  and plasticky next to POV-Ray's finish; `render_cartoon_hologram.py
  --roughness` (default `0.3`) is the Cycles-side answer to `--finish`,
  below.

- **`finish="metallic"` on `cartoon_inc()`.** Rewrites every colour PyMOL
  baked into the exported mesh with the vitrine's own brass recipe
  (`pov-scenes/vitrine/vitrine.inc`) -- bump normal, `metallic` specular and
  reflection, low diffuse -- but tinted with each baked colour instead of
  brass yellow, so `color="ss"` comes out as three metals rather than one
  shared material. `render_cartoon_hologram.py --finish metallic` wires it
  up; `--finish normal` (default) is unchanged behaviour. A `"glass"`
  option was prototyped and dropped: a cartoon is a lattice of 20+ crossing
  ribbons along a typical view ray, and per-surface tint compounds
  multiplicatively across every crossing, crushing to black well before any
  amount of added transparency or ambient light could compensate.

- **A Prerequisites table in the README**, and matching sections in
  `docs/install.md` for Blender/Cycles and PyMOL -- both had grown into core
  backends with zero install coverage in either doc.

- **`scripts/render_dna_helix_hologram.py`** -- a worked side-by-side of the
  Cycles and POV-Ray backends on one composed scene: a B-DNA double helix,
  built once as a `pv.Plotter` and rendered either directly (Cycles, via
  `render_cycles_quilt_from_plotter`) or re-expressed as analytic
  `Sphere`/`Cylinder` primitives sharing the plotter's own camera
  (`pov_camera_from_plotter`) and a `lights_from_bounds` rig (POV-Ray, via
  `render_pov_quilt`). Referenced from `docs/cycles.md` and `docs/povray.md`.

- **Lighting rigs for the Cycles backend.** The `ensure_light` flag (added
  above, never released) grew into a `lighting` parameter on
  `render_cycles_quilt()` / `render_cycles_views()`: `"soft"` keeps the
  neutral world-plus-sun default, `"studio"` builds a camera-relative
  three-point rig (key/fill/rim area lights over a near-black world),
  `"sky"` lights with Blender's physical Nishita sky (sun over the
  camera's left shoulder), a `.hdr`/`.exr` path becomes an HDRI
  environment world, and `None` adds nothing. Rigs apply only to imported
  scenes with no lights of their own, never touch a `.blend`, and are
  scaled by the focal distance with wattage growing as distance squared,
  so apparent brightness is invariant under scene scale. Constants were
  tuned against rendered output (the sky preset's sun rotation semantics
  were established empirically -- four candidate azimuths rendered and
  compared).

- **A PyVista bridge for the Cycles backend.**
  `render_cycles_quilt_from_plotter()` is the hardware-ray-traced sibling of
  `render_quilt()`: the same composed `pv.Plotter` in, the same quilt out,
  the same FOV/dolly convention -- but the views are path-traced by Cycles
  instead of rasterised by VTK, and the plotter is read, never mutated or
  rendered, so it works on headless machines with no GL stack at all.
  Behind it, `export_plotter_gltf()` pins the export settings the
  coordinate contract depends on (`rotate_scene=False`, because the Y-up
  rotation VTK otherwise bakes has varied across versions; Blender's
  importer then lands a VTK point `(x, y, z)` at `(x, -z, y)`, verified
  against imported geometry) and `cycles_camera_from_plotter()` translates
  the plotter's camera through that same rotation. Scalar-mapped colours
  survive the hop as a baked base-colour texture. The end-to-end test
  drives a real plotter through export, import and a Cycles render and
  asserts the focal-plane marker stays pinned -- the invariant a wrong
  coordinate hop breaks while every individual frame still looks right.

- **A third rendering backend: Blender Cycles, with hardware ray tracing
  where the GPU offers it.** `quiltwright.cycles` renders `.blend` files and
  mesh formats (glTF/GLB, OBJ, STL, PLY, USD, FBX, Alembic) into quilts and
  view sweeps through `render_cycles_quilt()` / `render_cycles_views()`,
  mirroring the POV-Ray backend's API. Cycles' Metal device runs
  ray/triangle intersection on Apple Silicon's ray-tracing cores (M3+), with
  OptiX/CUDA/HIP/oneAPI tried in turn elsewhere and CPU as the fallback --
  and unlike POV-Ray's one-parse-per-view, the whole sweep runs in a single
  Blender process with the BVH held across views (`use_persistent_data`).
  `CyclesCamera` is the right-handed Z-up twin of `PovCamera` (same
  `fov`/`focal_distance` surface, so `format_depth_budget` and `Clearance`
  apply unchanged), or pass `camera=None` to adopt a `.blend`'s own active
  camera with the focal plane taken from its DoF focus distance. The
  off-axis shear is expressed through Blender's camera shift, mirroring
  `BKE_camera_params_compute_viewplane`'s sensor-fit rules exactly --
  including AUTO fit sizing the sensor off `sensor_width` even when it
  resolves vertically -- because the naive reading of the docs pins nothing:
  every branch is guarded by end-to-end tests that render emissive markers
  at known depths and assert the focal-plane marker stays put across the
  sweep. Imports with no lights get a neutral world and a sun by default
  (`ensure_light=False` to opt out), since an unlit scene path-traces to
  black; a `.blend` is never touched. The end-to-end tests run against a
  real `blender` binary or, for CI, any interpreter carrying the `bpy`
  wheel via `QW_BPY_PYTHON`. Documented in `docs/cycles.md`.

### Fixed

- **Every POV-Ray colour in the package rendered 2-3x too bright.** No
  scene ever declared `assumed_gamma`, so POV-Ray 3.7 treated colours as
  already-linear light and gamma-encoded them again on output: `#1a1a1e`
  (26, 26, 30) rendered as (90, 90, 96). `assumed_gamma 1.0` -- POV-Ray's
  own fallback when nothing is declared, and what this package's test
  fixtures already used -- turned out to be a no-op, identical to declaring
  nothing at all; `2.2` overshoots, since a pure power-law gamma isn't the
  piecewise curve real displays use. `PovScene` now declares
  `assumed_gamma srgb`, POV-Ray's name for that exact curve, verified by
  round-tripping `#1a1a1e` back out of a render pixel for pixel.

- **`quiltwright.cycles`'s OBJ import turned the mesh 90 degrees against its
  own camera.** Blender's `wm.obj_import` defaults to remapping the
  Wavefront convention (Y-up) onto its own Z-up world; every OBJ this
  package writes (`cartoon_obj()`) is already Z-up, so the remap turned it
  sideways -- a beta barrel came out viewed down its pore instead of from
  the side. Fixed by importing with `forward_axis="Y", up_axis="Z"`, an
  identity transform, confirmed against Blender's full 30-combination axis
  matrix.

- **A failed PyMOL export surfaced as a bare `FileNotFoundError` on
  `body.pov`, many frames away from the actual cause.** PyMOL's `-cq` batch
  mode logs a bad `cmd.load`/`cmd.show`/selection and keeps going rather
  than raising, so a bad path or selection exited `0` with nothing written.
  `_run_export()` now checks that PyMOL actually wrote its expected output
  and raises with PyMOL's own traceback attached when it didn't.

- **Run reports recorded a warning where the POV-Ray build should be.**
  `povray_version()` read the first line of `--version`, but POV-Ray emits
  startup warnings ahead of its banner: on a box with no
  `~/.povray/3.7/povray.conf` the field came out as "povray: cannot open the
  user configuration file ...". The warning is harmless -- POV-Ray falls back
  to built-in defaults and renders normally -- but a provenance header that
  reads like an error is worse than one reading `unknown`. The banner is now
  matched by its own prefix rather than by position.

## [0.8.0] - 2026-08-24

### Added

- **A standard museum vitrine -- a stone plinth under a bell jar, lit like an
  exhibit -- for any molecule at all.** `scripts/render_vitrine.py` normalises
  the molecule to a unit sphere using the enclosing radius `pdb2pov` already
  writes into every file, so one camera and one depth budget serve GFP (31.2 A),
  hemoglobin (40.3 A), OmpF (51.0 A) and F1-ATPase (79.0 A) with no per-structure
  tuning. The bell jar and the plinth taper are both derived from that same
  radius, so neither can clip a structure the enclosing sphere describes
  correctly. Alongside it: a 2026 museum cut composed for a 16:9 panel rather
  than 10x8 paper, a metallic plaque wrapped round the plinth shaft, and
  `gallery/` moving to the repository top level -- it is presented work, not a
  build artefact, and living under `renders/` (which otherwise holds only
  output) made it look like one.

- **`quiltwright cartoon` -- Richardson cartoons through the same pipeline as
  every other exhibit.** `pdb2pov` has emitted atoms and bonds since 1993 and
  nothing else; the archive's one ribbon-cartoon image survived from a 1993-94
  mesh exporter whose output exists nowhere in any repository. `cartoon_inc()`
  now writes an object-only include on the same contract `pypdb2pov` writes --
  origin-centred, `<name>_enclosing_radius` alongside it, no camera, no lights
  -- so `render_pov_quilt`, `PovCamera` and the vitrine need no changes at all
  to mount one. Getting there needed a `mesh2` emitter povgen never had (Mesh2
  honours the flip-z winding contract explicitly, since a wrong triangle
  orientation lights a mesh from behind in a way that reads as a lighting bug)
  and a coalescer for PyMOL's `cmd.get_povray()`, which emits one `mesh2` per
  triangle -- OmpF arrives as 75,792 separate meshes and 41 MB and leaves as
  one mesh and single-digit MB, re-parsed 48 times per quilt otherwise.

- **`scripts/make_exhibit.py` -- fetch, convert, compose, render, sweep, in one
  command.** `python scripts/make_exhibit.py 7AHL --label "ALPHA-HEMOLYSIN"
  --quilt` replaces what used to be a `curl -O` into whatever directory you
  happened to be standing in. Structures land in `$PDB` (default `~/pdb`), the
  convention proteusPy already follows, so a file fetched for one tool is
  there for the next. Assembly 1 (the biological unit, not the deposited
  asymmetric unit) is the default, since nothing in a PDB file says the
  asymmetric unit is a fraction of the molecule -- ferritin's is a 24th of a
  ferritin. `--rep atoms` goes through `pypdb2pov`; every other representation
  through PyMOL, and the composed scene does not care which, because both
  write the same object-only contract.

- **The `molecules` extra.** `pip install "quiltwright[molecules]"` now
  resolves from PyPI now that `pypdb2pov` is published there, and
  `render_vitrine.py` asks the installed package for its include directory
  (`pypdb2pov.include_dir()`) instead of a machine-local path that was only
  ever true on the machine it was written on.

### Fixed

- **The `molecules` extra now floors at `pypdb2pov>=0.1.1`.** `0.1.0`'s
  published PyPI metadata reports `GPL-2.0-or-later`; the project is actually
  BSD-3-Clause, and PyPI metadata is immutable per release, so the only way
  not to hand someone the mislabelled release is to refuse to resolve to it.
- Release headings in this changelog used an inconsistent dash separator, so
  `fleet_audit.py`'s parser -- which expects `## [x.y.z] - YYYY-MM-DD` --
  silently matched fewer releases than actually shipped. Normalised to one
  hyphen throughout.

## [0.7.0] - 2026-08-18

### Added

- **`quiltwright cast`, `wallpaper` and `bridge` -- the CLI now covers the whole
  tail of the pipeline.** Everything downstream of the assembler operates on a
  quilt, so none of these care which backend produced the views.

  `cast` shows a saved quilt on the panel, recovering the tiling and aspect
  from the `_qs<cols>x<rows>a<aspect>` filename suffix so it usually needs no
  flags. `cast --check` lists what Bridge can actually see, and marks which
  heads are Looking Glass panels rather than ordinary monitors -- Bridge
  enumerates both, and a cast landing on a laptop screen is silent. `--head`
  pins the target; `cast_quilt()` gained a `head_index` parameter to carry it,
  defaulting to the previous `-1`.

  `wallpaper` completes the no-Bridge path: a woven frame is already
  interleaved for one panel, so setting it as that panel's desktop picture
  makes the desktop a hologram with nothing running. It matches frame to
  display by the panel serial both carry -- macOS reports each desktop's
  `display name`, which for a Looking Glass is its serial -- and refuses to
  guess when no desktop matches, because a woven frame on the wrong panel is a
  screenful of noise. Frames are copied into `~/Pictures/LKG-wallpapers/`
  first: macOS stores wallpaper as a *path*, so pointing the desktop into
  `renders/` blanks the panel the next time that directory is cleaned. Where
  the destination is already the current picture -- the re-weave case -- it
  bounces off another image first, because macOS caches by path and would
  otherwise keep showing the old pixels, which looks exactly like a weave that
  failed.

  `bridge status` and `bridge reset` exist because Bridge is the one component
  here that fails *dishonestly*. It keeps its HTTP port open and keeps issuing
  valid orchestration tokens after crashing internally, so a cast reports
  success at every step against a daemon that will never draw a pixel -- an
  hour of this session went into a black panel that was exactly that. `status`
  therefore distrusts a bare 200: it walks port, session, device enumeration
  and whether any device is a panel at all, then gives a verdict and a matching
  exit code, so it can gate a cast in a script. `reset` kills every Bridge
  process and relaunches, which is the only fix -- Bridge's own menu restart
  spawns a replacement that inherits the wedge.

- **Run reports -- `quiltwright.runreport`, and `--report` on both render
  scripts.** A quilt is a 25-40 MB PNG carrying nothing that says where it came
  from, and it is gitignored, so six months on the questions that matter are
  unanswerable from the file. Every full quilt from `make` now writes a
  Markdown provenance record to `renders/reports/`, which *is* committed.

  The header follows the fleet's convention (`_waverider/benchmarks/`):
  generated-at, machine, repository and commit, interpreter and tool versions,
  host, OS, and the exact command line. Two additions are specific to
  rendering. The scene file is hashed, not just named, because composing a
  scene means rendering against an edited working copy -- the commit alone can
  describe a tree the render never saw, and the header says `+ uncommitted
  changes` when that is the case. And the output's own SHA-256 is recorded,
  because a report is only evidence if it can be tied to one particular file.

  The body carries the run configuration, the camera and its *measured* near
  and far depths, the depth budget embedded verbatim as printed rather than
  recomputed, the parallelism actually used, and timings. That parallelism
  section resolves what the command line does not show: `--jobs` is POV-Ray
  *processes*, while threads per process come either from the `+WT` the
  renderer derives above one job, or from the `Work_Threads` in whatever INI
  `POVINI` names, or from POV-Ray's own all-cores default.

- **`bell_jar/bj_holo.pov` and `bell_jar/bj_portrait.pov` -- the DNA still life
  recomposed for a light-field panel, 16:9 and 9:16.** `bj.pov` puts its title
  and signature 70-74 units from the eye, in front of its own 72-unit near
  bound: they are camera-pinned overlays, so on a Looking Glass they float off
  the glass instead of sitting in the scene, and the title drags a mirrored
  copy through the water. Both new cuts move the lettering out to scene depth --
  the title onto the focal plane, the signature as close to it as the
  composition allows -- placed by projecting back from the frame rather than by
  eye, with the arithmetic written into each file. `bj.pov` is untouched and
  keeps its 1997 3:4 composition.

  Each needed its lens opened, for a different reason, and neither was
  discretionary. `bj.pov`'s framing has no sky: the jar and pedestal fill 91%
  of the frame height, leaving 29 pixels above the dome in a 1080-line render,
  so a title set above the glass could be at most ~20 pixels tall. 55.32
  degrees vertical with the aim raised to y=20.95 redistributes that slack to
  90 above and 54 below, at a cost of 4.6% of the subject's size. The portrait
  cut is bounded by width instead -- the pedestal's 32.5-unit radius overruns a
  9:16 frame outright -- so 65.92 degrees is what puts the base 69 pixels clear
  of each side.

  Two details are worth recording because guessing them wrong is easy. An
  ellipsoid seen from a pitched camera silhouettes at its *tangent point*, not
  its apex: the dome tops out 90 pixels down the 16:9 frame at y=60.27, z=-1.90,
  three units nearer than the apex, and that tangent is what the title has to
  clear. And anything sitting near the waterline projects *higher* in the frame
  the further out it is, so a signature cannot be both low in frame and on the
  focal plane -- 82 in the landscape cut is what drops it to the corner, a
  third of a pixel of parallax off zero.

  Both are driven by `render_still_life_hologram.py` as `bell-jar-holo` and
  `bell-jar-portrait`, with `make` targets to match, and both swept for their
  own depths rather than inheriting `bj.pov`'s. Neither bound comes out of the
  sweep unedited. The far end is the knee, as for every scene here: the sea
  never closes, so 0.133%/unit of backdrop creep off a 25.8% subject puts 95%
  of it in by 129 (landscape), 0.071%/unit off 50.4% by 113 (portrait). The
  portrait's near needed the same treatment at the other end -- its lens looks
  40.8 degrees down at the frame's lower rim, so the sea arrives there at 61,
  well in front of the subject, and buying zero parallax for a strip of
  foreground water would push the jar itself off the glass. Both cuts come out
  ahead of the existing `bell-jar` entry on disparity, 2.61 px and 1.86 px at
  the bounds against its 2.77 px.

- **`quiltwright.weave` -- pre-lensed native frames, no Bridge required.** The
  panel's lenticular sheet is a passive optic: anything that puts the correctly
  interleaved subpixels behind it fuses into a hologram, including the macOS
  wallpaper engine. `weave_quilt(quilt, spec, cal)` is a NumPy port of Bridge's
  `Lenticular_RGBA_With_Aspect` shader (nearest-view mode) that turns a quilt
  into a native-resolution image registered to one specific display; set it as
  that display's desktop wallpaper and the desktop is a static hologram -- OS
  wallpaper slideshows become hologram slideshows, with no Looking Glass
  software running at all. `Calibration.load()` reads the device's
  `visual.json` verbatim, `{"value": ...}` wrappers and all, and implements
  both calibration generations: the classic third-of-a-pixel RGB stripe and
  the configVersion 3.0 `subpixelCells`/`CellPatternMode` layouts of gen3
  panels, which put R and G on one row and B on the other and mirror between
  columns. Applying the classic formula to a gen3 panel misregisters 80% of
  subpixels on LKG-J00332, by a median of 2 views and at most 6 of 48 -- and
  by a different amount per channel, which is what turns it into colour
  fringing. The port is
  pinned by a scalar transliteration of the shader in the test suite and by
  `ProcessPitch`/`ProcessSlope` values cross-checked against LKG-Toolkit;
  registration was verified by eye on a real 16" Landscape (LKG-J00332),
  st-helens and porin quilts fusing as wallpaper on the first try.

- **`ty` type checking, in CI and pre-commit.** Astral's checker joins the dev
  group and gates `src/` in both places. Turning it on surfaced 17 diagnostics,
  all fixed below; it now runs clean in 0.24 s, which is fast enough to sit on
  every commit.

- **A pre-commit configuration.** Ruff, `detect-secrets` against a new
  `.secrets.baseline`, `ty`, and the standard hygiene hooks. Two adaptations
  matter for this repo. `pov-scenes/` is excluded wholesale: it is a 1995-1999
  archive, and `README.md` and `docs/about-the-image.md` both rest on the claim
  that Quiltwright ray-traces those files unmodified -- left in, the whitespace
  hooks rewrite 60 of them for 2624 insertions and 2713 deletions of no
  functional change. And `pytest` runs at `pre-push` rather than `pre-commit`,
  because the suite takes 61 s: it ray-traces with POV-Ray and drives a real GL
  context, and a minute per commit invites `--no-verify`, which would skip the
  fast hooks too.

- **A `quiltwright` console script, and `quiltwright weave` as its first
  command.** Weaving a wallpaper had meant hand-writing a script per quilt;
  `quiltwright weave scene_qs8x6a1.77778.png --cal visual.json` does the same
  job from a shell, recovering the tiling grid from the Looking Glass filename
  suffix when `--preset`/`--grid` are not given, and naming the output
  `<stem>_native_<serial>.png` by default. Built on click, matching every
  other repo in the fleet, which moves core's dependency footprint from numpy
  and pillow to numpy, pillow and click.

- **`lint`, `type-check` and `core-install` jobs in `tests.yml`.** The first two
  split work the test matrix was repeating once per interpreter. The third is
  new coverage: `pyproject.toml` keeps core to numpy, pillow and click so a
  machine that only casts pre-rendered quilts stays lean, and that holds only
  while the seven `import pyvista` sites in `__init__`, `lfd`, `hld` and
  `tvb_data` stay inside functions. Nothing else could see one move to module
  scope -- every
  other job installs `[viz,video]`, and the tests use
  `pytest.importorskip("pyvista")`, which skips when PyVista is missing rather
  than asserting it is unused. The gate was verified by hoisting an import and
  confirming it fails.

### Changed

- **The CLI is a package of `cmd_*` modules, matching the fleet.**
  `quiltwright/cli.py` becomes `quiltwright/cli/`, with a root group in
  `main.py`, shared option handling in `options.py`, and one module per
  command -- the layout `doc_kg`, `pycode_kg` and `gutenberg_kg` already use.
  The console-script entry point moves from `quiltwright.cli:main` to
  `quiltwright.cli.main:cli` accordingly.

  This is not only tidiness. Adding three commands touched no existing command
  code, and each module now carries its own hard-won knowledge in its docstring
  -- the three ways Bridge fails on real hardware, the macOS wallpaper path
  cache -- which in a single module either bloats one docstring or is dropped.
  Splitting also surfaced that `cast` needs the tile *aspect* from the
  filename, not just the grid, so `aspect_from_filename()` is shared rather
  than duplicated.

- **The README no longer describes Quiltwright as the tail of two specific
  pipelines.** The opening said it "takes scenes that already exist -- geometric
  ML manifolds from WaveRider, molecular structures from pdb2pov", which reads
  as a list of what it accepts rather than of who uses it. It accepts any
  PyVista/VTK scene in memory and any POV-Ray scene on disk, including files
  written decades ago by tools that no longer exist; WaveRider and pdb2pov are
  users, not prerequisites. Two further passages carried the same exclusivity
  and now say the same broader thing, matching the diagram above them, which
  was already labelled by backend.

  The README also gains a section on driving the whole thing from a shell --
  `make` for the bundled POV-Ray archive, the CLI for the stage after the
  assembler -- and `Latest news` is trimmed to the current release, since the
  older entries duplicated the changelog linked directly beneath them.

- **The 1993-96 copyright notice in `pov-scenes/bell_jar/` reads as written.**
  `it's resulting derivative images` and `all neccessary data files` are fixed
  to `its` and `necessary` across the 12 files carrying the notice. Comments
  only -- no geometry, camera or texture line moved, and every scene was
  re-parsed to confirm it. The two new scenes carry `(c) 1993-1996, 2026`: the
  earlier term covers the model and the still life they inherit, the later one
  the composition, which is new.

- **`docs/pdb2pov.md` covers `pypdb2pov`, the Python port of pdb2pov**, which
  writes byte-identical scenes from the same flags and is importable, so a
  conversion and a `render_pov_quilt()` call now fit in one script instead of
  a shell step and a file to scrape. The page gains a "Choosing one" section,
  the port's extra flags, and a worked example that goes from a compressed
  mmCIF straight to a saved quilt.

  Three things in the example were previously left implicit and are now
  written out. An `-o` include *declares* -- no camera, no lights, no
  `object { }` -- so the host scene supplying all three is spelled out rather
  than described. `include_dir()` gives `include_paths` a real path instead of
  `"path/to/pdb2pov"`. And `structure.enclosing_radius()` is the *unpadded*
  radius: the header comment and the emitted float carry it grown by 2%, so a
  depth budget built from the method without that factor is 2% short at both
  ends.

- **The alternate-conformation guidance is no longer just "the A conformer".**
  1CBN -- crambin, the molecule the page uses throughout -- is the counterexample:
  fourteen atoms carry only altLoc `C` and vanish under the blank-or-`A` rule,
  and residue 22 is modelled as both serine and proline at one sequence
  position. The page now documents `--altloc {a,first,occupancy,all}` and why
  the choice has to be made per residue rather than per atom.

- `docs/install.md` and the README name mmCIF alongside PDB, and offer the
  `pip install ./pdb2pov/python` route beside the `make` one. The port's
  command is `pypdb2pov`, so it and the C binary can share a `PATH`.

- **`povgen` and `povray` now say what they accept.** Signatures throughout
  `povgen` declared `Sequence[float]` for 3-vectors, but a NumPy array is not
  one -- it is not registered with the ABC, and its elements are `np.floating`.
  Every geometry engine the module consumes emits arrays, and the functions
  always accepted them, so the annotations understated the API rather than
  describing it. A `Vec` alias now covers both spellings. In `povray`, a
  `_triple()` helper replaces `tuple(...)` where a `PovCamera` coordinate is
  required, since `tuple(iterable)` types as `tuple[float, ...]` and states no
  arity. No runtime behaviour changes; 325 tests pass unchanged on 3.12 and
  3.13.

### Fixed

- **A render started outside `make` took every core on the machine.** POV-Ray
  threads one render across all of them, and neither existing guard applied at
  the documented `jobs=1`: the `+WT` split only happens above one process, and
  the `Work_Threads` cap lives in an INI that only the Makefile writes. So
  `make quilt-museum` held two cores back and
  `python scripts/render_museum_hologram.py` did not -- same render, same
  machine, silently different manners.

  `resolve_work_threads()` now applies a courtesy cap of `cpu_count - 2` when
  nothing else has spoken, and both render scripts take `--threads` (with `0`
  meaning "take everything", POV-Ray's own default). The condition matters more
  than the cap: a command-line `+WT` overrides `POVINI` outright, so capping
  unconditionally would have silently defeated
  `make quilts RENDER_THREADS=$(nproc)` -- the documented way to *use* the whole
  box. The cap therefore yields to a `Work_Threads` line, and to any `+WT` the
  caller passes itself. Run reports read the same resolver, so the recorded
  parallelism cannot disagree with what was run.

- **The DOI badge, which was blown on the GitHub front page.** GitHub proxies
  README images through `camo.githubusercontent.com`, Zenodo rate-limits camo,
  and camo served `502 Invalid upstream response (429)` to every reader.
  Fetching the badge directly returned a healthy `200`, which is why it went
  unnoticed. The image now comes from shields.io; the DOI and the `doi.org`
  link target are unchanged, and `10.5281/zenodo.21798503` was confirmed
  against the live record as the concept DOI.

- **The README hero image, which did not render on PyPI.** Repo-relative image
  paths break wherever the README is re-hosted. It is now pinned to
  `raw.githubusercontent.com` at `v0.6.0`, and switched from the 1280×720
  centre view of the quilt to `renders/stills/museum.png`, the full-quality
  1920×1080 canonical cut. **This line carries the version and must be bumped
  at release**: a stale pin keeps serving the previous release's image at
  `200 OK` rather than breaking visibly.

- **`docs/povgen.md` missing from the README documentation table** since it
  shipped in 0.5.0, and `save_and_cast_quilt` missing from Quick start since
  0.6.0.

### Removed

- **Three reference stills, and the targets and gallery entries behind them.**
  `porin_3porin2.png` was blank -- `3porin2.pov` is the stock POV-Ray "Basic
  Scene Example" template with `#include "3porin.inc"` appended, and that
  include only `#declare`s `porin`, so nothing instantiates it and the frame is
  sky and ground plane. `museum_dark.png` and `museum_worldmap.png` render
  fine and are dropped by choice. All three scenes stay in `pov-scenes/`;
  `renders/README.md` now says which are absent because they cannot render and
  which are absent because they were not wanted.

- **Four tags inherited from WaveRider** -- `v0.10.0`, `v0.10.1`, `v0.11.0`,
  `v0.12.0` -- deleted locally and on `origin`. Quiltwright was carved out of
  WaveRider in place and the version reset to `0.1.0`, so those pre-fork tags
  stayed in the namespace with higher numbers than any real release:
  `git tag --sort=-v:refname | head -1` answered `v0.12.0` instead of `v0.6.0`.
  No commit was orphaned -- all are reachable from `main` -- and no GitHub
  Release was attached. The fork itself is still marked by commit `70e703f`.

## [0.6.0] - 2026-08-16

### Added

- **`save_and_cast_quilt()` -- write a quilt, then hand Bridge the path to it.**
  `save_quilt` takes the array and `cast_quilt` takes a path, and confusing
  them is invisible until a display is connected: the caster raises
  `argument should be a str or an os.PathLike object ... not 'ndarray'`, which
  for a ray-traced quilt arrives minutes into the render. Composing the two
  correctly is now a single call.

  It confirms the file is on disk before contacting Bridge, and *returns* a
  failed cast as `(path, error)` rather than raising, so a Bridge that isn't
  running never costs the render. Consumers had been writing this wrapper
  themselves; `gutenberg_kg` had it as a private helper with the ndarray
  mistake documented in its docstring.

- **`QuiltSpec.scaled()` -- shrink a quilt without breaking its tiling.**
  Casting at full preset size costs little to render but a lot to load:
  Bridge's load time scales with PNG area, so halving the linear size
  quarters it. Scaling naively breaks the tiling -- the quilt stops dividing
  evenly into the view grid and every view lands on a fractional pixel
  boundary, smearing the light field. `scaled(factor)` rounds the new
  dimensions down to a multiple of the tile grid so the views stay
  pixel-aligned, and raises rather than returning a spec too small to hold
  one pixel per tile.

## [0.5.0] - 2026-08-16

### Added

- **`quiltwright.povgen` -- write POV-Ray scenes from analytic primitives.**
  The package had two backends that never met: `lfd` sweeps a live
  `pv.Plotter`, `povray` sweeps a `.pov` file on disk. `povgen` produces the
  second from the first, so a scene composed in Python can be ray-traced
  instead of rasterised by VTK.

  It re-emits *intent* rather than dumping triangles. A `pv.Plotter` holds
  tessellated geometry -- `pv.Sphere` is a triangulated ball, a swept tube is a
  strip of quads -- and a `mesh2` dump of that keeps VTK's facets while costing
  a great deal of text, re-parsed once per view, 48 times for a Portrait
  quilt. A limb is instead a `sphere_sweep` and a leaf a `sphere`. Measured on
  a 3000-leaf organic tree (192k triangles once tessellated): 839 KB of
  analytic SDL against roughly 12.5 MB for the equivalent `mesh2`, 15× to 25×
  smaller depending on how much per-leaf orientation is kept -- and with exact
  silhouettes at any zoom, which is the reason to leave VTK in the first
  place.

  Exports `PovScene`, `Texture`, `Finish`, `LightSource`, the primitives
  `Sphere` / `Cylinder` / `Box` / `SphereSweep` / `Union` / `Instance`, the
  bulk constructors `sphere_sweeps_from_paths` / `spheres_from_points` /
  `instances_from_frames`, and the helpers `to_pov`, `parse_color`,
  `lights_from_bounds`, `pov_camera_from_plotter` and
  `fov_horizontal_to_vertical`. `mesh2` remains unimplemented, as the fallback
  for geometry with no analytic description.

  Four decisions that are easy to get wrong and are made for the caller:

  - **Handedness.** PyVista, VTK and NumPy are right-handed and POV-Ray is
    left-handed, so scenes are authored right-handed and `z` is negated on
    emission -- applied to the camera as well as the geometry, so the image
    matches the PyVista render rather than mirroring it. Box corners are
    re-sorted and `Instance` rotations conjugated by the reflection.
  - **No camera is emitted.** `render_pov_quilt` appends one off-axis camera
    per view and POV-Ray uses the last one parsed, so a camera written here
    would be silently overridden. `pov_camera_from_plotter` carries the
    viewpoint across instead; VTK's `view_angle` and `PovCamera.fov` are both
    *vertical* degrees, so the lens maps one-to-one.
  - **Opacity becomes `transmit`, not `filter`.** `transmit` passes light
    through unchanged, which is the analogue of VTK's alpha; `filter` tints
    everything seen through the surface and would quietly recolour the scene.
  - **`SphereSweep` defaults to `linear_spline`,** which interpolates its
    control points, because callers hand over paths that have already been
    smoothed and a second approximating spline would pull the surface off the
    geometry PyVista tubed.

- **`tests/test_povgen_parity.py` -- dual-render verification.** Renders the
  same scene through both backends at a matched camera and compares
  silhouettes, with flat emissive surfaces so the comparison isolates geometry
  from the two renderers' different lighting models. Measured agreement on the
  reference scene is IoU ≈ 0.95 with identical silhouette bounding boxes; the
  residual is antialiasing at the rim.

  The fixture is deliberately asymmetric in depth, because a scene straddling
  the focal plane renders almost identically whether or not `z` was flipped
  and so cannot detect the most damaging bug the module could have. One sphere
  sits well in front of the focal plane and another well behind it at the same
  radius, so mirroring depth swaps which one perspective makes larger and IoU
  collapses to ~0. Confirmed by mutation rather than assumed -- reverting the
  flip fails five parity tests, and one test tilts the camera specifically
  because every other one leaves `up` at `(0, 1, 0)`, whose `z` is zero, where
  a bridge that forgot to convert `sky` passes unnoticed.

- **`docs/povgen.md`** -- the transcoding guide, including the gotcha list and
  the mutation-testing table.

- **`swept_scene` and `instances_by_color` -- the composer that makes a new
  consumer cheap.** Named for its geometry rather than for any subject: it
  knows swept tubes, oriented instances and scattered spheres, and nothing
  about what they depict. A tree is one caller -- limbs, leaves, annotation
  clouds -- but so is any producer with the same three shapes, and the name does
  not mislead a future one.

  What it saves is not the primitives, which were already here, but the
  assembly: prototype declaration, colour grouping, light rig, floor, and the
  order those go in. **Lights are placed before the ground**, which is the one
  piece of that order a caller cannot guess: the rig is sized from the scene
  bounds and the floor is wider than the subject, so measuring after laying it
  makes the "scene radius" the slab's half-diagonal, pushing the key light far
  enough out to flatten the subject and shrink its shadow to nothing. The
  failure is silent -- the scene is structurally perfect and looks dead.

  `instances_by_color` is the grouping on its own, for callers composing by
  hand: a crown of ten thousand blades in five colours becomes five textures
  and five unions, not ten thousand of each.

  `lights_from_bounds` gains `rim=` for the dim back light that separates an
  intricate silhouette from a dark background. Off by default; it is wasted on
  a solid form against a bright ground.

  `lights=False` leaves the rig out for a caller supplying its own; the scene
  then renders black, so it is not a default anyone reaches by accident.

  `lights_from_bounds` gains `key_side=` -- the direction from the subject
  toward the side the key should come from, normally the camera's own standoff
  direction. Bounds cannot supply it, and the side derived from `up` alone is
  `+y` for a `+z`-up scene, which is the far side from a
  `kg_utils.viz3d.frame_tree` camera. Left unsaid, the rig lights the back of
  the subject and the lens looks at its shadow: the scene is structurally
  perfect, every assertion passes, and the render is merely dark. The old
  advice for this case was "place your own lights", which is what
  `gutenberg_kg` had been doing and what removing its copy re-exposed. Only
  the component across `up` is used, so passing a camera direction chooses a
  side without also re-deciding the key's elevation. `swept_scene` forwards it.

  A test asserts that importing `povgen` pulls in no `kg_utils` and no KG
  package. The seam is arrays in both directions, and it has to stay that way.

- **`ground_slab` and `pov_camera_from_frame`** -- the two pieces a caller with
  no plotter needs, and the reason `gutenberg_kg` had written its own.

  `ground_slab` puts a finite floor under a subject for it to cast onto. A
  contact shadow is most of what makes a subject look *placed* rather than
  floating, and it is something VTK cannot give at all -- its headlight casts
  nothing -- so a scene that looked fine rasterised looks untethered once
  ray-traced. Finite on purpose: an effectively infinite plane guarantees
  off-budget disparity at the horizon. Its top face sits at the subject's base
  along `up`, so the subject stands on the floor rather than hovering over one
  parked underneath, and its edge is a multiple of the subject's own width so
  one value suits any scale. `base=` overrides that level for callers whose
  bounds are not the subject: a swept tube's bounds are padded by its radius,
  so a trunk rooted at `z = 0` reports a minimum of `-r` and the floor sinks
  that much, leaving the tree standing in a shallow dish.

  `pov_camera_from_frame` is the sibling of `pov_camera_from_plotter` for
  callers that have no plotter -- a headless box writing `.pov` files with no
  VTK installed, which is this module's whole purpose. It accepts three
  sequences or any object carrying `.position`, `.focal_point` and `.up`, which
  is what `kg_utils.viz3d.frame_tree` returns; duck-typed deliberately, since
  this package does not import that one and must not. A test asserts both
  bridges land on the same convention, because two camera paths that disagree
  is precisely the bug this replaces: an unconverted camera aims at empty space
  while every assertion comparing right-handed to right-handed passes.

- **`lights_from_bounds` takes `up`.** Its offsets place a key light "above
  and to the right," and *above* was hard-coded to `+y`. That is right for a
  VTK scene and wrong for a `+z`-up one -- which is what `kg_utils.viz3d`
  builds, and that package is this module's headline consumer. Left at the
  default there, the key light lands at `centre_z - 1.4·radius`: below the
  ground, lighting the subject from underneath.

  `up` defaults to `(0, 1, 0)`, so every existing caller is byte-for-byte
  unchanged and a test pins the old offsets exactly. Only the up axis is
  inferred -- which side counts as "front" cannot be derived from `up` alone,
  and the docstring says so rather than guessing.

### Changed

- **`povgen` no longer pulls in the rendering stack.** It is documented as
  NumPy-only and genuinely is, but it could not be *imported* without VTK: the
  package `__init__` re-exported `lfd` eagerly, `lfd` imports PyVista whenever
  it is installed, and `povgen` itself imported `povray` at module scope for
  `PovCamera` -- and `povray` imports `lfd`.

  `__init__` now binds its re-exports lazily (PEP 562) and `povgen` defers the
  `PovCamera` import into `pov_camera_from_plotter`, the only function that
  builds one and which has a live plotter by definition. The public API is
  unchanged; a test walks `__all__` to prove every name still resolves, and
  another asserts in a subprocess that importing `povgen` touches neither
  `pyvista`, `lfd`, nor `povray`.

### Fixed

- **`PovCamera` is documented as holding POV-Ray coordinates.** It predates
  `povgen` and is never converted -- only `pov_camera_from_plotter` runs
  `to_pov`, and `camera_block` emits whatever it is handed. Three places said
  otherwise: the class docstring's "in scene units", the `povgen` module
  docstring's "the conversion is applied to the camera as well as the
  geometry", and `docs/povgen.md` section 1, which built a camera by hand directly
  above the line "Coordinates are written right-handed".

  A consumer read that, framed in the scene's right-handed world, and got an
  immaculate render of empty space -- geometry at negative `z`, lens aimed at
  positive `z`, and every assertion comparing the camera against the bounds it
  was derived from passing. The section 1 example could not have caught it either:
  its ball sits at the origin, so `z` is zero and the flip is invisible, the
  same vacuous-fixture trap the parity fixture above was rebuilt to escape.

- **`PovScene.bounds()` says what it misses.** That `Instance` is skipped was
  documented; what that costs was not, and instancing is simultaneously what
  `bounds()` cannot see and the reason to use this module. A tree escapes it
  by construction -- its swept wood is measurable and reaches the crown -- but a
  scene whose subject *is* the instances measures as whatever prop happens to
  be a real primitive, so lights placed from those bounds sit inside the scene
  and a camera framed from them fills the tile with the prop. Both escape
  hatches are now written down, and a test demonstrates the narrow bounds and
  then the untextured `Box` that widens them.

## [0.4.0] - 2026-08-14

### Added

- **`depth_report()` and `scene_depths()` -- the depth budget for a PyVista
  scene.** `format_depth_budget()` has always done the arithmetic, but it
  takes a `PovCamera`, so every PyVista caller had to measure the scene by
  hand and then build a throwaway POV-Ray camera purely to carry a FOV and a
  focal distance. Two separate downstream consumers each wrote that same
  forty-line helper. `depth_report(plotter, spec)` replaces it: it reads the
  plotter's bounds and camera, and returns the report.

  It also takes the `fov` and `zoom` you intend to pass to `render_quilt()`,
  and models them -- which the hand-rolled copies did not. `render_quilt()`
  narrows the FOV and dollies back before sweeping, so a budget measured from
  the plotter as-composed is computed at the wrong FOV *and* the wrong focal
  distance, and describes a picture nobody is going to make. On a torus at
  the default framing the two differ by about 15%; the direction depends on
  the scene, because the dolly-back partly offsets the magnification.

  `scene_depths()` exposes the measurement on its own for callers that want
  the numbers rather than the report, and `DEPTH_LABELS` supplies neutral
  defaults ("nearest geometry" rather than any one domain's vocabulary).
  Neither mutates the plotter.

### Changed

- **Python 3.13 is supported: `requires-python` is now `>=3.12,<3.14`.** The
  old `<3.13` ceiling had no recorded rationale and no dependency behind it --
  numpy, pillow and pyvista all support 3.13 -- but it forced every consumer
  on a `<3.14` project to declare quiltwright marker-gated
  (`"quiltwright>=0.3.1; python_version < '3.13'"`), because an unmarked
  declaration made Poetry reject the whole resolution. That marker can now be
  dropped. CI runs the suite on both 3.12 and 3.13, so the classifier is a
  tested claim rather than an assertion.

## [0.3.1] - 2026-08-10

### Changed

- **The README documents the LitiHolo sweep as a third output, marked in
  development.** The pipeline diagram gained a branch for it and a `view
  sweeps` line in the middle box; the column header reads "outputs" rather
  than "displays", since one target is not a display. A new *Send it to a
  hologram printer* section in the quick start runs `LITIHOLO_SWEEP` through
  `render_pov_views()` end to end, with `format_depth_budget()` printed first
  and what the museum actually reports at a 45° cone -- ~43 px of adjacent-view
  disparity against an ~8 px ghosting threshold, which is the report doing its
  job rather than an example worth copying unchanged.

  The narrow claim travels with it: what quiltwright emits is a sweep matching
  the published specification, not a verified printer input, and this path is
  POV-Ray only. Both links now point into the relevant sections of
  `docs/lfd.md` rather than at the top of the file.

- **README housekeeping the 0.3.0 release left behind.** The scene-source
  paragraph mentions `quiltwright.tvb_data` and the PyVista example datasets,
  which 0.3.0 added while the README still described only the two upstream
  pipelines. `docs/gallery.md` joins the documentation table -- nothing in the
  repository linked to it -- and the `docs/lfd.md` row names the view sweeps it
  covers.

### Fixed

- **The vendor's name is spelled LitiHolo throughout.** It appeared both ways
  across the README, `docs/brand.md` and this changelog; the company styles it
  with the capital H.

- **The coarse-sampling figure is 2.75×, not 2.7×.** 45° over 22 intervals
  against 35° over 47 is 2.747. The inputs -- 2.05° and 0.74° -- were already
  consistent in all four places that quote them; only the ratio was rounded
  down.

- **`render_pov_views()` no longer overstates what is known about hogels.** Its
  docstring asserted that a hologram's hogels are "no more forgiving than a lens
  sheet", while `docs/lfd.md`, `docs/povray.md` and `docs/pov-workflow.md` all
  hold that question open. The docstring now hedges the way the documentation
  does.

## [0.3.0] - 2026-08-10

### Added

- **`quiltwright.tvb_data` -- brain geometry from The Virtual Brain as a scene
  source.** Cortical surfaces, structural connectomes, parcellations and
  sensor positions, downloaded on demand and returned as NumPy arrays or
  PyVista meshes ready for the LFD and HLD backends.

  This sits alongside POV-Ray scenes and the PyVista example datasets as a
  *source* of geometry, not an output backend. It arrives here rather than in
  a consumer because the package already reaches for real subjects to put on
  a display -- `scripts/render_pyvista_hologram.py` downloads the Allen
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
  build stays exactly where it was -- in the optional `video` group, out of
  the default install. Downloading GPL data at runtime rather than shipping
  it is the same line this package already draws around ffmpeg.

  Covers 11 surfaces, 8 connectomes, 4 parcellations and 9 sensor sets:
  `load_surface`, `load_connectivity`, `load_region_mapping`, `load_sensors`,
  plus `surface_polydata` / `connectome_polydata`.

  The archive is not uniformly formatted, and each quirk is handled and
  tested. Most consequential: `cortex_2x120k` indexes triangles from 1 while
  every other surface indexes from 0, so loading it naively yields an index
  one past the last vertex -- a silently corrupt mesh rather than an error.
  Also absorbed: split hemispheres, folder-nested members, float-encoded
  indices, bz2-compressed members, and an empty vertex-normals stub.

  Full reference in [docs/tvb-data.md](docs/tvb-data.md).

  [tvb-doi]: https://doi.org/10.5281/zenodo.10128131

- **`quiltwright.cache`** -- one answer to "where do runtime downloads go",
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
  re-fetched -- the 10 µm template is well over a gigabyte, and this script
  has not been in a release, so anyone holding one has it from a local run.

## [0.2.0] - 2026-08-08

### Added

- **View sweeps, for consumers that are not a light-field panel**
  (`sweep_spec()`, `LITIHOLO_SWEEP`, `render_pov_views()`). A quilt's view count
  is `columns × rows`, so a rectangular grid cannot express a prime one -- and
  the LitiHolo desktop hologram printer's published input specification asks for
  23 viewzone images per hogel. A single row expresses any count at all:
  - `quiltwright.lfd.sweep_spec(n_views, view_cone, tile_width, tile_height)`
    builds a single-row `QuiltSpec`. The camera sweep is identical to a quilt's;
    only the packing differs. Raises `ValueError` below 2 views.
  - `quiltwright.lfd.LITIHOLO_SWEEP` -- 23 views across a 45° lateral field,
    horizontal parallax only, matching the printer's published specification.
    The per-view pixel size is *not* published, so 1600×2000 errs high
    deliberately: it comfortably exceeds the ~102×127 hogel grid of a 4×5-inch
    plate at 1 mm hogels, and downsampling is cheap where re-rendering is not.
    Aspect 0.8 is that plate in portrait; transpose for landscape.
  - `quiltwright.povray.render_pov_views()` writes `view000.png ... viewNNN.png`
    into a directory, view 0 leftmost, and returns the paths in view order.
    Identical camera geometry to `render_pov_quilt()` -- the same off-axis
    sheared frustum, the same focal plane on `look_at` -- minus the quilt
    assembly.

  What this establishes is that quiltwright **emits a sweep matching the
  published specification**, which is a narrower claim than compatibility: no
  file has been through the printer's software. Two questions stand between the
  two. Whether a hogel slicer expects the off-axis sheared frusta quiltwright
  renders -- unambiguously correct for a lenticular panel -- or the toe-in
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
  - `PovCamera.aimed()` -- adopts a scene's own eye, aim and lens, then moves
    the focal plane along the original aim ray and slides the eye laterally
    with the look-at point riding along, so the view direction is untouched.
  - `Clearance` -- the measured lateral corridor of an enclosed scene, with the
    recentring offset (`centre`), the widest cone that still clears the walls
    (`cone()`), and the check that a given quilt fits (`fits()`).
  - `sweep_extent()` -- half-width of the lateral eye travel a quilt needs, in
    closed form.
  - `depth_budget()` / `format_depth_budget()` -- adjacent-view disparity at
    labelled depths, as data and as a pre-render report that flags soft depths
    and warns when the sweep would leave the room.
- **Test suite for the Gen3 16" Landscape** (`TestSixteenLandscape`), the
  device these renders target. Pins the preset against the defaultQuilt Bridge
  reports, and covers the property that makes it the awkward one: its tiles are
  stored *anamorphically*, 960x720 holding a 16:9 view rendered 1280x720, so
  tile pixel aspect deliberately disagrees with view aspect. Also anchors the
  published museum depth budget (3.58 px near/far, 6.95 px sky) to this
  device's real 720 px tiles, and pins the cost of its native 50-degree cone.
- `docs/about-the-image.md` -- what the museum scene is, what is on display in
  it, and the pipeline behind it: the B-DNA under the left bell jar is pdb2pov
  output from 14 Mar 1997, and pdb2pov still builds. The narrative moved here
  out of the `render_museum_hologram.py` docstring, which is now four sentences
  about the camera, and out of `povray.md section 4`, which is now only the numbers.
- `scripts/measure_depth_range.py` -- measures a scene's depth range instead of
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
  quilts` -- now four rather than three. The scene was already a registered
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
  git -- 25-40 MB each -- and become release assets instead; `.gitignore` now
  ignores everything under `renders/` except the README and the stills.
- **`pov-scenes/lambda/`** -- the 1998 "Lambda Repressor" poster scene from the
  archive: the 1LMB PDB file, the mesh converted from it
  (`lambda_complex2.inc`), the main scene with its sea, sky and chrome
  titling, and the original render `.ini` files.
- **Test coverage for the Looking Glass Bridge transport layer**
  (`cast_quilt`, `pause_quilt`, `resume_quilt`, `stop_quilt`, `_bridge_post`,
  `_enter_orchestration`), previously untested. A `FakeBridge` stands in for
  `urllib.request.urlopen` and pins the endpoint sequence -- including that
  `stop_quilt` never calls `delete_playlist`, which hung Bridge 2.6.3 twice in
  testing and needed a `kill -9` to recover; that fix had rested on a commit
  message alone until now. Verified by mutation: reintroducing
  `delete_playlist` fails two tests with a legible diff. `lfd.py` coverage
  83% -> 94%.

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
  it -- and that default is what carries the `Library_Path` entries for the
  standard includes, so an INI containing only `Work_Threads` makes
  `colors.inc` unfindable and every stock scene fails to parse. The generated
  file is therefore a copy of the discovered default with the cap appended.
  And a command-line `+WT` overrides the INI, which `quiltwright.povray`
  derives whenever `jobs > 1` -- so raising `JOBS` silently defeats the cap.
- **`JOBS` now defaults to 1 rather than the core count.** That is the render
  scripts' own default and what `povray.md section 6` already recommended: POV-Ray
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
  skip condition a Python dependency can lift -- the PyVista tests also need a
  system GL stack and an X server.
- `docs/install.md` records why ffmpeg stays an extra rather than a core
  dependency: the binary `imageio-ffmpeg` bundles is a GPLv3 build
  (`--enable-gpl --enable-version3`), which a BSD-3 project should hand people
  on request rather than by default. Also notes that encoding needs `libx264`
  and `libx265`, which a minimal or LGPL-only ffmpeg may lack -- a failure that
  surfaces at encode time, not install time.
- `poetry.lock` regenerated for the group changes.
- **README reframed around the pipelines it actually serves.** It read as a
  solution to a projection problem; the purpose is holographic output for two
  scientific rendering pipelines -- PyVista/VTK scenes from WaveRider and
  POV-Ray scenes from pdb2pov -- onto two display technologies, light-field
  (quilts) and hololuminescent (2-D video). The off-axis projection note stays,
  subordinated to what it is in service of.
- **Re-measured the museum's depth range, and everything derived from it.**
  `NEAR_DEPTH` moves 32 -> 31 and `FAR_DEPTH` 100 -> 96, which moves the focal
  plane 48.5 -> 46.9, the clearance-limited cone 25.6° -> 26.4°, and the
  near/far disparity 3.58 -> 3.68 px. Figures updated in `povray.md section 3-4`,
  the README, `about-the-image.md`, and the tests that pin them.

  Two corrections came out of measuring rather than estimating. The nearest
  geometry is the near pedestal's *tabletop*, not the bell jar it carries, so
  drawing the pedestals inward moved the near bound far less than the jar
  itself moved. And the sky is 6.1% of the frame, not the ~10% previously
  recorded. Re-measuring the *previous* layout with the same probe gives 26
  units, not the 32 documented for it, so the original figure was optimistic --
  the depth budget it produced was slightly tighter than believed, never
  looser.
- **Regenerated `museum_centre_view.png` and `museum_parallax.png`**, which
  still showed the old pedestal placement. The parallax figure is now views 0
  and 47 of the near pedestal against the painting behind it.
- The finished-quilt verification table in `povray.md section 4` is re-measured by
  cross-correlating feature crops between views 11 gaps apart, and now records
  the method's two failure modes: crops spanning a range of depths return a
  number belonging to no feature, and crops must be chosen on a view between
  the two being compared. It gains a row for a painting that sits within a unit
  of the focal plane and therefore does not move at all.
- **Corrected the museum scene's provenance.** It was described as "a 1994
  Michael Mittelstadt interior, later extended with molecular exhibits", which
  inverts the authorship: the scene is "Eric's Science Museum" (begun 10 Jun
  1995, revised 14 Mar 1997), and what it borrows from Mittelstadt's 1994 work
  is the room -- walls, columns, window, frames, pedestals -- while every exhibit
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
  normalised CRLF -> LF while every line was being touched anyway.
- **`3porin.pov` and `museum.pov` reframed at 16:9** (1920×1080), matching the
  16" landscape panel the holograms target. The porin's extra width over the
  old 3/4 portrait frame is sea and sky. The museum camera is dollied 5 units
  toward the aim point to bring the near jar out toward the left frame edge,
  and `render_museum_hologram.py`'s `EYE`, `NEAR_DEPTH` (31 -> 26) and
  `FAR_DEPTH` (96 -> 91) follow the dolly. Aspect tables in
  `docs/pov-workflow.md` and `renders/README.md` updated.
- **README hero caption names its display targets.** The museum quilt is now
  described as output for Looking Glass light-field and hololuminescent
  displays, plus LitiHolo holographic printers (in development), rather than
  just "a 48-view light-field quilt".

## [0.1.0] - 2026-08-04

Initial release. Extracted from
[WaveRider](https://github.com/Flux-Frontiers/waverider) 0.12.0, where this
code grew as `waverider.lfd` / `waverider.hld`; git history for those files is
preserved. Split out because three unrelated consumers now depend on it --
manifold visualisation, molecular rendering, and a POV-Ray scene archive -- and
none of them should have to depend on the others.

### Added

- **POV-Ray backend** (`quiltwright.povray`). Renders quilts from existing
  `.pov` scenes without modifying them: each view wraps the scene with
  `#include` and appends an off-axis camera, which POV-Ray honours because it
  uses the last camera it parses.
  - `PovCamera` -- camera in `look_at` form, where the aim point becomes the
    holographic focal plane.
  - `camera_block()` -- emits the sheared camera for one view. Never emits
    `angle`, which would override `|direction|` and silently destroy the
    shear.
  - `render_pov_quilt()` -- sweeps the cone, ray-traces each view, assembles.
- **Depth budget tools** in `quiltwright.lfd`:
  - `view_disparity()` -- adjacent-view pixel shift for content at a given
    depth. Verified against ray-traced renders to within 2%.
  - `focal_distance_for_range()` -- harmonic-mean focal distance, which
    equalises the disparity penalty between near and far content.
- `assemble_quilt()` -- renderer-agnostic tiling, extracted from
  `render_quilt()` so both backends share it. Consumes views lazily and
  validates the count.
- `docs/povray.md` and `docs/pdb2pov.md`.
- `scripts/render_museum_hologram.py` -- worked example driving a 1994 POV-Ray
  interior, including the depth and clearance measurements it needs.

### Changed

- `find_ffmpeg()` is now public. It was `_find_ffmpeg`, imported across module
  boundaries by `hld`, which is not appropriate for a private helper.
- POV-Ray camera vectors are emitted at full float64 precision. At 10
  significant figures the shear term -- a small correction to a large
  `direction` vector -- lost enough accuracy to move the focal plane
  measurably in large scenes.
- The default Bridge playlist name is now `"quiltwright"`.
