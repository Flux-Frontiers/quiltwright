//
// "DNA Under Glass" - checkerboard cut.
//
// The still life as it was framed for the museum's upper-right picture:
// B-DNA under the bell jar standing on the black-and-white checkerboard
// rather than the sea.  bj.pov carries both grounds behind DO_SEA and
// DO_CHECK and ships with the sea switched on; this is the other setting,
// written as its own scene so bj.pov stays as it was.
//
// The frame it hangs in is landscape, so the lens is 4:3 here where bj.pov
// is 3:4.  Same eye, same aim - the extra width is checkerboard.
//
// Render the picture the museum reads:
//
//   povray +Ibj_check.pov +Obell_jar.tga +W800 +H600 +FT +A0.3 \
//          +L<povray-include> +L../myinclude
//
// This data and its resulting derivative images are
// (c) 1993-1996, Eric G. Suchanek, Ph.D.
//

#version 3.0
global_settings { assumed_gamma 1.8 }

#include "colors.inc"
#include "shapes.inc"
#include "textures.inc"

// bna7_full.inc declares ATM_SCL, which the posed duplexes need, so the
// include order here matches bj.pov's rather than being tidied.
#include "bdna_bj.inc"
#include "bna7_full.inc"

camera {
   location < 0, 35, -95 >
   right <4/3, 0, 0>
   look_at <0, 18, 0>
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
}

sky_sphere { Sky }

// ----------------------------------------
// the checkerboard, in place of bj.pov's sea

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

//
// the actual scene objects
//

object { bna7_full_belljar translate <0.0, 0.0, 7.0>}

#declare titletext = object {
 text
 {
  ttf
  "timrom.ttf",
  "DNA Under Glass",
  .2,
  0
   pigment { BrightGold }
  finish { reflection .25 specular 1 ambient .3 }
 }
}

#declare egstext = object {
 text
 {
  ttf
  "timrom.ttf",
  "E. G. Suchanek, '97",
  .25,
  0
   pigment { BrightGold }
  finish { reflection .25 specular 1 ambient .3 }
 }
}

object {titletext
          rotate 15*x
          scale 5
          translate <-18, -9.5, -28>
         }

object {egstext
          scale 1.5
          translate <12, -11, -32>
          }
