// This file was created by PovChem version 1.00

#declare Camera_Position = < 88.1638, 0.00706596, 0.0127916 >

camera{
  location < 0, 0, 0 >
  direction < 0, 0, 2 >
  look_at < 0, 0, 88.158 >
  sky < 0, 1, 0 >
  up < 0, 1.333, 0 >
  right < 1, 0, 0 >
  rotate < 0, 0, -90 >
  rotate < 0, -90, 0 >
  translate Camera_Position
}

light_source { < 88.164, -35.256, 57.315 > color rgb < 1, 1, 1 > }
light_source { Camera_Position color rgb < 0.5, 0.5, 0.5 > }

background { color rgb < 0, 0, 0 > }

#declare Plastic =
  finish {
    ambient 0.2
    diffuse 0.7
    reflection 0.0
    brilliance 1.0
    phong 0.3
    phong_size 50
    specular 0.0
  }

// Unfortunately, if the atoms involved in hydrogen-bonding are
// resized, the hydrogen bonds will not be spaced properly. You
// will have to re-run PovChem and change the sizes there.

#declare Proportionality_Constant = 0.2
#declare Hydrogen_Radius = 1.2*Proportionality_Constant
#declare Carbon_Radius = 1.7*Proportionality_Constant
#declare Nitrogen_Radius = 1.55*Proportionality_Constant
#declare Oxygen_Radius = 1.52*Proportionality_Constant
#declare Phosphorus_Radius = 1.8*Proportionality_Constant

#declare Atom_Hydrogen_Color = color rgb <0.8, 0.8, 0.8>
#declare Atom_Carbon_Color = color rgb <0.3, 0.3, 0.3>
#declare Atom_Nitrogen_Color = color rgb <0.2, 0.2, 0.8>
#declare Atom_Oxygen_Color = color rgb <0.8, 0.2, 0.2>
#declare Atom_Phosphorus_Color = color rgb <0.1, 0.7, 0.3>

#declare Atom_Hydrogen =
  sphere {
   <0,0,0>, Hydrogen_Radius
    texture {
      pigment { color Atom_Hydrogen_Color }
      finish { Plastic }
    }
  }
#declare Atom_Carbon =
  sphere {
   <0,0,0>, Carbon_Radius
    texture {
      pigment { color Atom_Carbon_Color }
      finish { Plastic }
    }
  }
#declare Atom_Nitrogen =
  sphere {
   <0,0,0>, Nitrogen_Radius
    texture {
      pigment { color Atom_Nitrogen_Color }
      finish { Plastic }
    }
  }
#declare Atom_Oxygen =
  sphere {
   <0,0,0>, Oxygen_Radius
    texture {
      pigment { color Atom_Oxygen_Color }
      finish { Plastic }
    }
  }
#declare Atom_Phosphorus =
  sphere {
   <0,0,0>, Phosphorus_Radius
    texture {
      pigment { color Atom_Phosphorus_Color }
      finish { Plastic }
    }
  }

#declare H_Bond_Radius = 0.1
#declare H_Bond_Color = color rgb <1, 1, 0>
#declare H_Bond =
  cylinder {
    <0,0,0>, <1,0,0>, H_Bond_Radius
    texture {
      pigment { H_Bond_Color }
      finish { Plastic }
    }
  }

#declare All_Bond_Radius = 0.1

#declare Bond =
  cylinder {
    <0,0,0>, <1,0,0>, All_Bond_Radius
    finish { Plastic }
  }


#include "bna7_full.inc"
