# Quiltwright

[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD--3--Clause-blue.svg)](LICENSE)
[![PyPI](https://img.shields.io/pypi/v/quiltwright.svg)](https://pypi.org/project/quiltwright/)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/suchanek/quiltwright/releases)
[![Tests](https://github.com/suchanek/quiltwright/actions/workflows/tests.yml/badge.svg)](https://github.com/suchanek/quiltwright/actions/workflows/tests.yml)
[![DOI](https://zenodo.org/badge/1323414722.svg)](https://zenodo.org/badge/latestdoi/1323414722)

**Holographic output for Looking Glass displays.**

*Eric G. Suchanek, PhD — Flux-Frontiers*

Quiltwright turns a rendered scene into a **quilt** — the tiled multi-view
image that [Looking Glass](https://lookingglassfactory.com) lenticular
light-field displays fuse into real, glasses-free depth.
It renders from [PyVista](https://pyvista.org)/VTK scenes or from
[POV-Ray](https://www.povray.org) ray-traced scenes, manages the depth budget
that decides whether a hologram fuses or ghosts, and drives Looking Glass
Bridge directly.

![A POV-Ray museum interior rendered as a hologram](docs/museum_centre_view.png)

*Centre view of a 48-view quilt, ray-traced from a POV-Ray scene first
composed in 1994.*

---

## Why this exists

The hard part of light-field rendering is not tiling images into a grid. It is
that **each view must use an off-axis (asymmetric-frustum) projection** — the
camera slides sideways while continuing to face the same direction, and the
image plane is sheared back onto the original view axis.

The intuitive alternative is to swivel each camera to keep the subject centred.
That is "toe-in", and it introduces vertical parallax and keystone distortion,
so the display cannot fuse the views. You get ghosting instead of depth. This
is the single most common way light-field renders go wrong, and it produces
output that looks plausible in any individual frame.

Quiltwright does the off-axis projection correctly in both backends, and gives
you the arithmetic to know in advance whether a scene will fuse.

---

## Install

```bash
pip install quiltwright              # core: quilt geometry + Bridge control
pip install "quiltwright[viz]"       # + PyVista/VTK rendering backend
```

The POV-Ray backend needs a `povray` binary on `PATH` rather than a Python
package:

```bash
brew install povray                  # macOS
```

For the complete stack — renderers, ffmpeg, Looking Glass Bridge, pdb2pov —
see the [installation guide](docs/install.md).

---

## Quick start

### From a PyVista scene

```python
import pyvista as pv
from quiltwright import QUILT_PRESETS, render_quilt, save_quilt

p = pv.Plotter(off_screen=True)
p.add_mesh(pv.ParametricTorus())

spec = QUILT_PRESETS["portrait"]
save_quilt(render_quilt(p, spec), "torus", spec)   # -> torus_qs8x6a0.75.png
```

### From a POV-Ray scene

The scene file is never modified — each view wraps it with `#include` and
appends one camera.

```python
from quiltwright import QUILT_PRESETS, PovCamera, render_pov_quilt, save_quilt

camera = PovCamera(location=(15, 20, 6), look_at=(44, 19.2, 45.1), fov=53.13)
spec = QUILT_PRESETS["16-landscape"]
quilt = render_pov_quilt("pov-scenes/museum/museum.pov", spec, camera,
                         include_paths=["pov-scenes/myinclude", "pov-scenes"])
save_quilt(quilt, "museum", spec)
```

The museum scene above ships in [pov-scenes/](pov-scenes/), and
[scripts/render_museum_hologram.py](scripts/render_museum_hologram.py) renders
it end-to-end with a measured depth budget — it is the worked case study in
[docs/povray.md](docs/povray.md).

### Send it to the display

```python
from quiltwright import cast_quilt, pause_quilt, resume_quilt, stop_quilt

cast_quilt("museum_qs8x6a1.77778.png", spec)   # needs Looking Glass Bridge >= 2.2
```

Saved filenames carry the `_qs<cols>x<rows>a<aspect>` suffix that Looking Glass
Studio and Bridge parse, so playback settings are detected automatically.

---

## The depth budget

Whether a hologram fuses comes down to **adjacent-view disparity**: how far a
feature moves between neighbouring views. Roughly 4–5 px is the practical
ceiling; past ~8 px, hard edges ghost.

```python
from quiltwright import QUILT_PRESETS, focal_distance_for_range, view_disparity

# Put the focal plane where near and far content are equally penalised.
focal = focal_distance_for_range(near=32, far=100)      # harmonic mean, not midpoint
view_disparity(QUILT_PRESETS["16-landscape"], fov=53.13,
               focal_distance=focal, depth=32)          # -> px between adjacent views
```

Three results worth knowing before you frame a shot:

- Content **at** the focal plane has zero disparity — it is welded to the glass.
- The focal plane belongs at the **harmonic mean** of the depth range, not the
  midpoint. Disparity is asymmetric in depth, and near content is the expensive
  side.
- A **narrower field of view increases** disparity. Zooming in magnifies the
  scene and the parallax with it. The widely repeated "use ~14° FOV" advice is
  specific to object-centric scenes; applied to an interior it makes ghosting
  worse.

For interiors there is a fourth trap that no arithmetic will warn you about:
the camera sweep physically travels `focal_distance × tan(cone/2)` sideways,
and in a room that path can run through a wall. See
[docs/povray.md](docs/povray.md#3-sweep-clearance--the-constraint-peculiar-to-interiors).

---

## Supported devices

`QUILT_PRESETS` carries the official quilt settings for Portrait, Go, and the
16″/27″/32″/65″ panels in both orientations. The 16″ Gen3 Landscape entry is
verified against what Bridge reports for real hardware.

```python
from quiltwright import QUILT_PRESETS
QUILT_PRESETS["16-landscape"]      # 8x6 views, 7680x4320, aspect 1.7778
```

---

## Documentation

| Document | Contents |
|----------|----------|
| [docs/install.md](docs/install.md) | Installing the full stack: package extras, POV-Ray, ffmpeg, Bridge, pdb2pov |
| [docs/lfd.md](docs/lfd.md) | Light-field output, Bridge/Studio setup, device presets, the PyVista path |
| [docs/povray.md](docs/povray.md) | The POV-Ray backend: off-axis camera derivation, depth budget, sweep clearance, a worked case study |
| [docs/pdb2pov.md](docs/pdb2pov.md) | Rendering molecular structures from PDB files as holograms |
| [docs/hld.md](docs/hld.md) | Hololuminescent Displays, which play ordinary 2-D video rather than quilts |

> **Two different technologies.** Looking Glass sells a light-field line
> (Portrait, Go, 16″/27″/32″/65″ LFD) that consumes quilts, and a
> Hololuminescent line (16″/27″/86″ HLD) that plays ordinary video behind a
> fixed holographic optic. `quiltwright.lfd` targets the first;
> `quiltwright.hld` targets the second.

---

## Testing

```bash
pip install -e ".[viz]" && pip install pytest
pytest
```

Rendering tests skip cleanly on machines with no OpenGL stack, and the POV-Ray
tests skip when no `povray` binary is present. Under a headless CI runner, use
`xvfb-run -a pytest` to exercise them.

---

## Related

- [WaveRider](https://github.com/Flux-Frontiers/waverider) — manifold-aware
  geometric ML; its voxel visualiser renders through Quiltwright.
- [proteusPy](https://github.com/suchanek/proteusPy) — protein disulfide bond
  analysis and rendering.
- [pdb2pov](https://github.com/suchanek/pdb2pov) — PDB to POV-Ray converter,
  1993, still feeds this pipeline.

## Citation

If you use Quiltwright in your work, please cite it. Citation metadata is in
[CITATION.cff](CITATION.cff); GitHub's "Cite this repository" button generates
BibTeX/APA from it, and the DOI badge above resolves to the archived release
on Zenodo.

```bibtex
@software{suchanek_quiltwright,
  author  = {Suchanek, Eric G.},
  title   = {Quiltwright: Holographic Output for Looking Glass Displays},
  url     = {https://github.com/suchanek/quiltwright},
  version = {0.1.0},
  year    = {2026}
}
```

## License

BSD 3-Clause. See [LICENSE](LICENSE).
