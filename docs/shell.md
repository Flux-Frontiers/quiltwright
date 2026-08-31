# Driving it from the shell

**Companion to**: the README's [shell section](../README.md#driving-it-from-the-shell),
which carries the summary this page expands.

Everything in the library docs is where a scene arrives from whichever
pipeline built it. Three things sit around that:

| | What it is | What it is not |
|---|---|---|
| **Library** | `render_quilt` / `render_pov_quilt` / `render_cycles_quilt` from Python | a CLI |
| **`quiltwright` CLI** | Hardware and tooling on a finished quilt (`cast`, `weave`, `wallpaper`, `bridge`), plus three commands that take *arbitrary* input (`mesh`, `cartoon`, `probe`) | a generic `quiltwright render museum.pov` |
| **`scripts/`** | Composed exhibits for the scenes this repo ships -- museum, vitrine, still-life, DNA helix, cartoon comparison, `make_exhibit.py` | unfinished CLI |

The museum is a composed exhibit. It does not become a subcommand. A WaveRider
manifold or a freshly converted structure comes through the library, or
through `quiltwright mesh` if it is a file Blender can import.

---

## `make` -- the bundled archive

The repository ships the 1993-99 POV-Ray scenes, and a `Makefile` that renders
them with their measured depth budgets already dialled in, so a hologram from a
clean clone is one command rather than a script you have to write. This covers
the *bundled* scenes only. A WaveRider manifold or a freshly converted
structure does not come through here -- it comes through the library, or through
[scripts/render_pyvista_hologram.py](../scripts/render_pyvista_hologram.py) for
the PyVista subjects -- and it lands in the same `renders/quilts/`, where the
CLI below picks it up regardless of origin.

```bash
make                      # the default goal is help; rendering is always explicit
make help                 # every target, and the still names
```

### The gallery

One full-quality frame per scene, into [`gallery/`](../gallery/), cataloged in
[gallery.md](gallery.md). These are committed: they are the diffable record of
what each scene looks like, and the presented work rather than a build artifact
-- which is why they sit at the top level and not under `renders/`, where
everything is output and only `reports/` is kept.

```bash
make gallery                      # all of them
make still-bell_jar_bj_holo       # just one
```

Each renders at **its own declared aspect** -- POV-Ray maps `right` to image
width whatever pixel dimensions you ask for, so a mismatched frame stretches
silently. The Makefile carries the correct size per scene; the table is in
[pov-workflow.md](pov-workflow.md).

### Quilts

Into `renders/quilts/`, through the render scripts, which inject a device
camera and place the focal plane from measured near/far depths rather than
from the scene's own aim point:

```bash
make quilts                       # bell jar, porin, lambda, museum
make quilt-bell-jar-holo          # one, 16:9
make quilt-bell-jar-holo-2026     # the crystal cut
make quilt-bell-jar-portrait      # the 9:16 companion, for tall panels
make preview-museum               # quarter-size, for iterating on composition
```

Preview first when you are changing a composition -- a preview is seconds per
view where a full quilt is minutes, and the depth budget it prints is the same
one the full render will use.

Two knobs worth knowing:

```bash
make quilt-porin EXTRA_ARGS="--cast"          # send it to the panel when done
make quilt-museum EXTRA_ARGS="--antialias 0.1"
make quilts RENDER_THREADS=$(sysctl -n hw.ncpu)   # use the whole box
```

### Parallelism, and why it works the way it does

`RENDER_THREADS` defaults to **`ncpu - 2`**, leaving two cores for the rest of
the machine so a multi-minute render does not make the desktop unusable. It
reaches POV-Ray through a generated `POVINI`, because the render scripts invoke
`povray` themselves and a command-line `+WT` would override them. `JOBS` stays
at 1 on purpose: POV-Ray already threads one render across every core, so extra
processes only split it.

The same two cores are held back when you call a render script directly, where
there is no `POVINI` to carry the Makefile's value -- `--threads N` sets it
explicitly, and `--threads 0` lets POV-Ray take everything, which is its own
default. A `Work_Threads` line in `POVINI` always wins over the courtesy cap,
so `make quilts RENDER_THREADS=...` keeps working.

### Run reports

Every full quilt writes a Markdown provenance record to `renders/reports/`.
A quilt is a 25-40 MB gitignored release asset; the report is the committed
record of how it was made -- scene file *and its SHA-256*, repository commit and
whether the tree was dirty, camera and measured depths, the depth budget
verbatim, the parallelism actually used, timings, and the output's own digest.
Pass `--report` to either render script to get one outside `make`.

---

## `quiltwright` -- the CLI

Installed as `quiltwright`, core-only (numpy, pillow, click). Most commands
operate on a *quilt*, which is where the backends have already met: a
manifold swept out of PyVista and a molecular scene ray-traced from POV-Ray
produce the same artifact, and `cast` / `weave` / `wallpaper` treat them
identically. Three commands are a whole pipeline rather than a step after
one: `mesh`, `cartoon`, `probe`. None of them is a generic renderer for the
bundled scenes -- those stay in `scripts/`.

```bash
quiltwright bridge status       # is Bridge actually able to draw?
quiltwright bridge reset        # kill and relaunch a wedged daemon

quiltwright cast renders/quilts/bell-jar-holo_qs8x6a1.77778.png
quiltwright cast --check        # which displays can Bridge see?

quiltwright weave renders/quilts/bell-jar-holo_qs8x6a1.77778.png --cal visual.json
quiltwright wallpaper bell-jar-holo_native_LKG-J00332.png

quiltwright cartoon 2omf.cif.gz ompf_cartoon.inc   # a molecular ribbon, via PyMOL
quiltwright cartoon --check     # is PyMOL reachable, and by which route?

quiltwright mesh model.glb      # any mesh file -> a quilt, camera measured from it
quiltwright mesh scan.fbx --lighting sky --still

quiltwright probe pov-scenes/bell_jar/bj.pov --eye 0 35 -95 --aim 0 18 0
```

For a structure you have not downloaded yet, one command covers the whole
pipeline -- fetch, convert, compose, render -- narrating each step:

```bash
python scripts/make_exhibit.py 7AHL --label "ALPHA-HEMOLYSIN" --quilt
```

Structures land in `$PDB` (default `~/pdb`), and nothing already there is
fetched twice.

### What each command is for

`probe` is the measurement every POV-Ray depth budget starts from: it slides
an opaque plane along the view axis and reports where content actually begins
and ends, which is what `focal_distance_for_range()` wants.  Two cautions come
with it -- probe through the camera you will *render* with, and at `+Q8` or
above, since below that POV-Ray disables transparency and a room reports no
windows at all.  On a scene whose backdrop runs to the horizon the sweep never
closes and the printed *far* is the end of it; the command says so, and
`--rows` prints the curve to fit the knee from.

`mesh` is the exception to "downstream": it is a whole render, not a step
after one.  Hand it any file Blender can import and it measures the object's
bounds, frames a camera on them and path-traces the sweep -- the only command
here that needs no scene of ours at all.  It wants a `blender` binary; see
[docs/mesh-import.md](mesh-import.md).

`cartoon` is the one command that reaches outside the pipeline: it drives
PyMOL to draw the representations `pypdb2pov` cannot -- ribbons and surfaces --
and writes them on the same object-only contract, so a cartoon mounts in a
scene exactly where an atom model would. PyMOL is optional and never a
dependency; `--check` says whether it is reachable before anything is loaded.

`cast` recovers the tiling from the `_qs<cols>x<rows>a<aspect>` filename suffix
that `save_quilt()` writes, so it usually needs no flags whatever produced the
views. `weave` then `wallpaper` is the **no-Bridge path**:
a woven frame is already interleaved for one panel, so setting it as that
panel's desktop picture makes the desktop a hologram with nothing running.
`wallpaper` matches the frame to the right display by the panel serial both
carry.

When the glass stays black, `bridge status` is the first thing to run. Bridge
keeps its HTTP port open and keeps issuing session tokens after crashing
internally, so a cast can report success at every step against a daemon that
will never draw -- `status` checks the port, the session, the device list *and*
whether any device is actually a Looking Glass, then gives a verdict.
