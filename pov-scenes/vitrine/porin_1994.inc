//
// The 1994 porin mesh, brought onto the pdb2pov -o contract.
//
// pov-scenes/porin/3porin.inc is 39,390 lines of smooth_triangle produced by
// WCVT2POV V2.7 from an exporter nobody has any more, in an arbitrary scaled
// frame -- x spans -222 to 367 for a protein about 60 A across.
// It declares no radius and sits nowhere near the origin, so it cannot be
// mounted in a scene that expects either.
//
// This wrapper measures its 23505 vertices, centres them, and declares
// the radius, which is all the contract asks for.  The geometry is the
// original's, untouched.
//
//	Triangles: 7835
//	Enclosing Sphere: 511.500
//

#declare porin_1994_pov_version = version;
#version 3.7;

#declare porin_1994_enclosing_radius = 511.500;

#include "3porin.inc"

#declare porin_1994_obj = union {
  object { porin }
  translate <-72.4721, 21.4738, 63.1116>
}

#declare porin_1994 = object { porin_1994_obj }

#version porin_1994_pov_version;
