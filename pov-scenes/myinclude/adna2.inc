//
// PDB2POV (DOS) atom input prepared by pdb2pov 03/11/97 19:59:55
// Author: Eric G. Suchanek, Ph.D.
// Mac port: Richard G. Rothwell, Ph.D.
//	Atoms:  502
//	Extent:	Xmin: -13.796 Xmax: 11.885,
//		Ymin: -13.661, Ymax: 14.576
//		Zmin: -16.427 Zmax: 16.668
//	Enclosing Sphere: 20.377
//

#declare ADNA_Full_Inc_Temp = version
#version 3.0
#include "atoms_vdw.inc"
#include "atoms2.inc"
#include "bell_jar.inc"

#declare ATM_SCL = 1.00

#declare adna2_obj = union {
object {Atom_O scale ATM_SCL * .8 translate <-7.690, 1.620, 11.979> }
object {Atom_C scale ATM_SCL * .8 translate <-7.235, 2.864, 12.550> }
object {Atom_C scale ATM_SCL * .8 translate <-5.986, 2.640, 13.348> }
object {Atom_O scale ATM_SCL translate <-5.530, 3.931, 13.809> }
object {Atom_C scale ATM_SCL * .8 translate <-4.794, 1.957, 12.693> }
object {Atom_O scale ATM_SCL translate <-4.771, 0.537, 12.850> }
object {Atom_C scale ATM_SCL * .8 translate <-3.632, 2.613, 13.454> }
object {Atom_C scale ATM_SCL * .8 translate <-4.130, 4.049, 13.509> }
object {Atom_N scale ATM_SCL translate <-3.897, 4.791, 12.258> }
object {Atom_C scale ATM_SCL * .8 translate <-4.778, 5.250, 11.312> }
object {Atom_N scale ATM_SCL translate <-4.221, 5.894, 10.336> }
object {Atom_C scale ATM_SCL * .8 translate <-2.872, 5.859, 10.636> }
object {Atom_C scale ATM_SCL * .8 translate <-1.771, 6.400, 9.935> }
object {Atom_O scale ATM_SCL translate <-1.789, 7.028, 8.870> }
object {Atom_N scale ATM_SCL translate <-0.570, 6.149, 10.585> }
object {Atom_C scale ATM_SCL * .8 translate <-0.441, 5.454, 11.764> }
object {Atom_N scale ATM_SCL translate <0.798, 5.309, 12.254> }
object {Atom_N scale ATM_SCL translate <-1.463, 4.940, 12.432> }
object {Atom_C scale ATM_SCL translate <-2.648, 5.187, 11.810> }
object {Atom_H scale ATM_SCL translate <-8.523, 1.781, 11.449> }
object {Atom_H scale ATM_SCL translate <-7.947, 3.233, 13.147> }
object {Atom_H scale ATM_SCL translate <-7.045, 3.515, 11.815> }
object {Atom_H scale ATM_SCL translate <-6.276, 1.991, 14.051> }
object {Atom_H scale ATM_SCL translate <-4.784, 2.070, 11.699> }
object {Atom_H scale ATM_SCL translate <-2.770, 2.538, 12.952> }
object {Atom_H scale ATM_SCL translate <-3.521, 2.224, 14.368> }
object {Atom_H scale ATM_SCL translate <-3.634, 4.580, 14.196> }
object {Atom_H scale ATM_SCL translate <-5.765, 5.100, 11.371> }
object {Atom_H scale ATM_SCL translate <0.265, 6.501, 10.163> }
object {Atom_H scale ATM_SCL translate <1.579, 5.692, 11.760> }
object {Atom_H scale ATM_SCL translate <0.942, 4.818, 13.113> }
object {Atom_P scale ATM_SCL translate <-4.117, -0.472, 11.806> }
object {Atom_O scale ATM_SCL translate <-4.663, -0.170, 10.458> }
object {Atom_O scale ATM_SCL translate <-4.325, -1.862, 12.275> }
object {Atom_O scale ATM_SCL translate <-2.571, -0.111, 11.823> }
object {Atom_C scale ATM_SCL * .8 translate <-1.585, -0.664, 12.689> }
object {Atom_C scale ATM_SCL * .8 translate <-0.235, -0.060, 12.381> }
object {Atom_O scale ATM_SCL translate <-0.357, 1.361, 12.241> }
object {Atom_C scale ATM_SCL * .8 translate <0.425, -0.496, 11.075> }
object {Atom_O scale ATM_SCL translate <1.095, -1.752, 11.189> }
object {Atom_C scale ATM_SCL * .8 translate <1.437, 0.623, 10.889> }
object {Atom_C scale ATM_SCL * .8 translate <0.592, 1.812, 11.278> }
object {Atom_N scale ATM_SCL translate <-0.015, 2.495, 10.133> }
object {Atom_C scale ATM_SCL * .8 translate <-1.323, 2.577, 9.728> }
object {Atom_N scale ATM_SCL translate <-1.488, 3.327, 8.676> }
object {Atom_C scale ATM_SCL * .8 translate <-0.221, 3.778, 8.354> }
object {Atom_C scale ATM_SCL * .8 translate <0.214, 4.618, 7.307> }
object {Atom_O scale ATM_SCL translate <-0.450, 5.156, 6.411> }
object {Atom_N scale ATM_SCL translate <1.601, 4.791, 7.328> }
object {Atom_C scale ATM_SCL * .8 translate <2.441, 4.245, 8.261> }
object {Atom_N scale ATM_SCL translate <3.744, 4.532, 8.160> }
object {Atom_N scale ATM_SCL translate <2.042, 3.476, 9.254> }
object {Atom_C scale ATM_SCL translate <0.701, 3.272, 9.237> }
object {Atom_H scale ATM_SCL translate <-1.544, -1.654, 12.555> }
object {Atom_H scale ATM_SCL translate <-1.828, -0.465, 13.638> }
object {Atom_H scale ATM_SCL translate <0.325, -0.374, 13.148> }
object {Atom_H scale ATM_SCL translate <-0.223, -0.627, 10.325> }
object {Atom_H scale ATM_SCL translate <1.751, 0.685, 9.941> }
object {Atom_H scale ATM_SCL translate <2.225, 0.514, 11.495> }
object {Atom_H scale ATM_SCL translate <1.170, 2.521, 11.682> }
object {Atom_H scale ATM_SCL translate <-2.074, 2.108, 10.193> }
object {Atom_H scale ATM_SCL translate <2.009, 5.354, 6.610> }
object {Atom_H scale ATM_SCL translate <4.072, 5.113, 7.415> }
object {Atom_H scale ATM_SCL translate <4.390, 4.165, 8.829> }
object {Atom_P scale ATM_SCL translate <1.331, -2.670, 9.918> }
object {Atom_O scale ATM_SCL translate <0.171, -2.576, 8.997> }
object {Atom_O scale ATM_SCL translate <1.662, -4.036, 10.387> }
object {Atom_O scale ATM_SCL translate <2.598, -1.983, 9.229> }
object {Atom_C scale ATM_SCL * .8 translate <3.907, -2.054, 9.804> }
object {Atom_C scale ATM_SCL * .8 translate <4.852, -1.281, 8.921> }
object {Atom_O scale ATM_SCL translate <4.388, 0.089, 8.874> }
object {Atom_C scale ATM_SCL * .8 translate <4.936, -1.677, 7.454> }
object {Atom_O scale ATM_SCL translate <5.727, -2.858, 7.256> }
object {Atom_C scale ATM_SCL * .8 translate <5.587, -0.417, 6.905> }
object {Atom_C scale ATM_SCL * .8 translate <4.748, 0.642, 7.611> }
object {Atom_N scale ATM_SCL translate <3.583, 1.082, 6.821> }
object {Atom_C scale ATM_SCL * .8 translate <2.249, 0.827, 6.994> }
object {Atom_N scale ATM_SCL translate <1.492, 1.361, 6.086> }
object {Atom_C scale ATM_SCL * .8 translate <2.373, 2.024, 5.245> }
object {Atom_C scale ATM_SCL * .8 translate <2.129, 2.770, 4.074> }
object {Atom_O scale ATM_SCL translate <1.048, 3.041, 3.529> }
object {Atom_N scale ATM_SCL translate <3.309, 3.260, 3.521> }
object {Atom_C scale ATM_SCL * .8 translate <4.567, 3.029, 4.024> }
object {Atom_N scale ATM_SCL translate <5.600, 3.563, 3.356> }
object {Atom_N scale ATM_SCL translate <4.807, 2.307, 5.101> }
object {Atom_C scale ATM_SCL translate <3.663, 1.847, 5.672> }
object {Atom_H scale ATM_SCL translate <4.201, -3.008, 9.860> }
object {Atom_H scale ATM_SCL translate <3.896, -1.654, 10.720> }
object {Atom_H scale ATM_SCL translate <5.747, -1.455, 9.332> }
object {Atom_H scale ATM_SCL translate <4.071, -1.926, 7.019> }
object {Atom_H scale ATM_SCL translate <5.500, -0.357, 5.911> }
object {Atom_H scale ATM_SCL translate <6.552, -0.357, 7.160> }
object {Atom_H scale ATM_SCL translate <5.276, 1.483, 7.732> }
object {Atom_H scale ATM_SCL translate <1.891, 0.280, 7.751> }
object {Atom_H scale ATM_SCL translate <3.236, 3.822, 2.697> }
object {Atom_H scale ATM_SCL translate <5.435, 4.113, 2.537> }
object {Atom_H scale ATM_SCL translate <6.535, 3.411, 3.677> }
object {Atom_P scale ATM_SCL translate <5.652, -3.694, 5.879> }
object {Atom_O scale ATM_SCL translate <4.250, -4.075, 5.608> }
object {Atom_O scale ATM_SCL translate <6.627, -4.801, 5.963> }
object {Atom_O scale ATM_SCL translate <6.128, -2.580, 4.848> }
object {Atom_C scale ATM_SCL * .8 translate <7.538, -2.321, 4.662> }
object {Atom_C scale ATM_SCL * .8 translate <7.719, -1.528, 3.403> }
object {Atom_O scale ATM_SCL translate <6.996, -0.307, 3.483> }
object {Atom_C scale ATM_SCL * .8 translate <7.186, -2.176, 2.114> }
object {Atom_O scale ATM_SCL translate <8.183, -3.102, 1.721> }
object {Atom_C scale ATM_SCL * .8 translate <7.123, -0.943, 1.214> }
object {Atom_C scale ATM_SCL * .8 translate <6.563, 0.097, 2.169> }
object {Atom_N scale ATM_SCL translate <5.088, 0.117, 2.131> }
object {Atom_C scale ATM_SCL * .8 translate <4.163, -0.496, 2.942> }
object {Atom_N scale ATM_SCL translate <2.935, -0.197, 2.680> }
object {Atom_C scale ATM_SCL * .8 translate <3.035, 0.619, 1.561> }
object {Atom_C scale ATM_SCL * .8 translate <2.013, 1.188, 0.779> }
object {Atom_O scale ATM_SCL translate <0.794, 1.078, 0.952> }
object {Atom_N scale ATM_SCL translate <2.541, 1.961, -0.252> }
object {Atom_C scale ATM_SCL * .8 translate <3.867, 2.130, -0.518> }
object {Atom_N scale ATM_SCL translate <4.166, 2.876, -1.583> }
object {Atom_N scale ATM_SCL translate <4.827, 1.612, 0.213> }
object {Atom_C scale ATM_SCL translate <4.342, 0.843, 1.218> }
object {Atom_H scale ATM_SCL translate <8.032, -3.187, 4.588> }
object {Atom_H scale ATM_SCL translate <7.890, -1.801, 5.440> }
object {Atom_H scale ATM_SCL translate <8.713, -1.435, 3.344> }
object {Atom_H scale ATM_SCL translate <6.317, -2.671, 2.139> }
object {Atom_H scale ATM_SCL translate <6.513, -1.090, 0.435> }
object {Atom_H scale ATM_SCL translate <8.031, -0.685, 0.884> }
object {Atom_H scale ATM_SCL translate <6.881, 1.012, 1.922> }
object {Atom_H scale ATM_SCL translate <4.421, -1.124, 3.677> }
object {Atom_H scale ATM_SCL translate <1.891, 2.433, -0.848> }
object {Atom_H scale ATM_SCL translate <3.434, 3.270, -2.139> }
object {Atom_H scale ATM_SCL translate <5.122, 3.041, -1.825> }
object {Atom_P scale ATM_SCL translate <8.025, -4.350, 0.783> }
object {Atom_O scale ATM_SCL translate <6.844, -5.100, 1.210> }
object {Atom_O scale ATM_SCL translate <9.334, -5.088, 0.771> }
object {Atom_O scale ATM_SCL translate <7.857, -3.659, -0.645> }
object {Atom_C scale ATM_SCL * .8 translate <8.976, -3.110, -1.372> }
object {Atom_C scale ATM_SCL * .8 translate <8.510, -2.380, -2.593> }
object {Atom_O scale ATM_SCL translate <7.814, -1.183, -2.271> }
object {Atom_C scale ATM_SCL * .8 translate <7.569, -3.145, -3.522> }
object {Atom_O scale ATM_SCL translate <8.351, -4.012, -4.342> }
object {Atom_C scale ATM_SCL * .8 translate <6.889, -2.007, -4.249> }
object {Atom_C scale ATM_SCL * .8 translate <6.647, -1.045, -3.104> }
object {Atom_N scale ATM_SCL translate <5.360, -1.241, -2.445> }
object {Atom_C scale ATM_SCL * .8 translate <4.236, -0.590, -2.986> }
object {Atom_O scale ATM_SCL translate <4.388, 0.105, -4.000> }
object {Atom_N scale ATM_SCL translate <3.030, -0.763, -2.407> }
object {Atom_C scale ATM_SCL * .8 translate <2.917, -1.532, -1.321> }
object {Atom_N scale ATM_SCL translate <1.718, -1.685, -0.734> }
object {Atom_C scale ATM_SCL * .8 translate <4.037, -2.207, -0.767> }
object {Atom_C scale ATM_SCL * .8 translate <5.210, -2.034, -1.342> }
object {Atom_H scale ATM_SCL translate <9.585, -3.854, -1.647> }
object {Atom_H scale ATM_SCL translate <9.472, -2.475, -0.780> }
object {Atom_H scale ATM_SCL translate <9.376, -2.220, -3.066> }
object {Atom_H scale ATM_SCL translate <6.896, -3.753, -3.101> }
object {Atom_H scale ATM_SCL translate <6.031, -2.300, -4.671> }
object {Atom_H scale ATM_SCL translate <7.484, -1.607, -4.946> }
object {Atom_H scale ATM_SCL translate <6.551, -0.096, -3.405> }
object {Atom_H scale ATM_SCL translate <1.629, -2.260, 0.079> }
object {Atom_H scale ATM_SCL translate <0.914, -1.224, -1.110> }
object {Atom_H scale ATM_SCL translate <3.938, -2.796, 0.035> }
object {Atom_H scale ATM_SCL translate <6.012, -2.495, -0.961> }
object {Atom_P scale ATM_SCL translate <7.710, -5.288, -5.026> }
object {Atom_O scale ATM_SCL translate <6.917, -6.120, -4.109> }
object {Atom_O scale ATM_SCL translate <8.795, -5.998, -5.761> }
object {Atom_O scale ATM_SCL translate <6.692, -4.601, -6.032> }
object {Atom_C scale ATM_SCL * .8 translate <7.152, -3.946, -7.232> }
object {Atom_C scale ATM_SCL * .8 translate <5.897, -3.459, -7.929> }
object {Atom_O scale ATM_SCL translate <5.185, -2.572, -7.054> }
object {Atom_C scale ATM_SCL * .8 translate <4.880, -4.538, -8.317> }
object {Atom_O scale ATM_SCL translate <5.308, -5.209, -9.509> }
object {Atom_C scale ATM_SCL * .8 translate <3.620, -3.706, -8.402> }
object {Atom_C scale ATM_SCL * .8 translate <3.780, -2.760, -7.223> }
object {Atom_N scale ATM_SCL translate <3.019, -3.082, -6.023> }
object {Atom_C scale ATM_SCL * .8 translate <1.666, -2.717, -5.985> }
object {Atom_O scale ATM_SCL translate <1.172, -2.176, -6.978> }
object {Atom_N scale ATM_SCL translate <0.925, -3.004, -4.887> }
object {Atom_C scale ATM_SCL * .8 translate <1.478, -3.647, -3.860> }
object {Atom_N scale ATM_SCL translate <0.712, -3.906, -2.787> }
object {Atom_C scale ATM_SCL * .8 translate <2.845, -4.028, -3.877> }
object {Atom_C scale ATM_SCL * .8 translate <3.547, -3.769, -4.963> }
object {Atom_H scale ATM_SCL translate <7.648, -4.590, -7.814> }
object {Atom_H scale ATM_SCL translate <7.747, -3.175, -7.004> }
object {Atom_H scale ATM_SCL translate <6.239, -3.040, -8.770> }
object {Atom_H scale ATM_SCL translate <4.753, -5.310, -7.694> }
object {Atom_H scale ATM_SCL translate <2.803, -4.274, -8.303> }
object {Atom_H scale ATM_SCL translate <3.575, -3.204, -9.266> }
object {Atom_H scale ATM_SCL translate <3.341, -1.885, -7.428> }
object {Atom_H scale ATM_SCL translate <1.099, -4.387, -2.001> }
object {Atom_H scale ATM_SCL translate <-0.245, -3.618, -2.775> }
object {Atom_H scale ATM_SCL translate <3.263, -4.479, -3.089> }
object {Atom_H scale ATM_SCL translate <4.495, -4.084, -5.014> }
object {Atom_P scale ATM_SCL translate <4.596, -6.552, -9.982> }
object {Atom_O scale ATM_SCL translate <4.569, -7.517, -8.858> }
object {Atom_O scale ATM_SCL translate <5.210, -7.034, -11.233> }
object {Atom_O scale ATM_SCL translate <3.107, -6.093, -10.265> }
object {Atom_C scale ATM_SCL * .8 translate <2.557, -5.461, -11.410> }
object {Atom_C scale ATM_SCL * .8 translate <1.066, -5.311, -11.182> }
object {Atom_O scale ATM_SCL translate <0.801, -4.672, -9.931> }
object {Atom_C scale ATM_SCL * .8 translate <0.316, -6.650, -11.038> }
object {Atom_O scale ATM_SCL translate <0.080, -7.160, -12.352> }
object {Atom_C scale ATM_SCL * .8 translate <-0.967, -6.155, -10.379> }
object {Atom_C scale ATM_SCL * .8 translate <-0.407, -5.194, -9.369> }
object {Atom_N scale ATM_SCL translate <-0.375, -5.618, -7.979> }
object {Atom_C scale ATM_SCL * .8 translate <-1.542, -5.465, -7.215> }
object {Atom_O scale ATM_SCL translate <-2.544, -5.017, -7.764> }
object {Atom_N scale ATM_SCL translate <-1.524, -5.794, -5.897> }
object {Atom_C scale ATM_SCL * .8 translate <-0.418, -6.281, -5.343> }
object {Atom_N scale ATM_SCL translate <-0.461, -6.615, -4.050> }
object {Atom_C scale ATM_SCL * .8 translate <0.783, -6.414, -6.087> }
object {Atom_C scale ATM_SCL * .8 translate <0.762, -6.089, -7.371> }
object {Atom_H scale ATM_SCL translate <2.723, -6.022, -12.221> }
object {Atom_H scale ATM_SCL translate <2.974, -4.561, -11.536> }
object {Atom_H scale ATM_SCL translate <0.760, -4.800, -11.985> }
object {Atom_H scale ATM_SCL translate <0.771, -7.382, -10.530> }
object {Atom_H scale ATM_SCL translate <-1.467, -6.901, -9.940> }
object {Atom_H scale ATM_SCL translate <-1.564, -5.694, -11.035> }
object {Atom_H scale ATM_SCL translate <-1.057, -4.448, -9.226> }
object {Atom_H scale ATM_SCL translate <0.353, -6.984, -3.602> }
object {Atom_H scale ATM_SCL translate <-1.307, -6.496, -3.531> }
object {Atom_H scale ATM_SCL translate <1.622, -6.744, -5.654> }
object {Atom_H scale ATM_SCL translate <1.597, -6.189, -7.912> }
object {Atom_P scale ATM_SCL translate <-0.294, -8.663, -12.648> }
object {Atom_O scale ATM_SCL translate <0.676, -9.566, -12.023> }
object {Atom_O scale ATM_SCL translate <-0.427, -8.761, -14.127> }
object {Atom_O scale ATM_SCL translate <-1.744, -8.828, -12.010> }
object {Atom_C scale ATM_SCL * .8 translate <-2.868, -8.106, -12.538> }
object {Atom_C scale ATM_SCL * .8 translate <-4.107, -8.440, -11.782> }
object {Atom_O scale ATM_SCL translate <-4.130, -7.741, -10.540> }
object {Atom_C scale ATM_SCL * .8 translate <-4.495, -9.872, -11.507> }
object {Atom_O scale ATM_SCL translate <-5.320, -10.414, -12.564> }
object {Atom_C scale ATM_SCL * .8 translate <-5.250, -9.805, -10.189> }
object {Atom_C scale ATM_SCL * .8 translate <-4.756, -8.534, -9.543> }
object {Atom_N scale ATM_SCL translate <-3.953, -8.730, -8.339> }
object {Atom_C scale ATM_SCL * .8 translate <-4.610, -8.730, -7.105> }
object {Atom_O scale ATM_SCL translate <-5.839, -8.565, -7.101> }
object {Atom_N scale ATM_SCL translate <-3.904, -8.966, -5.977> }
object {Atom_C scale ATM_SCL * .8 translate <-2.594, -9.185, -6.049> }
object {Atom_N scale ATM_SCL translate <-1.912, -9.393, -4.921> }
object {Atom_C scale ATM_SCL * .8 translate <-1.896, -9.177, -7.295> }
object {Atom_C scale ATM_SCL * .8 translate <-2.610, -8.985, -8.398> }
object {Atom_H scale ATM_SCL translate <-2.994, -8.351, -13.499> }
object {Atom_H scale ATM_SCL translate <-2.692, -7.124, -12.464> }
object {Atom_H scale ATM_SCL translate <-4.792, -8.153, -12.451> }
object {Atom_H scale ATM_SCL translate <-3.701, -10.478, -11.462> }
object {Atom_H scale ATM_SCL translate <-5.558, -11.361, -12.349> }
object {Atom_H scale ATM_SCL translate <-5.038, -10.598, -9.618> }
object {Atom_H scale ATM_SCL translate <-6.236, -9.762, -10.347> }
object {Atom_H scale ATM_SCL translate <-5.544, -8.038, -9.179> }
object {Atom_H scale ATM_SCL translate <-0.927, -9.559, -4.956> }
object {Atom_H scale ATM_SCL translate <-2.386, -9.383, -4.041> }
object {Atom_H scale ATM_SCL translate <-0.906, -9.311, -7.335> }
object {Atom_H scale ATM_SCL translate <-2.158, -9.028, -9.289> }
object {Atom_O scale ATM_SCL translate <-7.194, -10.457, 3.441> }
object {Atom_C scale ATM_SCL * .8 translate <-8.533, -9.966, 3.627> }
object {Atom_C scale ATM_SCL * .8 translate <-9.308, -9.966, 2.346> }
object {Atom_O scale ATM_SCL translate <-8.950, -11.057, 1.493> }
object {Atom_C scale ATM_SCL * .8 translate <-9.104, -8.726, 1.489> }
object {Atom_O scale ATM_SCL translate <-9.920, -7.635, 1.911> }
object {Atom_C scale ATM_SCL * .8 translate <-9.501, -9.248, 0.120> }
object {Atom_C scale ATM_SCL * .8 translate <-8.769, -10.579, 0.145> }
object {Atom_N scale ATM_SCL translate <-7.357, -10.457, -0.235> }
object {Atom_C scale ATM_SCL * .8 translate <-6.224, -10.614, 0.525> }
object {Atom_N scale ATM_SCL translate <-5.118, -10.457, -0.138> }
object {Atom_C scale ATM_SCL * .8 translate <-5.530, -10.167, -1.426> }
object {Atom_C scale ATM_SCL * .8 translate <-4.760, -9.884, -2.576> }
object {Atom_O scale ATM_SCL translate <-3.523, -9.860, -2.707> }
object {Atom_N scale ATM_SCL translate <-5.574, -9.644, -3.683> }
object {Atom_C scale ATM_SCL * .8 translate <-6.940, -9.680, -3.678> }
object {Atom_N scale ATM_SCL translate <-7.525, -9.382, -4.853> }
object {Atom_N scale ATM_SCL translate <-7.672, -9.943, -2.609> }
object {Atom_C scale ATM_SCL translate <-6.897, -10.170, -1.515> }
object {Atom_H scale ATM_SCL translate <-6.709, -10.442, 4.315> }
object {Atom_H scale ATM_SCL translate <-8.489, -9.031, 3.978> }
object {Atom_H scale ATM_SCL translate <-9.003, -10.550, 4.289> }
object {Atom_H scale ATM_SCL translate <-10.254, -10.021, 2.665> }
object {Atom_H scale ATM_SCL translate <-8.179, -8.349, 1.530> }
object {Atom_H scale ATM_SCL translate <-9.174, -8.655, -0.616> }
object {Atom_H scale ATM_SCL translate <-10.490, -9.367, 0.038> }
object {Atom_H scale ATM_SCL translate <-9.132, -11.221, -0.530> }
object {Atom_H scale ATM_SCL translate <-6.248, -10.830, 1.501> }
object {Atom_H scale ATM_SCL translate <-5.122, -9.429, -4.549> }
object {Atom_H scale ATM_SCL translate <-6.962, -9.185, -5.656> }
object {Atom_H scale ATM_SCL translate <-8.522, -9.358, -4.923> }
object {Atom_P scale ATM_SCL translate <-9.281, -6.175, 1.856> }
object {Atom_O scale ATM_SCL translate <-7.885, -6.175, 2.313> }
object {Atom_O scale ATM_SCL translate <-10.176, -5.245, 2.596> }
object {Atom_O scale ATM_SCL translate <-9.401, -5.873, 0.297> }
object {Atom_C scale ATM_SCL * .8 translate <-10.683, -5.543, -0.286> }
object {Atom_C scale ATM_SCL * .8 translate <-10.552, -5.433, -1.790> }
object {Atom_O scale ATM_SCL translate <-9.806, -6.552, -2.293> }
object {Atom_C scale ATM_SCL * .8 translate <-9.793, -4.205, -2.280> }
object {Atom_O scale ATM_SCL translate <-10.656, -3.078, -2.369> }
object {Atom_C scale ATM_SCL * .8 translate <-9.312, -4.691, -3.640> }
object {Atom_C scale ATM_SCL * .8 translate <-8.884, -6.108, -3.277> }
object {Atom_N scale ATM_SCL translate <-7.506, -6.179, -2.800> }
object {Atom_C scale ATM_SCL * .8 translate <-6.983, -6.395, -1.545> }
object {Atom_N scale ATM_SCL translate <-5.689, -6.454, -1.503> }
object {Atom_C scale ATM_SCL * .8 translate <-5.304, -6.242, -2.817> }
object {Atom_C scale ATM_SCL * .8 translate <-4.012, -6.187, -3.391> }
object {Atom_O scale ATM_SCL translate <-2.918, -6.308, -2.825> }
object {Atom_N scale ATM_SCL translate <-4.076, -5.959, -4.760> }
object {Atom_C scale ATM_SCL * .8 translate <-5.222, -5.833, -5.491> }
object {Atom_N scale ATM_SCL translate <-5.093, -5.602, -6.805> }
object {Atom_N scale ATM_SCL translate <-6.430, -5.877, -4.971> }
object {Atom_C scale ATM_SCL translate <-6.398, -6.089, -3.632> }
object {Atom_H scale ATM_SCL translate <-11.000, -4.670, 0.084> }
object {Atom_H scale ATM_SCL translate <-11.343, -6.260, -0.062> }
object {Atom_H scale ATM_SCL translate <-11.496, -5.386, -2.116> }
object {Atom_H scale ATM_SCL translate <-9.053, -3.893, -1.684> }
object {Atom_H scale ATM_SCL translate <-8.544, -4.147, -3.979> }
object {Atom_H scale ATM_SCL translate <-10.048, -4.688, -4.317> }
object {Atom_H scale ATM_SCL translate <-8.898, -6.696, -4.086> }
object {Atom_H scale ATM_SCL translate <-7.555, -6.498, -0.731> }
object {Atom_H scale ATM_SCL translate <-3.209, -5.881, -5.252> }
object {Atom_H scale ATM_SCL translate <-4.184, -5.565, -7.219> }
object {Atom_H scale ATM_SCL translate <-5.906, -5.467, -7.371> }
object {Atom_P scale ATM_SCL translate <-10.124, -1.630, -1.942> }
object {Atom_O scale ATM_SCL translate <-9.322, -1.685, -0.712> }
object {Atom_O scale ATM_SCL translate <-11.295, -0.716, -1.904> }
object {Atom_O scale ATM_SCL translate <-9.229, -1.265, -3.209> }
object {Atom_C scale ATM_SCL * .8 translate <-9.915, -1.073, -4.485> }
object {Atom_C scale ATM_SCL * .8 translate <-8.877, -0.900, -5.559> }
object {Atom_O scale ATM_SCL translate <-8.077, -2.097, -5.571> }
object {Atom_C scale ATM_SCL * .8 translate <-7.833, 0.195, -5.301> }
object {Atom_O scale ATM_SCL translate <-8.383, 1.478, -5.554> }
object {Atom_C scale ATM_SCL * .8 translate <-6.743, -0.272, -6.243> }
object {Atom_C scale ATM_SCL * .8 translate <-6.741, -1.760, -5.960> }
object {Atom_N scale ATM_SCL translate <-5.784, -2.113, -4.904> }
object {Atom_C scale ATM_SCL * .8 translate <-5.981, -2.352, -3.564> }
object {Atom_N scale ATM_SCL translate <-4.905, -2.631, -2.926> }
object {Atom_C scale ATM_SCL * .8 translate <-3.899, -2.576, -3.885> }
object {Atom_C scale ATM_SCL * .8 translate <-2.508, -2.772, -3.759> }
object {Atom_O scale ATM_SCL translate <-1.885, -3.066, -2.724> }
object {Atom_N scale ATM_SCL translate <-1.848, -2.588, -4.971> }
object {Atom_C scale ATM_SCL * .8 translate <-2.467, -2.270, -6.154> }
object {Atom_N scale ATM_SCL translate <-1.696, -2.136, -7.244> }
object {Atom_N scale ATM_SCL translate <-3.763, -2.066, -6.277> }
object {Atom_C scale ATM_SCL translate <-4.422, -2.234, -5.102> }
object {Atom_H scale ATM_SCL translate <-10.492, -0.258, -4.439> }
object {Atom_H scale ATM_SCL translate <-10.481, -1.872, -4.688> }
object {Atom_H scale ATM_SCL translate <-9.393, -0.679, -6.386> }
object {Atom_H scale ATM_SCL translate <-7.497, 0.308, -4.366> }
object {Atom_H scale ATM_SCL translate <-5.862, 0.146, -6.022> }
object {Atom_H scale ATM_SCL translate <-6.974, -0.079, -7.197> }
object {Atom_H scale ATM_SCL translate <-6.456, -2.271, -6.771> }
object {Atom_H scale ATM_SCL translate <-6.880, -2.312, -3.128> }
object {Atom_H scale ATM_SCL translate <-0.854, -2.695, -4.980> }
object {Atom_H scale ATM_SCL translate <-0.709, -2.285, -7.180> }
object {Atom_H scale ATM_SCL translate <-2.108, -1.887, -8.120> }
object {Atom_P scale ATM_SCL translate <-7.864, 2.778, -4.823> }
object {Atom_O scale ATM_SCL translate <-7.742, 2.558, -3.370> }
object {Atom_O scale ATM_SCL translate <-8.762, 3.900, -5.216> }
object {Atom_O scale ATM_SCL translate <-6.414, 3.013, -5.428> }
object {Atom_C scale ATM_SCL * .8 translate <-6.256, 3.602, -6.733> }
object {Atom_C scale ATM_SCL * .8 translate <-4.821, 3.457, -7.143> }
object {Atom_O scale ATM_SCL translate <-4.368, 2.114, -6.949> }
object {Atom_C scale ATM_SCL * .8 translate <-3.813, 4.300, -6.399> }
object {Atom_O scale ATM_SCL translate <-3.849, 5.674, -6.822> }
object {Atom_C scale ATM_SCL * .8 translate <-2.514, 3.606, -6.725> }
object {Atom_C scale ATM_SCL * .8 translate <-2.959, 2.161, -6.653> }
object {Atom_N scale ATM_SCL translate <-2.666, 1.584, -5.343> }
object {Atom_C scale ATM_SCL * .8 translate <-3.505, 1.349, -4.270> }
object {Atom_N scale ATM_SCL translate <-2.906, 0.799, -3.269> }
object {Atom_C scale ATM_SCL * .8 translate <-1.588, 0.642, -3.678> }
object {Atom_C scale ATM_SCL * .8 translate <-0.475, 0.136, -2.973> }
object {Atom_O scale ATM_SCL translate <-0.437, -0.331, -1.836> }
object {Atom_N scale ATM_SCL translate <0.699, 0.246, -3.721> }
object {Atom_C scale ATM_SCL * .8 translate <0.767, 0.733, -5.001> }
object {Atom_N scale ATM_SCL translate <1.968, 0.701, -5.580> }
object {Atom_N scale ATM_SCL translate <-0.273, 1.192, -5.673> }
object {Atom_C scale ATM_SCL * .8 translate <-1.420, 1.129, -4.950> }
object {Atom_H scale ATM_SCL translate <-6.502, 4.571, -6.699> }
object {Atom_H scale ATM_SCL translate <-6.845, 3.131, -7.390> }
object {Atom_H scale ATM_SCL translate <-4.850, 3.757, -8.096> }
object {Atom_H scale ATM_SCL translate <-3.978, 4.362, -5.415> }
object {Atom_H scale ATM_SCL translate <-1.805, 3.810, -6.049> }
object {Atom_H scale ATM_SCL translate <-2.184, 3.847, -7.638> }
object {Atom_H scale ATM_SCL translate <-2.456, 1.613, -7.322> }
object {Atom_H scale ATM_SCL translate <-4.478, 1.582, -4.270> }
object {Atom_H scale ATM_SCL translate <1.552, -0.052, -3.292> }
object {Atom_H scale ATM_SCL translate <2.758, 0.354, -5.074> }
object {Atom_H scale ATM_SCL translate <2.079, 1.024, -6.520> }
object {Atom_P scale ATM_SCL translate <-4.015, 6.824, -5.728> }
object {Atom_O scale ATM_SCL translate <-4.633, 6.310, -4.477> }
object {Atom_O scale ATM_SCL translate <-4.699, 7.962, -6.344> }
object {Atom_O scale ATM_SCL translate <-2.483, 7.154, -5.415> }
object {Atom_C scale ATM_SCL * .8 translate <-1.560, 7.731, -6.344> }
object {Atom_C scale ATM_SCL * .8 translate <-0.162, 7.287, -6.006> }
object {Atom_O scale ATM_SCL translate <-0.146, 5.847, -5.884> }
object {Atom_C scale ATM_SCL * .8 translate <0.411, 7.754, -4.671> }
object {Atom_O scale ATM_SCL translate <0.923, 9.097, -4.718> }
object {Atom_C scale ATM_SCL * .8 translate <1.551, 6.738, -4.519> }
object {Atom_C scale ATM_SCL * .8 translate <0.774, 5.486, -4.861> }
object {Atom_N scale ATM_SCL translate <0.250, 4.752, -3.729> }
object {Atom_C scale ATM_SCL * .8 translate <1.175, 3.998, -2.964> }
object {Atom_O scale ATM_SCL translate <2.371, 4.092, -3.277> }
object {Atom_N scale ATM_SCL translate <0.742, 3.280, -1.912> }
object {Atom_C scale ATM_SCL * .8 translate <-0.563, 3.272, -1.612> }
object {Atom_N scale ATM_SCL translate <-0.965, 2.546, -0.565> }
object {Atom_C scale ATM_SCL * .8 translate <-1.520, 3.971, -2.390> }
object {Atom_C scale ATM_SCL * .8 translate <-1.076, 4.685, -3.408> }
object {Atom_H scale ATM_SCL translate <-1.614, 8.728, -6.292> }
object {Atom_H scale ATM_SCL translate <-1.789, 7.432, -7.270> }
object {Atom_H scale ATM_SCL translate <0.383, 7.684, -6.744> }
object {Atom_H scale ATM_SCL translate <-0.255, 7.786, -3.926> }
object {Atom_H scale ATM_SCL translate <1.914, 6.714, -3.588> }
object {Atom_H scale ATM_SCL translate <2.296, 6.908, -5.164> }
object {Atom_H scale ATM_SCL translate <1.384, 4.778, -5.217> }
object {Atom_H scale ATM_SCL translate <-1.933, 2.520, -0.316> }
object {Atom_H scale ATM_SCL translate <-0.298, 2.028, -0.030> }
object {Atom_H scale ATM_SCL translate <-2.496, 3.925, -2.176> }
object {Atom_H scale ATM_SCL translate <-1.733, 5.194, -3.963> }
object {Atom_P scale ATM_SCL translate <1.034, 9.964, -3.404> }
object {Atom_O scale ATM_SCL translate <-0.158, 9.705, -2.533> }
object {Atom_O scale ATM_SCL translate <1.175, 11.393, -3.750> }
object {Atom_O scale ATM_SCL translate <2.339, 9.391, -2.715> }
object {Atom_C scale ATM_SCL * .8 translate <3.601, 9.104, -3.298> }
object {Atom_C scale ATM_SCL * .8 translate <4.596, 8.598, -2.305> }
object {Atom_O scale ATM_SCL translate <4.610, 7.169, -2.225> }
object {Atom_C scale ATM_SCL * .8 translate <4.642, 9.116, -0.886> }
object {Atom_O scale ATM_SCL translate <5.439, 10.309, -0.784> }
object {Atom_C scale ATM_SCL * .8 translate <5.292, 7.958, -0.129> }
object {Atom_C scale ATM_SCL * .8 translate <4.691, 6.761, -0.852> }
object {Atom_N scale ATM_SCL translate <3.438, 6.326, -0.235> }
object {Atom_C scale ATM_SCL * .8 translate <3.522, 5.395, 0.817> }
object {Atom_O scale ATM_SCL translate <4.639, 4.991, 1.172> }
object {Atom_N scale ATM_SCL translate <2.389, 4.956, 1.404> }
object {Atom_C scale ATM_SCL * .8 translate <1.211, 5.419, 0.999> }
object {Atom_N scale ATM_SCL translate <0.116, 4.968, 1.616> }
object {Atom_C scale ATM_SCL * .8 translate <1.104, 6.357, -0.053> }
object {Atom_C scale ATM_SCL * .8 translate <2.221, 6.801, -0.615> }
object {Atom_H scale ATM_SCL translate <3.960, 9.941, -3.711> }
object {Atom_H scale ATM_SCL translate <3.475, 8.409, -4.006> }
object {Atom_H scale ATM_SCL translate <5.403, 9.007, -2.731> }
object {Atom_H scale ATM_SCL translate <3.742, 9.373, -0.533> }
object {Atom_H scale ATM_SCL translate <5.041, 7.966, 0.839> }
object {Atom_H scale ATM_SCL translate <6.288, 7.976, -0.216> }
object {Atom_H scale ATM_SCL translate <5.246, 5.932, -0.787> }
object {Atom_H scale ATM_SCL translate <-0.786, 5.296, 1.336> }
object {Atom_H scale ATM_SCL translate <0.198, 4.303, 2.358> }
object {Atom_H scale ATM_SCL translate <0.210, 6.678, -0.366> }
object {Atom_H scale ATM_SCL translate <2.167, 7.497, -1.331> }
object {Atom_P scale ATM_SCL translate <5.435, 11.228, 0.509> }
object {Atom_O scale ATM_SCL translate <4.082, 11.781, 0.707> }
object {Atom_O scale ATM_SCL translate <6.502, 12.252, 0.365> }
object {Atom_O scale ATM_SCL translate <5.809, 10.258, 1.704> }
object {Atom_C scale ATM_SCL * .8 translate <7.164, 9.984, 2.093> }
object {Atom_C scale ATM_SCL * .8 translate <7.121, 9.014, 3.217> }
object {Atom_O scale ATM_SCL translate <6.402, 7.825, 2.925> }
object {Atom_C scale ATM_SCL * .8 translate <6.448, 9.528, 4.505> }
object {Atom_O scale ATM_SCL translate <7.399, 10.392, 5.105> }
object {Atom_C scale ATM_SCL * .8 translate <6.393, 8.186, 5.253> }
object {Atom_C scale ATM_SCL * .8 translate <5.775, 7.366, 4.129> }
object {Atom_N scale ATM_SCL translate <4.313, 7.338, 4.142> }
object {Atom_C scale ATM_SCL * .8 translate <3.708, 6.494, 5.093> }
object {Atom_O scale ATM_SCL translate <4.444, 5.886, 5.879> }
object {Atom_N scale ATM_SCL translate <2.367, 6.369, 5.101> }
object {Atom_C scale ATM_SCL * .8 translate <1.626, 7.063, 4.239> }
object {Atom_N scale ATM_SCL translate <0.298, 6.922, 4.315> }
object {Atom_C scale ATM_SCL * .8 translate <2.221, 7.923, 3.280> }
object {Atom_C scale ATM_SCL * .8 translate <3.538, 8.037, 3.280> }
object {Atom_H scale ATM_SCL translate <7.611, 10.828, 2.388> }
object {Atom_H scale ATM_SCL translate <7.667, 9.591, 1.323> }
object {Atom_H scale ATM_SCL translate <8.099, 8.854, 3.353> }
object {Atom_H scale ATM_SCL translate <5.576, 10.014, 4.445> }
object {Atom_H scale ATM_SCL translate <5.808, 8.224, 6.063> }
object {Atom_H scale ATM_SCL translate <7.301, 7.856, 5.512> }
object {Atom_H scale ATM_SCL translate <5.957, 6.389, 4.237> }
object {Atom_H scale ATM_SCL translate <-0.295, 7.425, 3.686> }
object {Atom_H scale ATM_SCL translate <-0.102, 6.313, 5.000> }
object {Atom_H scale ATM_SCL translate <1.661, 8.428, 2.624> }
object {Atom_H scale ATM_SCL translate <3.973, 8.656, 2.626> }
object {Atom_P scale ATM_SCL translate <7.225, 11.259, 6.398> }
object {Atom_O scale ATM_SCL translate <6.180, 12.276, 6.153> }
object {Atom_O scale ATM_SCL translate <8.607, 11.769, 6.660> }
object {Atom_O scale ATM_SCL translate <6.744, 10.247, 7.539> }
object {Atom_C scale ATM_SCL * .8 translate <7.646, 9.815, 8.578> }
object {Atom_C scale ATM_SCL * .8 translate <7.100, 9.002, 9.668> }
object {Atom_O scale ATM_SCL translate <6.244, 7.935, 9.322> }
object {Atom_C scale ATM_SCL * .8 translate <6.608, 9.658, 10.932> }
object {Atom_O scale ATM_SCL translate <7.354, 9.175, 12.072> }
object {Atom_C scale ATM_SCL * .8 translate <5.165, 9.254, 10.991> }
object {Atom_C scale ATM_SCL * .8 translate <5.054, 8.025, 10.108> }
object {Atom_N scale ATM_SCL translate <3.819, 8.013, 9.322> }
object {Atom_C scale ATM_SCL * .8 translate <2.727, 7.291, 9.820> }
object {Atom_O scale ATM_SCL translate <2.863, 6.616, 10.839> }
object {Atom_N scale ATM_SCL translate <1.555, 7.342, 9.153> }
object {Atom_C scale ATM_SCL * .8 translate <1.440, 8.084, 8.050> }
object {Atom_N scale ATM_SCL translate <0.277, 8.080, 7.391> }
object {Atom_C scale ATM_SCL * .8 translate <2.534, 8.857, 7.556> }
object {Atom_C scale ATM_SCL * .8 translate <3.679, 8.798, 8.215> }
object {Atom_H scale ATM_SCL translate <8.041, 10.636, 8.989> }
object {Atom_H scale ATM_SCL translate <8.369, 9.280, 8.141> }
object {Atom_H scale ATM_SCL translate <7.996, 8.628, 9.908> }
object {Atom_H scale ATM_SCL translate <6.722, 10.651, 10.942> }
object {Atom_H scale ATM_SCL translate <7.018, 9.618, 12.903> }
object {Atom_H scale ATM_SCL translate <4.582, 9.988, 10.643> }
object {Atom_H scale ATM_SCL translate <4.901, 9.035, 11.930> }
object {Atom_H scale ATM_SCL translate <4.985, 7.201, 10.671> }
object {Atom_H scale ATM_SCL translate <0.170, 8.629, 6.562> }
object {Atom_H scale ATM_SCL translate <-0.486, 7.528, 7.727> }
object {Atom_H scale ATM_SCL translate <2.438, 9.425, 6.738> }
object {Atom_H scale ATM_SCL translate <4.457, 9.339, 7.896> }
}

#declare adna2 = object {
	object { adna2_obj rotate -30*x
             rotate 180*y} }

#declare bell_jar_adna = union {
	object {bell_jar scale <25, 11, 25> }
  	object {adna2 translate <0.0, 25, 0.0> }
}
#version ADNA_Full_Inc_Temp
