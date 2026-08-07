#include "colors.inc"
#include "textures.inc"
#include "metals.inc"
#include "skies.inc"

#version 3.0
global_settings { assumed_gamma 2.2 }


camera {
	location  <0, 0, -70>
	direction <0, 0,  1>
	up        <0, 1,  0>
	right   <4/3, 0,  0>
	look_at   <0, 0, 0>
}

light_source {<0, 0, -70.828445> color White}
light_source {<0, 177.071114, 0> color White}

// This object has the following minimum and maximum values:
// xmin=-34.526668, xmax=34.526673
// ymin=-21.436113, ymax=21.436113
// zmin=-19.307804, zmax=19.307804

#declare DO_LAMBDA = 1
#declare DO_SKY = 1
#declare DO_RAINBOW = 1

#include "rainbow.inc"
#include "lambda_sky.inc"

#if (DO_LAMBDA)
#include "lambda_complex2.inc"

object {lambda_complex translate <0,0,-5>}
#end



// Define the water surface

plane { y, -25
    pigment { MidnightBlue  } //Sapphire_Agate scale 10.0
    finish { reflection .35 specular 1 }
    normal { ripples .5 turbulence .5 scale 15 }
 }

 /*
plane { y, -25.000000
	pigment { Blue }
	normal {
		waves 0.05
		frequency 5000.0
		scale 106242.668152
	}
	finish { reflection 0.8 }
}
*/

// Sea floor (require for water to look right)
plane { y, -60.414223
	pigment { Blue }
	finish {
		ambient 1.0		diffuse 0.0
	}
}
// create a TrueType text shape
//
// my signature
//

#declare egstext = object {
 text
 {
  ttf                       // font type (only TrueType format for now)
  "timrom.ttf",             // Microsoft Windows-format TrueType font file name
  "E. G. Suchanek, 1998",   // the string to create
  .25,                     // the extrusion depth
  0                        // offset
  texture{T_Chrome_5D}
//   pigment { BrightGold }
//  finish { reflection .25 specular 1 ambient .3 }
 }
 scale <1.5,1.5,1>
}

#declare title_text = object {
 text
 {
  ttf                       // font type (only TrueType format for now)
  "timrom.ttf",             // Microsoft Windows-format TrueType font file name
  "Lambda Repressor '98",   // the string to create
  .25,                     // the extrusion depth
  0                        // offset
  texture{T_Chrome_5D}
 //  pigment { BrightGold }
//  finish { reflection .25 specular 1 ambient .3 }
 }
 scale <5,5,2>
}
object {title_text translate <-25,28,0>}
object {egstext translate <20,-24,-18>}

