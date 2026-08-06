#declare Marble_Inc_Temp = version
#version 1.0

// Persistence of Vision Raytracer Version 2.0
/*------- DECLARE TEXTURES FOR MULTI LAYERED MARBLES -----------*/


/*---------------LIGHT CREAM MOSS / GOOD FOR 1st LAYER TONE----------------*/
#declare marble1 = texture {
   marble
   colour_map {
      [0.000 0.154   colour red  0.690  green  0.612  blue  0.569  alpha  0.000
      colour red  0.737  green  0.596  blue  0.522  alpha  0.000]
      [0.154 0.368   colour red  0.737  green  0.596  blue  0.522  alpha  0.000
      colour red  0.776  green  0.702  blue  0.624  alpha  0.000]
      [0.368 0.538   colour red  0.776  green  0.702  blue  0.624  alpha  0.000
      colour red  0.796  green  0.678  blue  0.643  alpha  0.000]
      [0.538 0.846   colour red  0.796  green  0.678  blue  0.643  alpha  0.000
      colour red  0.690  green  0.612  blue  0.569  alpha  0.000]
      [0.846 0.932   colour red  0.690  green  0.612  blue  0.569  alpha  0.000
      colour red  0.773  green  0.612  blue  0.569  alpha  0.000]
      [0.932 1.001   colour red  0.773  green  0.612  blue  0.569  alpha  0.000
      colour red  0.690  green  0.612  blue  0.569  alpha  0.000]
   }      /* end_colour_map */
   turbulence 0.4
   0.1
}/* end_texture */

/*--------------------Crack & OverTint /Red---------------------*/
#declare marble4 = texture {
   marble
   color_map {
      [0.0 0.05 color Black alpha 0.6 color Black alpha 1.0]
      [0.05 0.90 color Red alpha 0.95 color Red alpha 0.95] 
      [0.90 1.001 color Black alpha 0.7 color Black alpha 1.0]
   }      /* end_color_map */
   turbulence 0.7
   0.03
}/* end_texture */	

#version Marble_Inc_Temp
