// textures for world2.pov - the meek museum
// -- 1994, Michael "meek" Mittelstadt
//
// You may want to increase some of the octaves values, I turned them
// down because I owned a slow computer when I did this.
//

#default
{ texture {
    finish { ambient 0.09 diffuse 0.91 } } }

#declare wall_tex=texture {
  pigment { color rgb <0.77,0.74,0.66> }
  finish { specular 0.45 roughness 0.3 } 
  normal { bumps 0.3 scale 1/2 omega 0.75 octaves 5 }  // slow!  
}

// if this looks 'off', blame my colourblindness.
#declare mould_tex = // Moulding around bottom of room
  texture {
    pigment { wood
              color_map { [0 color DarkWood]
                          [0.35 color rgb <0.35,0.15,0.18>]
                          [0.6 color rgb <0.25,0.16,0.11>]
                          [0.7 color rgb <0.22,0.17,0.07>]
                          [1 color DarkWood] } 
              
              turbulence 0.15
              lambda 3
              omega 0.55
     }
   finish { roughness 0.1 specular 0.43 }
} 

#declare wfloor_tex = // wooden floor in room
  texture {
    pigment { wood
              color_map { [0 color DarkTan]
			  [0.35 color MediumWood]
                          [0.6 color DarkWood]
                          [0.8 color MediumWood]
                          [1 color DarkTan] }
              turbulence 0.17 rotate <10,90,10> lambda 2.4 omega 1/3
              scale 2 
            }
    finish {  specular 0.4 roughness 0.08 phong 0.22 phong_size 70 
              reflection 0.15 
           }
  }


#declare column_tex = texture {
   pigment { granite
             color_map { [0 color Gray30]
                         [0.2 color rgb <0.4,0.31,0.28>]
                         [0.4 color rgb <0.5,0.36,0.25>]
                         [0.65 color rgb <0.58,0.4,0.29>]
                         [0.85 color rgb <0.45,0.38,0.31>]
                         [1 color rgb <0.4,0.31,0.28>] }
             omega 0.6 lambda 4.5 turbulence 0.4 
           }
   finish { phong 0.6 phong_size 33  reflection 0.15 
            } scale 1/2 }


// the gif was originally a .tga
// Please feel free to get out photoshop and do something
// better, or perhaps make 2X as many vertical "bands".

//#declare vasetex = texture { pigment { image_map
//{ gif "vmap.gif" map_type 2 once } scale <1,10,1> }  
//                             finish  { reflection 0.3 metallic 
//				       phong 0.85 phong_size 13 
//                                       brilliance 2.5 } }

// This object lands in the shadows. urrrrr.
#declare o3tex = texture { pigment { agate
             	                        scale 0.3 omega 1 lambda 4
   color_map { [0 color Black]
               [1/3 color Black]
               [2/3 color Coral]
               [1 color Black] }
    }
  finish { roughness 0.02 brilliance 1.3 specular 0.7 }  }
