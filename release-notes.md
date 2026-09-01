# Release Notes -- v0.11.0

> Released: 2026-08-31

This release closes the loop between a rendered scene and where people
actually see it every day: the desktop. `quiltwright dynamic` turns a set of
stills into a real macOS Dynamic Desktop file, and POV-Ray scenes gain the
day/night lighting to make that worth doing without hand-rolling `clock`
tricks. `bj_holo_2026.pov` is the first scene fully framed and lit for it.
Underneath, a duck-typed lens contract becomes a real protocol, and the
three rendering backends stop repeating the same handful of helpers.

## What changed

**`quiltwright dynamic` packs stills into a macOS Dynamic Desktop HEIC.**
It writes the same appearance (light/dark), solar (altitude/azimuth), and
time-of-day (`h24`) metadata Apple ships in `The Lake.heic` and
`Sonoma.heic`, onto image 0 of the packed file -- so a woven `_native_`
Looking Glass quilt or an ordinary 2-D still can drive macOS's own
light/dark wallpaper cycle. Woven frames encode lossless 4:4:4 so the
hologram survives the trip; ordinary stills may be lossy. `quiltwright
wallpaper` already installs the result by serial, same as it does a PNG.
Encoding lives behind the new `heic` extra (`pillow-heif`).

**POV-Ray scenes get `lighting=` and `sun=` instead of hand-rolled `clock`
tricks.** `clock` is POV-Ray's animation parameter (`+K`) and has nothing
to do with wall-clock time, so Dynamic Desktop lighting needed its own
knobs. `lighting=` and `sun=` on `render_pov_quilt` and `render_pov_views`
add them: `lighting="light"` leaves a scene's own lights alone, since an
additive key would wash the plate out; `lighting="dark"` appends a cool
moon and a short fog so Dark Mode still reads as night against an authored
white key; `sun=(altitude, azimuth)` sets an explicit parallel sun for
solar frames. A scene opts in through the `QW_Appearance` /
`QW_SunAltitude` / `QW_SunAzimuth` declares.

**`bj_holo_2026.pov` is framed and lit for the desktop.** The bell jar's
glass Y scale drops from 10.5 to 9.5 (the DNA inside is untouched) so the
dome leaves a sky band above it, and the title baseline moves from
`y=62.45` to `y=61.30` -- low enough that a macOS menu bar doesn't clip the
caps, high enough that the letters still clear the glass. Paired with
`lighting="light"|"dark"`, it's the normal plate by day and a fog night
after dark, on both a Mac and a woven Looking Glass HEIC.

**`HasLens` replaces the private lens protocol.** `depth_budget` and
`format_depth_budget` read a narrow `fov` / `focal_distance` surface;
`HasLens`, lazy-exported from the package root, makes that contract public
so anything shaped like a lens -- every `QuiltCamera`, or a tiny namespace
like `lfd`'s `_Lens` -- satisfies it without a special case. `PovCamera.aimed`
and `CyclesCamera.aimed` now share a parity suite in `tests/test_camera.py`
so that documented twin contract can't drift quietly.

**Shared helpers move into `quiltwright.runtime`.** `require_pyvista`
replaces three identical copies that had accumulated in `lfd`, `hld`, and
`tvb_data`; `triple` replaces the twin `_triple` helpers in `povray` and
`cycles`, imported there as `_triple` so call sites stay private.

## Upgrading

No breaking changes -- `pip install -U quiltwright` is enough. Packing a
Dynamic Desktop HEIC needs the new `heic` extra: `pip install
"quiltwright[heic]"`.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
