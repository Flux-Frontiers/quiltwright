/*	Eric's famous bell_jar object 1 unit in width, 3 in height

	Enclosing Sphere: 25.721
    (c) 1993-1997 Eric G. Suchanek, Ph.D. All rights reserved
*/

#include "colors.inc"
#include "shapes.inc"
#include "textures.inc"
#include "marble2.inc"

#declare MyGlass =
 texture
   {pigment
     {color red 0.98 green 0.98 blue 0.98 filter 0.9}
    finish
     {ambient 0.1
      diffuse 0.1
      specular 0.8
      reflection 0.1
      refraction 0.9
      ior 1.25
      roughness 0.0003
      phong 1 phong_size 300
     }
   }



/* The Bell Jar glass object */
#declare ohemi = object {
	intersection {
		       sphere { <0, 3, 0> , 1}
		       sphere { <0, 3, 0> , .9}
	               plane {  -y, 2.5 }
                     }
}

#declare hemi = object {
	intersection {
		       sphere { <0, 2.8, 0> , 1 hollow}
               plane {  -y, 2.85 }
              }
}

#declare cyl = object {
	cylinder { <0,0,0>, <0,2.8,0>, 1 open}
}



#declare bell = merge {
   object { cyl }
   object { hemi }
   scale <.8, 1.5, .8>
   texture { Glass3 }
   hollow
}

#declare bell2 = object {bell inverse
			 scale <.95, .95, .95>
}

#declare stanchion = object {
    cylinder { <0,.4,0>, <0,5.4,0>, .04 texture {Gold_Texture}}
}

/*-----------BASE OF COLUMN A / TOP FLOOR-------------------*/

#declare rings = union {
   object { stanchion translate <.9, .3, 0> }
   object { stanchion translate <-.9, .3, 0> }
   object { stanchion translate <0, .3, .9> }
   object { stanchion translate <0, .3, -.9> }
   torus {.86 .12 translate 5.7*y texture { Gold_Texture}}
   torus {.86 .11 translate 1*y texture { Gold_Texture}}
}
#declare base_a = union {
   object {rings}
   sphere { <0, 0, 0>, 1 scale <1.3, .55, 1.3> }
   sphere { <0, 0, 0>, 1 scale <1.1, .3, 1.1> translate .4*y  }
   cylinder { <0,0,0>, y, 1 scale <1.0, .4, 1.0> translate .5*y }
   torus {.91 .11 translate .62*y texture { Gold_Texture}}

   texture {
      marble1
      scale <.9, .6, .4>
      finish {
         ambient 0.2
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




#declare base_b = union {
   sphere { <0, 0, 0>, 1 scale <1.3, .55, 1.3> }
   sphere { <0, 0, 0>, 1 scale <1.1, .3, 1.1> translate .4*y  }
   cylinder { <0,0,0>, y, 1 scale <1.0, .4, 1.0> translate .5*y }
   torus {.91 .11 translate .62*y texture { Gold_Texture}}
   object {rings}
   texture {
      marble1
      scale <.9, .6, .4>
      finish {
         ambient 0.2
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
	object {base_a  translate <0, -.90, 0>}
	}

#declare bell_jar2 = union {
    object {bell }
    object {base_b translate <0, -.90, 0> }
}



