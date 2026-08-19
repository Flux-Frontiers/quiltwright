// F1-ATP SYNTHASE in the standard vitrine.
//
// Render the still at the vitrine's own aspect (16:9 by default):
//   povray +Iexhibit_f1atpase.pov +W1920 +H1080 +Q11 +A0.3 \
//          -L../../../pdb2pov/python/src/pypdb2pov/include
//
// The quilt is rendered by quiltwright with this file as the scene; the
// camera numbers it needs are printed by Vitrine_Report() at parse time.

#version 3.7;
global_settings { assumed_gamma 1.0 }

#include "colors.inc"
#include "textures.inc"
#include "atoms_vdw.inc"     // radii set; -c would want atoms_covalent.inc
#include "atoms2.inc"        // element textures

#declare VIT_LABEL = "F1-ATP SYNTHASE";
#include "vitrine.inc"
#include "f1atpase.inc"

Vitrine_Report()

Vitrine_Mount(f1atpase, f1atpase_enclosing_radius)
Vitrine_Case()
Vitrine_Plinth()
Vitrine_Room()
Vitrine_Lights()
Vitrine_Camera()
