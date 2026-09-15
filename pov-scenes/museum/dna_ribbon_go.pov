//
//
// This data and its resulting derivative images are
// (c) 1995-1999, 2026, Eric G. Suchanek, Ph.D.
//
// The 1995-1999 term covers the DNA cartoon, inherited from museum.pov and
// dna_cartoon.inc; 2026 covers this file, which is a new composition of it.
//
// The user is hereby licensed non-commercial use of these
// data and images, provided that this copyright notice remain
// attached to all necessary data files.
//
//
// The metallic DNA ribbon from the museum's top alcove, on its own, for the
// Looking Glass Go.
//
// obj_DNA_Cartoon -- 3450 smooth triangles in silver -- at its own scale, not
// the 0.45 the museum hangs it at: 17.8 units wide, 41.5 tall and 19.6 deep,
// with its long axis already vertical.  Framed alone and tight.
//
// An earlier cut hung it between the museum's two silver dishes inside a
// crystal column.  On the Go that read as a capsule and conveyed little depth:
// the dishes and the glass were broad smooth surfaces with nothing for the
// eye to fuse on, and they took the depth budget the ribbon needed.  The
// ribbon alone is a better subject for a light-field display than it looks
// in a still.  It is open -- the far strand shows through the near one's
// gaps -- so its whole 19.6-unit diameter is visible depth, where a
// space-filling model shows only its front half.
//
// Out of the room, the metal loses what it reflected.  A metallic finish shows
// its surroundings, and against the dark ground a hologram wants, silver
// reflects dark and reads as grey.  So the reflections are supplied by three
// soft panels that are `no_image`: present in every reflection, absent from
// the frame.  The ribbon keeps its bright highlights and the backdrop stays
// dark.  That is why this file is POV-Ray 3.7 syntax -- `no_image` and
// `emission` postdate the 3.0 the museum is written in -- with the 1990s
// include parsed under the version it was written for.

#version 3.7;
// The strands reflect one another; the default 5 bounces run out inside the
// helix and leave black patches on the inner faces.
global_settings { assumed_gamma 1.0 max_trace_level 10 }

#include "colors.inc"
#include "textures.inc"

// Converted to POV-Ray 2.2 by WCVT2POV, and never given a pragma of its own:
// parse it under 3.0, as museum.pov does, then restore.
#declare DNA_Ribbon_Go_Version = version;
#version 3.0;
#include "dna_cartoon.inc"
#version DNA_Ribbon_Go_Version;


// Centre the ribbon on its own bounding box.  dna_cartoon.inc ends with a
// `translate 21*y`, so the origin is not the middle until this undoes it.
#declare DNA_Ribbon_Centre = (min_extent(obj_DNA_Cartoon) + max_extent(obj_DNA_Cartoon)) / 2;

#ifndef (QW_Spin_Angle) #declare QW_Spin_Angle = 0; #end

object {
  obj_DNA_Cartoon
  translate -DNA_Ribbon_Centre
  rotate y*QW_Spin_Angle
}


// A 26-degree vertical lens at distance 95.34 frames 44.0 units of height at
// the subject, so the 41.5-unit ribbon fills 94% of it; the 24.8 units of
// width a 9:16 frame has there hold its 17.8 at 72%.  |direction| =
// 0.5/tan(13) = 2.165746 with a unit `up`; `right` is the aspect itself.
camera {
   location  < 0, 8, -95 >
   direction < 0, 0, 2.165746 >
   up        < 0, 1, 0 >
   right     < 0.5625, 0, 0 >
   look_at   < 0, 0, 0 >
}


// Key from the front and above, as the museum's spotlight was.
light_source {
  < 0, 40, -80 > color Gray70
  spotlight
  point_at < 0, 0, 0 >
  radius 15
  falloff 35
  tightness 20
}

// A dim fill from the side, so the far strand keeps its form.
light_source { < -80, 15, -40 > color Gray25 shadowless }


// Reflection panels.  no_image hides them from the camera; the metal still
// sees them.  Large, soft and emissive, the way a studio softbox is.
#declare Softbox = box {
  < -1, -1, 0 >, < 1, 1, 0.1 >
  texture { pigment { color White } finish { emission 1 diffuse 0 } }
  no_image
  no_shadow
}
object { Softbox scale < 50, 16, 1 >  rotate x*-60  translate < 0, 80, -40 > }   // overhead, front
object { Softbox scale < 16, 50, 1 >  rotate y*-70  translate < -90, 0, -15 > }  // left
object { Softbox scale < 14, 40, 1 >  rotate y*70   translate < 90, 5, 25 > }    // right, behind


// Darker than the first cut's: at assumed_gamma 1.0 small values are lifted
// on output, and that backdrop read navy-grey rather than dark.
sky_sphere {
  pigment {
    gradient y
    color_map {
      [0.0 color rgb < 0.000, 0.000, 0.002 >]
      [0.5 color rgb < 0.002, 0.002, 0.007 >]
      [1.0 color rgb < 0.004, 0.006, 0.018 >]
    }
    scale 2
    translate -1
  }
}
