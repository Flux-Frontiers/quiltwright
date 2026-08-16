# Release Notes — v0.6.0

> Released: 2026-08-16

Quiltwright 0.6.0 closes the last gap between rendering a quilt and seeing it
on a panel: one call now writes the file and hands Looking Glass Bridge the
path to it, and a quilt can be scaled down for fast casting without breaking
the tiling that makes it a light field.

## What changed

**Save and cast in one call.** `save_quilt` takes the pixel array and
`cast_quilt` takes a path, and confusing the two is invisible until a display
is connected — the caster's `ndarray` error arrives minutes into a ray-traced
render, at the worst possible moment. `save_and_cast_quilt()` composes the two
correctly: it confirms the file is on disk before contacting Bridge, and a
failed cast comes back as a `(path, error)` return rather than an exception,
so a Bridge that isn't running never costs you the render. Consumers had been
writing this wrapper by hand; now it ships in the box.

**Scaling that keeps the tiling.** Casting at full preset size is rarely worth
the wait — Bridge's load time scales with the PNG's area, so halving the
linear size quarters it. But scaling a quilt naively stops it dividing evenly
into the view grid, landing every view on a fractional pixel boundary and
smearing the light field. `QuiltSpec.scaled(factor)` rounds the new dimensions
down to a multiple of the tile grid so views stay pixel-aligned, and refuses
factors that would leave less than a pixel per tile.

## Upgrading

Nothing to migrate: both additions are new API, exported from the package
root, and no existing behaviour changed. Replace any hand-rolled save-then-cast
helper with `save_and_cast_quilt()` and drop your own size arithmetic in
favour of `spec.scaled(0.5)`.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
