# Release Notes -- v0.12.0

> Released: 2026-09-10

This release gives POV-Ray scenes the same Hololuminescent video path
PyVista scenes already had, and then goes further than a plain orbit:
`render_pov_hld_video()` can hold the camera still and spin the subject
instead, which is what a display that only rocks through a limited angle
actually wants. `bj_portrait.pov`'s DNA is the first scene to use it, spinning
in place inside its bell jar rather than swinging out of frame. Named device
presets and a companion script round out the pipeline end to end, and a
long-standing `cast_quilt()` blind spot -- reporting success when Bridge has
nowhere to actually show anything -- is closed.

## What changed

**`render_pov_hld_video()` in `quiltwright.povray`, the POV-Ray counterpart
to `render_hld_video()`.** It orbits a scene's own `PovCamera` around its
`look_at` point (`_orbit_camera`) rather than reaching for PyVista's
`camera.Azimuth`, either as a full 360-degree turntable or a seamless
`sway_degrees` back-and-forth for a display that only rocks through a
limited angle. `suppress_overlays` declares `QW_HLD_Turntable` before the
scene so camera-pinned text authored for one viewpoint -- a title, a
signature -- can guard itself with `#ifndef(QW_HLD_Turntable)` and skip
rendering mirrored from the back of an orbit. `bj_holo_2026.pov`'s title and
signature do this now.

**`spin_degrees`, independent of camera motion entirely.** Rather than
moving the camera, it declares `QW_Spin_Angle` before each frame and sweeps
it linearly over the clip (360 loops seamlessly), so a scene turns its own
subject in place while the composed shot stays exactly as authored. Getting
this right for `bell-jar-portrait` meant pivoting the spin on the DNA's own
tipped-upright bounding-box centre rather than its raw PDB origin or the
pre-tip frame -- either of those sent it swinging out of the jar or tumbling
from standing to lying flat instead of turning where it stands.

**`HLDDeviceSpec` / `HLD_DEVICES` / `MUSUBI` in `quiltwright.hld`.** Named
device presets bundling resolution, fps, encode target, and import-duration
cap. `MUSUBI` -- Looking Glass's small consumer HLD frame -- is measured
from the device's own generated clips rather than a published spec, since
LKG's musubi documentation gives no technical detail at all: 576x1024
portrait, H.264 Baseline, yuv420p, no audio, 30 fps, imports capped at 30s.

**`encode_args` on `render_pov_hld_video()`.** The default still targets
what HLD Author and the big Portrait HLD panels want (HEVC bt709), but a
device that plays video directly instead of through HLD Author may want
something else entirely, so `encode_args` replaces the ffmpeg output
arguments wholesale rather than forcing every HLD-family target through one
codec.

**`scripts/render_still_life_hld_video.py`.** Companion to
`render_still_life_hologram.py`, driving `render_pov_hld_video()` through
the same `SCENES` camera registry so the two renderers agree on
eye/aim/lens/focal-plane without duplicating those measured numbers.

**`bj_portrait.pov`'s glass is real now.** It picks up `bj_holo_2026.pov`'s
`BJ_CRYSTAL` treatment: a proper Fresnel-reflecting dome (`ior` 1.52) in
place of the 1996 jar's non-refracting wall, a thickened `BJ_WALL`, and a
raised `max_trace_level` for the extra bounces a refracting double wall
costs. The doubled grey outline a thickened non-refracting wall shows
edge-on resolves into the single bright band real glass has.

**`cast_quilt()` no longer reports success with nothing to show anything
on.** Bridge's orchestration calls all answer `200` whether or not anything
is actually registered as an output device, so a `cast_quilt()` call could
report success against a Bridge instance with zero devices attached --
confirmed live against a real machine. `cast_quilt` now checks
`available_output_devices()` (the same query `cast --check` already used,
factored out into `quiltwright.bridge` so both share it) before any
playback call and raises when Bridge reports none. Casting to an ordinary
monitor is unaffected.

## Upgrading

No breaking changes -- `pip install -U quiltwright` is enough. HLD video
rendering needs the existing `video` extra: `pip install "quiltwright[video]"`.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
