#include "picframe.inc"

// I made this with moray 1.3, and then made a few small mods by hand.
// Mar 94 - Michael Mittelstadt

#declare Edge1 = cylinder {
  <0,0,1>, <0,0,0>, 1
  texture {
    edgetex
  }
  scale <1.000000, 1.000000, 62.000000>
  rotate <-0.000000, -90.000000, -0.000000>
  translate <31.000000, 20.500000, 0.000000>
}

#declare Edgecut1 = box {
  <-1, -1, -1>, <1, 1, 1>
  texture {
    edgetex
  }
  scale <1.500000, 1.500000, 1.500000>
  rotate <-0.000000, -0.000000, -45.000000>
  translate <-31.266837, 19.634830, -0.162057>
}

#declare Edgecut2 = box {
  <-1, -1, -1>, <1, 1, 1>
  texture {
    edgetex
  }
  scale <1.500000, 1.500000, 1.500000>
  rotate <-0.000000, -0.000000, -45.000000>
  translate <31.270484, 19.635000, 0.000000>
}
#declare Edge2 = cylinder {
  <0,0,1>, <0,0,0>, 1
  texture {
    edgetex
  }
  scale <1.000000, 1.000000, 62.000000>
  rotate <-0.000000, -90.000000, -0.000000>
  translate <31.000000, 20.500000, 0.000000>
}

#declare Edgecut3 = box {
  <-1, -1, -1>, <1, 1, 1>
  texture {
    edgetex
  }
  scale <1.500000, 1.500000, 1.500000>
  rotate <-0.000000, -0.000000, -45.000000>
  translate <-31.266837, 19.634830, -0.162057>
}

#declare Edgecut4 = box {
  <-1, -1, -1>, <1, 1, 1>
  texture {
    edgetex
  }
  scale <1.500000, 1.500000, 1.500000>
  rotate <-0.000000, -0.000000, -45.000000>
  translate <31.270484, 19.635000, 0.000000>
}
#declare Edgecut5 = box {
  <-1, -1, -1>, <1, 1, 1>
  texture {
    edgetex
  }
  scale <1.500000, 1.500000, 1.500000>
  rotate <-0.000000, -0.000000, -45.000000>
  translate <-23.404276, 19.391658, -0.162057>
}

#declare Edgecut6 = box {
  <-1, -1, -1>, <1, 1, 1>
  texture {
    edgetex
  }
  scale <1.500000, 1.500000, 1.500000>
  rotate <-0.000000, -0.000000, -45.000000>
  translate <20.335492, 19.457608, -0.288853>
}
#declare Edge3 = cylinder {
  <0,0,1>, <0,0,0>, 1
  texture {
    edgetex
  }
  scale <1.000000, 1.000000, 42.000000>
  rotate <-0.000000, -90.000000, -0.000000>
  translate <19.408801, 20.418943, 0.000000>
}


#declare Edge4 = cylinder {
  <0,0,1>, <0,0,0>, 1
  texture {
    edgetex
  }
  scale <1.000000, 1.000000, 42.000000>
  rotate <-0.000000, -90.000000, -0.000000>
  translate <19.408801, 20.418943, 0.000000>
}

#declare Edgecut7 = box {
  <-1, -1, -1>, <1, 1, 1>
  texture {
    edgetex
  }
  scale <1.500000, 1.500000, 1.500000>
  rotate <-0.000000, -0.000000, -45.000000>
  translate <-23.404276, 19.391658, -0.162057>
}

#declare Edgecut8 = box {
  <-1, -1, -1>, <1, 1, 1>
  texture {
    edgetex
  }
  scale <1.500000, 1.500000, 1.500000>
  rotate <-0.000000, -0.000000, -45.000000>
  translate <20.335492, 19.457608, -0.288853>
}


#declare pic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture
//    pigment { image_map { tga "bell_jar.tga" once } // interpolate?
    pigment { image_map { tga "innov_full.tga" once } // interpolate?
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }
  }
  scale <30.000000, 20.000000, 0.200000>
}

difference {
box { <-30,-20,-1>,<30,20,0.2> }
box { <-27,-18,-1.1>,<27,18,0.3> }
texture { canvasstexture }}

difference {
  object { Edge1 }
  object { Edgecut1 }
  object { Edgecut2 }
}


difference {
  object { Edge2 }
  object { Edgecut3 }
  object { Edgecut4 }
  rotate <-180.000000, -0.000000, -0.000000>
}

difference {
  object { Edge3 }
  object { Edgecut5 }
  object { Edgecut6 }
  rotate <-180.000000, -0.000000, -90.000000>
  translate <-9.700090, -1.459032, -0.288853>
}

difference {
  object { Edge4 }
  object { Edgecut7 }
  object { Edgecut8 }
  rotate <-0.000000, -0.000000, -90.000000>
  translate <9.612944, -1.459032, -0.288853>
}

}

#declare pic2 =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture
      // did you run flamepov to make fire.tga??
      pigment { image_map { tga "ras.tga" once }
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }

  }
  scale <30.000000, 20.000000, 0.200000>
}

difference {
box { <-30,-20,-1>,<30,20,0.2> }
box { <-27,-18,-1.1>,<27,18,0.3> }
texture { canvasstexture }}

difference {
  object { Edge1 }
  object { Edgecut1 }
  object { Edgecut2 }
}


difference {
  object { Edge2 }
  object { Edgecut3 }
  object { Edgecut4 }
  rotate <-180.000000, -0.000000, -0.000000>
}

difference {
  object { Edge3 }
  object { Edgecut5 }
  object { Edgecut6 }
  rotate <-180.000000, -0.000000, -90.000000>
  translate <-9.700090, -1.459032, -0.288853>
}

difference {
  object { Edge4 }
  object { Edgecut7 }
  object { Edgecut8 }
  rotate <-0.000000, -0.000000, -90.000000>
  translate <9.612944, -1.459032, -0.288853>
}

}



#declare musepic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture

      pigment { image_map { tga "musepic2.tga" once }
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }

  }
  scale <30.000000, 20.000000, 0.200000>
}

difference {
box { <-30,-20,-1>,<30,20,0.2> }
box { <-27,-18,-1.1>,<27,18,0.3> }
texture { canvasstexture }}

difference {
  object { Edge1 }
  object { Edgecut1 }
  object { Edgecut2 }
}


difference {
  object { Edge2 }
  object { Edgecut3 }
  object { Edgecut4 }
  rotate <-180.000000, -0.000000, -0.000000>
}

difference {
  object { Edge3 }
  object { Edgecut5 }
  object { Edgecut6 }
  rotate <-180.000000, -0.000000, -90.000000>
  translate <-9.700090, -1.459032, -0.288853>
}

difference {
  object { Edge4 }
  object { Edgecut7 }
  object { Edgecut8 }
  rotate <-0.000000, -0.000000, -90.000000>
  translate <9.612944, -1.459032, -0.288853>
}

}


#declare prostapic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture
      pigment { image_map { tga "prostapic.tga" once }
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }

  }
  scale <30.000000, 20.000000, 0.200000>
}

difference {
box { <-30,-20,-1>,<30,20,0.2> }
box { <-27,-18,-1.1>,<27,18,0.3> }
texture { canvasstexture }}

difference {
  object { Edge1 }
  object { Edgecut1 }
  object { Edgecut2 }
}


difference {
  object { Edge2 }
  object { Edgecut3 }
  object { Edgecut4 }
  rotate <-180.000000, -0.000000, -0.000000>
}

difference {
  object { Edge3 }
  object { Edgecut5 }
  object { Edgecut6 }
  rotate <-180.000000, -0.000000, -90.000000>
  translate <-9.700090, -1.459032, -0.288853>
}

difference {
  object { Edge4 }
  object { Edgecut7 }
  object { Edgecut8 }
  rotate <-0.000000, -0.000000, -90.000000>
  translate <9.612944, -1.459032, -0.288853>
}

}

#declare mirrorpic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {mirrortexture}
  scale <30.000000, 20.000000, 0.200000>
}
difference {
  object { Edge1 }
  object { Edgecut1 }
  object { Edgecut2 }
}


difference {
  object { Edge2 }
  object { Edgecut3 }
  object { Edgecut4 }
  rotate <-180.000000, -0.000000, -0.000000>
}

difference {
  object { Edge3 }
  object { Edgecut5 }
  object { Edgecut6 }
  rotate <-180.000000, -0.000000, -90.000000>
  translate <-9.700090, -1.459032, -0.288853>
}

difference {
  object { Edge4 }
  object { Edgecut7 }
  object { Edgecut8 }
  rotate <-0.000000, -0.000000, -90.000000>
  translate <9.612944, -1.459032, 0.288853>
}

}


#declare lambdapic =
union {
box {   // backpanel
  <-1, -1, -1>, <1, 1, 1>
  texture {
      canvasstexture
      pigment { image_map { tga "lambdapic.tga" once }
      scale 1.8
      translate <-0.9,-0.9,-0.9> }
    normal { wrinkles 0.1 omega 0.7 }

  }
  scale <30.000000, 20.000000, 0.200000>
}

difference {
box { <-30,-20,-1>,<30,20,0.2> }
box { <-27,-18,-1.1>,<27,18,0.3> }
texture { canvasstexture }}

difference {
  object { Edge1 }
  object { Edgecut1 }
  object { Edgecut2 }
}


difference {
  object { Edge2 }
  object { Edgecut3 }
  object { Edgecut4 }
  rotate <-180.000000, -0.000000, -0.000000>
}

difference {
  object { Edge3 }
  object { Edgecut5 }
  object { Edgecut6 }
  rotate <-180.000000, -0.000000, -90.000000>
  translate <-9.700090, -1.459032, -0.288853>
}

difference {
  object { Edge4 }
  object { Edgecut7 }
  object { Edgecut8 }
  rotate <-0.000000, -0.000000, -90.000000>
  translate <9.612944, -1.459032, -0.288853>
}

}


