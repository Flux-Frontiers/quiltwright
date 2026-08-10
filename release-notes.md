# Release Notes — v0.3.1

> Released: 2026-08-10

A documentation release. The view sweep that feeds a hologram printer has been
in the package since 0.2.0, but the README treated it as an aside — one
paragraph tucked in after two display technologies had already had their say.
It is now a third output: a branch in the pipeline diagram, a section in the
quick start, and a status said out loud rather than implied. In development.

## What changed

**The LitiHolo path reads as an output.** The diagram gained a branch for it
and a `view sweeps` line in the middle box, and the column it sits in is
labelled "outputs" rather than "displays", because a printer is not a display.
A new *Send it to a hologram printer* section runs `LITIHOLO_SWEEP` through
`render_pov_views()` end to end — why 23 views cannot be a quilt grid, where
the frames land, and what the sweep is and is not.

What it is not travels with it, in each place a reader might stop: quiltwright
emits a sweep matching LitiHolo's published specification, which is a narrower
claim than compatibility with the printer. Nothing has been through the
printer's software. Whether a hogel slicer wants off-axis frusta or a toe-in
arc is still open, and so is whether 2.05° between views is too coarse. This
path is POV-Ray only.

**The worked example fails on purpose.** It prints `format_depth_budget()`
before it renders anything, and the museum at a 45° cone reports ~43 px of
adjacent-view disparity against an ~8 px ghosting threshold. That is the report
doing its job — a number worth having before the ray-tracer starts, not after —
and it seemed more useful than an example framed to look effortless.

**A consistency pass over the surrounding docs.** LitiHolo is spelled with the
capital H the company uses, in all five places it appears. The coarse-sampling
ratio is 2.75×, not the 2.7× that four files had rounded it down to; 45° over
22 intervals against 35° over 47 is 2.747. `render_pov_views()`'s docstring had
asserted that hogels are "no more forgiving than a lens sheet" while all three
prose docs hold that question open, so it now hedges the way they do. The
README's scene-source paragraph finally mentions `quiltwright.tvb_data`, which
0.3.0 added without the README following, and `docs/gallery.md` — which nothing
in the repository linked to — joins the documentation table.

## Upgrading

Nothing to do. No behaviour changed: one docstring was reworded, and every
signature, preset and rendered pixel is identical to 0.3.0. Upgrade only if you
want the version metadata to match.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
