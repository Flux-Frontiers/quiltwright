# CLI reference

**Installed as**: `quiltwright`, core-only (numpy, pillow, click) -- no
extra needed just to run `--help`.
**Source**: `src/quiltwright/cli/`

Most commands operate on a *quilt*, which is where the backends have
already met: a manifold swept out of PyVista and a molecular scene
ray-traced from POV-Ray produce the same artifact, and `cast` / `weave` /
`wallpaper` / `dynamic` treat them identically. Three commands are a whole
pipeline rather than a step after one -- `mesh`, `cartoon`, `probe` -- and none of
them is a generic renderer for the bundled scenes; those stay in
`scripts/`, covered in [shell.md](shell.md#make-the-bundled-archive).

This page is the flag-by-flag reference for every command. For the *why*
behind each one, see [shell.md](shell.md#what-each-command-is-for).

```
quiltwright [OPTIONS] COMMAND [ARGS]...
```

| Option | Effect |
|---|---|
| `--version` | Print the installed version and exit |
| `--help` | Show help and exit -- also works on any subcommand |

| Command | For |
|---|---|
| [`bridge`](#bridge) | Inspect and restart Looking Glass Bridge |
| [`cartoon`](#cartoon) | Convert a structure into a POV-Ray cartoon include |
| [`cast`](#cast) | Show a saved quilt on the connected Looking Glass |
| [`dynamic`](#dynamic) | Pack stills into a macOS Dynamic Desktop HEIC |
| [`mesh`](#mesh) | Auto-frame a mesh file and render it as a quilt |
| [`probe`](#probe) | Measure a scene's near and far depth by plane sweep |
| [`wallpaper`](#wallpaper) | Set a woven frame as the desktop picture of its own panel |
| [`weave`](#weave) | Weave a quilt into a native pre-lensed frame for one panel |

---

## `bridge`

```
quiltwright bridge COMMAND [ARGS]...
```

Inspect and restart Looking Glass Bridge.

```bash
quiltwright bridge status    # is it actually able to draw?
quiltwright bridge reset     # kill and relaunch a wedged daemon
```

### `bridge status`

```
quiltwright bridge status [OPTIONS]
```

Reports whether Bridge is running, responsive, and seeing a panel. Exits
non-zero if Bridge is unusable, so this can gate a cast in a script. Bridge
keeps its HTTP port open and keeps issuing session tokens after crashing
internally, so a cast can report success at every step against a daemon
that will never draw -- `status` checks the port, the session, the device
list *and* whether any device is actually a Looking Glass, then gives a
verdict.

| Option | Default | Effect |
|---|---|---|
| `--bridge-url TEXT` | `http://localhost:33334` | Bridge HTTP API base URL |
| `--timeout FLOAT` | `5.0` | Per-request timeout. A wedged Bridge hangs rather than refusing, so this is what separates "slow" from "dead" |

### `bridge reset`

```
quiltwright bridge reset [OPTIONS]
```

Terminates Bridge and starts it again. Bridge's own menu restart spawns a
replacement that inherits the wedge, which is why this kills the processes
outright. Anything currently playing on the panel stops.

| Option | Default | Effect |
|---|---|---|
| `--no-relaunch` | off | Terminate Bridge without starting it again |
| `--wait FLOAT` | `20.0` | Seconds to wait for the relaunched daemon to answer |
| `--bridge-url TEXT` | `http://localhost:33334` | Bridge HTTP API base URL |

---

## `cartoon`

```
quiltwright cartoon [OPTIONS] [SOURCE] [OUTPUT]
```

Converts a structure into a POV-Ray cartoon include, via headless PyMOL.
`SOURCE` is anything PyMOL can load -- `.pdb`, `.cif`, `.cif.gz`. `OUTPUT`
is the `.inc` to write. See [pdb2pov.md](pdb2pov.md) for the object-only
contract this writes to.

| Option | Default | Effect |
|---|---|---|
| `--rep TEXT` | `cartoon` | Representation. `cartoon` and `surface` are what pdb2pov cannot draw; `sticks` and `spheres` duplicate its `-b` and `-v` |
| `--color TEXT` | `spectrum` | `spectrum` ramps rainbow along the chain; any PyMOL color name is flat; `none` keeps PyMOL's own coloring |
| `--selection TEXT` | `polymer` | PyMOL selection to show. The default drops waters and ligands |
| `--assembly TEXT` | `1` | Biological assembly. `1` is the biological unit -- ferritin arrives as a 24-mer rather than a 24th of itself. `""` gives the asymmetric unit |
| `--transparency FLOAT` (0.0-1.0) | `0.0` | Exports as POV-Ray `transmit`, which is flat see-through rather than refractive |
| `--surface-quality INTEGER` | -- | PyMOL `surface_quality`; lower is coarser. Worth setting negative for a large `--rep surface`, which otherwise runs to millions of triangles |
| `--name TEXT` | output stem | POV-Ray identifier to declare. Defaults to the output stem, made legal (a leading digit gains an underscore) |
| `--raw` | off | Skip coalescing and keep PyMOL's one mesh per triangle. For comparing against the raw export; several times larger |
| `--check` | off | Report how PyMOL can be reached and exit, converting nothing |

```bash
quiltwright cartoon 2omf.cif.gz ompf_cartoon.inc   # a molecular ribbon, via PyMOL
quiltwright cartoon --check                         # is PyMOL reachable, and by which route?
```

---

## `cast`

```
quiltwright cast [OPTIONS] [QUILT]
```

Shows a saved quilt on the connected Looking Glass. `QUILT` is a quilt PNG
on this machine, normally one written by `save_quilt()` or `make
quilt-<name>`, whose `_qs<cols>x<rows>a<aspect>` filename suffix supplies
the tiling automatically.

Requires Looking Glass Bridge >= 2.2 running on the machine the panel is
plugged into. Quit Looking Glass Studio first -- it holds the display
exclusively, and Bridge will report success while the glass stays black.

| Option | Default | Effect |
|---|---|---|
| `--preset [16-landscape\|16-portrait\|27-landscape\|27-portrait\|32-landscape\|32-portrait\|65\|go\|portrait]` | -- | Quilt tiling grid and aspect, by device preset name |
| `--grid COLSxROWS` | from filename | Quilt tiling grid, explicit (e.g. `8x6`); defaults to parsing the `_qs<cols>x<rows>a<aspect>` filename suffix |
| `--aspect FLOAT` | from filename | Tile aspect, overriding the filename's. Rarely needed -- a value disagreeing with the panel is letterboxed by it |
| `--head INTEGER` | `-1` | Bridge head index to play on. `-1` lets Bridge choose, which is right until it picks an ordinary monitor; run `--check` for the list |
| `--playlist TEXT` | `quiltwright` | Bridge playlist name to create or replace |
| `--bridge-url TEXT` | `http://localhost:33334` | Bridge HTTP API base URL |
| `--check` | off | List the output devices Bridge can see and exit without casting. The first thing to run when the glass stays black |

```bash
# Cast a rendered quilt; tiling comes from the filename
quiltwright cast renders/quilts/bell-jar-holo_qs8x6a1.77778.png

# Which displays can Bridge see? Run this first when nothing appears
quiltwright cast --check

# Pin the panel when Bridge picks an ordinary monitor
quiltwright cast quilt.png --head 1

# A quilt whose filename carries no _qs suffix
quiltwright cast plain.png --grid 8x6 --aspect 1.77778
quiltwright cast plain.png --preset 16-landscape
```

---

## `mesh`

```
quiltwright mesh [OPTIONS] SOURCE
```

Auto-frames the mesh file `SOURCE` and renders it as a quilt through
Blender Cycles -- the only command here that needs no scene of ours at
all. See [mesh-import.md](mesh-import.md).

| Option | Default | Effect |
|---|---|---|
| `--device [16-landscape\|16-portrait\|27-landscape\|27-portrait\|32-landscape\|32-portrait\|65\|go\|portrait]` | `portrait` | Target display, which sets the quilt grid, size and view cone |
| `--lighting TEXT` | `studio` | Light rig for a mesh that carries none: one of `soft`, `studio`, `sky`, or a path to an `.hdr`/`.exr` environment map |
| `--fov FLOAT` | `14.0` | Vertical field of view in degrees. Object-centric, so narrow |
| `--view-direction X Y Z` | `0.0 -1.0 0.0` | Direction from the object's center to the eye (+z is up) |
| `--margin FLOAT` | `1.2` | Framing headroom beyond a tight fit; `1.0` is exactly tight |
| `--samples INTEGER` | `128` | Cycles samples per pixel |
| `--view-transform TEXT` | `Standard` | OCIO view transform (`Standard`, `AgX`, `Filmic`, ...); see [cycles.md](cycles.md) |
| `--compute [auto\|gpu\|cpu]` | `auto` | Cycles compute device. `auto` prefers a GPU, Metal first |
| `--preview` | off | Quarter-size quilt, for iterating on framing |
| `--still` | off | One center view as a flat image, at the device's aspect, instead of a quilt |
| `--out TEXT` | source name | Output stem; defaults to the source name under `renders/quilts/` (or `gallery/` with `--still`) |
| `--cast` | off | Send the result to Looking Glass Bridge |

```bash
quiltwright mesh model.glb
quiltwright mesh scan.fbx --lighting sky --still
quiltwright mesh asset.obj --device 27-portrait --samples 256 --cast
quiltwright mesh statue.ply --view-direction 0.5 -1 0.3 --fov 20
```

---

## `probe`

```
quiltwright probe [OPTIONS] SCENE
```

Measures `SCENE`'s near and far depth by plane sweep -- the measurement
every POV-Ray depth budget starts from: it slides an opaque plane along
the view axis and reports where content actually begins and ends, which is
what `focal_distance_for_range()` wants. Probe through the camera you will
*render* with, and at `+Q8` or above -- below that POV-Ray disables
transparency and a room reports no windows at all. On a scene whose
backdrop runs to the horizon the sweep never closes and the printed *far*
is the end of it; the command says so, and `--rows` prints the curve to
fit the knee from.

| Option | Default | Effect |
|---|---|---|
| `--eye X Y Z` | required | Camera position to probe through, in scene units |
| `--aim X Y Z` | required | Camera look-at point |
| `--fov FLOAT` | `53.13` | Vertical field of view in degrees. The default is POV-Ray's own unit direction/up lens, `2*atan(0.5)` |
| `--min-distance FLOAT` | 1% of `--max-distance` | Near end of the sweep. A scene composed far from its eye -- porin sits 1100 units out -- wants its probes where its content is, not 200 of them in front of it |
| `--max-distance FLOAT` | `400.0` | Far end of the sweep, before the one at infinity |
| `--probes INTEGER` | `200` | Number of planes between the two distances |
| `--include-path DIR` | -- | Extra `#include` directory; repeatable. The scene's own is automatic |
| `--width INTEGER` | `320` | Probe frame width |
| `--height INTEGER` | `180` | Probe frame height |
| `--quality INTEGER` | `11` | POV-Ray `+Q`. Below 8 it disables transparency and glass reads solid |
| `--pov-arg ARG` | -- | Extra POV-Ray argument, e.g. `+MV3.1` for a scene with no `#version` pragma of its own; repeatable |
| `--rows` | off | Print the whole curve, one distance per line |

```bash
quiltwright probe pov-scenes/bell_jar/bj.pov --eye 0 35 -95 --aim 0 18 0
quiltwright probe pov-scenes/porin/3porin.pov --eye 0 0 -1100 --aim 0 0 0 \
    --include-path pov-scenes/myinclude --min-distance 700 \
    --max-distance 1600 --pov-arg +MV3.1
```

---

## `dynamic`

```
quiltwright dynamic [OPTIONS]
```

Packs finished stills into a macOS Dynamic Desktop `.heic`. macOS picks the
frame from sun position, wall-clock time, or Light/Dark appearance -- with
no agent of ours running. Install the file with [`wallpaper`](#wallpaper).

This is **not** POV-Ray's `clock`. That identifier is POV-Ray's animation
parameter (`+K`). Real time of day lives in the HEIC metadata, which macOS
reads. POV-Ray's contribution is `render_pov_quilt(..., lighting="light")`
or `sun=(altitude, azimuth)` to *produce* the stills.

Woven `_native_` frames always encode lossless 4:4:4. Lossy HEVC 4:2:0
would mix the per-channel views and destroy the hologram. Encoding needs
the `heic` extra (`pip install 'quiltwright[heic]'`).

| Option | Default | Effect |
|---|---|---|
| `--appearance LIGHT DARK` | -- | Two stills: light appearance, then dark |
| `--solar FILE.json` | -- | JSON array with `altitude` / `azimuth` per still (wallpapper shape) |
| `--time FILE.json` | -- | JSON array with `time` (`HH:MM` or `HH:MM:SS`) per still |
| `-o, --output PATH` | -- | Output `.heic`. Required unless `--dump` |
| `--lossless` | off (on for `_native_`) | Force lossless 4:4:4 |
| `--lossy` | off | Force lossy HEVC. Refused for woven frames |
| `--dump PATH` | -- | Print `apple_desktop` metadata from an existing HEIC |

```bash
quiltwright dynamic --appearance day_native_LKG-J00332.png night_native_LKG-J00332.png \
    -o scene.heic
quiltwright dynamic --solar solar.json -o scene.heic
quiltwright wallpaper scene.heic
```

Give exactly one of `--appearance`, `--solar`, or `--time`.

---

## `wallpaper`

```
quiltwright wallpaper [OPTIONS] [WOVEN]
```

Sets a woven frame as the desktop picture of its own panel. `WOVEN` is a
native-resolution frame from `quiltwright weave` -- already interleaved
for one panel, so displayed 1:1 it fuses into a hologram with no Looking
Glass software running at all. The panel is identified from the
`_native_<serial>` filename and matched against each desktop's display
name.

The frame is copied into a stable pictures folder first, because macOS
stores wallpaper as a path: pointing the desktop into `renders/` means the
panel goes blank the next time that directory is cleaned.

| Option | Default | Effect |
|---|---|---|
| `--display TEXT` | serial in filename | Panel serial to target (e.g. `LKG-J00332`) |
| `--desktop INTEGER` | -- | Target desktop by 1-based index instead of by serial. Use `--list` to see them |
| `--dir DIRECTORY` | `~/Pictures/LKG-wallpapers` | Where to install the frame |
| `--no-install` | off | Set the file where it lies instead of copying it. Convenient, but the desktop breaks if that path is later cleaned |
| `--list` | off | List the desktops and their current pictures, then exit |

```bash
# Weave, then hang it on the panel it was woven for
quiltwright weave renders/quilts/bell-jar-holo_qs8x6a1.77778.png \
    --cal ~/Pictures/LKG-wallpapers/visual.json
quiltwright wallpaper bell-jar-holo_native_LKG-J00332.png

# What is on each desktop right now?
quiltwright wallpaper --list

# Target explicitly, when the filename carries no serial
quiltwright wallpaper frame.png --display LKG-J00332
quiltwright wallpaper frame.png --desktop 2

# Leave it where it is (it will break if renders/ is cleaned)
quiltwright wallpaper renders/quilts/x_native_LKG-J00332.png --no-install
```

---

## `weave`

```
quiltwright weave [OPTIONS] QUILT
```

Weaves `QUILT` into a native pre-lensed frame for one panel -- interleaved
for display 1:1, most usefully as its desktop wallpaper, with no Bridge
process required. See [docs/lfd.md](lfd.md) and `quiltwright.weave` for
the math.

| Option | Default | Effect |
|---|---|---|
| `--cal FILE` | required | Path to the panel's `visual.json` calibration file |
| `--preset [16-landscape\|16-portrait\|27-landscape\|27-portrait\|32-landscape\|32-portrait\|65\|go\|portrait]` | -- | Quilt tiling grid, by device preset name |
| `--grid COLSxROWS` | from filename | Quilt tiling grid, explicit (e.g. `8x6`); defaults to parsing the `_qs<cols>x<rows>` filename suffix |
| `-o, --output FILE` | `<quilt stem>_native_<serial>.png` | Output path |
| `--invert` | off | Reverse the view order if the fused result reads inside-out |

```bash
quiltwright weave renders/quilts/bell-jar-holo_qs8x6a1.77778.png --cal visual.json
```
