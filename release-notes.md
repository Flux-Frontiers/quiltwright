# Release Notes — v0.3.0

> Released: 2026-08-10

Quiltwright 0.3.0 adds a scene source. Until now the package took geometry you
already had — a POV-Ray scene, a PyVista mesh — and put it on a display.
`quiltwright.tvb_data` goes and fetches some: real cortical surfaces,
structural connectomes and parcellations from
[The Virtual Brain](https://www.thevirtualbrain.org/), downloaded on demand
and handed over as ordinary meshes.

## What changed

**Brain geometry, as a scene source.** `quiltwright.tvb_data` covers 11
surfaces, 8 connectomes, 4 parcellations and 9 sensor sets — human and
macaque — through `load_surface()`, `load_connectivity()`,
`load_region_mapping()` and `load_sensors()`, plus `surface_polydata()` and
`connectome_polydata()` for meshes that drop straight into a plotter. It sits
alongside the POV-Ray and PyVista paths as a *source* of geometry and says
nothing about how that geometry reaches a display.

This belongs here for the same reason `scripts/render_pyvista_hologram.py`
already downloads the Allen Institute mouse atlas: choosing subjects with real
depth structure, and going and getting them, is something this package was
already doing. `docs/pyvista-datasets.md` was already the place that thinking
lived.

**The data is fetched, never shipped.** `tvb-root` contains no data of its
own; the datasets live in `tvb-data`, a 337 MB archive on Zenodo
([doi:10.5281/zenodo.10128131](https://doi.org/10.5281/zenodo.10128131)),
licensed GPL-3.0. It is downloaded on first use, MD5-verified, and cached.
Nothing is vendored into this BSD-3 tree. That is the same line the package
already draws around ffmpeg — a GPL artefact is something we fetch on request,
never something we ship — now applied to data as well as binaries.

No new dependency comes with it. Loading needs only the standard library and
NumPy, both already core; the PyVista bridge uses the existing `viz` extra.
Nothing in the module encodes video, so `imageio-ffmpeg` stays exactly where
it was, in the optional `video` group, and a test asserts the module source
never reaches for it.

**One answer for where downloads go.** `quiltwright.cache` gives every runtime
download the platform's own cache directory — `~/Library/Caches/quiltwright`
on macOS, `$XDG_CACHE_HOME/quiltwright` on Linux, `%LOCALAPPDATA%` on Windows
— matching PyVista, which caches through `pooch.os_cache` and so has always
put its own downloads in `~/Library/Caches` on a Mac. The Allen atlas
downloader had hard-coded `~/.cache/quiltwright/allen_ccf`, which is only
native on Linux; it now shares the same root, honours
`$QUILTWRIGHT_ALLEN_CACHE`, and adopts an existing download at the old path
rather than silently re-fetching a volume that runs well over a gigabyte at
10 µm.

**The archive's inconsistencies are absorbed, not passed on.** `tvb-data` is
not uniformly formatted, and one of its quirks fails silently: `cortex_2x120k`
indexes triangles from 1 while every other surface indexes from 0, so a naive
load produces an index one past the last vertex — a corrupt mesh rather than
an error. That is detected and rebased, as are split hemispheres,
folder-nested members, indices written in float notation, bz2-compressed
members, and a 1-byte vertex-normals stub. Each has a test.

Decimating a parcellated surface re-assigns its region labels by nearest
neighbour, because quadric decimation discards point data and interpolating
between region 3 and region 70 would mean nothing.

## Upgrading

Nothing breaks. This release is additive: no existing signature changed, and
the only behavioural change is where the Allen atlas caches, which migrates
itself.

If you keep large downloads on a separate volume, the new environment
variables are `$QUILTWRIGHT_TVB_CACHE` and `$QUILTWRIGHT_ALLEN_CACHE`.

## Getting started

```python
import pyvista as pv
from quiltwright import QUILT_PRESETS, render_quilt, save_quilt
from quiltwright.tvb_data import surface_polydata

cortex = surface_polydata("cortex_16384", region_mapping="regionMapping_16k_76")
p = pv.Plotter(off_screen=True)
p.add_mesh(cortex, scalars="region", cmap="turbo", show_scalar_bar=False)

spec = QUILT_PRESETS["portrait"]
save_quilt(render_quilt(p, spec), "cortex", spec)
```

See [docs/tvb-data.md](docs/tvb-data.md) for the dataset reference, cache
layout and licensing.
