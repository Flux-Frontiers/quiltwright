//
// Eric's Museum (based on Meeks museum)
//
// Start Date - 10 Jun 1995
// End Date   -
//
// world2.pov - The Room. (lights, camera, #includes)
//
// This file is the main .pov for the scene.  All the others are included
// here.
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
#include "picframe.pov"

#include "display_base.pov"
#include "bell_jar_objs.inc"

#include "mytree.inc"
#include "window.pov"

#include "marble2.inc"


#declare ORIGINAL = 0.0
#declare NEW = 1.0
#declare VENUS = 0.0


#declare camera_zdna = camera {
  location <15,18.5,5>
  direction <0,0,0.89>
  up <0,1,0>
  right <4/3,0,0>
  look_at <66,5,58>
  angle 75
}

#declare camera_zdna2 = camera {
  location <15,20,6>
  direction <0,0,0.89>
  up <0,1,0>
  right <4/3,0,0>
  look_at <50,22,58>
}

#declare camera_zdna3 = camera {
  location <15,20,6.0>
  direction <0,0,0.89>
  up <0,1,0>
  right <4/3,0,0>
  look_at <55,19,50>
}

#declare camera_bdna = camera {
  location <35,18.5,5>
  direction <0,0,0.89>
  up <0,1,0>
  right <4/3,0,0>
  look_at <50,5,58>
}

#declare camera_front = camera {
  location <35, 18.5, 0>
  direction <0,0,0.89>
  up <0,1,0>
  right <4/3,0,0>
  look_at <35,20,58>
}

#if (ORIGINAL)
  camera {camera_zdna}
#else
  camera {camera_zdna3}
#end

// Spotlight above leftmost bell-jar

light_source {
   <50,58,18> color Gray85
   spotlight
   point_at <25,12,30>
   radius 33
   falloff 20
   tightness 5
   }

light_source {    <205,125,27> color rgb <1,1,0.8>   } // The Sun

// additional light in the room, if you really want it
//light_source {   <50,55,10> color rgb <0.125,0.125,0.115> }


// the ground.

plane { y,-15 pigment { color ForestGreen }
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


// some objects on the wall - pictures

object { pic2 scale 1/2 translate <25,20,59.5> }
object { mirrorpic scale 1/2 translate <75,20,59.5> }


#if (ORIGINAL)

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
   point_at <30,35,60>
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
		translate <5,16,5> }
  }

// The B-DNA object on its stand.

object {bdna_stand translate <80, .25, 37>}

// light to illuminate the rightmost bell-jar
light_source {
   <65,40,37> color Gray85
   spotlight
   point_at <80,15,38>
   radius 10
   falloff 25
   tightness 5
   }

// left-most B-DNA object and light source
object {bdna_stand translate <13, .25, 37>}

light_source {
   <12,40,37> color Gray85
   spotlight
   point_at <12,15,35>
   radius 10
   falloff 25
   tightness 5
   }
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
#end

/*
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
*/

#end

object { window translate <101,6,30> }

object { MyTree scale <.5, .75, .5>
	       translate <200, 0, 45>
       }

sky_sphere{Sky}

