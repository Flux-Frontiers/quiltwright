# Release Notes -- v0.15.1

> Released: 2026-09-22

Every PyMOL cartoon this library has produced was the mirror image of the
molecule it claimed to be. The folds were right, the colours were right,
and the secondary structure read cleanly, so nothing looked wrong. But every
alpha-helix turned the wrong way. A mirrored protein still looks like a
protein, which is why this survived an end-to-end render of F1-ATP synthase
that was written up at the time as proof the coordinate handling could be
trusted.

It came to light while rendering fibrinogen for a disulfide chemist, where
a left-handed helix would have been the first thing noticed. A lit
alpha-helix, rendered through both backends and compared with PyMOL's own
ray trace of the same export, showed the enantiomer every time. This release
fixes both backends and adds tests that would have caught it.

## What changed

**PyMOL cartoons now have the handedness of the molecule.** With the
identity view the export script sets, `cmd.get_povray()` writes the model's
own right-handed coordinates, offset only by the view centre and camera
pull-back; PyMOL's POV header compensates with a right-handed camera rather
than by reflecting the geometry. `cartoon_inc()` and `cartoon_obj()` both
assumed the opposite. The POV-Ray include therefore skipped the z flip
pypdb2pov has always applied to atoms, and the Cycles OBJ negated a z that
needed no conversion. The include now ends with `scale <1, 1, -1>`, and the
OBJ keeps PyMOL's coordinates and winding. Atom scenes from pypdb2pov were
never affected.

**Tests that measure geometry, not strings.** A cartoon ribbon runs through
its own CA atoms, so the new tests export crambin through each backend, put
the mesh where the renderer will put it, and measure how far each CA sits
from it. Correct handedness gives 0.27 A on average; the mirror image gives
2.80 A. Every earlier test of this module checked the shape of the include
and would have passed either way.

**What upgrading changes.** Any camera placed for the old cartoon geometry
now sees the molecule from its other face. That view is the correct one, and
it now matches a pypdb2pov atom scene of the same structure in the same
vitrine, but a composition tuned against the mirrored render may want
re-aiming. The gallery's OmpF cartoon is re-rendered with the fix.

**`make_exhibit.py` records a command that works.** The scene header it
writes named the file stem where the PDB ID belongs, so an exhibit made with
`--name` recorded a regenerate command the RCSB rejects. The header now
carries the ID plus any `--name` and `--label`.
