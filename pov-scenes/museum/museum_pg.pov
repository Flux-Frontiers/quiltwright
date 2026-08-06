// Persistence of Vision Ray Tracer Scene Description File
// File: museum.pov
// Vers: 4.1
// Desc: Eric's Science Museum, main scene file.
// Start Date: 10 Jun 1995
// Date: 1/1/1999
// Auth: Eric G. Suchanek, Ph.D.
/* museum_new_990101.pov */
/* $Log$ */


//
// This file is now heavily POV-Ray 3.0 dependent. Don't try this one with
// prior versions, since all of the conditionals will fail.
//

#version 3.0

#declare PC = true          // settings specific to V3.1 of POV-RAY

// pc gamma is about 2.5
// mac gamma is about 1.8
// unix gamma is about 1.7
// note that 1.8 is the closest to uncorrected gamma (typical MAC), so
// we'll assume that's the case here. Using a gamma of 1.8 also optimizes
// the image for CMYK printing, since this gamma value approximates CMYK ink
// (according to Photoshop). As a result, the image should print with relatively
// true colors.


#if (PC)
  global_settings { assumed_gamma 2.2 max_trace_level 9}
#else
  global_settings { assumed_gamma 1.8 max_trace_level 12}
#end

#include "colors.inc"
#include "skies.inc"


#include "world2.inc"
#include "column.inc"
#include "picframe.inc"
#include "picframe_new.pov"
#include "risedronate3.inc"

#include "display_base.pov"
#include "bell_jar_objs.inc"

#include "mytree.inc"
#include "window.pov"

#include "marble2.inc"


//
// some useful switch variables for cameras, views and objects
//

#declare ORIGINAL = false       // true for the 'classic' version
#declare NEW_VERS = true        // now the default

#declare VENUS = false          // set to true to include Venus deMilo
#declare WORLD = false          // set to true to include the world map
#declare ATMOS = false          // set to true to include atmosphere - long!
#declare OUTSIDE_VIEW = false   // set to true to view from the outside
#declare DO_RAINBOW = true      // do the rainbow
#declare BRIGHT = false         // bright interior spotlight, cool shadows
#declare DAYTIME = true         // create the sun outside
#declare DNA_CARTOON = true     // the DNA cartoon mobile
#declare LAMBDA = true          // lambda repressor picture
#declare MIRROR_FRAME = false   // oval mirror on wall
#declare DO_RISED3D = false     // risedronate coming out of picture.
#declare DO_STAINED_GLASS = false // P&G stained glass logo
#declare DO_HEALTHCARE_FLOOR = true
#declare DO_LOGO_VIEW = false


#include "aspect.inc"

// 3500x2300

#declare ASPECT=5/4 // for 10"x8"

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
  the_lens
  location <15,18.5,5>
  look_at <66,5,58>
  angle 75
}

#declare camera_zdna2 = camera {
  the_lens
  location <15,20,6>
  look_at <50,22,58>
}

#declare camera_zdna3 = camera {
  the_lens
  location <15,20,6.0>
  look_at <58,19,53>  // 52
}

#declare camera_bdna = camera {
  the_lens
  location <35,18.5,5>
  look_at <50,5,58>
}

#declare camera_zdna_new = camera {
  the_lens
  location <50,20,15>
  look_at <13,5,40>
}

#declare camera_front = camera {
  the_lens
  location <35, 18.5, 00>
  look_at <35,20,58>
}

#declare camera_frame_corner = camera {
  the_lens
  location <40, 30, 35>
  look_at <40,30,58>
}

#declare camera_outside_belljar = camera {
  the_lens
  location <100, 18, 50>
  look_at <13, 20, 0 >
}

#declare camera_outside_far = camera {
  the_lens
  location <180, 18, 45>
  look_at <13, 20, 0 >
  }

#declare camera_outside = camera {
  the_lens
  location <110, 18, 45>
  look_at <13, 20, -10 >

}


#declare camera_rised = camera {
  the_lens
  location <80, 40, 45>
  look_at <100, 40, 45 >
  }

#declare CYL_Z = 30

#declare camera_stained_logo = camera {
  the_lens
  location <70, 30, 20>
  look_at <0, 30, CYL_Z >
  }

//
// finally, actually define the camera to use
//

#if (ORIGINAL)
  camera {camera_zdna}
#else
 #if (OUTSIDE_VIEW)
   camera {camera_outside}
 #else
  #if (DO_LOGO_VIEW)
      camera {camera_stained_logo}
  #else
   camera {camera_zdna3}
  #end
 #end
#end

#declare shiny_gold = texture {pigment { BrightGold } finish { Metal } }
#declare _redmetal = texture {pigment {color Orange} finish {Metal}}
#declare _bluemetal = texture {pigment {color LightBlue} finish {Metal}}

//
// Spotlight above rightmost bell-jar
//

light_source {
   <55,38,18> color White
   spotlight
   point_at <35,15,30> // <35,12,30>
   radius 19           // 16
   falloff 20
   tightness 20
   }

#if (DAYTIME)
light_source {    <205,125,27> color rgb <1,1,0.8>   } // The Sun
#end

// additional light in the room, if you really want it
light_source {   <50,55,10> color rgb <0.125,0.125,0.115> }

//
// invariant room stuff
// the ground.

plane { y,0 pigment { color Brown }
	normal { bumps 1.0 octaves 5 scale 20 }
        finish { crand 0.003 ambient 0.6 diffuse 0.4 }}


#declare walls = difference { // the Room
  box { <-1,-5,-5>,<102,65,65> } // -5 -5 -5
  box { <0,0,0>,<100,60,60>  }
  box { <99.5,5,19>,<102.5,46,41> }

  cylinder {<-5,35,CYL_Z>, <5,35,CYL_Z>, 20} // for stained glass

  cylinder { <99.5,46,30>,<102.5,46,30>,11 }
  texture { wall_tex }
}

#declare wall2 = union {
         object {walls}
         box { <40, 20, 65>, <60, 55, 85> texture {wall_tex} }
}

#declare  walls_alcove = difference {
          object {wall2}
          cylinder { <50,30,60>, <50, 50, 60>, 6.5 texture {wall_tex}}
}

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
  box {<0,0,0>,<100,3,60> }
  box { <1/2,-1/100,1/2>,<99.5,3.01,59.5> }  texture {  mould_tex } }

cylinder { <0,3,0>,<100,3,0>,1/2 texture { mould_tex }}
cylinder { <0,3,0>,<0,3,60>,1/2 texture { mould_tex }}

cylinder { <0,3,60>,<100,3,60>,1/2 texture { mould_tex }}
cylinder { <100,3,0>,<100,3,60>,1/2 texture { mould_tex }}


// healthcare logo floor definitions
#declare logo_plane = object {
 plane
 {
  z, -.01
  texture
  {
    pigment
    {
      image_map
      {
        tga "hclogo.tga"
        interpolate 2 // smooth it
        once   // don't tile image, just one copy
      }
      // transform it to unit-size (-1 to +1)
      translate -0.5*(x+y) // center on the origin
      scale 2              // make it unit-sized
    }
    finish {Shiny}
  }
 }
}


#declare ring = object {
torus
{  .99,  0.017}
  texture {_bluemetal}
  rotate x*90 }


#declare logo_disk = object {
  union{
     intersection {
         object {logo_plane}
         cylinder { 0*z,-.02*z,1 open}
     }

    object {ring}
  }
  rotate x * 90  // now oriented with Y up.
 }

#if (DO_HEALTHCARE_FLOOR)
 object {logo_disk scale 22 translate <55,0.1,35>}
#else
 box { // rug
  <5,1/4,15>,<85,1/2,45>
  pigment { //color red 0.4 }
  image_map { gif "rug.gif" once  interpolate 2   }
  scale <70,30,1> translate <15,15,0> rotate x*90  }
  normal { wrinkles 0.66 scale 2.5 omega 0.4 octaves 5 }
  finish { roughness 0.88 specular 0.05 }
 }

#end

//// stained glass ////
#if (DO_STAINED_GLASS)

#declare logo_plane_transp = object {
 plane
 {
  z, -.01
  texture
  {
    pigment
    {
      image_map
      {
        gif "hclogo.gif"
        interpolate 2 // smooth it
        once   // don't tile image, just one copy
        filter all .9  // make 1st color mostly transparent
 //       filter 1 0.8  // make 2nd color mostly transparent
      }
      // transform it to unit-size (-1 to +1)
      translate -0.5*(x+y) // center on the origin
      scale 2              // make it unit-sized
    }
    finish {Metal}
  }
 }
}

#declare logo_disk_transp = object {
  union{
     intersection {
         object {logo_plane_transp}
         cylinder { 0*z,-.02*z,1 open}
     }

    object {ring}
  }
  rotate y*-90
 }

// object { MyTree scale <.5, .5, .5> translate <-80, 0, 10> }
object {logo_disk_transp scale 20 translate <.5,35,CYL_Z>}

//light_source {   <.2,35,25> color rgb <.3, .3, .3> }


// create a point "spotlight" (conical directed) light source

  light_source {
   <65,50,25> color Gray60
   spotlight
   point_at <0,35,25>
   radius 30
   falloff 20
   tightness 70
   }

#end


object { column translate <100,0,60> }
object { column translate <0,0,60> } // okay, so you can't directly see it.
object { column translate <0,0,0> }

//
// some objects on the wall - pictures defined in picframe.inc
//

//object { raspic scale 1/2 translate <25,20,59.5> }
object { fluprostpic scale 1/2 translate <75,20,59.5> }


//object { lambdapic scale 1/2 translate <75,20,59.5>

#if (LAMBDA)
    object { lambdapic scale 1/2 translate <25,20,59.5> }
#else
     object { mirrorpic scale 1/2 translate <75,20,59.5> }
#end
// point at the lambdapic

light_source {
   <75,35,20> color Gray40
   spotlight
//   point_at <85,25,70>
   point_at <75,20,60>
   radius 5
   falloff 20
   tightness 20.0
   }

object { window translate <101,6,30> }
object { window translate <51,6,0> rotate y*90 }

#if (DO_STAINED_GLASS)
#else
object { MyTree scale <.5, 1, .5> translate <205, 0, 50> }

#end

//object { MyTree scale <.75, 1, .75> translate <300, 0, -90> }

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

object { small_case_base scale 0.5 translate <23.5,0.24,22> }
object { small_case_base scale 0.5  translate <50.0,0.24,22> }

object { bell_jar_zdna scale <.10, .10, .10> translate <27, 13.5, 25> }
object { bna7_full_belljar scale <.1, .1, .1> translate <53.5, 13.5, 25>}

object { pic scale 1/2 translate <75,20,59.5> }

//object {bdna_bell_jar_on_stand translate <23.5, 0.0, 22.0> }
//object {bell_jar_on_stand translate <50, 0.0, 22.0> }


object { pic scale 1/2 translate <75,20,59.5> }

#end // if original

//
//

#if (NEW_VERS)

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
	object { bna7_full_belljar
              scale .15
		      translate <5,15.0,6>
           }
  }

#declare zdna_bell_jar_on_stand = union {
    object {small_case_base scale <.8, .6, .8>}
    object { bell_jar_zdna
               scale 0.15
		       translate <5,15.0,6>
           }
   }


object {zdna_bell_jar_on_stand translate <80, .25, 37>}

// light to illuminate the rightmost bell-jar
// right-most B-DNA object and light source



light_source {
//   <80,40,20> color Gray85
   <70,40,30> color Gray85
   spotlight
   point_at <80,20,38>
   radius 10
   falloff 25
   tightness 20
   }



object {bdna_stand translate <16, .25, 37>}
// light it up
light_source {
   <12,40,20> color Gray85
//<16,40,30> color Gray85
   spotlight
   point_at <16,20,38>
   radius 15
   falloff 25
   tightness 20
   }

//
//

#if (BRIGHT)
light_source {
   <50,4,30> color Gray85
  }
#end


#if (DNA_CARTOON)
#include "dna_cartoon.inc"
#include "glass.inc"

#declare glass_front = intersection {
         cylinder { <50,30,61>, <50,50,61>, 6.0 hollow}
         plane {-z, 61}
         texture { T_Glass2 }
#if (PC)
          interior{I_Glass} 
#end  
         }



#declare myMetal = texture {pigment {color Silver} finish {Metal}}
// create a sphere shape

#declare bowl2 = object {
intersection {
 sphere
 {
  <0, 0, 0> // center of sphere <X Y Z>
  7       // radius of sphere
  hollow
 }
 plane { y, .01}
} // intersection

texture {myMetal}

} // object

#declare bowl = union {

// torus {MAJOR, MINOR} // (in the X-Z plane)
// MAJOR = float value giving the major radius
// MINOR = float specifying the minor radius
// The major radius extends from the center of the hole
// to the mid-line of the rim while the minor radius
// is the radius of the cross-section of the rim.
torus
{
  7.05,
  0.5
}

intersection {
 sphere
 {
  <0, 0, 0> // center of sphere <X Y Z>
  7       // radius of sphere
  hollow
 }
 plane { y, .01}
} // intersection

texture {myMetal}

} // object

object {walls_alcove}
object {glass_front}

object {bowl translate <50, 30, 61> }

//object {bowl rotate z*180 translate <50, 56.5, 61> }
object {bowl rotate z*180 translate <50, 50, 61> }

object {obj_DNA_Cartoon scale .4  translate <50, 32, 60> }

light_source {
   <50,50,0> color Gray60
   spotlight
   point_at <50,30,70>
   radius 10
   falloff 25
   tightness 50
   }
#end

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
         scale <5,5,5>
         finish {
           ambient 0.3
           diffuse .8
         }
      }
       rotate <0,30,0>
       scale 1
       translate <50, 11, 40>
       }

#declare base_b = union {
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

object {base_b  translate <50, 10, 40>
        scale <10,10,10>}

// create a point "spotlight" (conical directed) light source

  light_source {
   <50,40,0> color Gray60
   spotlight
   point_at <50,15,44>
   radius 5
   falloff 15
   tightness 70
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
        translate <50, 0, 40>
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

#if (MIRROR_FRAME)
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
#else


#declare rised = object {
	risedpic
	scale <.3,.3,.3>
	rotate <0,0,90>
}
object {rised
       rotate <0,90,0>
        translate <100, 40, 49>
        }

light_source {
   <50,30,50> color Gray70
   spotlight
   point_at <100,40,50>
   radius 5
   falloff 18
   tightness 20.0
   }


#if (DO_RISED3D)
#declare rised_orient = object {risedronate3 rotate <0,0,90>}

//////

object {rised_orient
        rotate <0, 115, 0>
        translate <99, 42.0, 49.0> }
#end

#end


#if (DO_RAINBOW)

#declare r_violet1 = colour rgbf<1.0, 0.5, 1.0, 1.0>
#declare r_violet2 = colour rgbf<1.0, 0.5, 1.0, 0.8>
#declare r_indigo  = colour rgbf<0.5, 0.5, 1.0, 0.8>
#declare r_blue    = colour rgbf<0.2, 0.2, 1.0, 0.8>
#declare r_cyan    = colour rgbf<0.2, 1.0, 1.0, 0.8>
#declare r_green   = colour rgbf<0.2, 1.0, 0.2, 0.8>
#declare r_yellow  = colour rgbf<1.0, 1.0, 0.2, 0.8>
#declare r_orange  = colour rgbf<1.0, 0.5, 0.2, 0.8>
#declare r_red1    = colour rgbf<1.0, 0.2, 0.2, 0.8>
#declare r_red2    = colour rgbf<1.0, 0.2, 0.2, 1.0>

rainbow {
    angle 240
    width 5
    distance 1.0e7
    direction <0.2, -0.2, 1>
    jitter 0.01
    arc_angle 150
    falloff_angle 30

    colour_map {
      [0.000  colour r_violet1 transmit 0.98]
      [0.100  colour r_violet2 transmit 0.96]
      [0.214  colour r_indigo  transmit 0.94]
      [0.328  colour r_blue    transmit 0.92]
      [0.442  colour r_cyan    transmit 0.90]
      [0.556  colour r_green   transmit 0.92]
      [0.670  colour r_yellow  transmit 0.94]
      [0.784  colour r_orange  transmit 0.96]
      [0.900  colour r_red1    transmit 0.98]
    }
  }

#end // if do_rainbow


#end  // if (NEW_VERS)

// end of file museum.pov


