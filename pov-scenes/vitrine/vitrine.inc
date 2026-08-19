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
#ifndef (VIT_SIGN)       #declare VIT_SIGN       = 1;     #end  // 0 = unsigned
#ifndef (VIT_SIGN_TEXT)  #declare VIT_SIGN_TEXT  = "EGS 2026"; #end
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
// Vitrine_Wrapped_Text(Str, Sc, Rad, Yd, ACtr, Dp) -- lettering laid round a
// cylinder, one glyph at a time.
//
// Each glyph is measured with max_extent() and given its own angle, so the
// spacing stays proportional on the curve instead of the monospaced look a
// fixed angular step gives.  Emits bare objects and no texture, so the caller
// wraps the call in a union and textures that.
//
// :param Str: the string.
// :param Sc: glyph scale.
// :param Rad: radius of the surface the lettering stands on.
// :param Yd: vertical offset from the run's own centre line.
// :param ACtr: centre angle in degrees; 0 is dead front, positive is right.
// :param Dp: how far the lettering stands proud, in units.
// ---------------------------------------------------------------------------

#macro Vitrine_Wrapped_Text(Str, Sc, Rad, Yd, ACtr, Dp)
   #local W_N = strlen(Str);
   #local W_Gap = Sc * 0.16;
   // `scale` inside text{} scales the extrusion too, so ask for a depth that
   // survives it: without this the lettering is a hundredth of a unit deep and
   // sits buried in the brass, showing only the tips of the capitals.
   #local W_Dp = Dp / Sc;

   // Pass one: total width, so the string can be centred on ACtr.
   #local W_W = 0;
   #local W_I = 1;
   #while (W_I <= W_N)
      #local W_Ch = substr(Str, W_I, 1);
      #if (strcmp(W_Ch, " ") = 0)
         #local W_W = W_W + Sc * 0.42;
      #else
         #local W_G = text { ttf "timrom.ttf" W_Ch W_Dp, 0 scale Sc };
         #local W_W = W_W + (max_extent(W_G).x - min_extent(W_G).x) + W_Gap;
      #end
      #local W_I = W_I + 1;
   #end

   // Pass two: place them.  POV-Ray is left-handed and its default camera
   // looks along +z, so text{} already reads correctly to a viewer on the -z
   // side and needs no flip -- it extrudes away from that viewer, into the
   // surface, which is exactly what raised lettering should do.
   #local W_Cur = -W_W / 2;
   #local W_I = 1;
   #while (W_I <= W_N)
      #local W_Ch = substr(Str, W_I, 1);
      #if (strcmp(W_Ch, " ") = 0)
         #local W_Cur = W_Cur + Sc * 0.42;
      #else
         #local W_G = text { ttf "timrom.ttf" W_Ch W_Dp, 0 scale Sc };
         #local W_Gw = max_extent(W_G).x - min_extent(W_G).x;
         #local W_A = ACtr + degrees((W_Cur + W_Gw / 2) / Rad);
         object {
            W_G
            translate <-(min_extent(W_G).x + W_Gw / 2), Yd - Sc * 0.36, 0>
            translate <0, 0, -(Rad + Dp)>
            rotate -W_A * y
         }
         #local W_Cur = W_Cur + W_Gw + W_Gap;
      #end
      #local W_I = W_I + 1;
   #end
#end

// ---------------------------------------------------------------------------
// Vitrine_Plinth_R(Y) -- the shaft's radius at height Y.
//
// The shaft is tapered, so anything that has to sit flush against it -- the
// plaque, for one -- needs the local radius rather than the nominal one.
// ---------------------------------------------------------------------------

#macro Vitrine_Plinth_R(Y)
   (VIT_PLINTH_R * 1.06
    + (Y - VIT_FLOOR) / ((VIT_PLINTH_TOP - 0.16) - VIT_FLOOR)
      * (VIT_PLINTH_R - VIT_PLINTH_R * 1.06))
#end

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
   // Plaque.  A flat slab tangent to a round plinth reads as a sticker, so
   // this is a band of the plinth's own surface: a conical shell sharing the
   // shaft's taper, with the lettering laid around it glyph by glyph.
   #local P_H  = 0.21;                       // half-height
   #local P_T  = 0.028;                      // how far it stands proud
   #local P_Y  = VIT_PLINTH_TOP - 0.60;      // centre height
   #local P_Rb = Vitrine_Plinth_R(P_Y - P_H);
   #local P_Rt = Vitrine_Plinth_R(P_Y + P_H);
   #local P_Rm = (P_Rb + P_Rt) / 2;
   #local P_Arc = 2.10;                      // arc length of the brass, in units
   #local P_HalfA = degrees(P_Arc / 2 / P_Rm);
   #local P_Xh = (P_Rm + P_T) * sin(radians(P_HalfA));

   union {
      intersection {
         difference {
            cone { <0, -P_H, 0>, P_Rb + P_T, <0, P_H, 0>, P_Rt + P_T }
            cone { <0, -P_H - 0.02, 0>, P_Rb - 0.004, <0, P_H + 0.02, 0>, P_Rt - 0.004 }
         }
         box { <-P_Xh, -P_H - 0.01, -(P_Rm + P_T + 0.02)>, <P_Xh, P_H + 0.01, -0.02> }
         texture { Vit_Brass_Tex }
      }

      // Lettering.
      #local L_N  = strlen(VIT_LABEL);
      #local L_Sc = min(0.175, 1.86 / (L_N * 0.62));
      union {
         Vitrine_Wrapped_Text(VIT_LABEL, L_Sc, P_Rm + P_T, 0.026, 0, 0.038)
         texture {
            pigment { color rgb <0.15, 0.12, 0.06> }
            finish { ambient 0.04 diffuse 0.40 specular 0.18 roughness 0.03 }
         }
      }

      // Signature, lower right, the way a maker's mark sits on a real plate:
      // small, shallower, and set in from the edge rather than centred.
      #if (VIT_SIGN & strlen(VIT_SIGN_TEXT) > 0)
      #local S_Sc = L_Sc * 0.40;
      union {
         Vitrine_Wrapped_Text(VIT_SIGN_TEXT, S_Sc, P_Rm + P_T,
                              -P_H * 0.60, P_HalfA * 0.58, 0.020)
         texture {
            pigment { color rgb <0.20, 0.16, 0.09> }
            finish { ambient 0.04 diffuse 0.38 specular 0.14 roughness 0.04 }
         }
      }
      #end

      translate <0, P_Y, 0>
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
      <-2.6, 5.4, -3.0>
      color rgb <1.00, 0.965, 0.90> * (1.10 * VIT_KEY)
      spotlight
      point_at <0, VIT_PLINTH_TOP - 0.2, 0.2>
      radius 19 falloff 34 tightness 6
      #if (VIT_SOFT)
      area_light <0.9, 0, 0>, <0, 0, 0.9>, 5, 5
      adaptive 1
      jitter
      #end
   }
   light_source {
      <4.6, 2.1, -6.4>
      color rgb <0.86, 0.91, 1.00> * (0.24 * VIT_KEY)
      shadowless
   }
   light_source {
      <0, 3.4, 1.4>
      color rgb <0.90, 0.95, 1.00> * (0.22 * VIT_KEY)
      shadowless
   }
   // Ceiling downlight.  The key rakes across the case and models it, but a
   // raking light throws its shadow mostly out of frame.  This one comes from
   // almost overhead and slightly front, so the plinth and jar lay a shadow
   // on the floor that the eye can actually read -- the cue that says the
   // exhibit is standing on something rather than pasted onto it.
   light_source {
      <-1.3, VIT_CEIL - 0.25, -1.9>
      color rgb <1.00, 0.98, 0.94> * (1.00 * VIT_KEY)
      spotlight
      point_at <0.5, VIT_FLOOR, 0.7>
      radius 15 falloff 27 tightness 10
      #if (VIT_SOFT)
      area_light <0.7, 0, 0>, <0, 0, 0.7>, 5, 5
      adaptive 1
      jitter
      #end
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
      color rgb <1.00, 0.94, 0.86> * (0.08 * VIT_KEY)
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
