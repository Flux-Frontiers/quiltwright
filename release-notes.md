# Release Notes -- v0.8.0

> Released: 2026-08-24

Quiltwright's molecular exhibits had one composition: an object against an
empty sky. This release gives them a room, and gives the room a second way to
draw a molecule at all. A standard museum vitrine now hosts anything `pdb2pov`
or PyMOL can produce -- atoms, bonds, or a full Richardson cartoon -- on one
camera and one depth budget, with no per-structure tuning. Alongside it, the
`molecules` extra resolves straight from PyPI, and a single command runs the
whole pipeline from a PDB ID to a rendered quilt.

## What changed

**A room, not a sky.** `scripts/render_vitrine.py` normalises any molecule to
a unit sphere using the enclosing radius `pdb2pov` already writes into every
file, and builds a stone plinth, a bell jar, and an alcove around that one
number. GFP (31.2 A), hemoglobin (40.3 A), OmpF (51.0 A) and F1-ATPase (79.0
A) -- a 2.5x range of molecular radius -- share one camera and one depth
budget, with no per-structure tuning, because the jar and the plinth taper are
both derived from the same enclosing sphere and cannot clip a structure it
describes correctly. A 2026 cut composed for a 16:9 panel joins the original
1999 room, and `gallery/` moves to the repository top level -- it is
presented work, not a build artefact, and it looked like one buried under
`renders/`, which otherwise holds only output.

**Richardson cartoons, forty years late.** `pdb2pov` has emitted atoms and
bonds since 1993 and nothing else; the archive's one ribbon-cartoon image
survived from a 1993-94 mesh exporter whose output exists in no repository
anywhere. `quiltwright cartoon` closes that gap: `cartoon_inc()` writes an
object-only include on the same contract `pypdb2pov` writes -- origin-centred,
enclosing radius alongside it, no camera, no lights -- so the vitrine and the
rest of the render pipeline need no changes at all to mount one. Getting there
needed a `mesh2` primitive povgen never had, built to honour the flip-z
winding contract explicitly (get the triangle orientation wrong and POV-Ray
lights a mesh from behind, which reads as a lighting bug for an hour), and a
coalescer for PyMOL's `cmd.get_povray()`, which writes one `mesh2` per
triangle: OmpF arrives as 75,792 separate meshes and 41 MB, and leaves as one
mesh POV-Ray parses in a fraction of the time.

**One command, start to finish.** `scripts/make_exhibit.py` fetches a
structure, converts it, composes the scene, renders it, and sweeps the depth
budget -- `python scripts/make_exhibit.py 7AHL --label "ALPHA-HEMOLYSIN"
--quilt` is the whole pipeline. Structures land in `$PDB` (default `~/pdb`),
the convention proteusPy already follows, so a file fetched for one tool is
there for the next. It defaults to the biological assembly rather than the
deposited asymmetric unit, because nothing in a PDB file says the asymmetric
unit can be a fraction of the molecule -- ferritin's is a 24th of a ferritin.

**The `molecules` extra is real.** `pip install "quiltwright[molecules]"` now
resolves straight from PyPI, floored at `pypdb2pov>=0.1.1` because `0.1.0`'s
published metadata mislabels the licence as GPL -- the project is actually
BSD-3-Clause, and PyPI metadata is immutable per release, so refusing to
resolve to `0.1.0` is the only way not to hand someone the mislabelled
version. `render_vitrine.py` now asks the installed package for its include
directory instead of a path that was only ever true on the machine it was
written on.

## Upgrading

Nothing to migrate. `pip install -U quiltwright` or
`pip install -U "quiltwright[molecules]"` for the molecular exhibits, and
`quiltwright cartoon --help` covers the new command.

---

_Full changelog: [CHANGELOG.md](CHANGELOG.md)_
