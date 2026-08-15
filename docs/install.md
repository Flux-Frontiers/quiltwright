# Installing the full stack

Quiltwright is a Python package plus, depending on what you want to do, up to
three external pieces: a renderer (PyVista/VTK or POV-Ray), an encoder
(ffmpeg), and the Looking Glass Bridge driver. Nothing needs all of them —
this page goes layer by layer, and each section says who can skip it.

| You want to… | You need |
|---|---|
| Compute quilt geometry, tile views, cast pre-rendered quilts | core package + Bridge |
| Render quilts from PyVista/VTK scenes | `[viz]` extra |
| Ray-trace quilts from POV-Ray scenes | `povray` binary |
| Encode quilt video or HLD masters | ffmpeg (or `[video]` extra) |
| Render molecular structures from PDB files | pdb2pov |

---

## 1. The Python package

Requires Python 3.12 or 3.13.

```bash
pip install quiltwright              # core: quilt geometry + Bridge control
pip install "quiltwright[viz]"       # + PyVista/VTK rendering backend
pip install "quiltwright[video]"     # + bundled ffmpeg for video encoding
```

Core deliberately depends on nothing but numpy and pillow, so a machine that
only casts pre-rendered quilts stays lean.

From source (for the example scenes, scripts, and tests):

```bash
git clone https://github.com/suchanek/quiltwright
cd quiltwright
pip install -e ".[viz,video]"
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

The repo ships a complete test scene — "Eric's Science Museum", 1995-97, see
[about-the-image.md](about-the-image.md) — under [pov-scenes/](../pov-scenes/),
so you can exercise this layer with no scene files of your own:

```bash
python scripts/render_museum_hologram.py --preview
```

## 3. Looking Glass Bridge (driving the display)

Skip this if you only produce quilt files for Studio or another player.
Displays, specs, and software all live at the
[Looking Glass website](https://lookingglassfactory.com).

1. Download **Looking Glass Bridge** (≥ 2.2) from
   <https://lookingglassfactory.com/software/looking-glass-bridge> and
   install it on the computer the display is plugged into. It runs in the
   background as a menu-bar/tray daemon serving HTTP on `localhost:33334`.
2. Connect the display with **both** cables: USB-C (data and calibration)
   and HDMI/DisplayPort (video).
3. Probe the device before your first render — quilt specs differ between
   hardware generations, and Bridge reports the truth. The probe commands
   and the fields to read are in
   [lfd.md § Ask the panel what it wants](lfd.md#2-ask-the-panel-what-it-wants).
4. Optionally install **Looking Glass Studio** (same downloads page), a
   quilt player/library: drag any `*_qs*.png` / `*_qs*.mp4` in and playback
   settings are auto-detected from the filename.

`cast_quilt()` and the scripts' `--cast` flag then send renders straight to
the glass.

## 4. ffmpeg (video encoding)

Only needed for `render_quilt_video()` (quilt MP4s) and the HLD masters in
`quiltwright.hld`. Quiltwright looks for `ffmpeg` on `PATH` first, then
falls back to the binary bundled with the `[video]` extra
(`imageio-ffmpeg`) — so either of these works:

```bash
brew install ffmpeg                  # system ffmpeg
pip install "quiltwright[video]"     # or the bundled one
```

**Why this is an extra and not a core dependency.** Three reasons, and the
first is the one that matters:

- **Licence.** The `imageio-ffmpeg` wrapper is BSD-2-Clause, but the binary it
  bundles is built `--enable-gpl --enable-version3` — a GPLv3 ffmpeg. Calling
  it as a subprocess does not affect Quiltwright's own BSD-3-Clause terms, but
  anyone *redistributing* a bundled environment (a Docker image, a conda pack,
  a PyInstaller app) inherits GPLv3 obligations. That should be a choice, not
  a default. A system ffmpeg — whose build and licence you control — avoids
  the question entirely, which is why `PATH` is searched first.
- **Size.** ~21–31 MB to download, ~80 MB installed, against a core of numpy
  and pillow.
- **Redundancy.** If you already have ffmpeg on `PATH`, the bundled copy is
  never executed.

Encoding uses `libx264` and `libx265` (HEVC above 6000 px); a minimal or
LGPL-only ffmpeg build may lack them, and fails at encode time rather than at
install time. Check with `ffmpeg -h encoder=libx265`.

## 5. pdb2pov (molecular scenes)

Optional; feeds the POV-Ray backend with molecular structures. It is a 1993
C program whose portability fixes now live upstream, so a fresh clone just
builds:

```bash
git clone https://github.com/suchanek/pdb2pov
cd pdb2pov && make pdb2pov
```

See [pdb2pov.md](pdb2pov.md) for the build notes and the render pipeline.

---

## Checking the stack

Each layer can be verified independently:

```bash
python -c "import quiltwright; print(quiltwright.__version__)"   # package
povray --version                                                 # renderer
curl -s -X PUT -H 'Content-Type: application/json' \
     -d '{"name":"probe"}' http://localhost:33334/enter_orchestration  # Bridge
```

The test suite is layered the same way — tests skip cleanly for layers that
are absent, and report what they skipped:

```bash
pip install pytest
pytest -v
```

A skipped test reports success while asserting nothing, so for real coverage
install the layers too. Everything runs green with:

```bash
sudo apt install xvfb libgl1 libglx-mesa0 libxrender1 povray   # or brew
pip install -e ".[viz,video]" pytest
xvfb-run -a pytest
```

`poetry install --with dev` pulls `imageio-ffmpeg` for the same reason — it is
the only skip condition a Python dependency can lift, since the PyVista tests
additionally need a GL stack and an X server. Add `--with viz,video` for the
rest.
