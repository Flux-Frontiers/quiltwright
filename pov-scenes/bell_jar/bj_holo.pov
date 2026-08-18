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
// Light-field recomposition of bj.pov.  Same scene, same eye, same lens --
// only the frame and the lettering differ, so bj.pov keeps its 1997 3:4
// composition untouched.
//
// Two changes, both for the Looking Glass:
//
//   * 16:9 rather than 3:4, matching the landscape panel the hologram
//     targets and what render_still_life_hologram.py actually renders.
//
//   * The lens opened from 53.13 to 55.32 degrees vertical and the aim
//     raised from y=18 to y=20.95.  bj.pov's framing has no sky: the jar
//     and pedestal fill 91% of the frame height, leaving 29 pixels above
//     the dome and 70 below the base in a 1080-line render, so a title set
//     above the glass could be at most ~20 pixels tall.  The wider lens and
//     the raised aim redistribute that slack to 90 above and 54 below,
//     which is what makes a full-size title possible at all.  The subject
//     shrinks 4.6% for it.
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

// Same eye as bj.pov, re-framed.  |direction| = 0.954563 with a unit `up`
// gives a vertical half-angle of atan(0.5/0.954563) = 27.662 degrees, so
// 55.325 degrees vertical; `right` at 16/9 makes the horizontal half-angle
// atan(0.888889/0.954563) and the frame a true 16:9.  The aim at y=20.95
// pitches the axis 8.41 degrees below horizontal instead of 10.14.
camera {
   location  < 0, 35, -95 >
   direction < 0, 0, 0.954563 >
   up        < 0, 1, 0 >
   right     < 16/9, 0, 0 >
   look_at   < 0, 20.95, 0 >
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


// ---- lettering, on the focal plane -----------------------------------
//
// Placed by projecting back from the frame rather than by eye.  The view
// axis is 96.033 units long and pitches down 8.41 degrees; the focal plane
// sits 92.418 units out -- the harmonic mean of this scene's own measured
// near and far depths, 72 and 129, which is where
// render_still_life_hologram.py puts the display's zero-parallax plane.
// On that plane the frame is 96.816 units tall and 172.119 wide, and its
// centre is <0, 21.479, -3.577>.
//
// Both objects are rotated 8.41 degrees about x so they stand square to the
// camera rather than leaning away from it, and POV rotates a text object
// about its own baseline-left origin, so each translate below *is* the
// baseline-left corner of the string.
//
// Title: centred, in the sky above the dome.  What bounds it is the glass,
// not taste -- the dome's silhouette tops out 90 pixels down a 1080-line
// frame, and an ellipsoid seen from a pitched camera silhouettes at its
// tangent point (y=60.27, z=-1.90), not at its apex, so the tangent is what
// the title has to clear.  The baseline sits 12 pixels above it and the
// caps stop 26 pixels short of the top edge.  In world terms the baseline
// is at y=62.45, z=2.48, comfortably outside the glass.
//
// no_shadow because the light is at <-13.1,70,-30.9> and the title is now
// 62 units up: the shadow ray reaches the sea some 340 units downrange,
// which projects as a smeared dark copy of the lettering lying across the
// horizon.  The signature keeps its shadow -- that one lands directly
// beneath the string and grounds it on the water.
object {titletext
          rotate 8.41*x
          scale 6.68
          translate <-25.21, 62.45, 2.48>
          no_shadow
        }

// Signature: out over open water at the lower right.
//
// This one is not on the focal plane, and cannot be.  Anything sitting near
// the waterline projects *higher* in the frame the further out it is, so on
// the 92.42 plane the string rode a tenth of the frame too high; bringing it
// forward to depth 82 is what drops it to the bottom corner.  It stays well
// inside the measured 72-129 band, which puts it 0.29 px per adjacent view
// off zero parallax -- still on the glass for any practical purpose.  (The
// lambda scene does the same thing for the same reason.)
//
// The pedestal is a 32.5-radius ellipsoid centred on z=7, so at this depth
// anything with |x| < 19.4 is buried in marble; starting the string at
// x=39.82 clears it and still ends a quarter of the frame short of the right
// edge.  y=-11.8 floats it 0.7 above the sea -- enough that the descenders
// stay dry and the shadow lands directly beneath.
object {egstext
          rotate 8.41*x
          scale 2.30
          translate <39.82, -11.8, -19.03>
        }
