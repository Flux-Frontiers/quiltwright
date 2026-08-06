//
// PDB2POV (DOS) atom input prepared by pdb2pov 02/24/97 11:42:08
// Author: Eric G. Suchanek, Ph.D.
// Mac port: Richard G. Rothwell, Ph.D.
//	Atoms:   27
//	Extent:	Xmin: -6.940 Xmax: 6.391,
//		Ymin: -4.792, Ymax: 4.518
//		Zmin: -4.921 Zmax: 3.946
//	Enclosing Sphere: 7.097

#version 3.0
global_settings {
   max_trace_level 10
   assumed_gamma 1.8 }


#include "atoms_vdw.inc"
#include "atoms2.inc"
#include "bonds.inc"

#declare ATM_SCL = 1.00

#declare risedronate3_obj = union {
object {Atom_C scale ATM_SCL * .8 translate <-0.942, 0.277, 0.650> }
object {Atom_C scale ATM_SCL * .8 translate <-1.662, -0.876, 0.979> }
object {Atom_C scale ATM_SCL * .8 translate <-3.000, -0.983, 0.598> }
object {Atom_C scale ATM_SCL * .8 translate <-3.607, 0.078, -0.078> }
object {Atom_N scale ATM_SCL translate <-2.915, 1.217, -0.328> }
object {Atom_C scale ATM_SCL * .8 translate <-1.600, 1.320, -0.010> }
object {Atom_C scale ATM_SCL * .8 translate <0.551, 0.388, 0.973> }
object {Atom_H scale ATM_SCL translate <-1.184, -1.695, 1.509> }
object {Atom_H scale ATM_SCL translate <-3.561, -1.886, 0.821> }
object {Atom_H scale ATM_SCL translate <-4.640, -0.012, -0.403> }
object {Atom_H scale ATM_SCL translate <-1.051, 2.218, -0.275> }
object {Atom_C scale ATM_SCL * .8 translate <1.362, 0.294, -0.339> }
object {Atom_P scale ATM_SCL translate <3.132, 0.097, 0.152> }
object {Atom_P scale ATM_SCL translate <0.808, -1.206, -1.280> }
object {Atom_O scale ATM_SCL translate <4.091, 0.319, -0.966> }
object {Atom_O scale ATM_SCL translate <-0.667, -1.217, -1.497> }
object {Atom_O scale ATM_SCL translate <1.445, -1.318, -2.621> }
object {Atom_O scale ATM_SCL translate <3.510, 1.174, 1.266> }
object {Atom_O scale ATM_SCL translate <3.302, -1.267, 0.730> }
object {Atom_O scale ATM_SCL translate <1.193, -2.492, -0.415> }
object {Atom_O scale ATM_SCL translate <1.167, 1.501, -1.098> }
object {Atom_H scale ATM_SCL translate <0.764, 1.344, 1.473> }
object {Atom_H scale ATM_SCL translate <0.859, -0.427, 1.646> }
object {Atom_H scale ATM_SCL translate <3.681, 1.982, 0.800> }
object {Atom_H scale ATM_SCL translate <2.112, -2.384, -0.173> }
object {Atom_H scale ATM_SCL translate <0.242, 1.547, -1.322> }
object {Atom_H scale ATM_SCL translate <-3.390, 2.009, -0.790> }
}

#declare risedronate3 = object {
	object { risedronate3_obj } }

