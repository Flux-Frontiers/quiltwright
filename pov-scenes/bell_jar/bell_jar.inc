//
// BellJar object.
//
// This data and it's resulting derivative images are
// (c) 1993-1996, Eric G. Suchanek, Ph.D.
//
// The user is hereby licensed non-commercial use of these
// data and images, provided that this copyright notice remain
// attached to all neccessary data files.
//
//

#declare BellJar_Inc_Temp = version
#version 3.0
#include "marble2.inc"

/* The Bell Jar glass object */

// Wall thickness, in pre-scale units.  The jar was originally a zero-
// thickness surface -- an `open` cylinder merged with a sphere -- which
// refracts once instead of twice, so it read as a soap film rather than
// as glass: no rim, no edge, barely visible against a bright sky.  Giving
// it a real wall costs nothing and matters more on a light-field display
// than on a still, because a dome the display cannot see is a dome it
// cannot fuse.  Set to 0 for the original surface.
#declare BJ_WALL = 0.06

#include "glass.inc"

#if (BJ_WALL = 0)

#declare hemi = object {
        intersection {
                       sphere { <0, 3, 0> , .9}
                       plane {  -y, 2.5 }
                     }
   hollow
}



#declare cyl = object {
        cylinder { <0,0,0>, <0,3.0,0>, .9 open}
   hollow
}
#declare bell = merge {
   object { cyl }
   object { hemi }
   scale <1, 1.5, 1>
   texture { T_Glass3 }

  hollow
}

#else

// Outer surface: solid capsule.  The sphere sits at the cylinder's top rim
// and shares its radius, so the two are flush and the merge is a dome on a
// tube.
#declare bell_outer = merge {
   cylinder { <0, 0, 0>, <0, 3.0, 0>, .9 }
   sphere   { <0, 3, 0>, .9 }
}

// Cavity: the same shape inset by the wall, running below y=0 so the jar
// is open at the bottom rather than a sealed bubble.
#declare bell_cavity = merge {
   cylinder { <0, -0.5, 0>, <0, 3.0, 0>, .9 - BJ_WALL }
   sphere   { <0, 3, 0>, .9 - BJ_WALL }
}

#declare bell = difference {
   object { bell_outer }
   object { bell_cavity }
   scale <1, 1.5, 1>
   texture { T_Glass3 }
   hollow
}

#end

/*-----------BASE OF COLUMN A / TOP FLOOR-------------------*/
#declare base_a = union {
   sphere { <0, 0, 0>, 1 scale <1.3, .55, 1.3> }
   sphere { <0, 0, 0>, 1 scale <1.1, .3, 1.1> translate .4*y  }
   cylinder { <0,0,0>, y, 1 scale <1.0, .4, 1.0> translate .5*y }
  // torus {.91 .11 translate .62*y texture { Gold_Texture}}
   torus {.91 .05 translate .98*y texture { Gold_Texture}}

   texture {
      marble1
      scale <.9, .6, .4>
      finish {
         ambient 0.3
         diffuse 1
      }
   }
   texture {
      marble4
      scale <.7, .12, .9>
      rotate <0, 0, -40>
      finish {
         diffuse 1.0
         phong 0.6
         phong_size 50
      }
   }


   rotate 40*y

}

#declare bell_jar = union {
        object { bell }
        object {base_a  translate <0, -1.0, 0>}
   }

#version BellJar_Inc_Temp

