#include "colors.inc"
#include "shapes.inc"
#include "textures.inc"

/* Texture declarations for object 'worldmap' */
#declare worldmap_1 = texture {
    finish { Shiny }
    pigment { color red 0.000 green 0.000 blue 1.000 }}
#declare worldmap_2 = texture {    finish { Shiny }
         pigment { color red 0.000 green 1.000 blue 0.000 }}

#include "worldmap.inc"
camera {
         location <8.4370, 11.7010, -39.7320>
         look_at <-0.7400, -0.5350, 0.0350>}
         light_source {
                      <35.9680, 48.4090, -159.0330> color White}
