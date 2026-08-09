# PyVista Dataset Ideas for Holograms

**Source**: `pyvista.examples.downloads` (checked directly against the
installed package, PyVista 0.48.4 — `.venv/lib/python3.12/site-packages/pyvista/examples/downloads.py`)

A survey of PyVista-reachable datasets worth feeding into the
[LFD](lfd.md) / [HLD](hld.md) pipeline, focused on subjects with real depth
structure — the thing that actually makes a quilt fuse into something worth
looking at.

---

## Geography / topography

These have strong, legible elevation relief — good raw material for
parallax. Check the [disparity budget](povray.md) once you pick a camera
setup; global-scale datasets can blow it if the near/far range isn't tamed.

| Function | Type | What it is | Notes |
|---|---|---|---|
| `examples.download_crater_topo()` + `download_crater_imagery()` | `ImageData` + `Texture` | Mt. St. Helens crater DEM with a draped aerial GeoTIFF | PyVista's own "Topographic Map" tutorial. A real crater bowl plus a photo-realistic texture — good first candidate, controlled depth range. |
| `examples.download_st_helens()` | `ImageData` | Mt. St. Helens post-eruption DEM | `dataset.plot(cmap="gist_earth")`. Terrain relief alone, no texture — simpler than the crater pair above. |
| `examples.download_topo_global()` | `PolyData` | Whole-Earth topography + bathymetry, as a sphere | Full globe, pole-to-trench depth range. Striking, but the depth range is huge — expect to need a narrow view cone or a tight focal-plane placement. |
| `examples.download_topo_land()` | `PolyData` | Land-only global elevation | `clim=[-2000, 3000], cmap="gist_earth"`. Same globe without the ocean floor — cleaner, smaller depth budget than the full version. |
| `examples.download_damavand_volcano()` | `ImageData` | Mt. Damavand (Iran) volumetric data | Isosurface or volume-render. A single conical peak is easy to reason about depth-wise — good for a first hologram test. |

Zero-download option for pipeline iteration: `examples.load_random_hills()`
is synthetic rolling terrain, useful for testing the quilt/sweep code before
pointing it at a real multi-MB DEM.

---

## Brain volumes

### Human — native to PyVista

Checked directly against the installed package: no dataset named "mouse" or
"mouse brain" exists in `pyvista.examples`. What PyVista ships is human,
and both are volume-render-ready `ImageData` with no download plumbing
needed beyond the `examples.download_*()` call itself:

| Function | What it is | Notes |
|---|---|---|
| `examples.download_brain()` | Classic VTK `brain.vtk` volume — a human head MRI | `dataset.plot(volume=True)`. Used in PyVista's own volume-rendering, slicing, depth-peeling, and moving-isovalue tutorials — well-trodden, predictable behavior. |
| `examples.download_brain_atlas_with_sides()` | `avg152T1_RL_nifti.nii.gz` — the MNI152 averaged human brain template, left/right labeled | `dataset.slice(normal="z").plot(cpos="xy")`. An *averaged* brain (152 subjects) rather than one individual's scan — smoother, less idiosyncratic anatomy than `download_brain()`. |

Both are good, zero-friction volume-render subjects for testing the LFD
volume-sweep path before moving to the much larger Allen mouse data below.

### Mouse — the real volume: Allen Institute CCFv3

The [Allen Mouse Brain Common Coordinate Framework](https://atlas.brain-map.org/)
is a real 3-D mouse atlas built from 1,675 C57BL/6J mice, distributed as
plain NRRD files — no API key, no AllenSDK dependency required:

```
http://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/average_template/average_template_50.nrrd
```

- Resolutions: 10 / 25 / 50 / 100 µm isotropic (`average_template_{res}.nrrd`).
  Start with **50 µm** — the finer volumes get large fast.
- There's also a **labeled** version at the same resolutions:
  `mouse_ccf/annotation/ccf_2017/annotation_50.nrrd` — same shape, but every
  voxel is a brain-region ID instead of grayscale intensity. This is
  probably the more striking hologram candidate: a segmented, colorable
  volume rather than plain grayscale.
- PyVista reads `.nrrd` natively (`pv.read()` / `pv.NRRDReader`), so it
  drops into an `ImageData` volume exactly like `download_brain()` does —
  no extra plumbing needed in `lfd.py` / `hld.py`.

```python
import pyvista as pv

vol = pv.read("average_template_50.nrrd")   # -> pyvista.ImageData
vol.plot(volume=True, cmap="bone")
```

Allen Institute data is free for non-commercial use under their terms — see
the [data license](https://alleninstitute.org/terms-of-use/) before any
redistribution.

---

## Other strong-depth candidates worth a look

Not geography, but structurally similar in that they have real
self-occlusion and depth layering rather than a flat relief:

- `examples.download_frog()` / `examples.load_frog_tissues()` — classic
  segmented full-body CT scan (frog), colorful multi-organ volume.
- `examples.download_whole_body_ct_male()` / `_female()` — human whole-body
  CT, much larger and more detailed than the frog.
- `99-advanced/gyroid`, `99-advanced/atomic_orbitals`,
  `99-advanced/sphere_eversion` — abstract math surfaces with deep
  self-occlusion; useful as parallax stress tests outside the "real world
  scan" category.

---

## Sources

- [pyvista.examples.downloads — PyVista docs](https://docs.pyvista.org/api/examples/_autosummary/pyvista.examples.downloads.html)
- [Topographic Map — PyVista docs](https://docs.pyvista.org/examples/02-plot/topo_map.html)
- [Allen Mouse CCF — accessing and using related data and tools](https://community.brain-map.org/t/allen-mouse-ccf-accessing-and-using-related-data-and-tools/359)
- [Allen Institute `average_template` download index](http://download.alleninstitute.org/informatics-archive/current-release/mouse_ccf/average_template/)
- [pyvista.NRRDReader — PyVista docs](https://docs.pyvista.org/api/readers/_autosummary/pyvista.nrrdreader)
