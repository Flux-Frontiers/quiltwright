// GFP as a Richardson cartoon, in the standard vitrine.
//
// Note what is *not* here: no atoms_vdw.inc, no atoms2.inc.  A cartoon
// carries its own textures, so the only include is the geometry itself.
//
// gfp_cartoon.inc is generated, and gitignored because it is large.  Make it with:
//
//   python -c "from quiltwright.pymol import cartoon_inc; \
//              cartoon_inc('1ema.cif.gz', 'pov-scenes/vitrine/gfp_cartoon.inc')"
//
// where 1ema.cif.gz came from
// https://files.rcsb.org/download/1ema-assembly1.cif.gz

#version 3.7;
global_settings { assumed_gamma 1.0 }

#include "colors.inc"
#include "textures.inc"

#declare VIT_LABEL = "GFP CARTOON";
#include "vitrine.inc"
#include "gfp_cartoon.inc"

Vitrine_Report()

Vitrine_Mount(gfp_cartoon, gfp_cartoon_enclosing_radius)
Vitrine_Case()
Vitrine_Plinth()
Vitrine_Room()
Vitrine_Lights()
Vitrine_Camera()
