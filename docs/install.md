# Installing the full stack

Quiltwright is a Python package plus, depending on what you want to do, up to
five external pieces: a renderer (PyVista/VTK, POV-Ray, or Blender's Cycles),
PyMOL (for molecular cartoons), an encoder (ffmpeg), and the Looking Glass
Bridge driver. Nothing needs all of them -- this page goes layer by layer,
and each section says who can skip it.

| You want to... | You need |
|---|---|
| Compute quilt geometry, tile views, cast pre-rendered quilts | core package + Bridge |
| Render quilts from PyVista/VTK scenes | `[viz]` extra |
| Ray-trace quilts from POV-Ray scenes | `povray` binary |
| Path-trace quilts from `.blend`/glTF/OBJ/etc. scenes, with GPU ray tracing | `blender` binary (4.x+) |
| Render molecular structures from PDB or mmCIF files | `[molecules]` extra |
| Render secondary-structure cartoons (`quiltwright cartoon`) | `pymol` binary |
| Encode quilt video or HLD masters | ffmpeg (or `[video]` extra) |

---

## 1. The Python package

Requires Python 3.12 or 3.13.

```bash
pip install quiltwright              # core: quilt geometry + Bridge control
pip install "quiltwright[viz]"       # + PyVista/VTK rendering backend
pip install "quiltwright[video]"     # + bundled ffmpeg for video encoding
pip install "quiltwright[molecules]" # + PDB and mmCIF, via pypdb2pov
```

Core deliberately depends on nothing but numpy, pillow and click, so a
machine that only casts pre-rendered quilts stays lean.

From source (for the example scenes, scripts, and tests):

```bash
git clone https://github.com/Flux-Frontiers/quiltwright
cd quiltwright
pip install -e ".[viz,video]"
```

Or with Poetry, which is how this repo is developed. Every extra above has a
Poetry group of the same name, so `poetry install --with viz` and `pip install
".[viz]"` produce the same environment. All groups are optional, so a bare
`poetry install` gives you the core package alone:

```bash
poetry install                       # core: quilt geometry + Bridge control
poetry install --with viz            # + PyVista/VTK rendering backend
poetry install --with video          # + bundled ffmpeg for video encoding
poetry install --with molecules      # + PDB and mmCIF, via pypdb2pov
poetry install --with dev            # + pytest, pytest-cov, ruff, ty, pre-commit
poetry install --with viz,video,dev  # groups combine
```

No space after the comma: Poetry reads the name following it as a positional
argument and refuses the command.

One group has no pip equivalent, deliberately. `kg` installs the `pycodekg`
and `dockg` CLIs that index this repo for agents -- maintainer tooling this
repo runs, not a feature of the package, so it is a group only and never
reaches the published wheel metadata:

```bash
poetry install --with kg
poetry install --all-extras --with dev,kg   # everything
```

The `[viz]` extra pulls in VTK, which needs a working OpenGL stack. On a
headless box (CI, remote server) prefix commands with `xvfb-run -a`; without
a GL stack the PyVista path raises and the rendering tests skip.

## 2. POV-Ray (ray-traced backend)

Skip this if you only render from PyVista. The POV-Ray backend shells out to
a `povray` binary rather than using a Python package:

```bash
brew install povray                  # macOS
sudo apt install povray              # Debian/Ubuntu
sudo dnf install povray              # Fedora
```

On Windows, install [POV-Ray 3.7](https://www.povray.org/download/) and point
Quiltwright at the console binary.

The binary is found via the `POVRAY_BINARY` environment variable first, then
`povray` on `PATH`; `render_pov_quilt(..., binary=...)` overrides both.
Verify with:

```bash
povray --version
```

The repo ships a complete test scene -- "Eric's Science Museum", 1995-97, see
[about-the-image.md](about-the-image.md) -- under [pov-scenes/](../pov-scenes/),
so you can exercise this layer with no scene files of your own:

```bash
python scripts/render_museum_hologram.py --preview
```

## 3. Blender / Cycles (hardware-ray-traced backend)

Skip this if you only render from PyVista or POV-Ray. The Cycles backend
shells out to a `blender` binary (4.x or later) rather than using a Python
package -- installing the full application also gets you its bundled Python
and `bpy`, so nothing further needs to be pip-installed:

```bash
brew install --cask blender          # macOS
```

Elsewhere, download from [blender.org](https://www.blender.org/download/).
The standard `/Applications` install (macOS) is found automatically; point
Quiltwright anywhere else with `BLENDER_BINARY=/path/to/blender`.

```bash
blender --version
```

The end-to-end Cycles tests instead look for `QW_BPY_PYTHON`, naming a Python
interpreter with the [`bpy` wheel](https://pypi.org/project/bpy/) installed --
the CI/container case, where a full Blender install isn't practical. With
neither a `blender` binary nor `QW_BPY_PYTHON`, those tests skip cleanly. See
[cycles.md](cycles.md) for the backend itself.

## 4. PyMOL (molecular cartoons)

Skip this if you only render atoms and bonds via pdb2pov/pypdb2pov. PyMOL
draws the secondary-structure ribbons (`quiltwright cartoon`,
`cartoon_inc()`/`cartoon_obj()`) that pdb2pov has never been able to write.
It is not OSI-licensed, so it can never be a hard dependency of a BSD-3
package, and stays a binary you install yourself:

```bash
brew install pymol                          # macOS, stable
conda install -c conda-forge pymol-open-source
pip install --pre pymol-open-source         # alphas only -- PyPI has no stable release
```

Quiltwright drives PyMOL **in-process when it can import it, by subprocess
when it can't** -- Homebrew's build bundles its own interpreter that no
project virtualenv can import from, so the subprocess path is the common
case on macOS. Either way, no code changes: `quiltwright.pymol.available()`
picks automatically and reports which. Verify with:

```bash
pymol -cq -d "print('ok')"
```

## 5. Looking Glass Bridge (driving the display)

Skip this if you only produce quilt files for Studio or another player.
Displays, specs, and software all live at the
[Looking Glass website](https://lookingglassfactory.com).

1. Download **Looking Glass Bridge** (≥ 2.2) from
   <https://lookingglassfactory.com/software/looking-glass-bridge> and
   install it on the computer the display is plugged into. It runs in the
   background as a menu-bar/tray daemon serving HTTP on `localhost:33334`.
2. Connect the display with **both** cables: USB-C (data and calibration)
   and HDMI/DisplayPort (video).
3. Probe the device before your first render -- quilt specs differ between
   hardware generations, and Bridge reports the truth. The probe commands
   and the fields to read are in
   [lfd.md: Ask the panel what it wants](lfd.md#2-ask-the-panel-what-it-wants).
4. Optionally install **Looking Glass Studio** (same downloads page), a
   quilt player/library: drag any `*_qs*.png` / `*_qs*.mp4` in and playback
   settings are auto-detected from the filename.

`cast_quilt()` and the scripts' `--cast` flag then send renders straight to
the glass.

## 6. ffmpeg (video encoding)

Only needed for `render_quilt_video()` (quilt MP4s) and the HLD masters in
`quiltwright.hld`. Quiltwright looks for `ffmpeg` on `PATH` first, then
falls back to the binary bundled with the `[video]` extra
(`imageio-ffmpeg`) -- so either of these works:

```bash
brew install ffmpeg                  # system ffmpeg
pip install "quiltwright[video]"     # or the bundled one
```

**Why this is an extra and not a core dependency.** The license, mostly:

- **License.** The `imageio-ffmpeg` wrapper is BSD-2-Clause, but the binary it
  bundles is built `--enable-gpl --enable-version3` -- a GPLv3 ffmpeg. Calling
  it as a subprocess does not affect Quiltwright's own BSD-3-Clause terms, but
  anyone *redistributing* a bundled environment (a Docker image, a conda pack,
  a PyInstaller app) inherits GPLv3 obligations. That should be a choice, not
  a default. A system ffmpeg -- whose build and license you control -- avoids
  the question entirely, which is why `PATH` is searched first.
- **Size.** ~21-31 MB to download, ~80 MB installed, against a core of numpy
  and pillow.
- **Redundancy.** If you already have ffmpeg on `PATH`, the bundled copy is
  never executed.

Encoding uses `libx264` and `libx265` (HEVC above 6000 px); a minimal or
LGPL-only ffmpeg build may lack them, and fails at encode time rather than at
install time. Check with `ffmpeg -h encoder=libx265`.

## 7. pypdb2pov (molecular scenes)

Optional; feeds the POV-Ray backend with molecular structures. There are two
implementations, writing byte-identical scenes.

**`pypdb2pov`, the Python port** -- no compiler, no dependencies, reads mmCIF,
and importable from the same script that renders the quilt. It has its own
repository and PyPI release as of 0.1.0; the `python/` tree inside the C repo
is retired. Take it as an extra:

```bash
pip install "quiltwright[molecules]"
poetry install --with molecules     # the equivalent group
```

or on its own, which is the same package:

```bash
pip install pypdb2pov
```

**Why an extra and not a core dependency.** Only the molecular scenes need
it, and a machine rendering anything else should not carry it -- the same
ground the `viz` extra stands on. There is no license obstacle: pypdb2pov is
BSD-3-Clause like quiltwright itself.

**`pdb2pov`, the C program** -- the 1993 original, whose portability fixes now
live upstream, so a fresh clone just builds:

```bash
git clone https://github.com/suchanek/pdb2pov
cd pdb2pov && make pdb2pov
```

The two commands differ only in name, so both can sit on one `PATH`.

Either way the scenes reference POV-Ray include files that must be on the
library path. `pypdb2pov --include-dir` prints where the Python package keeps
them -- inside the package, so wherever it is installed is where they are;
with the C program they sit in the clone.
[`scripts/render_vitrine.py`](../scripts/render_vitrine.py) asks the package
directly rather than being told a path.

See [pdb2pov.md](pdb2pov.md) for which to choose, the build notes, and the
render pipeline.

---

## Checking the stack

Each layer can be verified independently:

```bash
python -c "import quiltwright; print(quiltwright.__version__)"   # package
povray --version                                                 # POV-Ray
blender --version                                                # Cycles
pymol -cq -d "print('ok')"                                       # PyMOL
curl -s -X PUT -H 'Content-Type: application/json' \
     -d '{"name":"probe"}' http://localhost:33334/enter_orchestration  # Bridge
```

The test suite is layered the same way -- tests skip cleanly for layers that
are absent, and report what they skipped:

```bash
poetry install --with dev            # or: pip install pytest
pytest -v
```

A skipped test reports success while asserting nothing, so for real coverage
install the layers too. Everything runs green with:

```bash
sudo apt install xvfb libgl1 libglx-mesa0 libxrender1 povray   # or brew
poetry install --with viz,video,dev     # or: pip install -e ".[viz,video]" pytest
xvfb-run -a pytest
```

The `dev` group pulls `imageio-ffmpeg` itself, for the same reason -- it is the
only skip condition a Python dependency can lift, since the PyVista tests
additionally need a GL stack and an X server, and the POV-Ray and Cycles tests
need their binaries.
