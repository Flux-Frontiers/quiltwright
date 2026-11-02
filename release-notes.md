# Release Notes -- v0.17.0

> Released: 2026-11-02

A camera that moves needs one render per frame, and until now the Cycles
backend could only make them one call at a time. Each `render_cycles_quilt()`
call starts Blender, imports the scene and rebuilds Cycles' BVH before it
traces a single ray. For a fly-in over a satprint city that start-up was
about a quarter of every frame. This release renders the whole path in one
Blender session.

It is also a security release. quiltwright now requires Pillow 13.0.0, so a
fresh install can no longer resolve the 12.x line and its 41 advisories.

## What changed

**`render_cycles_path()` renders a camera path in one Blender session.** It
takes one `CyclesCamera` per frame and writes `frame_0000.png`,
`frame_0001.png`, and so on, ready for ffmpeg. The scene imports once and
Cycles keeps its BVH across frames, so on a 6 MB city GLB at 64 samples a
1956x1100 frame went from 4.3 s to 3.4 s. With `spec.still()` each frame is a
flat image; with a device preset each frame is a full quilt, for a quilt
video. The lighting rig is placed from the first camera and stays fixed in
the world while the camera moves, so the light does not swing with the view.
A test pins every frame of a path to the quilt its camera renders alone.

**Pillow 13.0.0 is the floor.** quiltwright reads and writes every quilt
through Pillow, and its old range, `pillow>=10.0`, allowed Pillow 12.3.0.
Raising the floor puts the fix in the package metadata, so every fleet repo
that installs quiltwright gets it too. Two lock refreshes also moved certifi,
filelock, urllib3 and virtualenv to patched releases.

## Upgrading

`pip install -U quiltwright`. pip moves Pillow to 13.x if needed. No existing
call changes; `render_cycles_path()` is new.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
