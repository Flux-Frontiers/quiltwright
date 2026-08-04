
// Persistence of Vision Ray Tracer Scene Description File
// File: .pov
// Vers: 3
// Desc: 
// Date: 
// Auth: 


// ==== Standard POV-Ray Includes ====
#include "colors.inc"	// Standard Color definitions
#include "textures.inc"	// Standard Texture definitions


// ==== Additional Includes ====
#include "CHARS.INC"   // FIXME-add comments describing each of these
#include "CONSTS.INC"
#include "METALS.INC"
#include "SHAPES.INC"
#include "SHAPES2.INC"
#include "SHAPESQ.INC"
#include "SKIES.INC"
#include "STONES.INC"
#include "STONES2.INC"
#include "WOODMAPS.INC"
#include "WOODS.INC"


// flat circular FINITE (no CSG) shape, center hole cutout is optional
#declare disc1 = object {
 disc
 {
  <0, 1, 0>  // center position
  x,         // normal vector
  1.0,       // outer radius
  0.8        // optional hole radius
 }
}
 
// set viewer's position in the scene
camera
{
// (camera types)
//  perspective (default) | orthographic | fisheye |
//  ultra_wide_angle | omnimax | panoramic | cylinder 1
  location  <0.0, 1.0, -6.0> // position of camera <X Y Z>
  direction 2.0*z            // which way are we looking <X Y Z> & zoom
//  sky       y                // rarely used
  up        y                // which way is +up <X Y Z>
  right     4/3*x            // which way is +right <X Y Z> and aspect ratio
  look_at   <0.0, 0.0,  0.0> // point center of view at this point <X Y Z>
//  angle FLOAT                // overrides "direction" with specific angle
//  normal { ripples 0.2 }     // perturb the camera lens with a pattern
// (focal blur extras)
//  aperture 0.2               // 0...N (bigger is narrower depth of field)
//  blur_samples 4             // # of rays per pixel
//  focal_point <VECTOR>       // x,y,z point that is in focus
}

