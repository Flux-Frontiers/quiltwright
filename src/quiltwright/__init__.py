"""
Quiltwright — holographic output for Looking Glass displays.

Turns a rendered scene into a *quilt*: the tiled multi-view image that
lenticular light-field displays fuse into real depth.  Two rendering
backends feed the same assembler:

    quiltwright.lfd      PyVista / VTK scenes, plus quilt geometry,
                         video encoding, and Looking Glass Bridge control
    quiltwright.povray   POV-Ray scenes, ray-traced off-axis views
    quiltwright.hld      Hololuminescent Displays, which play ordinary
                         2-D video rather than quilts

Every view uses an off-axis (asymmetric-frustum) projection rather than a
"toe-in" rotation, which is the geometric requirement for a display to fuse
the views instead of ghosting them.

Typical usage::

    import pyvista as pv
    from quiltwright import QUILT_PRESETS, render_quilt, save_quilt

    p = pv.Plotter(off_screen=True)
    p.add_mesh(pv.ParametricTorus())
    spec = QUILT_PRESETS["portrait"]
    save_quilt(render_quilt(p, spec), "torus", spec)

Author: Eric G. Suchanek, PhD
"""

from .hld import (
    HLD_RESOLUTION,
    HLD_SAFE_MARGINS,
    add_floor_shadow,
    apply_safe_area,
    hld_orbit_speed,
    render_hld_still,
    render_hld_video,
    style_plotter_for_hld,
)
from .lfd import (
    BRIDGE_URL,
    QUILT_PRESETS,
    QuiltSpec,
    assemble_quilt,
    cast_quilt,
    find_ffmpeg,
    focal_distance_for_range,
    pause_quilt,
    render_quilt,
    render_quilt_video,
    resume_quilt,
    save_quilt,
    stop_quilt,
    view_disparity,
    view_offsets,
)
from .povray import PovCamera, camera_block, render_pov_quilt

__version__ = "0.1.0"
__all__ = [
    # Quilt geometry
    "QuiltSpec",
    "QUILT_PRESETS",
    "assemble_quilt",
    "view_offsets",
    # Depth budget
    "view_disparity",
    "focal_distance_for_range",
    # PyVista backend
    "render_quilt",
    "render_quilt_video",
    # POV-Ray backend
    "PovCamera",
    "render_pov_quilt",
    "camera_block",
    # Output
    "save_quilt",
    "find_ffmpeg",
    # Looking Glass Bridge
    "BRIDGE_URL",
    "cast_quilt",
    "pause_quilt",
    "resume_quilt",
    "stop_quilt",
    # Hololuminescent Display
    "HLD_RESOLUTION",
    "HLD_SAFE_MARGINS",
    "render_hld_video",
    "render_hld_still",
    "style_plotter_for_hld",
    "apply_safe_area",
    "add_floor_shadow",
    "hld_orbit_speed",
]
