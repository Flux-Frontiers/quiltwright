// Full-quality single frame of 3porin.pov: radiosity plus photon caustics.
// The 1997 scene parses under language version 3.1; the quality features
// need 3.5+, so the version switches to 3.7 after the include. Starting
// in 3.1 (not 3.7) keeps POV-Ray's legacy gamma mode so the scene's
// original brightness survives.
//
// The scene's infinite water plane cannot be a photon target (unbounded),
// so a finite disc of the same water rides 0.1 above it, marked as the
// reflection target: wavy reflected caustics onto the barrel from below.
#version 3.1;
#include "3porin.pov"
#version 3.7;

global_settings {
	max_trace_level 8
	radiosity {
		count 200
		error_bound 0.5
		recursion_limit 2
		pretrace_start 0.08
		pretrace_end 0.01
		nearest_count 8
		// Legacy mode keeps the scene's ambient terms alive, so radiosity
		// stacks on top of them — run it at partial strength.
		brightness 0.35
	}
	photons {
		count 200000
		autostop 0
		jitter 0.4
	}
}

disc { <0, -444.9, 0>, y, 1500
	pigment { MidnightBlue }
	normal {
		waves 0.7
		frequency 10.0
		scale 50.355804
	}
	finish { reflection 0.6 }
	photons { target reflection on collect off }
}

// Back to 3.1 so the renderer stays in legacy gamma mode.
#version 3.1;
