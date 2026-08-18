//
//
// This data and it's resulting derivative images are
// (c) 1993-1996, Eric G. Suchanek, Ph.D.
//
// The user is hereby licensed non-commercial use of these
// data and images, provided that this copyright notice remain
// attached to all neccessary data files.
//
//
// PDB2POV atom input prepared by pdb2pov 11/12/93 09:55:44
//      Atoms:486 */
//      Extent: Xmin: -13.112 Xmax: 14.289,
//              Ymin: -22.614, Ymax: 24.691
//              Zmin: -15.449 Zmax: 15.632
//      Enclosing Sphere: 25.721
//
// Portrait light-field recomposition of bj.pov, the 9:16 companion to
// bj_holo.pov.  Same scene and same eye; only the frame and the lettering
// differ, so bj.pov keeps its 1997 3:4 composition untouched.
//
// Two changes, both for the Looking Glass:
//
//   * 9:16 rather than 3:4 -- the aspect every portrait preset in
//     QUILT_PRESETS declares (16-portrait, 27-portrait, 32-portrait, go).
//     The legacy `portrait` preset is 0.75 and is what bj.pov already fits;
//     this file is for the tall panels.
//
//   * The lens opened to 65.92 degrees vertical and the aim raised to
//     y=21.92.  A 9:16 frame is narrow, and the pedestal is the widest
//     thing in the scene: at bj.pov's lens its 32.5-unit radius overruns
//     the frame edges entirely.  The lens is set by that width -- it puts
//     the base 69 pixels clear of each side in a 1080x1920 render -- and
//     the aim then splits the vertical slack 330 pixels of sky above the
//     dome against 243 of water below the base.
//
//   * The title and signature moved from camera-pinned overlays out to
//     scene depth.  In bj.pov they sit 70-74 units from the eye, in front
//     of the 72-unit near bound and some 20 units short of the focal
//     plane, so on a light-field display they float off the glass.  Both
//     now sit *on* the focal plane, where the display holds them sharp.


#version 3.0
global_settings { assumed_gamma 1.8 }

#include "colors.inc"
#include "shapes.inc"
#include "textures.inc"
#include "skies.inc"

#include "bdna_bj.inc"
#include "bna7_full.inc"

#include "zdna_bj.inc"

#declare DO_SEA = true
#declare DO_CHECK = false

// Same eye as bj.pov, re-framed.  |direction| = 0.771724 with a unit `up`
// gives a vertical half-angle of atan(0.5/0.771724) = 32.960 degrees, so
// 65.92 degrees vertical.  `right` is the aspect itself (0.5625 = 9/16),
// which makes the horizontal half-angle atan(0.28125/0.771724).  The aim at
// y=21.92 pitches the axis 7.84 degrees below horizontal instead of 10.14.
camera {
   location  < 0, 35, -95 >
   direction < 0, 0, 0.771724 >
   up        < 0, 1, 0 >
   right     < 0.5625, 0, 0 >
   look_at   < 0, 21.92, 0 >
}


object {
  light_source {
     <-13.112195, 70, -30.898306>
     color White

  }
}


background { color MidnightBlue }

#declare Sky = sky_sphere {
  pigment {
    gradient y
    color_map {
      [0.5  color CornflowerBlue]
      [1.00  color MidnightBlue]
    }
    scale 2
    translate <-1, -1, -1>
  }
  pigment {
    bozo
    turbulence 0.4
    octaves 7
    omega .49876
    lambda 2.5432
    color_map {
      [0.0 color rgbf<.75, .75, .75, 0.1>]
      [0.4 color rgbf<.9, .9, .9, .9>]
      [0.7 color rgbf<1, 1, 1, 1>]
    }
    scale 6/10
    scale <1, 0.3, 0.3>
  }
  pigment {
    bozo
    turbulence 0.4
    octaves 8
    omega .5123
    lambda 2.56578
    color_map {
      [0.0 color rgbf<.375, .375, .375, 0.2>]
      [0.4 color rgbf<.45, .45, .45, .9>]
      [0.6 color rgbf<0.5, 0.5, 0.5, 1>]
    }
    scale 6/10
    scale <1, 0.3, 0.3>
  }
}


// ----------------------------------------

#if (DO_CHECK)
plane
{
  y, -12.5
  texture
  {
    pigment {checker color White color Black
            scale 20}
    finish {reflection 0.2}
  }
}
#end

#if (DO_SEA)
plane { y, -12.5
 pigment { Sapphire_Agate  scale 15.0}
   finish {
      specular 0.6
      ambient 0.2
      diffuse 0.8
   }
}
#end


sky_sphere { Sky }

// my signature
//

#declare egstext = object {
 text
 {
  ttf          // font type (only TrueType format for now)
  "timrom.ttf",  // Microsoft Windows-format TrueType font file name
  "E. G. Suchanek, '97",   // the string to create
  .25,           // the extrusion depth
  0            // offset
   pigment { BrightGold }
  finish { reflection .25 specular 1 ambient .3 }
 }
}

#declare titletext = object {
 text
 {
  ttf          // font type (only TrueType format for now)
  "timrom.ttf",  // Microsoft Windows-format TrueType font file name
  "DNA Under Glass",   // the string to create
  .2,           // the extrusion depth
  0            // offset
   pigment { BrightGold }
  finish { reflection .25 specular 1 ambient .3 }
 }
}


//
// the actual scene objects
//

object { bna7_full_belljar translate <0.0, 0.0, 7.0>}


// ---- lettering ------------------------------------------------------
//
// Placed by projecting back from the frame, as bj_holo.pov does, but against
// this camera: the view axis is 96.007 units long and pitches down 7.84
// degrees, and the frame at depth d is 1.2958*d tall by 0.72889*d wide.
// Both strings are rotated 7.84 degrees about x so they stand square to the
// camera; POV rotates a text object about its baseline-left origin, so each
// translate is that corner.
//
// The focal plane is at 84.91 -- the harmonic mean of 68 and 113, this
// framing's own swept depths.  Two notes on those, because neither is what
// the sweep prints unedited:
//
//   * The sweep returns a near of 61.  That is the sea arriving at the
//     bottom edge, not the subject: this lens looks 40.8 degrees down at the
//     frame's lower rim, which meets the waterline well in front of anything
//     else.  Buying zero parallax for a strip of foreground water would push
//     the jar itself off the glass, so it is excluded the same way the far
//     sea is.  68 is the signature, the nearest content meant to be read.
//
//   * The far bound is the knee, not the raw 95%.  The sea never closes, so
//     the raw rule returns the end of the sweep; subtracting the 0.071%/unit
//     backdrop creep from the 50.4% subject puts 95% of it in by 113.
//
// Title: centred in the sky above the dome.  Unlike the 16:9 cut, what caps
// the title here is the frame's *width*, not the glass -- 330 pixels of sky
// is more headroom than a 1080-wide frame can spend, so the string is set to
// 78% of the frame width and centred in the band, 126 pixels clear top and
// bottom.  Baseline y=65.99, z=-5.03, well outside the dome.
object {titletext
          rotate 7.84*x
          scale 6.42
          translate <-24.24, 65.99, -5.03>
          no_shadow
        }

// Signature: bottom right, on the water below the pedestal.
//
// Everything visible in that band is nearer than the pedestal -- the water
// under the base runs from about 61 at the frame's edge to 75 where the
// marble meets it -- so a signature down there is foreground by construction,
// and depth 68 is what puts it 135 pixels clear of the bottom edge.  It is
// the near bound rather than a violation of it.  y=-11.8 floats it 0.7 above
// the sea; at this depth it sits entirely in front of the pedestal, so no
// clearance term applies.
object {egstext
          rotate 7.84*x
          scale 1.85
          translate <7.39, -11.8, -32.80>
        }
