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


#version 3.0
global_settings { assumed_gamma 1.8 }

#include "colors.inc"
#include "shapes.inc"
#include "textures.inc"

#include "skies.inc"

/* render in 4/5 aspect! */

#declare original_camera = camera {
   location < 0, 30, -60 + clock * 30 >
   direction < 0, 0, 1>
   up <0, 1, 0>
   right <4/8, 0, 0>
   look_at <0, 25, 0>
}


#declare camera_major_groove = camera {
   location < 0, 35, -20 >
   direction < 0, 0, 1>
   up <0, 1, 0>
   right <4/5, 0, 0>
   look_at <5, 25, 0>
}

camera {original_camera}

object {
  light_source {
     <-13.112195, 70, -30.898306>
     color red 1 green 1 blue 1
     /* area_light x y 2 2 */

  }
}

object {
  light_source {
     <313.112195, 10, 10.1>
     color red 1 green 1 blue 1

  }
}



background {color Black}
// background { color SkyBlue }

#declare Sky = sky_sphere {
  pigment {
    gradient y
    color_map {
      [0.75  color CornflowerBlue]
      [1.00  color MidnightBlue]
    }
    scale 2
    translate <-1, -1, -1>
  }
  pigment {
    bozo
    turbulence 0.6
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
    turbulence 0.6
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


/* Create the beloved famous raytrace checkered floor */
/*
plane { y, 0
      pigment {
      checker colour Black colour White
      scale 12.450930
     }
     finish {
       ambient 0.2
       diffuse 0.8
     }
}
*/

#include "bdna_bj.inc"
#include "bna7_full.inc"

#declare bna7_reoriented = object { bna7_full_obj 
                                    rotate clock * y * 360.0}
object { bna7_reoriented
       // rotate x*90
       // translate y*25

       }

// sky_sphere { Sky }


