//
// Porin trimer, 9:16 -- the tall companion to 3porin.pov's 16:9.
//
// Same camera, lights, sky and geometry: 3porin.pov's own ASPECT, CAM_X and
// CAM_Z declares are guarded with #ifndef precisely so a wrapper can set them
// first. Nothing about the barrel's depth composition changes -- the title
// and signature already sit at scene depth 900, inside the near/far bounds
// either aspect measures.
//
// CAM_Z pulls the camera back from -1100 to -1300: at the original distance
// the barrel overflowed a 9:16 frame on both sides and clipped the
// signature. CAM_X recentres it, and not at its vertex bounding-box centroid
// (72.47, from xmin -222.48/xmax 367.43) -- that overshot, confirmed live on
// a Looking Glass Go as "offset to the left a bit". 20 was found by
// rendering, masking the subject by hue/saturation against the sea-and-sky
// backdrop, and measuring the actual pixel centroid: -7.2% of frame width at
// 72.47, +0.7% at 20. The bounding box is not where the rendered pixels sit.
#declare ASPECT = 0.5625;
#declare CAM_X = 20;
#declare CAM_Z = -1300.000000;
#include "3porin.pov"
