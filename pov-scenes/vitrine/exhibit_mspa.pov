// MSPA PORIN in the standard vitrine.  Written by scripts/make_exhibit.py.
//
// Regenerate the geometry with:
//   python scripts/make_exhibit.py MSPA

#version 3.7;
global_settings { assumed_gamma 1.0 }

#include "colors.inc"
#include "textures.inc"
// A cartoon carries its own textures; no atom includes needed.

#declare VIT_LABEL = "MSPA PORIN";
#declare VIT_FILL = 1.12;
#include "vitrine.inc"
#include "mspa_cartoon.inc"

Vitrine_Report()

Vitrine_Mount(mspa_cartoon, mspa_cartoon_enclosing_radius)
Vitrine_Case()
Vitrine_Plinth()
Vitrine_Room()
Vitrine_Lights()
Vitrine_Camera()
