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

Scene sources are separate from the backends above:

    quiltwright.tvb_data  Real brain geometry from The Virtual Brain —
                          cortical surfaces, connectomes, parcellations,
                          downloaded on demand

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
    LITIHOLO_SWEEP,
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
    sweep_spec,
    view_disparity,
    view_offsets,
)
from .povray import (
    Clearance,
    PovCamera,
    camera_block,
    depth_budget,
    format_depth_budget,
    render_pov_quilt,
    render_pov_views,
    sweep_extent,
)
from .tvb_data import (
    CONNECTIVITIES,
    REGION_MAPPINGS,
    SENSORS,
    SURFACES,
    Connectome,
    connectome_polydata,
    load_connectivity,
    load_region_mapping,
    load_sensors,
    load_surface,
    surface_polydata,
)

__version__ = "0.3.0"
__all__ = [
    # Quilt geometry
    "QuiltSpec",
    "QUILT_PRESETS",
    "assemble_quilt",
    "view_offsets",
    # View sweeps (hologram printers, lenticular interlacers)
    "sweep_spec",
    "LITIHOLO_SWEEP",
    # Depth budget
    "view_disparity",
    "focal_distance_for_range",
    "depth_budget",
    "format_depth_budget",
    "sweep_extent",
    "Clearance",
    # PyVista backend
    "render_quilt",
    "render_quilt_video",
    # POV-Ray backend
    "PovCamera",
    "render_pov_quilt",
    "render_pov_views",
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
    # Scene source: The Virtual Brain datasets
    "SURFACES",
    "CONNECTIVITIES",
    "REGION_MAPPINGS",
    "SENSORS",
    "Connectome",
    "load_surface",
    "load_connectivity",
    "load_region_mapping",
    "load_sensors",
    "surface_polydata",
    "connectome_polydata",
]
