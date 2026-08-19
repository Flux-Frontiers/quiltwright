"""
Quiltwright -- holographic output for Looking Glass displays.

Turns a rendered scene into a *quilt*: the tiled multi-view image that
lenticular light-field displays fuse into real depth.  Two rendering
backends feed the same assembler:

    quiltwright.lfd      PyVista / VTK scenes, plus quilt geometry,
                         video encoding, and Looking Glass Bridge control
    quiltwright.povray   POV-Ray scenes, ray-traced off-axis views
    quiltwright.hld      Hololuminescent Displays, which play ordinary
                         2-D video rather than quilts
    quiltwright.weave    CPU port of the lenticular shader: pre-lensed
                         native frames a panel shows without Bridge
                         (e.g. as the desktop wallpaper)

Scene sources are separate from the backends above:

    quiltwright.tvb_data  Real brain geometry from The Virtual Brain --
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

# ---------------------------------------------------------------------------
# Lazy re-exports (PEP 562)
#
# ``lfd`` imports PyVista when it is installed, and ``povray`` imports ``lfd``
# for the quilt assembler.  Eager re-exports here meant that reaching for
# ``quiltwright.povgen`` -- a NumPy-only module whose whole purpose is writing
# scenes without a rendering stack -- loaded VTK on the way past.  Binding the
# names on first use instead keeps the public API identical while letting the
# analytic path stay as light as it claims to be.
# ---------------------------------------------------------------------------

_LAZY: dict[str, str] = {
    "BRIDGE_URL": "lfd",
    "Box": "povgen",
    "CONNECTIVITIES": "tvb_data",
    "Calibration": "weave",
    "Clearance": "povray",
    "Connectome": "tvb_data",
    "Cylinder": "povgen",
    "DEPTH_LABELS": "lfd",
    "Finish": "povgen",
    "HLD_RESOLUTION": "hld",
    "HLD_SAFE_MARGINS": "hld",
    "Instance": "povgen",
    "LITIHOLO_SWEEP": "lfd",
    "LightSource": "povgen",
    "Mesh2": "povgen",
    "PovCamera": "povray",
    "PovScene": "povgen",
    "Primitive": "povgen",
    "QUILT_PRESETS": "lfd",
    "QuiltSpec": "lfd",
    "REGION_MAPPINGS": "tvb_data",
    "SENSORS": "tvb_data",
    "SURFACES": "tvb_data",
    "Sphere": "povgen",
    "SphereSweep": "povgen",
    "SubpixelCell": "weave",
    "Texture": "povgen",
    "Union": "povgen",
    "add_floor_shadow": "hld",
    "apply_safe_area": "hld",
    "assemble_quilt": "lfd",
    "camera_block": "povray",
    "cast_quilt": "lfd",
    "connectome_polydata": "tvb_data",
    "depth_budget": "povray",
    "depth_report": "lfd",
    "find_ffmpeg": "lfd",
    "focal_distance_for_range": "lfd",
    "format_depth_budget": "povray",
    "coalesce_mesh2": "povgen",
    "fov_horizontal_to_vertical": "povgen",
    "hld_orbit_speed": "hld",
    "instances_from_frames": "povgen",
    "lights_from_bounds": "povgen",
    "load_connectivity": "tvb_data",
    "load_region_mapping": "tvb_data",
    "load_sensors": "tvb_data",
    "load_surface": "tvb_data",
    "ground_slab": "povgen",
    "instances_by_color": "povgen",
    "swept_scene": "povgen",
    "pov_camera_from_frame": "povgen",
    "parse_color": "povgen",
    "pause_quilt": "lfd",
    "pov_camera_from_plotter": "povgen",
    "render_hld_still": "hld",
    "render_hld_video": "hld",
    "render_pov_quilt": "povray",
    "render_pov_views": "povray",
    "render_quilt": "lfd",
    "render_quilt_video": "lfd",
    "resume_quilt": "lfd",
    "save_and_cast_quilt": "lfd",
    "save_quilt": "lfd",
    "scene_depths": "lfd",
    "sphere_sweeps_from_paths": "povgen",
    "spheres_from_points": "povgen",
    "stop_quilt": "lfd",
    "style_plotter_for_hld": "hld",
    "surface_polydata": "tvb_data",
    "sweep_extent": "povray",
    "sweep_spec": "lfd",
    "to_pov": "povgen",
    "view_disparity": "lfd",
    "view_offsets": "lfd",
    "weave_quilt": "weave",
}


def __getattr__(name: str):
    """Import the submodule owning *name* on first access.

    :param name: Attribute being looked up.
    :return: The re-exported object.
    :raises AttributeError: If *name* is not a public export.
    """
    module = _LAZY.get(name)
    if module is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    import importlib

    value = getattr(importlib.import_module(f".{module}", __name__), name)
    globals()[name] = value  # bind, so this runs once per name
    return value


def __dir__() -> list[str]:
    """:return: Public names, so tab completion still sees the lazy ones."""
    return sorted(set(globals()) | set(_LAZY))


__version__ = "0.7.0"
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
    "scene_depths",
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
    # POV-Ray scene generation
    "PovScene",
    "Primitive",
    "Texture",
    "Finish",
    "Sphere",
    "Cylinder",
    "Box",
    "SphereSweep",
    "Mesh2",
    "Union",
    "Instance",
    "LightSource",
    "to_pov",
    "parse_color",
    "coalesce_mesh2",
    "sphere_sweeps_from_paths",
    "spheres_from_points",
    "instances_from_frames",
    "lights_from_bounds",
    "ground_slab",
    "instances_by_color",
    "swept_scene",
    "pov_camera_from_frame",
    "pov_camera_from_plotter",
    "fov_horizontal_to_vertical",
    # Output
    "save_quilt",
    "save_and_cast_quilt",
    "find_ffmpeg",
    # Native weaving (pre-lensed frames, no Bridge)
    "Calibration",
    "SubpixelCell",
    "weave_quilt",
    # Looking Glass Bridge
    "BRIDGE_URL",
    "DEPTH_LABELS",
    "cast_quilt",
    "depth_report",
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
