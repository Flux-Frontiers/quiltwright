// textures for the small display case.
//
#declare PC = 0

#declare Basetex = texture {
 pigment { wood color_map {
		   [0   color rgb <0.6,0.53,0.36>]
                   [0.3 color rgb <0.55,0.45,0.32>]
                   [0.5 color rgb <0.4,0.23,0.18>]
                   [3/4 color rgb <0.55,0.45,0.32>]
                   [1 color rgb <0.6,0.53,0.36>] }
           scale <1/2,1/2,1>
           turbulence <0.2,0.2,0.1>
     }
      finish { phong 0.7 phong_size 30 } 
}



#declare shelftex = texture {
 pigment { granite
           omega 0.4
           lambda 1
           turbulence 0.25
           scale 1.2
           color_map { [0 color Gray30]
                       [0.4 color rgb <0.45,0.35,0.45>]
                       [0.5 color rgb <0.5,0.37,0.5>]
                       [0.6 color rgb <0.45,0.37,0.38>]
                       [1 color Gray30] }
 }
 finish {
   roughness 0.23
   specular 0.5
   reflection 0.12
 }
}



#declare casetex = texture {
 pigment { color red  0.890 green  0.867 blue  0.505 }
 finish {
  reflection 0.6
  brilliance   2.500
  phong   0.77
  phong_size  15.00
  metallic
 }
}


#declare panetex = texture {
 pigment { color red  1.000 green  1.000 blue  1.000 filter 0.999 }

#if (PC)
 finish {
//  reflection 0.1  // WARNING: uncommenting will add MUCH rendering time.
                    // (but make the picture more 'real')
  ambient 0
  diffuse 0.0
  brilliance   1.25
  phong   0.80
  phong_size  18.00 
  }
  
#else   
finish {
//  reflection 0.1  // WARNING: uncommenting will add MUCH rendering time.
                    // (but make the picture more 'real')
  ambient 0
  diffuse 0.0
  brilliance   1.25
  phong   0.80
  phong_size  18.00
  refraction 1
  ior 1.55
  }
#end

}


