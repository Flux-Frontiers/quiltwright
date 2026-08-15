# Release Notes — v0.4.0

> Released: 2026-08-14

Two things a downstream project had to work around are now the library's job.
`depth_report()` measures a PyVista scene's depth budget directly, replacing a
forty-line helper that two separate consumers had each written for themselves —
and it models the framing `render_quilt()` actually uses, which those copies did
not. Separately, the `<3.13` ceiling is gone: quiltwright runs on Python 3.13,
and the marker every consumer carried to work around that ceiling can be dropped.

## What changed

**The depth budget for a PyVista scene, without a throwaway camera.**
`format_depth_budget()` has always done the arithmetic, but it takes a
`PovCamera`, so a PyVista caller had to measure the scene by hand and then build
a POV-Ray camera it would never render with, purely as a vehicle for a FOV and a
focal distance. `depth_report(plotter, spec)` reads the plotter's bounds and
camera and returns the report.

The reason it is worth having in the library rather than copied a third time is
the part the copies got wrong. `render_quilt()` narrows the FOV and dollies back
before it sweeps, so a budget measured from the plotter as-composed describes a
picture nobody is going to make — wrong FOV *and* wrong focal distance. On a
torus at the default framing the two answers differ by about 15%, and the sign
of that error depends on the scene, because dollying back partly offsets the
magnification. `depth_report()` takes the `fov` and `zoom` you intend to pass to
`render_quilt()` and models both.

`scene_depths()` exposes the measurement alone, for callers that want numbers
instead of a formatted report, and `DEPTH_LABELS` supplies domain-neutral
defaults — "nearest geometry" rather than any one field's vocabulary. Neither
function mutates the plotter.

**Python 3.13 is supported.** `requires-python` is now `>=3.12,<3.14`. The old
ceiling had no recorded rationale and no dependency behind it — numpy, pillow and
pyvista all support 3.13 — but it propagated outward: any project allowing
`<3.14` had to declare quiltwright marker-gated, because an unmarked declaration
made Poetry reject the entire resolution. CI now runs the suite on both 3.12 and
3.13, so the classifier is a tested claim rather than an assertion.

## Upgrading

Nothing breaks. `depth_report()`, `scene_depths()` and `DEPTH_LABELS` are new
exports; every existing signature and rendered pixel is unchanged.

If you carry the marker-gated declaration — `"quiltwright>=0.3.1; python_version
< '3.13'"` — you can now drop the marker and pin plainly:

```toml
quiltwright = ">=0.4.0"
```

If you hand-rolled a depth budget for a PyVista scene, replace it with
`depth_report(plotter, spec, fov=..., zoom=...)` and pass the same `fov` and
`zoom` you give `render_quilt()`. Expect the numbers to move — that is the fix,
not a regression.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
