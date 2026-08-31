//
// BellJar object.
//
// This data and its resulting derivative images are
// (c) 1993-1996, Eric G. Suchanek, Ph.D.
//
// The user is hereby licensed non-commercial use of these
// data and images, provided that this copyright notice remain
// attached to all necessary data files.
//
//

#declare BellJar_Inc_Temp = version
#version 3.0
#include "marble2.inc"

/* The Bell Jar glass object */

// Wall thickness, in pre-scale units.  The jar was originally a zero-
// thickness surface -- an `open` cylinder merged with a sphere -- which
// refracts once instead of twice, so it read as a soap film rather than
// as glass: no rim, no edge, barely visible against a bright sky.  Giving
// it a real wall costs nothing and matters more on a light-field display
// than on a still, because a dome the display cannot see is a dome it
// cannot fuse.  Set to 0 for the original surface.
#ifndef (BJ_WALL)
#declare BJ_WALL = 0.06
#end

// Real refracting crystal rather than the 1996 tinted film.
//
// The 1996 texture has no `interior` at all, so its index of refraction is
// 1.0 and it bends nothing: it is a surface that filters what passes through
// it, which is a soap bubble's optics, not glass's.  With BJ_WALL giving the
// jar two surfaces that reads as two grey outlines down each side of the
// dome, because the filter simply applies twice where the wall is seen
// edge-on.  Turning this on replaces it with ior 1.52 and a Fresnel
// reflection, so the wall refracts instead of tinting and the silhouette
// becomes one bright band -- which is what a glass rim actually looks like.
//
// Off by default: eight scenes share this include, and none of the others
// were composed for a jar that magnifies what is under it.  Set it before
// the #include to turn it on.
#ifndef (BJ_CRYSTAL)
#declare BJ_CRYSTAL = false
#end

#include "glass.inc"

// The crystal texture and interior need POV-Ray 3.6 syntax (`interior` is
// 3.1, Fresnel reflection is 3.6), but the rest of this file -- and every
// scene that includes it -- is composed for 3.0's tone mapping.  Raising the
// language version for the whole file would re-grade the image; bumping it
// around the crystal branch alone does not, and the 1996 path never sees it.
#if (BJ_CRYSTAL)
#declare BellJar_Crystal_Temp = version
#version 3.6;

// Lead crystal.  `rgbt` rather than `rgbf`: transmit passes light through
// unchanged where filter tints it, and clear crystal does not tint -- what
// colour it has comes from absorption over distance, below.
#declare BJ_GLASS_TEXTURE = texture {
   pigment { color rgbt <1, 1, 1, 1> }
   finish {
      ambient 0
      diffuse 0
      specular 0.45
      roughness 0.0012
      // 0.02 head-on rising to 1.0 at grazing incidence, which is what puts
      // the sky into the shoulder of the dome and leaves the front clear.
      reflection { 0.02, 1.0 fresnel on }
      conserve_energy
   }
}

// No dispersion, deliberately.  It is the line you reach for first on
// crystal and it does not pay here.  Measured on bj_holo_2026 at 640x360
// +WT1, `dispersion 1.015` with 7 samples costs 4.5x the render (17.5s
// against 3.9s) and returns a mean difference of 0.63/255 over the jar --
// wide but vanishingly shallow, and concentrated in the rim, where a 6x
// zoom could barely separate the two.  On a quilt it is worse than useless:
// each of the 48 views reaches the eye through lenticular optics with real
// angular crosstalk, which erases a sub-1/255 chromatic shift completely.
// At 960x540 per view it was costing 36 s/view, ~29 minutes a sweep, for
// something the panel cannot deliver.
//
// The fade below is the opposite bargain -- free (17.8s with it removed)
// and it moves 72% of the jar's pixels.  That is the green collecting along
// the silhouette where a ray runs down the length of the glass rather than
// straight through it, and that gradient is what reads as thickness.  With
// ior, the Fresnel reflection and the wall, it does all the visible work.
#declare BJ_GLASS_INTERIOR = interior {
   ior 1.52
   fade_power 1001
   fade_distance 40
   fade_color <0.86, 0.95, 0.90>
}

#end

#if (BJ_WALL = 0)

#declare hemi = object {
        intersection {
                       sphere { <0, 3, 0> , .9}
                       plane {  -y, 2.5 }
                     }
   hollow
}



#declare cyl = object {
        cylinder { <0,0,0>, <0,3.0,0>, .9 open}
   hollow
}
#declare bell = merge {
   object { cyl }
   object { hemi }
   scale <1, 1.5, 1>
   #if (BJ_CRYSTAL)
   texture { BJ_GLASS_TEXTURE }
   interior { BJ_GLASS_INTERIOR }
   #else
   // T_Glass3, inlined from glass_old.inc (the named texture is
   // deprecated and warns on every use); values are verbatim.
   texture {
      pigment { color rgbf <0.98, 0.98, 0.98, 0.9> }
      finish {
         ambient 0.1
         diffuse 0.1
         reflection 0.1
         specular 0.8
         roughness 0.003
         phong 1
         phong_size 400
      }
   }
   #end

  hollow
}

#else

// Outer surface: solid capsule.  The sphere sits at the cylinder's top rim
// and shares its radius, so the two are flush and the merge is a dome on a
// tube.
#declare bell_outer = merge {
   cylinder { <0, 0, 0>, <0, 3.0, 0>, .9 }
   sphere   { <0, 3, 0>, .9 }
}

// Cavity: the same shape inset by the wall, running below y=0 so the jar
// is open at the bottom rather than a sealed bubble.
#declare bell_cavity = merge {
   cylinder { <0, -0.5, 0>, <0, 3.0, 0>, .9 - BJ_WALL }
   sphere   { <0, 3, 0>, .9 - BJ_WALL }
}

#declare bell = difference {
   object { bell_outer }
   object { bell_cavity }
   scale <1, 1.5, 1>
   #if (BJ_CRYSTAL)
   texture { BJ_GLASS_TEXTURE }
   interior { BJ_GLASS_INTERIOR }
   #else
   // T_Glass3, inlined from glass_old.inc (the named texture is
   // deprecated and warns on every use); values are verbatim.
   texture {
      pigment { color rgbf <0.98, 0.98, 0.98, 0.9> }
      finish {
         ambient 0.1
         diffuse 0.1
         reflection 0.1
         specular 0.8
         roughness 0.003
         phong 1
         phong_size 400
      }
   }
   #end
   hollow
}

#end

#if (BJ_CRYSTAL)
#version BellJar_Crystal_Temp;
#end

/*-----------BASE OF COLUMN A / TOP FLOOR-------------------*/
#declare base_a = union {
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

#declare bell_jar = union {
        object { bell }
        object {base_a  translate <0, -1.0, 0>}
   }

#version BellJar_Inc_Temp

