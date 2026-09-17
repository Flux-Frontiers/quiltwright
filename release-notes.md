# Release Notes -- v0.14.1

> Released: 2026-09-17

A small release that fixes the PyVista path's framing and depth report.
Both bugs came to light when another agent wrote against the library from
outside the repository: its focal plane landed at 30.5 scene units when the
scene called for 23.4, and nothing in the output said so. The library had
two calls that must describe the render `render_quilt()` is about to make,
and neither could be told enough about that render to do it.

## What changed

**`frame_and_focus()` takes `spec=`.** It fits the camera to the scene at
the plotter's current window aspect, but `render_quilt()` resizes that
window to the display aspect before sweeping. A caller has to size the
window correctly beforehand, and the natural choice, the quilt tile, is
wrong wherever tile and view shapes differ: `16-landscape` tiles are
960x720 (4:3) while its views are 1280x720 (16:9). On a test torus the
tile-shaped window put the focal plane at 34.3 instead of 26.2. With
`spec=`, `frame_and_focus()` sets the window through the same helper
`render_quilt()` uses, so there is nothing for the caller to get right.

**`depth_report()` takes `view_cone=`.** `render_quilt()` has always
accepted a cone override, and the render scripts and CLI cap wide panels at
35 degrees. `depth_report()` had no matching argument, so a render capped
through `render_quilt(..., view_cone=35)` on `16-landscape` was reported at
the preset's 50 degrees -- 8.58 px of disparity against a real 5.80, with no
warning. The report now takes the same override.

Both docstrings also say to frame and report before adding a floor or
backdrop: both functions measure the plotter's full bounds, and a floor
that reaches past the camera is otherwise measured as the subject. The new
parameters are keyword-only and optional, so existing calls are unchanged.
