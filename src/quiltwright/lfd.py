"""
Looking Glass Quilt Renderer
============================

Renders any PyVista scene into a *quilt* -- the tiled multi-view image format
used by Looking Glass holographic light-field displays.

A quilt packs N renders of the same scene, captured from camera positions
swept horizontally across a viewing cone, into a single image.  Views are
tiled left-to-right, bottom-to-top: view 0 (leftmost camera) sits at the
bottom-left tile and view N-1 (rightmost camera) at the top-right.  Looking
Glass software (Bridge, Studio) detects quilt settings from the filename
suffix ``_qs<cols>x<rows>a<aspect>.png``, so files saved through
:func:`save_quilt` are recognised automatically.

Each view uses an *off-axis* (asymmetric-frustum) projection rather than a
"toe-in" rotation: the camera translates along its horizontal axis while the
frustum is sheared back toward the focal plane.  This keeps the focal plane
identical across views -- the geometric requirement for the display's lenticular
optics to fuse the views into a stable hologram.  Content at the focal plane
appears at the physical screen surface; content nearer/farther floats in
front of / behind the glass.

Quilt geometry (:class:`QuiltSpec`, :data:`QUILT_PRESETS`,
:func:`assemble_quilt`, :func:`save_quilt`) lives in :mod:`quiltwright.quilt`.
Bridge control (:func:`cast_quilt`) lives in :mod:`quiltwright.bridge`.  Both
are re-exported from here so existing ``from quiltwright.lfd import ...``
callers keep working.

**Optional dependencies** -- install the ``viz`` extras group::

    poetry install --with viz   # pyvista, pillow, scipy, ...

Typical usage::

    import pyvista as pv
    from quiltwright.lfd import QUILT_PRESETS, render_quilt, save_quilt

    p = pv.Plotter(off_screen=True)
    p.add_mesh(pv.ParametricTorus())
    spec = QUILT_PRESETS["portrait"]
    quilt = render_quilt(p, spec)
    save_quilt(quilt, "torus", spec)        # -> torus_qs8x6a0.75.png
    p.close()

The saved quilt can be displayed on the device by dragging it into Looking
Glass Studio, or cast directly from Python via :func:`cast_quilt` if Looking
Glass Bridge is running on the machine driving the display.

Part of Quiltwright -- https://github.com/suchanek/quiltwright
Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

# pylint: disable=import-outside-toplevel  # pyvista/imageio-ffmpeg are optional extras and pillow is heavy; all lazy-loaded only when needed
import math
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from quiltwright.bridge import (
    BRIDGE_URL,
    cast_quilt,
    pause_quilt,
    resume_quilt,
    save_and_cast_quilt,
    stop_quilt,
)
from quiltwright.quilt import (
    LITIHOLO_SWEEP,
    QUILT_PRESETS,
    QuiltSpec,
    assemble_quilt,
    focal_distance_for_range,
    save_quilt,
    sweep_spec,
    view_disparity,
    view_offsets,
    window_shear,
)
from quiltwright.runtime import find_ffmpeg

# Re-exports: fleet and tests import these from lfd.  Names in __all__ are
# used, so ruff F401 does not treat the imports above as dead.
__all__ = [
    "BRIDGE_URL",
    "DEPTH_LABELS",
    "LITIHOLO_SWEEP",
    "QUILT_PRESETS",
    "QuiltSpec",
    "assemble_quilt",
    "cast_quilt",
    "depth_report",
    "find_ffmpeg",
    "focal_distance_for_range",
    "frame_and_focus",
    "pause_quilt",
    "render_quilt",
    "render_quilt_video",
    "resume_quilt",
    "save_and_cast_quilt",
    "save_quilt",
    "scene_depths",
    "stop_quilt",
    "sweep_spec",
    "camera_frame",
    "view_disparity",
    "view_offsets",
]

try:
    import pyvista as pv  # noqa: F401  (re-exported pattern matches voxel_viz)

    _PYVISTA_AVAILABLE = True
except ImportError:
    _PYVISTA_AVAILABLE = False


def _require_pyvista(fn_name: str) -> None:
    """Raise a clear ImportError if pyvista is not installed."""
    if not _PYVISTA_AVAILABLE:
        raise ImportError(
            f"{fn_name}() requires pyvista.\nInstall with:  poetry install --with viz"
        )


def frame_and_focus(
    plotter,
    *,
    fov: float = 14.0,
    margin: float = 1.15,
) -> tuple[float, float, float]:
    """Frame a PyVista scene tightly at its final view, and focus it.

    The PyVista counterpart to
    :func:`~quiltwright.cycles.frame_camera`, and the thing to call once the
    camera is pointing where you want it.  ``reset_camera()`` fits the
    *un-tilted* bounds, so once the view is tilted -- by an orbit, or an
    explicit ``camera_position`` -- that framing is too loose and the subject
    reads as small with a lot of empty margin: ask for a mountain hologram
    and get a speck.

    This re-fits from scratch at the final view direction.  The eight
    bounding-box corners are projected onto the camera's own right/up/forward
    axes, which accounts for foreshortening -- a flat, elongated terrain
    viewed obliquely needs far less distance than its bounding *sphere* would
    suggest -- giving the tightest distance that still keeps every corner in
    frame at the target FOV and window aspect.  The focal plane then goes at
    the harmonic mean of the resulting near and far depths, the same balance
    :func:`focal_distance_for_range` gives the POV-Ray path, measured from
    exact geometry rather than a rendered plane sweep.

    **The camera is modified**, unlike :func:`scene_depths`, which measures
    copies: position, view angle and focal point are all overwritten.  Only
    the view *direction* survives.  Having locked the camera here, pass
    ``fov=None`` to :func:`render_quilt` so it does not frame the scene a
    second time from scratch.

    :param plotter: A ``pv.Plotter`` with the data added, ``window_size``
        already set to the final render resolution (the aspect matters), and
        the camera pointing in the desired direction.
    :param fov: Vertical field of view to lock the camera to, in degrees.
        Must match what the render actually uses, or the depth budget
        describes a different camera than the one that renders.
    :param margin: Headroom beyond the tight corner-projected fit, as a
        fraction -- ``1.15`` leaves 15% so the subject does not touch the
        frame edges.
    :return: ``(near, far, focal_distance)`` in scene units, measured from
        the final camera position -- the numbers :func:`view_disparity`
        expects.
    :raises ImportError: If PyVista is not installed.
    """
    _require_pyvista("frame_and_focus")
    camera = plotter.camera
    position = np.asarray(camera.position, dtype="d")
    focus = np.asarray(camera.focal_point, dtype="d")
    up = np.asarray(camera.up, dtype="d")
    forward = focus - position
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    true_up = np.cross(right, forward)

    xmin, xmax, ymin, ymax, zmin, zmax = plotter.bounds
    lo = np.array([xmin, ymin, zmin], dtype="d")
    hi = np.array([xmax, ymax, zmax], dtype="d")
    centre = (lo + hi) / 2.0
    corners = np.array(
        [[x, y, z] for x in (xmin, xmax) for y in (ymin, ymax) for z in (zmin, zmax)],
        dtype="d",
    )
    offsets = corners - centre
    f = offsets @ forward  # signed depth of each corner relative to the centre
    r = offsets @ right
    u = offsets @ true_up

    win_w, win_h = plotter.window_size
    half_v = math.tan(math.radians(fov) / 2.0)
    half_h = half_v * (win_w / win_h)

    # Smallest distance-from-centre D such that every corner's angular extent
    # |u_i|/(D + f_i) (and |r_i|/half_h) still fits inside the FOV.
    needed = np.concatenate([np.abs(u) / half_v - f, np.abs(r) / half_h - f])
    distance = margin * max(float(needed.max()), 1.0)

    camera.position = tuple(centre - forward * distance)
    camera.view_angle = fov
    depths = distance + f  # each corner's distance from the new camera
    near = float(depths.min())
    far = float(depths.max())

    focal_distance = focal_distance_for_range(near, far)
    camera.focal_point = tuple(np.asarray(camera.position) + forward * focal_distance)
    return near, far, focal_distance


#: Labels used by :func:`depth_report` for the three depths it measures
#: itself.  Deliberately neutral -- a corpus renderer calls its far extent
#: "farthest foliage", a CAD one "back wall"; pass *labels* to say so.
DEPTH_LABELS: tuple[str, str, str] = (
    "nearest geometry",
    "focal plane (display surface)",
    "farthest geometry",
)


def scene_depths(
    plotter,
    *,
    fov: float | None = 14.0,
    zoom: float | None = None,
    labels: tuple[str, str, str] = DEPTH_LABELS,
) -> dict[str, float]:
    """Near, focal and far distances for the scene, as :func:`render_quilt` will see them.

    Measures the plotter's bounding box along the view axis, then applies the
    same framing :func:`render_quilt` applies before sweeping -- narrowing the
    FOV and dollying back, then the optional zoom dolly.  Reading the camera
    as-is instead is the tempting shortcut and it is wrong: the render's FOV
    and focal distance are both different by then, so the disparity computed
    from them describes a picture nobody is going to make.  Nothing is
    mutated; the arithmetic is done on copies.

    :param plotter: A ``pv.Plotter`` with the scene composed and the camera
        positioned as it will be for the render.
    :param fov: The vertical FOV that will be passed to :func:`render_quilt`.
        ``None`` keeps the plotter's current FOV, matching that argument.
    :param zoom: The zoom that will be passed to :func:`render_quilt`.
    :param labels: Names for the near, focal and far entries, in that order.
    :return: Labelled distances from the render camera, in scene units,
        ready to hand to :func:`~quiltwright.povray.format_depth_budget`.
    """
    _require_pyvista("scene_depths")
    camera = plotter.camera
    pos, focal, _right, _up, distance = camera_frame(camera)
    forward = (focal - pos) / distance

    # Mirror render_quilt's framing: narrow the FOV, dolly back to preserve
    # the framing, then apply the zoom dolly (VTK divides the distance).
    final_distance = distance
    if fov is not None:
        half_height = distance * math.tan(math.radians(camera.view_angle) / 2.0)
        final_distance = half_height / math.tan(math.radians(fov) / 2.0)
    if zoom is not None and zoom != 1.0:
        final_distance /= zoom

    # The camera retreats along -forward, so every measured depth grows by
    # the same shift; the focal plane sits at the new distance by definition.
    shift = final_distance - distance
    xmin, xmax, ymin, ymax, zmin, zmax = plotter.bounds
    corners = np.array(
        [[x, y, z] for x in (xmin, xmax) for y in (ymin, ymax) for z in (zmin, zmax)],
        dtype="d",
    )
    along = (corners - pos) @ forward
    return {
        labels[0]: float(along.min()) + shift,
        labels[1]: final_distance,
        labels[2]: float(along.max()) + shift,
    }


@dataclass(frozen=True)
class _Lens:
    """The two numbers :func:`format_depth_budget` reads off a camera."""

    fov: float
    focal_distance: float


def depth_report(
    plotter,
    spec: QuiltSpec,
    *,
    fov: float | None = 14.0,
    zoom: float | None = None,
    labels: tuple[str, str, str] = DEPTH_LABELS,
    extra_depths: Mapping[str, float] | None = None,
    soft_px: float = 5.5,
) -> str:
    """Depth budget for a PyVista scene, as a report to print before rendering.

    The PyVista counterpart to
    :func:`~quiltwright.povray.format_depth_budget`.  Pass the same *fov*
    and *zoom* you will pass to :func:`render_quilt`, so the numbers
    describe the render you are about to make.

    :param plotter: Plotter with the scene composed and the camera framed.
    :param spec: Quilt specification.
    :param fov: FOV that will be used for the render; see :func:`render_quilt`.
    :param zoom: Zoom that will be used for the render.
    :param labels: Names for the near, focal and far depths.
    :param extra_depths: Further labelled depths to include, e.g.
        ``{"sky": math.inf}`` for a backdrop at infinity.
    :param soft_px: Disparity above which a row is flagged as soft.
    :return: Multi-line report.
    """
    from quiltwright.povray import format_depth_budget

    depths = scene_depths(plotter, fov=fov, zoom=zoom, labels=labels)
    if extra_depths:
        depths.update(extra_depths)
    lens = _Lens(
        fov=float(plotter.camera.view_angle if fov is None else fov),
        focal_distance=float(depths[labels[1]]),
    )
    return format_depth_budget(spec, lens, depths, soft_px=soft_px)


def camera_frame(camera) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float]:
    """Decompose a vtkCamera into position, focal point, right/up basis, distance.

    :param camera: A ``pv.Camera`` / vtkCamera.
    :return: ``(position, focal_point, right, up, distance)``.
    """
    pos = np.asarray(camera.position, dtype="d")
    focal = np.asarray(camera.focal_point, dtype="d")
    up = np.asarray(camera.up, dtype="d")
    forward = focal - pos
    distance = float(np.linalg.norm(forward))
    forward /= distance
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    true_up = np.cross(right, forward)
    return pos, focal, right, true_up, distance


def _apply_off_axis_view(camera, base, offset: float, tile_aspect: float) -> None:
    """Position *camera* for one quilt view using an off-axis projection.

    The camera and focal point translate together by *offset* along the
    camera's right vector (no rotation -- view direction stays parallel), then
    the projection window centre is sheared so the original focal point stays
    centred on screen.  VTK's ``WindowCenter`` shifts the frustum by
    ``wcx * half_width`` at every depth, so setting
    ``wcx = -offset / half_width_at_focal_plane`` re-centres the focal plane
    exactly -- the standard Looking Glass off-axis recipe.

    :param camera: ``pv.Camera`` / vtkCamera to mutate.
    :param base: Tuple from :func:`camera_frame` of the *original* camera.
    :param offset: Lateral world-space offset for this view.
    :param tile_aspect: Width/height of the render viewport.
    """
    pos, focal, right, true_up, distance = base
    camera.position = tuple(pos + right * offset)
    camera.focal_point = tuple(focal + right * offset)
    camera.up = tuple(true_up)
    camera.SetWindowCenter(window_shear(offset, distance, camera.view_angle, tile_aspect), 0.0)


# ---------------------------------------------------------------------------
# Quilt rendering
# ---------------------------------------------------------------------------


def render_quilt(
    plotter,
    spec: QuiltSpec,
    *,
    view_cone: float | None = None,
    fov: float | None = 14.0,
    zoom: float | None = None,
) -> np.ndarray:
    """Render the plotter's scene into a quilt image.

    The plotter's current camera defines the centre view; its focal point
    becomes the holographic focal plane (the physical surface of the
    display).  Position the camera before calling -- e.g. via
    ``plotter.camera_position`` or ``plotter.reset_camera()`` -- exactly as
    you would for a normal screenshot.

    :param plotter: An *off-screen* ``pv.Plotter`` with the scene composed.
    :param spec: Quilt specification (grid, size, aspect, cone).
    :param view_cone: Override the spec's view cone in degrees.
    :param fov: Vertical field of view in degrees for the quilt cameras.
        Looking Glass recommends ~14° (matches real-world parallax at
        typical viewing distance); the camera is dollied back so the scene
        stays the same size in frame.  Pass ``None`` to keep the plotter's
        current FOV and distance.
    :param zoom: Optional camera zoom factor applied after framing, before
        the view sweep.  Values > 1 make the subject fill more of each tile,
        which is what drives perceived depth -- parallax is proportional to
        on-screen size, so a subject occupying a third of the frame yields a
        third of the available look-around.
    :return: ``uint8`` RGB array of shape ``(quilt_height, quilt_width, 3)``.
    """
    _require_pyvista("render_quilt")
    if view_cone is not None:
        spec = replace(spec, view_cone=view_cone)

    # Views are *captured* at the declared view aspect (= display aspect) so
    # the frustum is undistorted, then resampled into the tile.  For most
    # devices these match; some ideal quilts (e.g. 27") store views
    # anamorphically, with tile pixel aspect != view aspect.
    render_h = spec.tile_height
    render_w = round(render_h * spec.aspect)
    plotter.window_size = (render_w, render_h)
    if not plotter.camera.is_set:
        # Mirror pyvista's first-render behaviour (it only runs on
        # show()/screenshot(), after we have already read the camera).
        plotter.camera_position = plotter.renderer.get_default_cam_pos()
        plotter.reset_camera()
    plotter.render()

    camera = plotter.camera
    if fov is not None:
        # Narrow the FOV and dolly back so the focal plane stays the same
        # size in frame: new_distance = half_height / tan(fov/2).
        pos, focal, _, _, distance = camera_frame(camera)
        half_height = distance * math.tan(math.radians(camera.view_angle) / 2.0)
        new_distance = half_height / math.tan(math.radians(fov) / 2.0)
        forward = (focal - pos) / distance
        camera.position = tuple(focal - forward * new_distance)
        camera.view_angle = fov
    if zoom is not None and zoom != 1.0:
        # Dolly rather than narrow the view angle: pulling the camera in
        # magnifies the subject while preserving the FOV the parallax
        # geometry was built around, and the focal plane stays on the
        # display surface.  view_offsets() rescales with the new distance,
        # so the angular look-around is unchanged.
        camera.Dolly(zoom)
    base = camera_frame(camera)
    distance = base[4]
    offsets = view_offsets(spec, distance)
    render_aspect = render_w / render_h

    def views():
        for offset in offsets:
            _apply_off_axis_view(camera, base, float(offset), render_aspect)
            # The dolly + lateral sweep move the camera well outside the range
            # VTK computed for the original position; re-fit it to the scene.
            plotter.renderer.reset_camera_clipping_range()
            # screenshot() alone returns the previous framebuffer; force a
            # render so each view reflects this view's camera.
            plotter.render()
            yield plotter.screenshot(None, return_img=True)

    quilt = assemble_quilt(views(), spec)

    # Restore the centre view so the plotter is reusable afterwards.
    _apply_off_axis_view(camera, base, 0.0, render_aspect)
    camera.SetWindowCenter(0.0, 0.0)
    plotter.renderer.reset_camera_clipping_range()
    return quilt


# ---------------------------------------------------------------------------
# Quilt video (turntable / animated holograms)
# ---------------------------------------------------------------------------


def _encode_args(spec: QuiltSpec, crf: int) -> list[str]:
    """ffmpeg output arguments for the official quilt-video requirements.

    MP4 with ``yuv420p`` pixel format is required by Looking Glass players.
    H.264 is fine for quilts up to 6000 px on their longest side (Portrait,
    Go, 16" portrait); anything larger uses HEVC.  yuv420p also needs even
    dimensions, so odd quilt sizes are padded by one pixel.
    """
    codec = "libx265" if max(spec.quilt_width, spec.quilt_height) > 6000 else "libx264"
    args = ["-vcodec", codec, "-crf", str(crf), "-pix_fmt", "yuv420p"]
    if spec.quilt_width % 2 or spec.quilt_height % 2:
        args += ["-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2"]
    return args


def render_quilt_video(
    plotter,
    spec: QuiltSpec,
    out_stem: str | Path,
    *,
    n_frames: int = 180,
    fps: int = 24,
    orbit_degrees: float = 360.0,
    view_cone: float | None = None,
    fov: float | None = 14.0,
    zoom: float | None = None,
    crf: int = 18,
    on_frame=None,
    progress: bool = True,
) -> Path:
    """Render an animated quilt video (default: a full turntable orbit).

    Renders one quilt per frame, rotating the camera about the focal point
    between frames, then encodes the sequence to MP4 per the Looking Glass
    quilt-video spec (``yuv420p``; H.264, or HEVC for 8K quilts).  The
    filename carries the ``_qs<cols>x<rows>a<aspect>`` suffix so Studio /
    Bridge auto-detect playback settings.

    Note the cost: a Portrait video renders ``n_frames x 48`` views.

    :param plotter: An *off-screen* ``pv.Plotter`` with the scene composed.
    :param spec: Quilt specification (grid, size, aspect, cone).
    :param out_stem: Output path; quilt suffix + ``.mp4`` are appended.
    :param n_frames: Number of video frames (with *fps* sets loop duration).
    :param orbit_degrees: Total camera orbit over the clip; 360 loops
        seamlessly.  Pass 0 to disable the turntable (use *on_frame*).
    :param view_cone: Override the spec's view cone in degrees.
    :param fov: Per-view vertical FOV; see :func:`render_quilt`.
    :param zoom: Camera dolly factor; see :func:`render_quilt`.
    :param crf: x264/x265 quality (lower = better; 15-20 sensible).
    :param on_frame: Optional ``callback(frame_index)`` invoked before each
        frame renders -- mutate the scene here for custom animation.
    :param progress: Print a progress line while rendering.
    :return: Path of the quilt MP4 written.
    """
    import subprocess
    import tempfile

    _require_pyvista("render_quilt_video")
    ffmpeg = find_ffmpeg()

    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            "render_quilt_video() requires pillow.\nInstall with:  poetry install --with viz"
        ) from exc

    out_stem = Path(out_stem)
    if out_stem.suffix.lower() == ".mp4":
        out_stem = out_stem.with_suffix("")
    out_path = out_stem.parent / spec.filename(out_stem.name, ext="mp4")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    step = orbit_degrees / n_frames if n_frames else 0.0
    with tempfile.TemporaryDirectory(prefix="quilt_frames_") as tmp:
        for i in range(n_frames):
            if on_frame is not None:
                on_frame(i)
            # Zoom only on the first frame: render_quilt leaves the camera at
            # the dollied distance, and Azimuth() preserves it, so re-applying
            # it every frame would compound into a creeping zoom-in.
            quilt = render_quilt(
                plotter, spec, view_cone=view_cone, fov=fov, zoom=zoom if i == 0 else None
            )
            Image.fromarray(quilt).save(f"{tmp}/frame{i:05d}.png")
            plotter.camera.Azimuth(step)
            if progress:
                print(f"\r  quilt frame {i + 1}/{n_frames}", end="", flush=True)
        if progress:
            print()

        cmd = [
            ffmpeg,
            "-y",
            "-framerate",
            str(fps),
            "-i",
            f"{tmp}/frame%05d.png",
            *_encode_args(spec, crf),
            str(out_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed ({result.returncode}):\n{result.stderr[-2000:]}")
    return out_path
