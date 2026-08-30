# TVB Brain Datasets

*Eric G. Suchanek, PhD -- Flux-Frontiers*

Real human, macaque and mouse brain geometry from
[The Virtual Brain](https://www.thevirtualbrain.org/) (TVB), fetched on
demand and turned into PyVista meshes ready for the
[LFD](lfd.md) and [HLD](hld.md) backends.

This is a **scene source**, not an output backend -- the same role POV-Ray
scenes and the PyVista example datasets in
[pyvista-datasets.md](pyvista-datasets.md) play. It produces geometry and
says nothing about how that geometry reaches a display. Loading is NumPy
only; the GPL-3.0 archive is fetched at runtime and never vendored, so the
module stays in the default public API rather than behind a `tvb` extra.

Module: `quiltwright.tvb_data`

---

## Where the data comes from

The [tvb-root](https://github.com/the-virtual-brain/tvb-root) source tree
contains **no data**. Every demonstration dataset ships separately as
`tvb-data`, published on Zenodo as a single ~337 MB archive:

| | |
|---|---|
| DOI | [10.5281/zenodo.10128131](https://doi.org/10.5281/zenodo.10128131) |
| Version | 2.8.1 |
| Archive | `tvb_data.zip`, 337,115,643 bytes |
| MD5 | `08ae19833ba8ac158c91fbcb988b9bf0` |
| License | GPL-3.0 |

The old `tvb-data` GitHub repository is deprecated, and the PyPI package
carries a reduced file set because of size limits, so Zenodo is the
canonical source and the only one this module reads.

### Licensing

`tvb-data` is GPL-3.0; Quiltwright is BSD-3. Nothing is vendored -- the
archive is downloaded at runtime and cached outside the source tree, the
same pattern `pyvista.examples` uses for its own downloads. That keeps the
GPL data out of this repository and out of any Quiltwright distribution.

This is the same line [install.md](install.md) draws around ffmpeg: a
GPL-licensed artifact is something the package fetches on request, never
something it ships or pulls in by default.

If you publish work using these datasets, TVB asks that you cite the
platform; the requested citation is available as
`quiltwright.tvb_data.TVB_CITATION`.

### Dependencies

Loading needs only the standard library and NumPy -- both already core
dependencies. The PyVista bridge (`surface_polydata`,
`connectome_polydata`) needs the `viz` extra:

```bash
poetry install --with viz          # enough for stills and quilts
```

**No ffmpeg.** Nothing in this module encodes video, so nothing here pulls
in `imageio-ffmpeg`. Rendering a TVB scene to a quilt still or an HLD still
needs `viz` only. Video output -- `render_quilt_video()`, `render_hld_video()`
-- is the same optional `video` group it has always been, and finds a system
ffmpeg on `PATH` first.

### Caching

The archive is downloaded once, to `$QUILTWRIGHT_TVB_CACHE` if set,
otherwise to the platform's native per-user cache directory:

| Platform | Location |
|---|---|
| macOS | `~/Library/Caches/quiltwright/tvb` |
| Linux | `$XDG_CACHE_HOME/quiltwright/tvb`, default `~/.cache/quiltwright/tvb` |
| Windows | `%LOCALAPPDATA%\quiltwright\Cache\tvb` |

Resolved by `quiltwright.cache`, which every runtime download shares -- the
Allen mouse atlas in `scripts/render_pyvista_hologram.py` lands in
`allen_ccf` beside `tvb` under the same root. It uses
[`platformdirs`](https://pypi.org/project/platformdirs/), matching PyVista --
which caches its own downloads via `pooch.os_cache` and so puts them in
`~/Library/Caches/pyvista_3` on macOS. Hard-coding `~/.cache` would drop a
337 MB file somewhere non-native on two of the three platforms.

Downloads stream to a temporary file and are moved into place only after the
MD5 check passes, so an interrupted transfer can never leave a truncated
archive behind. Individual files are read straight out of the zip -- the
337 MB is never expanded on disk.

```python
from quiltwright.tvb_data import clear_cache
clear_cache()
```

---

## Datasets

### Surfaces -- `load_surface`, `surface_polydata`

| Name | Points | Triangles | Notes |
|---|---|---|---|
| `cortex_16384` | 16,384 | 32,760 | The workhorse -- closed, and a comfortable quilt budget |
| `cortex_80k` | 81,924 | 163,840 | Detail pass |
| `cortex_2x120k` | 283,380 | 566,752 | Two hemispheres; decimate before a view sweep |
| `inner_skull_4096` / `outer_skull_4096` / `outer_skin_4096` | 4,096 | 8,188 | Nested head shells |
| `inner_skull_642` / `outer_skull_642` | 642 | 1,280 | Coarse variants |
| `scalp_1082` | 1,082 | 2,160 | |
| `face_8614` | 8,614 | 17,224 | |
| `macaque_147k` | 147,460 | 294,912 | Macaque cortex |

### Connectomes -- `load_connectivity`, `connectome_polydata`

`connectivity_66`, `_68`, `_76`, `_80`, `_96`, `_192`, `_998`, and
`macaque_84`. Each carries a weights matrix, a tract-length matrix, and
named 3-D region centers.

### Region mappings -- `load_region_mapping`

Per-vertex parcellation labels, paired by vertex count:

| Mapping | Vertices | Pairs with |
|---|---|---|
| `regionMapping_16k_76` | 16,384 | `cortex_16384` |
| `regionMapping_80k_80` | 81,924 | `cortex_80k` |
| `regionMapping_147k_84` | 147,460 | `macaque_147k` |
| `regionMapping_16k_192` | 16,500 | *no surface in the archive matches* |

`surface_polydata` validates the pairing and raises rather than producing a
mis-colored mesh.

### Sensors -- `load_sensors`

EEG (`eeg_63`, `eeg_brainstorm_65`, `eeg_unitvector_62`), MEG (`meg_151`,
`meg_248`, `meg_brainstorm_276`) and sEEG (`seeg_39`, `seeg_588`,
`seeg_brainstorm_960`) electrode positions.

---

## Usage

```python
from quiltwright.tvb_data import load_surface, load_connectivity

vertices, triangles, normals = load_surface("cortex_16384")   # downloads once
conn = load_connectivity("connectivity_76")

conn.weights.shape        # (76, 76) structural connection strengths
conn.tract_lengths.shape  # (76, 76) fiber lengths in mm
conn.centres.shape        # (76, 3)  region centers in mm
conn.labels[:3]           # ['rA1', 'rA2', 'rAMYG']
conn.degree               # weighted degree per region
```

A cortex on a Looking Glass, end to end:

```python
import pyvista as pv
from quiltwright import QUILT_PRESETS, render_quilt, save_quilt
from quiltwright.tvb_data import surface_polydata

cortex = surface_polydata(
    "cortex_16384", region_mapping="regionMapping_16k_76", smooth_iters=30
)
p = pv.Plotter(off_screen=True)
p.add_mesh(cortex, scalars="region", cmap="turbo", smooth_shading=True,
           show_scalar_bar=False)

spec = QUILT_PRESETS["portrait"]
save_quilt(render_quilt(p, spec), "cortex", spec)
```

A connectome -- region centers sized by weighted degree, strongest tracts as
weight-colored tubes, inside a translucent cortex:

```python
from quiltwright.tvb_data import connectome_polydata, surface_polydata

shell = surface_polydata("cortex_16384", smooth_iters=30)
nodes, edges = connectome_polydata("connectivity_76", percentile=90.0)

p = pv.Plotter(off_screen=True)
p.add_mesh(shell, color="#4477aa", opacity=0.06, smooth_shading=True)
p.add_mesh(edges, scalars="weight", cmap="autumn", show_scalar_bar=False)
p.add_mesh(nodes, color="#ffe8a0")
```

A full connectome is far too dense to fuse as a hologram -- `percentile`
keeps only the strongest tracts. 90 is a good default at 76 regions; push it
to 99 at 998.

### Choosing a triangle budget

A quilt renders the whole scene **once per view** -- 48 times on a Portrait.
`cortex_16384` sweeps comfortably; `cortex_2x120k` at full density does not.
Use `decimate` for quilts, and keep it low for HLD video, which is one
ordinary render per frame.

Decimating a parcellated surface is safe: region labels are re-assigned to
the decimated vertices by nearest neighbor, because interpolating between
region 3 and region 70 would be meaningless.

### Color on an HLD

White is transparent on a Hololuminescent Display, so avoid pure white for
any surface meant to be visible. `turbo` is safe for parcellations; clamp
the light end of a sequential ramp.

---

## A ready-made CLI

[WaveRider](https://github.com/Flux-Frontiers/waverider) wires scene presets
and a command line on top of this module:

```bash
waverider-voxel-viz --tvb-demo --tvb-dataset connectome --quilt portrait --cast
```

See its `docs/waverider/tvb_data.md` for the preset list.

---

## Archive quirks the loader absorbs

The TVB archive is not uniformly formatted. These are handled transparently,
and each is covered by a test:

| Quirk | Where | Handling |
|---|---|---|
| **1-based triangle indices** | `cortex_2x120k` | Detected and rebased. Loading as-is yields an index one past the last vertex -- a silently corrupt mesh, not an error. |
| **Split hemispheres** | `cortex_2x120k` | `verticesl`/`verticesr` concatenated, right-hemisphere indices offset by the left vertex count, after each side is rebased independently. |
| **Folder-nested members** | `macaque_147k` | Members matched by basename. |
| **Float-encoded indices** | `macaque_147k` | `1.0000000e+00` parsed and checked for integrality. |
| **bz2-compressed members** | `connectivity_68`, some sensors | Decompressed transparently. |
| **Empty normals stub** | `face_8614` | A 1-byte `vertex_normals.txt` reads as "no normals"; PyVista computes its own. |

---

## Not yet wired up

The archive holds more than this module exposes:

- **Simulated time series** -- `nifti/time_series_152.nii.gz` and
  `gifti/sample.time_series.gii`. These would drive a per-vertex scalar over
  time, turning an HLD turntable into an activity animation rather than a
  static orbit. Needs a NIfTI/GIFTI reader (`nibabel`).
- **Mouse brains** -- `mouse/allen_2mm` and `mouse/calabrese`, stored as HDF5
  and NIfTI volumes rather than plain-text surfaces. Note the overlap with
  the Allen CCFv3 atlas that `scripts/render_pyvista_hologram.py` already
  downloads directly; worth unifying if both get used.
- **Sensors in a scene** -- loadable today via `load_sensors`, but no helper
  yet places electrodes over the scalp shell.
- **Projection matrices** and **local connectivity** -- present in the
  archive, no obvious holographic use yet.

---

*Part of Quiltwright -- https://github.com/suchanek/quiltwright*
