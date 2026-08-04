// Window - Beveled
// 15 Mar 1994 - Michael Mittelstadt

// use the two below for testing this as a standalone file
//light_source { <-45,40,-17> color rgb <1,1,1> }
//camera { location <-56,45,7> up y right 1.3333*z direction x look_at <-1,30,0> }
                           
#declare PC = true                           
#declare leadtex = texture { pigment { color rgb <1/10,1/10,1/10> }
                             finish { specular 0.35 roughness 0.1 }
                             normal { bumps 0.7 octaves 4 } }

#declare bevel = box { <-1,-1,-1>,<1,1,1> rotate 45*z translate x*-1.707 }
#declare lead  = cylinder { <0,0,-1>,<0,0,1>,0.25 texture { leadtex } }

#declare wind_side = object {
   difference {

     box { <-1,0,-10>,<0,60,10> } // let the windowframe clip the rest.

     object { bevel scale <1,1,11> translate y*10 }
     object { bevel scale <1,1,11> translate y*20 }
     object { bevel scale <1,1,11> translate y*30 }
     object { bevel scale <1,1,5.1> translate <0,40,-10> }
     object { bevel scale <1,1,5.1> translate <0,40,10> }
     object { bevel scale <1,1,17.5> rotate 90*x translate 17.5*y }
     object { bevel scale <1,1,20> rotate 90*x translate <0,20,-5> }
     object { bevel scale <1,1,20> rotate 90*x translate <0,20,5> }
     object { bevel scale <1,1,20> rotate 90*x translate <0,20,10> }
     object { bevel scale <1,1,20> rotate 90*x translate <0,20,-10> }
     object { bevel scale <1,1,5> rotate 90*x translate 50*y }
     object { bevel scale <1,1,11> }
     torus { 5,1 rotate z*90 translate <-1,40,0> }

     pigment { color rgbf <1,0.99,0.99,0.985> }
    
#if (PC)
     finish { diffuse 0.1 specular 0.8 roughness 1/2000 phong 1 phong_size 400  }
     interior {refraction 0.85 ior 1.45 }   
#else
     finish { diffuse 0.1 specular 0.8 roughness 1/2000 phong 1 phong_size 400  refraction 0.85 ior 1.45}
#end     
            } // difference
}

#declare window = object { union {
    object { wind_side }
   
/*        merge {
          object { wind_side }
          object { wind_side rotate 180*y } }
          */
     object { torus { 5,0.25 rotate 90*z translate 40*y texture { leadtex } } }
     object { lead scale <1,1,11> translate y*10 }
     object { lead scale <1,1,11> translate y*20 }
     object { lead scale <1,1,11> translate y*30 }
     object { lead scale <1,1,5.1> translate <0,40,-10> }
     object { lead scale <1,1,5.1> translate <0,40,10> }
     object { lead scale <1,1,17.5> rotate 90*x translate 17.5*y }
     object { lead scale <1,1,20> rotate 90*x translate <0,20,-5> }
     object { lead scale <1,1,20> rotate 90*x translate <0,20,5> }
     object { lead scale <1,1,5> rotate 90*x translate 50*y }
      }
     }


// also, for testing the scene.  Gotta have a backdrop to see the
// 'clear' window.
// plane { y,0 pigment { color rgb <1,1,1> } }
// plane { -x,-10 pigment { color rgb <1,1,0.8> } }

