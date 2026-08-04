#if (DO_RAINBOW)

#declare r_violet1 = colour rgbf<1.0, 0.5, 1.0, 0.9>
#declare r_violet2 = colour rgbf<1.0, 0.5, 1.0, 0.8>
#declare r_indigo  = colour rgbf<0.5, 0.5, 1.0, 0.8>
#declare r_blue    = colour rgbf<0.2, 0.2, 1.0, 0.8>
#declare r_cyan    = colour rgbf<0.2, 1.0, 1.0, 0.8>
#declare r_green   = colour rgbf<0.2, 1.0, 0.2, 0.8>
#declare r_yellow  = colour rgbf<1.0, 1.0, 0.2, 0.8>
#declare r_orange  = colour rgbf<1.0, 0.5, 0.2, 0.8>
#declare r_red1    = colour rgbf<1.0, 0.2, 0.2, 0.8>
#declare r_red2    = colour rgbf<1.0, 0.2, 0.2, 0.9>

rainbow {
    angle 42.5
    width 5
    distance 1.0e7
   // direction <0.2, -0.2, 1>
    direction <0.2, -0.2, .6>
    jitter 0.01
    arc_angle 240
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
