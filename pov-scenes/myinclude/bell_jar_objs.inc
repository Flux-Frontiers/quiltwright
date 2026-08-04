/* PDB2POV atom input prepared by pdb2pov 11/12/93 09:55:44 */
/*	Atoms:486 */
/*	Extent:	Xmin: -13.112 Xmax: 14.289,
		Ymin: -22.614, Ymax: 24.691
		Zmin: -15.449 Zmax: 15.632
	Enclosing Sphere: 25.721
*/

#include "colors.inc"
#include "shapes.inc"
#include "textures.inc"
#include "skies.inc"

#include "atoms_vdw.inc"
#include "atoms2.inc"
#include "marble2.inc"


#declare ATM_SCL = 1.00

background { color SkyBlue }

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


#include "bell_jar.inc"
#include "bna7_full.inc"
#include "zdna_bj.inc"

