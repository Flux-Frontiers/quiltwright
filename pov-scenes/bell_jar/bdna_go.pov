//
//
// This data and its resulting derivative images are
// (c) 1993-1996, 2026, Eric G. Suchanek, Ph.D.
//
// The 1993-1996 term covers the model, inherited from bna7_full.inc; 2026
// covers this file, which is a new composition of it.
//
// The user is hereby licensed non-commercial use of these
// data and images, provided that this copyright notice remain
// attached to all necessary data files.
//
//
// PDB2POV (UNIX) atom input prepared by pdb2pov 10/01/96 14:35:22
//      Atoms: 758
//      Extent: Xmin: -13.118 Xmax: 14.283,
//              Ymin: -15.454, Ymax: 16.551
//              Zmin: -25.488 Zmax: 23.591
//      Enclosing Sphere: 26.475
//
// The B-DNA from DNA Under Glass, out of the jar, for the Looking Glass Go.
//
// The duplex is the one bj_portrait.pov and bj_holo_2026.pov put under the
// dome -- bna7_full_obj, space-filling, as pdb2pov wrote it in 1996 -- stood
// upright the same way they stand it: `rotate x*90` tips the long axis, which
// the model carries along z, onto world y.  Nothing else from the still life
// comes with it.  No jar, no pedestal, no sea: on a 6-inch panel the molecule
// is the whole exhibit.
//
// Upright, the helix is 27.4 units wide and 49.1 tall, a 0.56 frame -- the
// Go's own 9:16 to within a few percent, so a narrow panel holds it without
// cropping either axis or leaving a band of empty frame.
//
// It floats against a dark gradient rather than a sky.  A light-field display
// reads a subject against a dark ground as standing in front of the glass,
// and the three lights are placed for that: a key high on the left, a dim
// fill low on the right so the grooves keep their shape in shadow, and a rim
// from behind that outlines the backbone against the dark.

#version 3.0
global_settings { assumed_gamma 1.8 }

#include "colors.inc"
#include "shapes.inc"
#include "textures.inc"

// Declarations only -- it also pulls in atoms_vdw.inc, atoms2.inc and
// bell_jar.inc, none of which places anything in the scene.
#include "bna7_full.inc"


// Stand the duplex upright, then centre it on its own bounding box so the
// origin is the middle of the molecule.  Same order bj_portrait.pov uses:
// tip first, then measure, since the long axis is not y until after the tip.
#declare BDNA_Go_Tipped = object { bna7_full_obj rotate x*90 }
#declare BDNA_Go_Centre = (min_extent(BDNA_Go_Tipped) + max_extent(BDNA_Go_Tipped)) / 2;

// Spin about the upright axis, for a turntable render.  Undeclared for a
// still or a quilt, the same QW_* convention bj_holo_2026.pov follows.
#ifndef (QW_Spin_Angle) #declare QW_Spin_Angle = 0; #end

object {
  BDNA_Go_Tipped
  translate -BDNA_Go_Centre
  rotate y*QW_Spin_Angle
}


// Eye a little above the molecule's middle, aimed at it.  Distance 113.64
// and a 26-degree vertical lens give a frame 52.5 units tall at the subject,
// so the 49.1-unit helix fills 94% of the height and its 27.4-unit width 93%
// of the 29.5 units a 9:16 frame is wide there.  |direction| = 0.5/tan(13)
// = 2.165746 with a unit `up`; `right` is the aspect itself.
//
// 26 rather than a roomier 30 is for depth, not size.  A space-filling model
// hides its own far side, so what the display can separate is only the
// front ~14 units of a 27-unit-wide subject; filling the frame is what turns
// that into parallax.  On the Go at its native 54-degree cone this measured
// 1.44 px of adjacent-view disparity, against 1.24 px at 30 degrees.  23
// reaches 1.64 but crops the ends of the helix.  The edges of the duplex sit
// at mid-depth, near the focal plane, so the tight width does not clip in
// the outer views.  A narrow lens is deliberate in any case: a wide one
// exaggerates the near atoms against the far ones, which the display then adds
// its own parallax on top of.
camera {
   location  < 0, 12, -113 >
   direction < 0, 0, 2.165746 >
   up        < 0, 1, 0 >
   right     < 0.5625, 0, 0 >
   look_at   < 0, 0, 0 >
}


// Key: high, left, in front.
light_source { < -70, 90, -110 > color White }

// Fill: low, right, dim.
light_source { < 90, -30, -80 > color Gray35 shadowless }

// Rim: behind and above, so the backbone separates from the dark ground.
light_source { < 20, 70, 140 > color Gray55 shadowless }


sky_sphere {
  pigment {
    gradient y
    color_map {
      [0.0 color rgb < 0.00, 0.00, 0.02 >]
      [0.5 color rgb < 0.02, 0.03, 0.08 >]
      [1.0 color rgb < 0.05, 0.07, 0.18 >]
    }
    scale 2
    translate -1
  }
}
