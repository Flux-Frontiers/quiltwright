
// Persistence of Vision Ray Tracer Scene Description File
// File: ?.pov
// Vers: 3
// Desc: Basic Scene Example
// Date: mm/dd/yy
// Auth: ?
//

#version 3

#include "colors.inc"

// ==== Standard POV-Ray Includes ====
#include "colors.inc"	// Standard Color definitions
#include "textures.inc"	// Standard Texture definitions


global_settings
{
  assumed_gamma 1.0
}

// ----------------------------------------
camera
{
  location  <0.0, 0.5, -500>
  direction 1.5*z
  right     4/3*x
  look_at   <0.0, 0.0,  0.0>
}

sky_sphere
{
  pigment
  {
    gradient y
    color_map { [0.0 color blue 0.6] [1.0 color rgb 1] }
  }
}

light_source
{
  0*x // light's position (translated below)
  color red 1.0  green 1.0  blue 1.0  // light's color
  translate <-30, 30, -30>
}

// ----------------------------------------
plane { y, -450 pigment {color rgb <0.7,0.5,0.3>}}



#include "3porin.inc"

