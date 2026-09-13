# ParaView scenes

Source, not output. The sibling of [`pov-scenes/`](../pov-scenes/) for the
ParaView backend: one directory per subject, each holding the `.pvsm` state
file and whatever data it reads.

A state file is the whole session -- pipeline, colour maps, transfer
functions, representations and camera -- so unlike a POV-Ray scene there is
nothing else to carry. `quiltwright paraview <state>.pvsm` hands it back to
ParaView's own `pvpython` and sweeps the camera in place. See
[docs/paraview.md](../docs/paraview.md).

## Data paths are resolved against the working directory

ParaView stores an absolute path to every file a reader opens, and it does
**not** resolve a relative one against the state file's own location -- it
resolves against the process's working directory. The states here are written
with repo-root-relative paths (`paraview-scenes/<subject>/<data>`), so they
load correctly when run from the repository root and nowhere else. `make`
already runs from the root; if you invoke `quiltwright paraview` by hand, do
it from the root too.

The failure mode is silent and worth knowing, because it does not look like a
failure: a state whose data file cannot be found still loads, still reports a
plausible camera, and still renders -- an empty scene with the colour legend
floating on the background. If a render comes back as bare background plus a
scalar bar, the reader found nothing. Check the path before anything else.

| Subject | Data | Render |
|---|---|---|
| `mount-hood/` | `terrain.csv`, 9 MB | `make quilt-mount-hood` |

## mount-hood

Mount Hood, Oregon, as an elevation surface coloured by height. The data and
the original state file come from
[Mike Bailey's ParaView course page](https://web.engr.oregonstate.edu/~mjb/paraview/)
at Oregon State University, distributed there as `Examples.zip` for teaching
use; `terrain.csv` is his, unmodified.

Two things were changed from the state he ships, both camera-only -- the
pipeline and colour map are as distributed:

- **The data path.** His state points at `Y:\ParaView\Data\terrain.csv`, a
  drive letter from the machine he authored it on. Repointed at the copy here.
- **An 18 degree downward pitch.** His camera looks down at roughly 50 degrees
  above the horizon, which reads as a relief map rather than a landscape and
  gives a light-field display almost no parallax to work with. One
  `vtkCamera.Elevation(-18)` about the focal point drops it to a raking angle
  where the peak stands above the surrounding ridges.

The release quilt is rendered at `--zoom 1.62`, which is the ceiling for this
framing: it lands at 5.49 px near-view disparity against the 5.5 px soft
threshold `depth_report()` flags. Going further ghosts on the panel. Going
much below wastes the depth the tilt bought.

`make quilt-mount-hood` and `make still-mount-hood` reproduce the release
quilt and the gallery still. Reproduce, not reproduce bit-for-bit: two runs of
the same state differ across about 4% of pixels, almost all of it the specular
sparkle on the terrain, which VTK's renderer does not resolve identically run
to run. The mean difference is 0.26/255 and the images are indistinguishable.
Compare renders by eye or by mean difference, never by checksum.
