//  Description: display case - small.
//
//  Mar 1994 - Michael Mittelstadt
//

#include "display.inc"

#declare Bound001 = box {
   <-1.0, -1.0, -1.0>, <1.0, 1.0, 1.0>
  scale <7.960000, 0.460000, 7.960000>
  translate <7.500000, 0.000000, 7.500000>
}

#declare edge = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <0.250000, 0.250000, 15.000000>
}

#declare edge1 = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <0.250000, 0.250000, 15.000000>
  translate <15.000000, 0.000000, 0.000000>
}

#declare edge2 = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <0.250000, 0.250000, 15.000000>
  rotate <-0.000000, -90.000000, -0.000000>
  translate <15.000000, 0.000000, 0.000000>
}

#declare edge3 = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <0.250000, 0.250000, 15.000000>
  rotate <-0.000000, -90.000000, -0.000000>
  translate <15.000000, 0.000000, 15.000000>
}

#declare corner = object {
  sphere {<0,0,0>,1}
  scale <0.250000, 0.250000, 0.250000>
}

#declare corner1 = object {
  sphere {<0,0,0>,1}
  scale <0.250000, 0.250000, 0.250000>
  translate <0.000000, 0.000000, 15.000000>
}

#declare corner2 = object {
  sphere {<0,0,0>,1}
  scale <0.250000, 0.250000, 0.250000>
  translate <15.000000, 0.000000, 0.000000>
}

#declare corner3 = object {
  sphere {<0,0,0>,1}
  scale <0.250000, 0.250000, 0.250000>
  translate <15.000000, 0.000000, 15.000000>
}


#declare Bound002 = box {
   <-1.0, -1.0, -1.0>, <1.0, 1.0, 1.0>
  scale <14.006667, 11.506667, 14.006667>
  translate <7.500000, 11.000000, 7.500000>
}

#declare baseblock = box {
  <-1, -1, -1>, <1, 1, 1>
  scale <7.500000, 10.000000, 7.500000>
  translate <7.500000, 10.000000, 7.500000>
}

#declare basecut = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <6.000000, 10.000000, 16.000000>
  translate <0.000000, 12.000000, -0.500000>
}

#declare basecut1 = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <6.000000, 10.000000, 16.000000>
  rotate <-0.000000, -90.000000, -0.000000>
  translate <15.500000, 12.000000, 0.000000>
}

#declare basecut2 = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <6.000000, 10.000000, 16.000000>
  translate <15.000000, 12.000000, -0.500000>
}

#declare basecut3 = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <6.000000, 10.000000, 16.000000>
  rotate <-0.000000, -90.000000, -0.000000>
  translate <15.500000, 12.000000, 15.000000>
}



#declare edge4 = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <0.250000, 0.250000, 15.000000>
}

#declare edge5 = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <0.250000, 0.250000, 15.000000>
  translate <15.000000, 0.000000, 0.000000>
}

#declare edge6 = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <0.250000, 0.250000, 15.000000>
  rotate <-0.000000, -90.000000, -0.000000>
  translate <15.000000, 0.000000, 0.000000>
}

#declare edge7 = cylinder {
  <0,0,1>, <0,0,0>, 1
  scale <0.250000, 0.250000, 15.000000>
  rotate <0.000000, -90.000000, 0.000000>
  translate <15.000000, 0.000000, 15.000000>
}

#declare corner4 = object {
  sphere {<0,0,0>,1}
  scale <0.250000, 0.250000, 0.250000>
}

#declare corner5 = object {
  sphere {<0,0,0>,1}
  scale <0.250000, 0.250000, 0.250000>
  translate <0.000000, 0.000000, 15.000000>
}

#declare corner6 = object {
  sphere {<0,0,0>,1}
  scale <0.250000, 0.250000, 0.250000>
  translate <15.000000, 0.000000, 0.000000>
}

#declare corner7 = object {
  sphere {<0,0,0>,1}
  scale <0.250000, 0.250000, 0.250000>
  translate <15.000000, 0.000000, 15.000000>
}

//-------------------------------------------//


#declare old_small_case_base=
union {

 difference {
  object { baseblock }
  object { basecut }
  object { basecut1 }
  object { basecut2 }
  object { basecut3 }
  texture {
    Basetex
  }
 }
//  bounded_by { Bound002 }
 box {   // shelfbox
  <-1, -1, -1>, <1, 1, 1>
  texture {
    shelftex
  }
  scale <8.500000, 1.200000, 8.500000>
  translate <7.500000, 22.500000, 7.500000>
 }
}

#declare mytop = object {
  sor
  {
    5, // # of points
    <0.000000, 0.000000> // list of <u,v> points
    <0.5, 0.000000>
    <0.9, 0.5>
    <0.5, 0.9>
    <0.0, .9>
    
    texture {shelftex}
  }
  scale <10, 2.5, 10>
  translate <7.500000, 20, 7.500000>
}
  
#declare small_case_base=
union {

 difference {
  object { baseblock }
  object { basecut }
  object { basecut1 }
  object { basecut2 }
  object { basecut3 }
  texture {
    Basetex
  }
 } // diff
 object { mytop }
 
}

  
#declare small_case_base2=
union {

 difference {
  object { baseblock }
  object { basecut }
  object { basecut1 }
  object { basecut2 }
  object { basecut3 }
  texture {
    Basetex
   }
  }
 
//  bounded_by { Bound002 }
 box {   // shelfbox
  <-1, -1, -1>, <1, 1, 1>
  texture {
    shelftex
  }
  scale <8.500000, 1.200000, 8.500000>
  translate <7.500000, 22.500000, 7.500000>
 }
}






