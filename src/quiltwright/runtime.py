"""Process-level defaults shared by more than one backend.

Nothing here knows about quilts, cameras, or a renderer.  The courtesy
core cap is the one constant both POV-Ray and Cycles need so a quilt
does not take every core on the machine.

Part of Quiltwright -- https://github.com/suchanek/quiltwright
Author: Eric G. Suchanek, PhD
"""

#: Cores held back from a render by default, so a multi-minute quilt does
#: not make the rest of the machine unusable.  POV-Ray's own default is
#: every core it can see; Blender's ``-t 0`` is the same.
COURTESY_CORES_HELD_BACK = 2
