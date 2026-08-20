// The OmpF porin trimer as a Richardson cartoon, in the standard vitrine.
//
// The archive aesthetic, regenerated: pov-scenes/porin/3porin.inc is the
// same subject drawn the same way in 1994, by an exporter nobody has any
// more.  This one comes from a PDB ID and a command line.
//
// Note what is *not* here: no atoms_vdw.inc, no atoms2.inc.  A cartoon
// carries its own textures, so the only include is the geometry itself.
//
// ompf_cartoon.inc is generated, and gitignored because it is large.  Make it with:
//
//   python -c "from quiltwright.pymol import cartoon_inc; \
//              cartoon_inc('2omf.cif.gz', 'pov-scenes/vitrine/ompf_cartoon.inc')"
//
// where 2omf.cif.gz came from
// https://files.rcsb.org/download/2omf-assembly1.cif.gz

#version 3.7;
global_settings { assumed_gamma 1.0 }

#include "colors.inc"
#include "textures.inc"

#declare VIT_LABEL = "OMPF PORIN";
#include "vitrine.inc"
#include "ompf_cartoon.inc"

Vitrine_Report()

Vitrine_Mount(ompf_cartoon, ompf_cartoon_enclosing_radius)
Vitrine_Case()
Vitrine_Plinth()
Vitrine_Room()
Vitrine_Lights()
Vitrine_Camera()
