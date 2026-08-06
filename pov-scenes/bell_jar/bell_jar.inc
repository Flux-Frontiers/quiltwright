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
#include "glass.inc"
#declare bell = merge {
   object { cyl }
   object { hemi }
   scale <1, 1.5, 1>
   texture { T_Glass3 }

  hollow
}

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

