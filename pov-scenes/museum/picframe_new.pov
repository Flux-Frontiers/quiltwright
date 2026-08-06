//
// picture frame definitions for Eric's museum shot
//
// 5/15/98 -egs-

/* $Version$ */
/* $Log$ */

//  $MRY$: 'canvasstexture'
#declare canvasstextureO = texture {
 pigment { color rgb <0.075,0.075,0.07> }
 finish { roughness 0.3 specular 0.3 }
 normal { wrinkles 0.25 omega 0.666 octaves 3 scale 1/3 }
}

#declare canvasstexture = texture {
 pigment { color rgb <0.075,0.075,0.07> }
 finish { roughness 0.1 specular 0.3 }
 normal { wrinkles 0.1 omega 0.666 octaves 3 scale 1/3 }
}

#declare mirrortexture = texture {
  pigment {color rgb <.9, .9, .9> }
  finish { reflection 1.0 ambient 0 diffuse 0 }
 }

//  $MRY$: 'edgetex'
#declare edgetex = texture {
 pigment {
  wood
  color_map { [0  color rgb <0.3,0.23,0.14>]
              [0.6 color rgb <0.32,0.24,0.15>]
              [0.8  color rgb <0.4,0.35,0.19>]
              [1 color rgb <0.3,0.23,0.14>] }
       turbulence 0.4
       scale 0.7
       omega 2/3
     }
  finish {
  phong   0.65
  phong_size  23.00
 }
}

#declare myedgebottom = cylinder {
  <-1, 0, 0>, <1, 0, 0> , 1 texture {edgetex}
}

//
// the cutting planes to create a bevel
//

#declare rbevel = plane { <.71, .71, 0>, 0 }
#declare lbevel = plane { <-.71, .71, 0>, 0}

//
// little beveled end caps to be added
#declare rcyl_bevel =
	intersection {
	  cylinder { <0,0,0>, <1, 0, 0>, 1 texture {edgetex} }
	  object {rbevel translate <1 - .707, 0, 0>}
//	  pigment { color Brown }
	 texture {edgetex}

}

#declare lcyl_bevel =
	 object { rcyl_bevel rotate <0,180,0> }




// one piece of the frame, centered, oriented along X,
// size -1 -> 1

#declare frame_bottom = union {
	object {myedgebottom scale <31,1,1> }
	object {rcyl_bevel translate <30.9, 0, 0>}
	object {lcyl_bevel translate <-30.9, 0, 0>}
}

#declare frame_top = object {frame_bottom rotate 180*z}

#declare edge_side = union {
	object {myedgebottom scale <21,1,1> }
	object {rcyl_bevel translate <20.9, 0, 0>}
	object {lcyl_bevel translate <-20.9, 0, 0>}
}

#declare frame_left = object {edge_side
	rotate <0,0,-90>
}


#declare frame_right = object {edge_side
	rotate <0,0,90>
}

#declare egs_frame = union {
	object {frame_bottom translate <0,-21,0>}
	object {frame_top translate <0,21,0>}
	object {frame_left translate <-31.25, 0, 0>}
	object {frame_right translate <31.25, 0, 0>}
	difference {
  		box { <-30,-20,-1>,<30,20,0.2> }
  		box { <-27,-18,-1.1>,<27,18,0.3> }
  		texture { canvasstexture }
	}

}



#declare pic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture
//    pigment { image_map { tga "./pics/bell_jar.tga" once } // interpolate?
    pigment { image_map { tga "./pics/innov_full.tga" once } // interpolate?
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }
  }
  scale <30.000000, 20.000000, 0.200000>
 }

 object{egs_frame}
}

#declare raspic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture
      // did you run flamepov to make fire.tga??
      pigment { image_map { tga "./pics/ras.tga" once }
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }

  }
  scale <30.000000, 20.000000, 0.200000>
}
object{egs_frame}
}



#declare musepic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture

      pigment { image_map { tga "./pics/musepic2.tga" once }
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }

  }
  scale <30.000000, 20.000000, 0.200000>
 }
object{egs_frame}
}


#declare prostapic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture
      pigment { image_map { tga "./pics/prostapic.tga" once }
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }

  }
  scale <30.000000, 20.000000, 0.200000>
 }
object{egs_frame}
}


#declare mirrorpic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {mirrortexture}
  scale <30.000000, 20.000000, 0.200000>
 }
object{egs_frame}
}


#declare lambdapic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture
      pigment { image_map { tga "./pics/lambdapic.tga" once }
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }

  }
  scale <30.000000, 20.000000, 0.200000>
}
object{egs_frame}

}

#declare risedpic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture
      pigment { image_map { tga "./pics/risedpic.tga" once }
      scale 1.9
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }

  }
  scale <30.000000, 20.000000, 0.200000>

}
object{egs_frame}

}


#declare fluprostpic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture
      pigment { image_map { tga "./pics/fluprostpic.tga" once }
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }

  }
  scale <30.000000, 20.000000, 0.200000>
}
object{egs_frame}

}
