// vitrine.inc -- a standard museum exhibit case for a molecule.
//
// (c) 2026, Eric G. Suchanek, Ph.D.
//
// The archive's molecules stand against an infinite sky.  This puts one in a
// gallery instead: a plinth in a shallow alcove, under a bell jar, lit like an
// exhibit.  It is parametric in exactly one thing that matters -- the
// molecule's enclosing sphere radius, which pdb2pov already writes into every
// scene it produces -- so hemoglobin (R = 40 A) and an MS2 capsid (R = 147 A)
// arrive at the same size on the plinth with no per-structure tuning.
//
// EXHIBIT UNITS.  Everything below is expressed in multiples of the
// molecule's own radius: the molecule is a unit sphere centred on the origin,
// and the room is built around it.  Vitrine_Mount() does the conversion.
//
// LIGHT-FIELD SAFETY.  The alcove is open toward -z and its side walls stand
// at +-VIT_SIDE with the eye at z = -VIT_CAM_D.  The lateral corridor is
// therefore VIT_SIDE wide *by construction*, and Vitrine_Clearance() reports
// it, so the sweep-clearance failure that cost the museum eleven of its
// forty-eight views cannot occur here without being visible in the numbers
// first.  See docs/povray.md section 3.
//
// USAGE
//
//   #declare VIT_LABEL = "HAEMOGLOBIN";
//   #include "vitrine.inc"
//   #include "2hhb.inc"                       // pdb2pov -o output
//   Vitrine_Mount(_2hhb, _2hhb_enclosing_radius)
//   Vitrine_Room()
//   Vitrine_Lights()
//   Vitrine_Camera()
//
// Include order matters only in that vitrine.inc must precede the macro calls.

#ifndef (VITRINE_INC_TEMP)
#declare VITRINE_INC_TEMP = version;
#version 3.7;

#include "colors.inc"
#include "textures.inc"
#include "stones.inc"
#include "shapes.inc"

// ---------------------------------------------------------------------------
// Parameters.  Set any of these *before* including this file to override.
// ---------------------------------------------------------------------------

// Geometry, in exhibit units (molecule radius = 1).
#ifndef (VIT_JAR)        #declare VIT_JAR        = 1;     #end  // 0 = open plinth
// The jar is DERIVED from the molecule, not tuned against it: a hemisphere of
// radius VIT_FILL * VIT_JAR_GAP centred on the molecule, on a tube down to the
// plinth.  That makes it a concentric shell, so it fits any structure the
// enclosing sphere describes without a per-molecule adjustment.
#ifndef (VIT_JAR_GAP)    #declare VIT_JAR_GAP    = 1.22;  #end  // shell/molecule
#ifndef (VIT_JAR_WALL)   #declare VIT_JAR_WALL   = 0.055; #end
#ifndef (VIT_PLINTH_TOP) #declare VIT_PLINTH_TOP = -1.34; #end  // jar sits here
#ifndef (VIT_PLINTH_R)   #declare VIT_PLINTH_R   = 1.62;  #end
#ifndef (VIT_FLOOR)      #declare VIT_FLOOR      = -2.95; #end
#ifndef (VIT_BACK)       #declare VIT_BACK       =  3.40; #end  // alcove back wall
#ifndef (VIT_SIDE)       #declare VIT_SIDE       =  5.30; #end  // alcove side walls
#ifndef (VIT_CEIL)       #declare VIT_CEIL       =  4.10; #end
#ifndef (VIT_THICK)      #declare VIT_THICK      =  0.35; #end  // wall thickness
// The enclosing sphere circumscribes the structure, so a molecule scaled to
// radius 1 reads smaller than the jar it sits in.  VIT_FILL corrects for it.
#ifndef (VIT_FILL)       #declare VIT_FILL       =  1.12;  #end
#ifndef (VIT_MOL_Y)      #declare VIT_MOL_Y      = -0.22;  #end  // seat height
#ifndef (VIT_POST)       #declare VIT_POST       =  1;     #end  // brass mount pin

// Camera.
#ifndef (VIT_CAM_D)      #declare VIT_CAM_D      =  8.00; #end  // eye at z = -this
#ifndef (VIT_CAM_Y)      #declare VIT_CAM_Y      =  0.78; #end
#ifndef (VIT_AIM_Y)      #declare VIT_AIM_Y      = -0.42; #end
#ifndef (VIT_FOV_V)      #declare VIT_FOV_V      = 38.5;  #end  // vertical, degrees
#ifndef (VIT_ASPECT)     #declare VIT_ASPECT     = 16/9;  #end

// Look.
#ifndef (VIT_LABEL)      #declare VIT_LABEL      = "";    #end  // "" = no plaque
#ifndef (VIT_SOFT)       #declare VIT_SOFT       = 0;     #end  // area light: slow, better
#ifndef (VIT_WALL_HUE)   #declare VIT_WALL_HUE   = <0.30, 0.33, 0.34>; #end
#ifndef (VIT_KEY)        #declare VIT_KEY        = 1.00;  #end  // key light scale
#ifndef (VIT_MARGIN)     #declare VIT_MARGIN     = 0.50;  #end  // sweep safety margin

// ---------------------------------------------------------------------------
// Derived
// ---------------------------------------------------------------------------

#declare VIT_JAR_R     = VIT_FILL * VIT_JAR_GAP;
#declare VIT_JAR_TOP   = VIT_MOL_Y + VIT_JAR_R;
#declare VIT_JAR_FRONT = -VIT_JAR_R;
#declare VIT_CAM       = <0, VIT_CAM_Y, -VIT_CAM_D>;
#declare VIT_AIM       = <0, VIT_AIM_Y, 0>;
#declare VIT_DIR       = 0.5 / tan(radians(VIT_FOV_V) / 2);

// ---------------------------------------------------------------------------
// Textures.  Defined inline rather than pulled from marble2.inc, whose
// POV-1.0 dither warns on every render and cannot be modernised pixel-exactly.
// ---------------------------------------------------------------------------

#declare Vit_Wall_Tex = texture {
   pigment {
      granite
      turbulence 0.10
      scale 5.5
      color_map {
         [0.00 color rgb VIT_WALL_HUE * 0.96]
         [0.45 color rgb VIT_WALL_HUE]
         [0.70 color rgb VIT_WALL_HUE * 1.04]
         [1.00 color rgb VIT_WALL_HUE * 0.98]
      }
   }
   finish { ambient 0.06 diffuse 0.72 specular 0.02 roughness 0.6 }
}

#declare Vit_Floor_Tex = texture {
   pigment {
      granite
      turbulence 0.28
      scale 1.4
      color_map {
         [0.00 color rgb <0.085, 0.080, 0.078>]
         [0.50 color rgb <0.135, 0.128, 0.122>]
         [1.00 color rgb <0.070, 0.068, 0.070>]
      }
   }
   // A little reflection is not decoration: the mirrored jar is a second depth
   // cue under the object, and depth cues are the whole point of the display.
   finish { ambient 0.03 diffuse 0.35 reflection 0.16 specular 0.35 roughness 0.012 }
}

#declare Vit_Plinth_Tex = texture {
   pigment {
      granite
      turbulence 0.22
      scale 0.9
      color_map {
         [0.00 color rgb <0.74, 0.72, 0.67>]
         [0.40 color rgb <0.81, 0.79, 0.73>]
         [0.75 color rgb <0.68, 0.66, 0.62>]
         [1.00 color rgb <0.78, 0.76, 0.71>]
      }
   }
   finish { ambient 0.05 diffuse 0.70 specular 0.14 roughness 0.05 }
}

#declare Vit_Slab_Tex = texture {
   pigment {
      granite
      turbulence 0.3
      scale 0.7
      color_map {
         [0.00 color rgb <0.20, 0.20, 0.22>]
         [0.55 color rgb <0.28, 0.28, 0.30>]
         [1.00 color rgb <0.17, 0.17, 0.19>]
      }
   }
   finish { ambient 0.04 diffuse 0.5 reflection 0.06 specular 0.4 roughness 0.02 }
}

#declare Vit_Brass_Tex = texture {
   pigment { color rgb <0.78, 0.64, 0.30> }
   finish { ambient 0.08 diffuse 0.42 brilliance 3 reflection 0.30
            specular 0.75 roughness 0.015 metallic }
}

// Museum glass.  Unlike the 1993 bell jar this has a real interior, so it
// refracts twice and reads as glass rather than as a soap film.
#declare Vit_Glass_Tex = texture {
   pigment { color rgbf <0.97, 0.99, 0.98, 0.94> }
   finish {
      ambient 0.0
      diffuse 0.02
      reflection { 0.04, 0.22 fresnel on }
      specular 0.85
      roughness 0.0016
      phong 1 phong_size 400
   }
}

#declare Vit_Glass_Int = interior { ior 1.52 fade_distance 3.0 fade_power 1001
                                   fade_color <0.92, 0.97, 0.95> }

// ---------------------------------------------------------------------------
// Vitrine_Mount(Obj, EncR) -- normalise a pdb2pov object onto the plinth.
//
// pdb2pov centres its structures on the origin and reports the enclosing
// sphere radius, so dividing by that radius yields a unit sphere.  Pass the
// declared `<name>_enclosing_radius` float; do not measure it yourself.
// ---------------------------------------------------------------------------

#macro Vitrine_Mount(Obj, EncR)
   object {
      Obj
      scale <VIT_FILL/EncR, VIT_FILL/EncR, VIT_FILL/EncR>
      translate <0, VIT_MOL_Y, 0>
   }
#end

// The same, for a scene that wants the object somewhere other than dead centre.
#macro Vitrine_Mount_At(Obj, EncR, Where)
   object {
      Obj
      scale <VIT_FILL/EncR, VIT_FILL/EncR, VIT_FILL/EncR>
      translate Where
   }
#end

// ---------------------------------------------------------------------------
// Vitrine_Case() -- the bell jar, hollow, open at the bottom.
// ---------------------------------------------------------------------------

#macro Vitrine_Case()
#if (VIT_JAR)
   difference {
      merge {
         cylinder { <0, VIT_PLINTH_TOP, 0>, <0, VIT_MOL_Y, 0>, VIT_JAR_R }
         sphere   { <0, VIT_MOL_Y, 0>, VIT_JAR_R }
      }
      merge {
         cylinder { <0, VIT_PLINTH_TOP - 0.4, 0>, <0, VIT_MOL_Y, 0>,
                    VIT_JAR_R - VIT_JAR_WALL }
         sphere   { <0, VIT_MOL_Y, 0>, VIT_JAR_R - VIT_JAR_WALL }
      }
      texture { Vit_Glass_Tex }
      interior { Vit_Glass_Int }
      hollow
   }
   #if (VIT_POST)
   // Mount pin.  A specimen under glass is held on a stand; without one the
   // molecule reads as levitating, which is the wrong kind of strange.
   union {
      cylinder { <0, VIT_PLINTH_TOP, 0>, <0, VIT_MOL_Y - VIT_FILL * 0.55, 0>, 0.055 }
      cylinder { <0, VIT_PLINTH_TOP, 0>, <0, VIT_PLINTH_TOP + 0.06, 0>, 0.21 }
      torus { 0.20, 0.028 translate <0, VIT_PLINTH_TOP + 0.06, 0> }
      texture { Vit_Brass_Tex }
   }
   #end
   // Brass collar where the jar meets the stone -- reads as a seated fit
   // rather than a jar resting on a surface, and catches the key light.
   torus {
      VIT_JAR_R, 0.045
      translate <0, VIT_PLINTH_TOP + 0.012, 0>
      texture { Vit_Brass_Tex }
   }
#end
#end

// ---------------------------------------------------------------------------
// Vitrine_Plinth() -- stone pedestal, dark slab top, brass plaque.
// ---------------------------------------------------------------------------

#macro Vitrine_Plinth()
union {
   // Shaft, very slightly tapered.
   cone {
      <0, VIT_FLOOR, 0>, VIT_PLINTH_R * 1.06,
      <0, VIT_PLINTH_TOP - 0.16, 0>, VIT_PLINTH_R
      texture { Vit_Plinth_Tex }
   }
   // Foot.
   cylinder {
      <0, VIT_FLOOR, 0>, <0, VIT_FLOOR + 0.14, 0>, VIT_PLINTH_R * 1.20
      texture { Vit_Plinth_Tex }
   }
   // Slab top.
   cylinder {
      <0, VIT_PLINTH_TOP - 0.16, 0>, <0, VIT_PLINTH_TOP, 0>, VIT_PLINTH_R * 1.10
      texture { Vit_Slab_Tex }
   }
   // Brass edge line under the slab.
   torus {
      VIT_PLINTH_R * 1.10, 0.022
      translate <0, VIT_PLINTH_TOP - 0.165, 0>
      texture { Vit_Brass_Tex }
   }

   #if (strlen(VIT_LABEL) > 0)
   // Plaque, canted up toward the eye the way a real one is.
   union {
      box {
         <-1.02, -0.20, -0.030>, <1.02, 0.20, 0.030>
         texture { Vit_Brass_Tex }
      }
      // Auto-fit: a plaque is a fixed size and the label is not, so derive the
      // type size from the string length rather than letting "GREEN
      // FLUORESCENT PROTEIN" run off the brass.
      #local L_Sc = min(0.185, 1.62 / (strlen(VIT_LABEL) * 0.62));
      text {
         ttf "timrom.ttf" VIT_LABEL 0.05, 0
         scale L_Sc
         // Centre it: text{} grows to +x from the origin.
         translate <-strlen(VIT_LABEL) * L_Sc * 0.31, -L_Sc * 0.34, -0.052>
         texture {
            pigment { color rgb <0.16, 0.13, 0.07> }
            finish { ambient 0.05 diffuse 0.45 specular 0.15 }
         }
      }
      rotate -20 * x
      translate <0, VIT_PLINTH_TOP - 0.62, -VIT_PLINTH_R * 1.02>
   }
   #end
}
#end

// ---------------------------------------------------------------------------
// Vitrine_Room() -- the alcove.  Open toward -z; that opening is what keeps
// the view sweep legal.
// ---------------------------------------------------------------------------

#macro Vitrine_Room()
union {
   // Floor.  Bounded rather than an infinite plane so the depth budget has a
   // finite near edge; it runs from just behind the eye to the back wall.
   box {
      <-VIT_SIDE, VIT_FLOOR - VIT_THICK, -VIT_CAM_D - 1.0>,
      < VIT_SIDE, VIT_FLOOR,              VIT_BACK>
      texture { Vit_Floor_Tex }
   }
   // Back wall.
   box {
      <-VIT_SIDE, VIT_FLOOR, VIT_BACK>,
      < VIT_SIDE, VIT_CEIL,  VIT_BACK + VIT_THICK>
      texture { Vit_Wall_Tex }
   }
   // Side walls.  These bound the sweep corridor; see Vitrine_Clearance().
   box {
      <-VIT_SIDE - VIT_THICK, VIT_FLOOR, -VIT_CAM_D - 1.0>,
      <-VIT_SIDE,             VIT_CEIL,   VIT_BACK + VIT_THICK>
      texture { Vit_Wall_Tex }
   }
   box {
      < VIT_SIDE,             VIT_FLOOR, -VIT_CAM_D - 1.0>,
      < VIT_SIDE + VIT_THICK, VIT_CEIL,   VIT_BACK + VIT_THICK>
      texture { Vit_Wall_Tex }
   }
   // Ceiling.  Mostly out of frame; it closes the box so stray light and any
   // future radiosity bounce behave.
   box {
      <-VIT_SIDE - VIT_THICK, VIT_CEIL,              -VIT_CAM_D - 1.0>,
      < VIT_SIDE + VIT_THICK, VIT_CEIL + VIT_THICK,   VIT_BACK + VIT_THICK>
      texture { Vit_Wall_Tex }
   }
}
#end

// ---------------------------------------------------------------------------
// Vitrine_Lights() -- three-point gallery lighting.
//
// Key from above-front-left as a spot, so the plinth throws one clean shadow
// and the jar gets a specular seam.  Fill is shadowless and cool, to open the
// shadow without adding a second one.  The wash separates jar from wall.
// ---------------------------------------------------------------------------

#macro Vitrine_Lights()
   light_source {
      <-3.2, 4.6, -3.8>
      color rgb <1.00, 0.965, 0.90> * (1.15 * VIT_KEY)
      spotlight
      point_at <0, VIT_PLINTH_TOP + 0.4, 0>
      radius 17 falloff 30 tightness 6
      #if (VIT_SOFT)
      area_light <0.9, 0, 0>, <0, 0, 0.9>, 5, 5
      adaptive 1
      jitter
      #end
   }
   light_source {
      <4.6, 2.1, -6.4>
      color rgb <0.86, 0.91, 1.00> * (0.34 * VIT_KEY)
      shadowless
   }
   light_source {
      <0, 3.4, 1.4>
      color rgb <0.90, 0.95, 1.00> * (0.22 * VIT_KEY)
      shadowless
   }
   // Wall pool: a broad soft spot on the back wall behind the case, so the
   // silhouette separates instead of sitting on a flat field.
   light_source {
      <0, 2.6, -1.6>
      color rgb <1.00, 0.96, 0.90> * (0.42 * VIT_KEY)
      spotlight
      point_at <0, 0.2, VIT_BACK>
      radius 22 falloff 42 tightness 4
      shadowless
   }
   // Floor bounce, faint, keeps the underside of the molecule from going flat.
   light_source {
      <0, VIT_FLOOR + 0.3, -2.2>
      color rgb <1.00, 0.94, 0.86> * (0.13 * VIT_KEY)
      shadowless
   }
#end

// ---------------------------------------------------------------------------
// Vitrine_Camera() -- the still camera.  A quilt render replaces this via
// quiltwright's render_pov_quilt; the numbers it needs are printed by
// Vitrine_Report().
// ---------------------------------------------------------------------------

#macro Vitrine_Camera()
   camera {
      location  VIT_CAM
      look_at   VIT_AIM
      up        <0, 1, 0>
      right     <VIT_ASPECT, 0, 0>
      direction <0, 0, VIT_DIR>
   }
#end

// ---------------------------------------------------------------------------
// Vitrine_Report() -- print the four numbers quiltwright asks for, so they
// come out of the scene rather than being guessed at the Python end.
// ---------------------------------------------------------------------------

#macro Vitrine_Report()
   #debug concat("\n[vitrine] eye        = <0, ", str(VIT_CAM_Y,0,3), ", ",
                 str(-VIT_CAM_D,0,3), ">\n")
   #debug concat("[vitrine] aim        = <0, ", str(VIT_AIM_Y,0,3), ", 0>\n")
   #debug concat("[vitrine] fov_v      = ", str(VIT_FOV_V,0,2),
                 "   aspect = ", str(VIT_ASPECT,0,4), "\n")
   #debug concat("[vitrine] near       = ", str(VIT_CAM_D + VIT_JAR_FRONT,0,3),
                 "   (jar front)\n")
   #debug concat("[vitrine] far        = ", str(VIT_CAM_D + VIT_BACK,0,3),
                 "   (back wall)\n")
   #debug concat("[vitrine] jar_r      = ", str(VIT_JAR_R,0,3),
                 "   fill ", str(VIT_FILL,0,2), "\n")
   #debug concat("[vitrine] clearance  = +-", str(VIT_SIDE,0,3),
                 "   margin ", str(VIT_MARGIN,0,2), "\n")
   #debug concat("[vitrine] max cone   = ",
                 str(2 * degrees(atan((VIT_SIDE - VIT_MARGIN) /
                     (2 / (1/(VIT_CAM_D + VIT_JAR_FRONT) + 1/(VIT_CAM_D + VIT_BACK))))),0,2),
                 " deg\n\n")
#end

#version VITRINE_INC_TEMP;
#end
