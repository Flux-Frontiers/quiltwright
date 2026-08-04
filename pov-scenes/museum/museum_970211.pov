// Persistence of Vision Ray Tracer Scene Description File
// File: museum.pov
// Vers: 3
// Desc: Eric's Science museum, main scene file.
// Start Date: 10 Jun 1995
// Date: 1/18/97
// Auth: Eric G. Suchanek, Ph.D.
//

//
// This file is now heavily POV-Ray 3.0 dependent. Don't try this one with
// prior versions, since all of the conditionals will fail.
//

#version 3.0
// pc gamma is about 2.2
// mac gamma is about 1.8
// unix gamma is about 2.2

global_settings {
           assumed_gamma 1.8
           max_trace_level 10
                }

#include "colors.inc"
#include "skies.inc"

#include "world2.inc"
#include "column.inc"
#include "picframe.inc"
#include "picframe.pov"

#include "display_base.pov"
#include "bell_jar_objs.inc"

#include "mytree.inc"
#include "window.pov"

#include "marble2.inc"

//
// some useful switch variables for cameras, views and objects
//

#declare ORIGINAL = 0.0     // set to 1 for the 'classic' version
#declare NEW = true         // now the default
#declare VENUS = false      // set to true to include Venus deMilo
#declare WORLD = false      // set to true to include the world map
#declare ATMOS = false      // set to true to include atmosphere - long!
#declare OUTSIDE = false    // set to true to view from the outside

//
// preset aspect ratios for convenient rendering to different output media
//

#declare PC_ASPECT = 1.33333
#declare HDTV =      1.77778
#declare FOURBYFIVE = .8
#declare FIVEBYFOUR = 1.25

//#declare ASPECT = FIVEBYFOUR
#declare ASPECT = PC_ASPECT


//
// lots of camera views
//

#declare wide_lens = camera {
   direction <0,0,1>
   up <0,1,0>
   right <ASPECT,0,0>
  angle 85
  }

#declare the_lens = camera {
   direction <0,0,1>
   up <0,1,0>
   right <ASPECT,0,0>
 //  angle 55
}


#declare camera_zdna = camera {
  location <15,18.5,5>
  direction <0,0,0.89>
  up <0,1,0>
  right <ASPECT,0,0>
  look_at <66,5,58>
  angle 75
}

#declare camera_zdna2 = camera {
  location <15,20,6>
  direction <0,0,0.89>
  up <0,1,0>
  right <ASPECT,0,0>
  look_at <50,22,58>
}

//
// note use of named camera here
//
#declare camera_zdna3 = camera {
  the_lens
  location <15,20,6.0>
  look_at <52,19,53>
}

#declare camera_bdna = camera {
  location <35,18.5,5>
  direction <0,0,0.89>
  up <0,1,0>
  right <ASPECT,0,0>
  look_at <50,5,58>
}

#declare camera_zdna_new = camera {
  location <50,20,15>
  direction <0,0,1>
  up <0,1,0>
  right <ASPECT,0,0>
  look_at <13,5,40>
}

#declare camera_front = camera {
  location <35, 18.5, 0>
  direction <0,0,0.89>
  up <0,1,0>
  right <ASPECT,0,0>
  look_at <35,20,58>
}

#declare camera_outside_belljar = camera {
  location <100, 18, 50>
  direction <0, 0, .89 >
  up <0, 1, 0>
  right <ASPECT,0,0>
  look_at <13, 20, 0 >


}

#declare camera_outside_far = camera {
  location <180, 18, 45>
  direction <0, 0, .89 >
  up <0, 1, 0>
  right <ASPECT,0,0>
  look_at <13, 20, 0 >

}

#declare camera_outside = camera {
  location <110, 18, 45>
  direction <0, 0, .89 >
  up <0, 1, 0>
  right <ASPECT,0,0>
  look_at <13, 20, -10 >

}


//
// finally, actually define the camera to use
//

#if (ORIGINAL)
  camera {camera_zdna}
#else
 #if (OUTSIDE)
   camera {camera_outside}
 #else
  camera {camera_zdna3}
//camera {camera_zdna_new}
 #end
#end


//
// Spotlight above rightmost bell-jar
//

light_source {
   <55,38,18> color Gray85
   spotlight
   point_at <35,15,30> // <35,12,30>
   radius 18           // 16
   falloff 20
   tightness 20
   }

light_source {    <205,125,27> color rgb <1,1,0.8>   } // The Sun

// additional light in the room, if you really want it
//light_source {   <50,55,10> color rgb <0.125,0.125,0.115> }

//
// invariant room stuff
// the ground.

plane { y,0 pigment { color MidnightBlue }
	normal { bumps 1.0 octaves 5 scale 20 }
        finish { crand 0.003 ambient 0.6 diffuse 0.4 }}

difference { // the Room
  box { <-5,-5,-5>,<102,65,65> }
  box { <0,0,0>,<100,60,60>  }
  box { <99.5,5,19>,<102.5,46,41> }
  cylinder { <99.5,46,30>,<102.5,46,30>,11 }
  texture { wall_tex } }

box { <99.5,5,19>,<102.5,46,20> texture { mould_tex } }
box { <99.5,5,40>,<102.5,46,41> texture { mould_tex } }
box { <99,5,19>,<103,6,41> texture { mould_tex } }

difference {
   cylinder { <99.5,46,30>,<102.5,46,30>,11 }
   cylinder { <99.4,46,30>,<102.6,46,30>,10 }
   box { <99.4,29,18.5>,<102.6,46,41.5> }
  texture { mould_tex }
}

plane { // Wood floor
  y,1/4
  texture { wfloor_tex }
  }

difference {
  box {
    <0,0,0>,<100,3,60> }
  box {
    <1/2,-1/100,1/2>,<99.5,3.01,59.5> }
  texture {  mould_tex } }

cylinder {
  <0,3,0>,<100,3,0>,1/2 texture { mould_tex }}

cylinder {
  <0,3,0>,<0,3,60>,1/2 texture { mould_tex }}

cylinder {
  <0,3,60>,<100,3,60>,1/2 texture { mould_tex }}

cylinder {
  <100,3,0>,<100,3,60>,1/2 texture { mould_tex }}


box { // rug
  <15,1/4,15>,<85,1/2,45>
  pigment { //color red 0.4 }
     image_map { gif "rug.gif" once  interpolate 2
      }
     scale <70,30,1> translate <15,15,0> rotate x*90  }
   normal { wrinkles 0.66 scale 2.5 omega 0.4 octaves 5 }
  finish { roughness 0.88 specular 0.05 }
  }


object { column translate <100,0,60> }
object { column translate <0,0,60> } // okay, so you can't directly see it.
object { column translate <50,0,60> }

//
// some objects on the wall - pictures defined in picframe.inc
//
object { pic2 scale 1/2 translate <25,20,59.5> }
object { mirrorpic scale 1/2 translate <75,20,59.5> }

object { window translate <101,6,30> }
object { window translate <51,6,0>
         rotate y*90
          }

object { MyTree scale <.5, .75, .5>
	       translate <200, 0, 45>
       }

object { MyTree scale <.75, 1, .75>
	       translate <300, 0, -90>
       }

sky_sphere{Sky}

//
// end of invariant stuff
//

//
// some variable stuff
//
#if (ORIGINAL)

//
// DNA in bell jar
//
//
// DNA in bell jar
//
object { small_case_base scale 0.5
                         translate <23.5,0.24,22>
       }

object { small_case_base scale 0.5
                         translate <50.0,0.24,22>
       }

object { bell_jar_zdna scale <.10, .10, .10>
                       translate <27, 13.5, 25>
       }

object { bna7_full_belljar scale <.1, .1, .1>
                       translate <53.5, 13.5, 25>
       }

object { pic scale 1/2 translate <75,20,59.5> }




object {bdna_bell_jar_on_stand
         translate <23.5, 0.0, 22.0>
       }

object {bell_jar_on_stand
         translate <50, 0.0, 22.0>
       }


object { pic scale 1/2 translate <75,20,59.5> }

#end


#if (NEW)

// pictures
object { prostapic scale 1/2 translate <25,44,59.5> }

// old bell-jar image
object { pic scale 1/2 translate <75,44,59.5> }
//object { musepic scale 1/2 translate <75,44,59.5> }

// point at the prostapic

light_source {
   <25,58,0> color Gray70
   spotlight
   point_at <25,35,60>
   radius 1
   falloff 20
   tightness 20.0
   }


// point at the museumpic
light_source {
   <75,58,0> color Gray70
   spotlight
   point_at <75,40,60>
   radius 1
   falloff 20
   tightness 20.0
   }

#declare bdna_stand = union {
	object {small_case_base scale <.8, .6, .8>}
	object {bna7_full_belljar scale <.15, .15, .15>
		translate <5,15.0,6> }
  }

#declare zdna_bell_jar_on_stand = union {
    object {small_case_base scale 0.5 }
    object {bell_jar_zdna scale 0.1
               translate 13.5*y
            }
   }


// The B-DNA object on its stand (left)
light_source {
   <12,40,30> color Gray85
   spotlight
   point_at <12,18,40>
   radius 20
   falloff 25
   tightness 5
   }


object {bdna_stand translate <13, .25, 37>}

// light to illuminate the rightmost bell-jar
// right-most B-DNA object and light source


object {zdna_bell_jar_on_stand translate <80, .25, 37>}

light_source {
   <65,40,37> color Gray85
   spotlight
   point_at <80,15,38>
   radius 10
   falloff 25
   tightness 20
   }

//
//



#if (VENUS)
#include "stones.inc"
#include "venus1.inc"

//
// Venus de Milo
//
object {
      VenusDeMilo
       pigment { color White }
      texture {
      T_Stone12
         scale <1,1,1>
         finish {
           ambient 0.3
           diffuse .8
         }
      }
       rotate <0,45,0>
       scale <3, 3, 3>
       translate <92, 11, 52>
       }
#end   // if (VENUS)

#if (ATMOS=true)
#include "atmos.inc"

 atmosphere {
    type 1
    samples 50
    distance 4
    scattering 0.2
    //aa_level 10
    //aa_threshold 0.1
    //jitter 0.2
  }
#end // if (ATMOS)


#if (WORLD=true)
#declare worldmap_1 = texture {
    finish { Shiny }
    pigment { color red 0.000 green 0.000 blue 1.000 }}

#declare worldmap_2 = texture {    finish { Shiny }
         pigment { color red 0.000 green 1.000 blue 0.000 }}

#include "worldsphere.inc"
#include "worldmap.inc"

#declare world_top = union {
object {world_base
        scale .9
        //translate <50, 0, 40>
       }

object { world
         scale .6
         translate <0, 12, 0>
       }
}

object {world_top
        translate <50, 10, 40>
        }

light_source {
   <40,40,50> color Gray85
   spotlight
   point_at <40,20,30>
   radius 10
   falloff 25
   tightness 5
   }
#end   // if(world)

#declare mirror_frame = union {
   sphere { <0, 0, 0>, 1 scale <1.3, .55, 1.3> }
   sphere { <0, 0, 0>, 1 scale <1.1, .3, 1.1> translate .4*y  }
   cylinder { <0,0,0>, y, 1 scale <1.0, .2, 1.0> translate .5*y
             texture{mirrortexture}}
   torus {1.0 .025 translate .98*y texture { Gold_Texture}}
   texture {
      marble1
      scale <.9, .6, .4>
      finish {
         ambient 0.1
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

object {mirror_frame
        scale <5.0,1.0,4.0>
        rotate z * 90
        translate <100, 40, 49>
        }



#end  // if (NEW)

// end of file museum.pov
