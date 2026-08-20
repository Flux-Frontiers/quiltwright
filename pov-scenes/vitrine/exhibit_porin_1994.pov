// The 1994 porin mesh, in the standard vitrine.
//
// The companion to exhibit_ompf_cartoon.pov: same room, same camera, same
// plinth, same lighting.  What differs is only the geometry -- 7,835
// triangles from a lost 1994 exporter against 75,792 from a PDB ID.
//
// porin_1994.inc includes ../porin/3porin.inc, so POV-Ray needs that
// directory on its library path:
//
//   povray +Iexhibit_porin_1994.pov -L../porin -L.

#version 3.7;
global_settings { assumed_gamma 1.0 }

#include "colors.inc"
#include "textures.inc"

#declare VIT_LABEL = "PORIN 1994";
#include "vitrine.inc"
#include "porin_1994.inc"

Vitrine_Report()

Vitrine_Mount(porin_1994, porin_1994_enclosing_radius)
Vitrine_Case()
Vitrine_Plinth()
Vitrine_Room()
Vitrine_Lights()
Vitrine_Camera()
