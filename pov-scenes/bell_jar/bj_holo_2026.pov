//
//
// This data and its resulting derivative images are
// (c) 1993-1996, 2026, Eric G. Suchanek, Ph.D.
//
// The 1993-1996 term covers the model and the still life, inherited from
// bj.pov; 2026 covers this file, which is a new composition of them.
//
// The user is hereby licensed non-commercial use of these
// data and images, provided that this copyright notice remain
// attached to all necessary data files.
//
//
// PDB2POV atom input prepared by pdb2pov 11/12/93 09:55:44
//      Atoms:486 */
//      Extent: Xmin: -13.112 Xmax: 14.289,
//              Ymin: -22.614, Ymax: 24.691
//              Zmin: -15.449 Zmax: 15.632
//      Enclosing Sphere: 25.721
//
// The 2026 cut of bj_holo.pov.  Same eye, same lens, same framing, same
// lettering placement -- bj_holo.pov keeps its own composition untouched and
// this file changes exactly two things: the glass is real, and the signature
// is re-dated.
//
// The glass.  The 1996 jar has no `interior`, so its index of refraction is
// 1.0: it bends nothing, and every ray crossing it is merely filtered.  Once
// BJ_WALL gave the jar two surfaces, that filter applied twice wherever the
// wall was seen edge-on, which is why the dome carries two grey outlines
// down each side instead of one glass rim.  BJ_CRYSTAL (see bell_jar.inc)
// swaps in ior 1.52 with a Fresnel reflection, so the wall refracts rather
// than tints.  The doubled outline resolves into a
// single bright band, the sky lands in the shoulder of the dome where the
// Fresnel term climbs, and the duplex behind the glass is magnified the way
// a real jar magnifies what is under it.
//
// max_trace_level is the other half of that change and is not optional: the
// default of 5 is spent before a ray has crossed both walls, reflected off
// an atom and come back out, and what it cannot finish it renders black.
//
// The whole diff against bj_holo.pov: max_trace_level and the two BJ_
// declares below; `no_reflection` on the title; the light_source unwrapped
// from its 1996 `object { ... }`; and the signature string.  Eye, lens,
// framing, lettering placement, sky, sea and molecule are untouched.  The
// original composition note follows.
//
// Light-field recomposition of bj.pov.  Same scene, same eye, same lens --
// only the frame and the lettering differ, so bj.pov keeps its 1997 3:4
// composition untouched.
//
// Three changes, all for the Looking Glass:
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
//     of the 72-unit near bound, so on a light-field display they float
//     off the glass.  The title now sits *on* the focal plane; the
//     signature sits at 82, a third of a pixel of parallax off it, which
//     is what puts it low in the frame.  See the note above each.


#version 3.0
// max_trace_level 15: a ray now enters the outer wall, leaves the inner
// wall, crosses the cavity, reflects off an atom and retraces the same two
// walls on the way out.  That is eight levels before the sea behind the jar
// is reached at all, and POV-Ray returns black once it runs out.
//
// No photons, though the jar is exactly the kind of object they exist for.
// Enabling them was tried and is worse here: POV-Ray stops passing direct
// light through a photon target and expects the photon map to replace it,
// and at this scale it does not.  The duplex goes flat and muddy for want of
// the light that used to reach it through the glass, and the jar drops a
// hard black ellipse across the sea to the right where its soft shadow used
// to be.  Raising the count from 220k to 900k moved neither, and cost 7x the
// render.  Caustics are not worth the picture.
global_settings { assumed_gamma 1.8 max_trace_level 15 }

// Read by bell_jar.inc, which the atom includes below pull in.  It has to be
// set before them or the #ifndef guard there wins and the jar comes out 1996.
#declare BJ_CRYSTAL = true

// A heavier wall than bj_holo.pov's 0.06.  Thickness is what a refracting
// jar has to spend to be seen at all: it sets how wide the bright band at
// the silhouette is and how much of a rim the jar shows where it meets the
// pedestal.  At 0.06 the crystal is very nearly invisible.
#declare BJ_WALL = 0.20

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


// Unwrapped from the `object { light_source { ... } }` bj_holo.pov inherits
// from 1996.  Same light, same place, same colour; the wrapper was doing
// nothing, and it is one of the things that hides a light from POV-Ray's
// photon pass, which is worth not re-discovering if caustics are ever
// revisited here.
light_source {
   <-13.112195, 70, -30.898306>
   color White
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
  "E. G. Suchanek, '26",   // the string to create
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


// ---- lettering -------------------------------------------------------
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
          // no_reflection is new in 2026 and exists only because the glass
          // is now real: a dome that reflects returns the title as a
          // mirrored ghost lying across its shoulder.  The reflection is
          // correct -- the title is a scene object at depth 92, not an
          // overlay -- but it reads as a smear, and it is the one place
          // where honest optics make the picture worse.
          no_reflection
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
