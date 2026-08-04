
//  Persistance of Vision Raytracer V2.0
//  Texture include file for picframe.MDL scene.
//
//  This file was generated for POV-Ray V2.0 by
//  MORAY.EXE (c) '91 '92 '93 SoftTronics by Lutz Kretzschmar + Markus Lutz
//
//  ..and subsequently messed up by someone who is colorblind :)
//

//  $MRY$: 'canvasstexture'
#declare canvasstextureO = texture {
 pigment { color rgb <0.075,0.075,0.07> }
 finish { roughness 0.3 specular 0.3 }
 normal { wrinkles 0.25 omega 0.666 octaves 3 scale 1/3 }
}

#declare canvasstexture = texture {
 pigment { color rgb <0.075,0.075,0.07> }
 finish { roughness 0.1 specular 0.3 }
 normal { wrinkles 0.1 omega 0.666 octaves 3 scale 1/3 }
}

#declare mirrortexture = texture {
  pigment {color rgb <.9, .9, .9> }
  finish { reflection 1.0 ambient 0 diffuse 0 }
  //normal { wrinkles 0.25 omega 0.666 octaves 3 scale 1/3 }
 }

//  $MRY$: 'edgetex'
#declare edgetex = texture {
 pigment {
  wood
  color_map { [0  color rgb <0.3,0.23,0.14>]
              [0.6 color rgb <0.32,0.24,0.15>]
              [0.8  color rgb <0.4,0.35,0.19>]
              [1 color rgb <0.3,0.23,0.14>] }
       turbulence 0.4
       scale 0.7
       omega 2/3
     }
  finish {
  phong   0.65
  phong_size  23.00
 }
}





