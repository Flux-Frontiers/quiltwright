"""
POV-Ray Quilt Renderer
======================

Drives the `POV-Ray <https://www.povray.org/>`_ ray-tracer to produce *quilts*
for Looking Glass holographic displays, so existing ``.pov`` scenes can be
shown as holograms without being ported to another renderer.

The scene file is never modified.  Rendering wraps it::

    #include "<your scene>.pov"
    camera { ... }               // off-axis camera for one view

POV-Ray uses the *last* camera statement it parses and warns about the
earlier ones, so appending a camera overrides whatever the scene declared
while leaving its geometry and, by default, its lighting untouched.  One
wrapper is written per view, each carrying that view's camera.

Optional *lighting* on :func:`render_pov_quilt` appends a parallel sun
(and prefix ``#declare QW_*`` so a scene can opt in).  That is real sun
altitude/azimuth -- not POV-Ray's ``clock``, which is the animation
parameter (``+K``) and has nothing to do with wall-clock time.

**Off-axis projection.**  POV-Ray builds its frustum from ``location`` (the
eye), ``direction`` (which places the centre of the image plane) and
``right``/``up`` (which span it), and it does *not* re-orthogonalise those
vectors.  Tilting ``direction`` while holding ``right`` and ``up`` fixed
therefore shears the frustum, leaving the image plane parallel to itself --
exactly the projection a light-field display needs.  Using ``look_at``
instead would *rotate* the camera ("toe-in"), which introduces vertical
parallax and keystone distortion and prevents the views from fusing.

For an eye offset ``s`` along the unit right vector ``r``, with focal
distance ``Z`` and image-plane distance ``D``:

.. code-block:: text

    location  = L + s*r
    direction = D*f - (s*D/Z)*r

The subtracted term slides the image-plane centre back onto the original
view axis, so the look-at point stays pinned to the centre of every view.
That point is the holographic focal plane: it lands on the physical glass,
with nearer geometry floating in front and farther geometry behind.

POV-Ray emits ``Camera vectors are not perpendicular`` for such a camera.
That warning is expected and benign -- it is the shear.

**Framing an existing scene.**  A scene composed as a still needs three
things changed before it sweeps well, and all three are measured from the
scene rather than guessed: the focal plane moves to the distance that
balances the disparity budget, the eye slides to the middle of whatever
lateral corridor the geometry leaves, and the view cone is derived from the
clearance that remains.  :meth:`PovCamera.aimed` performs the first two
without disturbing the view direction or the lens, :class:`Clearance` holds
the measured corridor and the cone it permits, and
:func:`format_depth_budget` reports the result before the ray-tracer is
asked to spend an hour on it.

**Requirements** -- a ``povray`` binary on ``PATH`` (``brew install povray``),
plus pillow for quilt assembly (``poetry install --with viz``).

Typical usage::

    from quiltwright.quilt import QUILT_PRESETS, save_quilt
    from quiltwright.povray import PovCamera, render_pov_quilt

    camera = PovCamera(location=(35, 18.5, 0), look_at=(35, 20, 58), fov=14)
    spec = QUILT_PRESETS["portrait"]
    quilt = render_pov_quilt("museum.pov", spec, camera,
                             include_paths=["../myinclude"])
    save_quilt(quilt, "museum", spec)   # -> museum_qs8x6a0.75.png

Part of Quiltwright -- https://github.com/Flux-Frontiers/quiltwright
Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from quiltwright.quilt import (
    HasLens,
    QuiltSpec,
    assemble_quilt,
    sweep_extent,
    view_disparity,
    view_offsets,
    window_shear,
)
from quiltwright.runtime import COURTESY_CORES_HELD_BACK
from quiltwright.runtime import triple as _triple

#: Environment variable overriding which POV-Ray binary is used.
POVRAY_ENV = "POVRAY_BINARY"


def _find_povray(binary: str | None = None) -> str:
    """Locate the POV-Ray executable.

    :param binary: Explicit path or command name; falls back to the
        ``POVRAY_BINARY`` environment variable, then ``povray`` on ``PATH``.
    :return: Path to the executable.
    :raises RuntimeError: If no POV-Ray binary can be found.
    """
    candidate = binary or os.environ.get(POVRAY_ENV) or "povray"
    found = shutil.which(candidate)
    if found:
        return found
    raise RuntimeError(
        f"POV-Ray binary {candidate!r} not found.\n"
        "Install it (macOS:  brew install povray) or set "
        f"{POVRAY_ENV} to its full path."
    )


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PovCamera:
    """A POV-Ray camera in ``look_at`` form, plus the quilt's focal geometry.

    The *look_at* point defines the holographic focal plane, so aim it at
    whatever should sit on the surface of the glass.  Geometry closer to the
    camera floats out of the display; geometry beyond it recedes.

    **Coordinates here are POV-Ray's own -- left-handed -- not the right-handed
    world :mod:`quiltwright.povgen` authors scenes in.**  Nothing converts a
    camera you construct yourself: :func:`camera_block` emits it verbatim.
    Only :func:`~quiltwright.povgen.pov_camera_from_plotter` converts, by
    running :func:`~quiltwright.povgen.to_pov` over the plotter's position,
    focal point and up vector.

    So a scene written with the default ``handedness="flip-z"`` needs its
    camera converted too::

        from quiltwright.povgen import to_pov

        camera = PovCamera(
            location=to_pov((0.0, -8.0, 3.0)),   # right-handed, +z up
            look_at=to_pov((0.0, 0.0, 3.0)),
            sky=to_pov((0.0, 0.0, 1.0)),
        )

    Skip that and the geometry sits at negative *z* while the lens aims at
    positive *z*: POV-Ray renders a clean picture of empty space.  Nothing in
    the scene file looks wrong, and any check comparing the camera against the
    right-handed bounds it was derived from will pass.

    :param location: Eye position ``(x, y, z)``, in POV-Ray coordinates.
    :param look_at: Point the camera is aimed at, in POV-Ray coordinates.
        Becomes the focal plane.
    :param sky: Up-hint used to build the camera basis, matching POV-Ray's
        ``sky`` vector, in POV-Ray coordinates.  Must not be parallel to the
        view direction.  A ``+z``-up right-handed scene wants ``(0, 0, -1)``
        here, which is what ``to_pov((0, 0, 1))`` returns.
    :param fov: *Vertical* field of view in degrees.  Looking Glass
        recommends ~14° for object-centric content, where the camera is
        dollied in until the subject fills the frame.  Do not carry that
        number over to architectural interiors: a narrow FOV *magnifies*
        parallax along with everything else (see
        :func:`~quiltwright.lfd.view_disparity`), so a room shot at 14° ghosts
        where the same room at its native wide angle fuses cleanly.  Set the
        depth budget with the focal plane and the view cone instead, and
        keep the scene's own FOV.
    """

    location: tuple[float, float, float]
    look_at: tuple[float, float, float]
    sky: tuple[float, float, float] = (0.0, 1.0, 0.0)
    fov: float = 14.0

    @property
    def focal_distance(self) -> float:
        """Distance from the eye to the focal plane, in scene units."""
        return float(np.linalg.norm(np.asarray(self.look_at, dtype="d") - self.location))

    def basis(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Orthonormal camera basis ``(forward, right, up)``.

        POV-Ray is left-handed -- with ``up`` at ``+y`` and ``direction`` at
        ``+z``, ``right`` is ``+x`` -- which is what ``right = sky x forward``
        reproduces.  Getting this ordering wrong mirrors the view sweep and
        inverts the hologram's depth.

        :return: Three unit vectors as ``(3,)`` arrays.
        :raises ValueError: If the camera is degenerate (zero-length view
            direction, or *sky* parallel to it).
        """
        loc = np.asarray(self.location, dtype="d")
        forward = np.asarray(self.look_at, dtype="d") - loc
        norm = np.linalg.norm(forward)
        if norm == 0:
            raise ValueError("PovCamera.location and look_at are identical")
        forward = forward / norm

        right = np.cross(np.asarray(self.sky, dtype="d"), forward)
        norm = np.linalg.norm(right)
        if norm < 1e-12:
            raise ValueError(
                f"PovCamera.sky {self.sky} is parallel to the view direction; "
                "pick a different up-hint"
            )
        right = right / norm
        return forward, right, np.cross(forward, right)

    def image_plane_distance(self) -> float:
        """``|direction|`` reproducing *fov* for a unit-height image plane.

        The emitted camera sets ``up`` to a unit vector, so the image plane
        is one unit tall and ``tan(fov/2) = 0.5 / |direction|``.
        """
        return 0.5 / math.tan(math.radians(self.fov) / 2.0)

    @classmethod
    def aimed(
        cls,
        location: Sequence[float],
        aim: Sequence[float],
        *,
        fov: float,
        focal_distance: float | None = None,
        lateral_shift: float = 0.0,
        sky: tuple[float, float, float] = (0.0, 1.0, 0.0),
    ) -> PovCamera:
        """Adopt a scene's own viewpoint, re-aimed and re-centred for a sweep.

        A scene's camera was composed for a still: its aim point was chosen
        for framing, and its eye sits wherever the composition wanted it.
        Neither survives contact with a quilt unedited -- the focal plane
        wants the distance that balances the disparity budget (see
        :func:`~quiltwright.lfd.focal_distance_for_range`), and inside an
        interior the eye wants to sit in the middle of whatever lateral
        corridor the walls leave (see :class:`Clearance`).

        Both are changed here without touching the view *direction* or the
        lens: the new look-at point stays on the original aim ray, so the
        scene is framed as its author framed it.

        :param location: The scene's eye position.
        :param aim: The scene's aim point.  Used for direction only unless
            *focal_distance* is ``None``.
        :param fov: Vertical field of view in degrees -- usually the scene's
            own, see :class:`PovCamera`.
        :param focal_distance: Distance along the aim ray to place the focal
            plane.  Defaults to the scene's own aim distance.
        :param lateral_shift: Distance to slide the eye along the camera's
            right vector before re-aiming.  The look-at point slides with
            it, so the view direction is unchanged.
        :param sky: Up-hint, as on :class:`PovCamera`.
        :return: The centre-view camera.
        :raises ValueError: If the camera is degenerate (see :meth:`basis`)
            or *focal_distance* is not positive.
        """
        base = cls(location=_triple(location), look_at=_triple(aim), sky=sky, fov=fov)
        forward, right, _ = base.basis()
        distance = base.focal_distance if focal_distance is None else float(focal_distance)
        if distance <= 0:
            raise ValueError(f"focal_distance must be positive, got {distance}")
        eye = np.asarray(base.location, dtype="d") + right * float(lateral_shift)
        return cls(
            location=_triple(eye),
            look_at=_triple(eye + forward * distance),
            sky=sky,
            fov=fov,
        )


def _vec(v: Iterable[float]) -> str:
    """Format a vector as POV-Ray ``<x, y, z>`` syntax.

    Emitted at full float64 precision: the shear term is a small correction
    to a large ``direction`` vector, and rounding it costs focal-plane
    accuracy in proportion to the scene's scale.
    """
    return "<" + ", ".join(f"{float(c):.17g}" for c in v) + ">"


def camera_block(camera: PovCamera, offset: float, aspect: float) -> str:
    """Emit the POV-Ray ``camera { }`` statement for one quilt view.

    :param camera: Base (centre-view) camera.
    :param offset: Lateral eye offset along the camera's right vector, in
        scene units, from :func:`~quiltwright.lfd.view_offsets`.
    :param aspect: Width / height of the rendered view.
    :return: A POV-Ray camera statement.
    """
    forward, right, up = camera.basis()
    dist = camera.image_plane_distance()
    eye = np.asarray(camera.location, dtype="d") + right * offset
    # Shear: slide the image-plane centre back onto the original view axis so
    # the focal plane stays pinned across the sweep.  window_shear is in
    # half-widths; the image plane is ``aspect`` wide, so the world-space
    # slide along ``right`` is ``shear * aspect / 2``.  Never emit `angle`
    # here -- it would override |direction| and silently undo this.
    shear = window_shear(offset, camera.focal_distance, camera.fov, aspect)
    direction = forward * dist + right * (shear * aspect / 2.0)
    return (
        "camera {\n"
        f"  location  {_vec(eye)}\n"
        f"  direction {_vec(direction)}\n"
        f"  right     {_vec(right * aspect)}\n"
        f"  up        {_vec(up)}\n"
        "}\n"
    )


# Appearance presets for Dynamic Desktop stills.  Azimuth is degrees from
# +Z toward +X in POV-Ray's Y-up frame -- the same convention as
# :func:`sun_direction`.  Light is a high, hot key; dark is a moon fill
# plus fog (see :func:`lighting_block`) so scene lights do not wash out
# the night look.
APPEARANCE_SUN: dict[str, tuple[float, float]] = {
    "light": (55.0, 120.0),
    "dark": (-15.0, 280.0),
}


def sun_direction(altitude: float, azimuth: float) -> tuple[float, float, float]:
    """Unit vector pointing *toward* the sun, POV-Ray Y-up.

    :param altitude: Degrees above the Y = 0 plane (horizon).  90 is +Y.
    :param azimuth: Degrees from +Z toward +X, ``[0, 360)``.
    :return: ``(x, y, z)`` of length 1.
    """
    alt = math.radians(altitude)
    az = math.radians(azimuth)
    cos_alt = math.cos(alt)
    return (math.sin(az) * cos_alt, math.sin(alt), math.cos(az) * cos_alt)


def _sun_color(altitude: float, *, appearance: str | None = None) -> tuple[float, float, float]:
    """RGB intensity for a parallel sun at *altitude* degrees.

    ``appearance="dark"`` is a cool moon fill; fog in :func:`lighting_block`
    does the night separation.  Bare *altitude* (solar frames) uses a
    milder curve so a high sun does not blow out a scene that already has
    its own key light.
    """
    if appearance == "dark":
        # Cool moonlight -- fog (below) does most of the night separation.
        return (0.35, 0.42, 0.70)
    if altitude >= 20:
        return (0.85, 0.78, 0.68)
    if altitude >= 6:
        t = (altitude - 6) / 14.0
        return (0.9, 0.7 + 0.15 * t, 0.45 + 0.3 * t)
    if altitude >= -6:
        t = (altitude + 6) / 12.0
        return (0.7 * t + 0.15, 0.3 * t + 0.12, 0.15 * t + 0.25)
    return (0.18, 0.22, 0.38)


def lighting_declares(
    *,
    appearance: str | None = None,
    sun: tuple[float, float] | None = None,
) -> str:
    """``#declare QW_*`` prefix so a scene can honour the sun without a parser.

    :param appearance: ``"light"`` or ``"dark"``, or ``None``.
    :param sun: ``(altitude, azimuth)`` overriding the appearance preset.
    :return: SDL to emit *before* the ``#include``, or ``""``.
    """
    if appearance is None and sun is None:
        return ""
    if appearance is not None and appearance not in APPEARANCE_SUN:
        raise ValueError(f"appearance must be 'light' or 'dark', got {appearance!r}")
    alt, az = sun if sun is not None else APPEARANCE_SUN[appearance or "light"]
    flag = 0 if appearance == "dark" else 1
    return (
        f"#declare QW_Appearance = {flag};\n"
        f"#declare QW_SunAltitude = {float(alt):.10g};\n"
        f"#declare QW_SunAzimuth = {float(az):.10g};\n"
    )


def lighting_block(
    camera: PovCamera,
    *,
    appearance: str | None = None,
    sun: tuple[float, float] | None = None,
) -> str:
    """Lighting appended after the camera for Dynamic Desktop stills.

    ``appearance="light"`` leaves the scene alone: an additive key on top of
    an authored white light washes the plate out.  ``appearance="dark"``
    adds a cool moon plus fog so Dark Mode still reads as night without
    editing the scene.  Pass *sun* ``(altitude, azimuth)`` for solar frames
    that need an explicit parallel sun.  This is real sun position -- not
    POV-Ray's ``clock``.

    :param camera: Centre-view camera; ``look_at`` is ``point_at``.
    :param appearance: ``"light"`` or ``"dark"``, or ``None``.
    :param sun: ``(altitude, azimuth)``; defaults to the appearance preset
        when *appearance* is ``"dark"``.
    :return: POV-Ray SDL, or ``""``.
    """
    if appearance is None and sun is None:
        return ""
    if appearance is not None and appearance not in APPEARANCE_SUN:
        raise ValueError(f"appearance must be 'light' or 'dark', got {appearance!r}")
    # Light Mode = scene as authored.  Declares still go out via
    # lighting_declares so a scene can branch on QW_Appearance.
    if appearance == "light" and sun is None:
        return ""
    alt, az = sun if sun is not None else APPEARANCE_SUN[appearance or "light"]
    direction = np.asarray(sun_direction(alt, az), dtype="d")
    look = np.asarray(camera.look_at, dtype="d")
    distance = max(camera.focal_distance * 8.0, 1.0)
    location = look + direction * distance
    r, g, b = _sun_color(alt, appearance=appearance)
    parts = [
        "// quiltwright lighting: parallel sun (not POV-Ray clock)\n"
        "light_source {\n"
        f"  {_vec(location)} color rgb <{r:.5g}, {g:.5g}, {b:.5g}>\n"
        "  parallel\n"
        f"  point_at {_vec(look)}\n"
        "}\n"
    ]
    if appearance == "dark":
        # Soften the scene's own lights without burying the subject.  Fog
        # distance scales with focal distance; ~1.2x keeps Dark Mode
        # readable on a Mac laptop while still separating from Light.
        fog_d = max(camera.focal_distance * 1.2, 1.0)
        parts.append(
            "background { color rgb <0.04, 0.05, 0.10> }\n"
            "global_settings { ambient_light rgb <0.08, 0.09, 0.14> }\n"
            "fog {\n"
            "  fog_type 1\n"
            f"  distance {fog_d:.6g}\n"
            "  color rgb <0.05, 0.06, 0.12>\n"
            "}\n"
        )
    return "".join(parts)


def _wrapper_source(
    scene_path: Path,
    index: int,
    n_views: int,
    offset: float,
    camera: PovCamera,
    aspect: float,
    *,
    lighting_prefix: str = "",
    lighting_suffix: str = "",
) -> str:
    """One per-view wrapper: optional lighting declares, include, camera, sun."""
    return (
        lighting_prefix + f'#include "{scene_path}"\n'
        f"// view {index + 1}/{n_views}, "
        f"eye offset {offset:+.6g} scene units\n"
        + camera_block(camera, offset, aspect)
        + lighting_suffix
    )


# ---------------------------------------------------------------------------
# Framing: wall clearance, depth budget
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Clearance:
    """The lateral corridor an interior leaves for the view sweep.

    This is the constraint peculiar to enclosed scenes, and the one that
    bites hardest.  A cone chosen without checking it does not fail loudly:
    the centre view -- the one you preview -- is perfect, while the outer
    views quietly render the unlit back face of a wall.

    Measure the corridor by rendering at candidate eye offsets along the
    camera's right vector and watching for the frame to collapse.  It is
    rarely symmetric about the scene's own eye position, hence *centre*,
    which slides the eye to the middle of the room before the sweep starts.

    :param left: Most negative usable offset along the right vector, in
        scene units.
    :param right: Most positive usable offset.
    :param margin: Safety margin held back at each end.  Walls are not
        perfectly planar and grazing one dims the outer views well before
        the camera actually passes through it.
    """

    left: float
    right: float
    margin: float = 0.0

    def __post_init__(self) -> None:
        if self.right <= self.left:
            raise ValueError(f"clearance right ({self.right}) must exceed left ({self.left})")
        if self.margin < 0:
            raise ValueError(f"clearance margin must be non-negative, got {self.margin}")

    @property
    def centre(self) -> float:
        """Offset that puts the eye in the middle of the corridor."""
        return (self.left + self.right) / 2.0

    @property
    def half_width(self) -> float:
        """Usable travel to either side of :attr:`centre`, net of *margin*."""
        return (self.right - self.left) / 2.0 - self.margin

    def cone(self, focal_distance: float) -> float:
        """Widest view cone whose outermost eye still clears the walls.

        ``cone = 2 * atan((half_width) / focal_distance)``.  Narrowing the
        cone to fit costs less than it looks: with the focal plane at the
        harmonic mean of the depth range, disparity at the extremes tracks
        the physical baseline and the scene's depth range, so trading cone
        for clearance trades look-around, not sharpness.

        :param focal_distance: Camera-to-focal-plane distance, in scene units.
        :return: Total sweep in degrees.
        :raises ValueError: If the margin has consumed the whole corridor,
            or *focal_distance* is not positive.
        """
        if focal_distance <= 0:
            raise ValueError(f"focal_distance must be positive, got {focal_distance}")
        if self.half_width <= 0:
            raise ValueError(
                f"clearance margin {self.margin} leaves no room in a corridor "
                f"of width {self.right - self.left}"
            )
        return 2.0 * math.degrees(math.atan(self.half_width / focal_distance))

    def fits(self, spec: QuiltSpec, focal_distance: float) -> bool:
        """True if the sweep *spec* asks for stays inside the corridor.

        A cone from :meth:`cone` lands the sweep exactly on
        :attr:`half_width`, where rounding can put it a few ulps over, so
        the comparison is made to within a relative tolerance rather than
        reporting a wall strike for the cone this class just derived.
        """
        sweep = sweep_extent(spec, focal_distance)
        return sweep <= self.half_width or math.isclose(sweep, self.half_width, rel_tol=1e-9)


def depth_budget(
    spec: QuiltSpec, camera: HasLens, depths: Mapping[str, float]
) -> list[tuple[str, float, float]]:
    """Adjacent-view disparity at each depth of interest.

    A thin pairing of :func:`~quiltwright.quilt.view_disparity` with the
    labelled depths measured from a scene, kept separate from
    :func:`format_depth_budget` so the numbers can be asserted on rather
    than only printed.

    :param spec: Quilt specification.
    :param camera: Centre-view camera; a :class:`~quiltwright.quilt.QuiltCamera`
        or anything with ``fov`` and ``focal_distance``
        (:class:`~quiltwright.quilt.HasLens`).
    :param depths: Labelled distances from the camera, in scene units.  Use
        ``math.inf`` for sky or a backdrop at infinity.
    :return: ``(label, depth, disparity_px)`` in the order given.
    """
    return [
        (label, depth, view_disparity(spec, camera.fov, camera.focal_distance, depth))
        for label, depth in depths.items()
    ]


def format_depth_budget(
    spec: QuiltSpec,
    camera: HasLens,
    depths: Mapping[str, float],
    *,
    clearance: Clearance | None = None,
    soft_px: float = 5.5,
    indent: str = "  ",
) -> str:
    """Render the sweep geometry and depth budget as a report.

    Print this before committing to a render: it is where a blown disparity
    budget or a sweep that walks through a wall shows up, at no cost, rather
    than after the ray-tracer has spent an hour on it.

    :param spec: Quilt specification.
    :param camera: Centre-view camera; a :class:`~quiltwright.quilt.QuiltCamera`
        or anything with ``fov`` and ``focal_distance``
        (:class:`~quiltwright.quilt.HasLens`).
    :param depths: Labelled depths, as for :func:`depth_budget`.
    :param clearance: Measured lateral corridor, if the scene is enclosed.
        When given, the sweep is checked against it and a warning emitted if
        the outer views would leave the room.
    :param soft_px: Disparity above which a row is flagged as soft.  Roughly
        4-5 px is the practical ceiling; past ~8 px expect visible ghosting.
    :param indent: Leading whitespace for the outermost lines.
    :return: A multi-line report, without a trailing newline.
    """
    z = camera.focal_distance
    sweep = sweep_extent(spec, z)
    lines = [
        f"{indent}focal plane      {z:.1f} units",
        f"{indent}view cone        {spec.view_cone:.1f} deg over {spec.n_views} views",
    ]
    if clearance is None:
        lines.append(f"{indent}eye sweep        +/-{sweep:.1f} units")
    else:
        lines.append(
            f"{indent}eye sweep        +/-{sweep:.1f} units "
            f"(clearance +/-{clearance.half_width:.1f} after {clearance.margin:.1f} margin)"
        )
        if not clearance.fits(spec, z):
            lines.append(f"{indent}  WARNING: sweep exceeds clearance; outer views will be black")

    lines.append(f"{indent}adjacent-view disparity:")
    for label, depth, px in depth_budget(spec, camera, depths):
        flag = "" if px <= soft_px else "  <- soft"
        lines.append(f"{indent}  {label:<18} {depth:>8.1f}  {px:5.2f} px{flag}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Depth probing
# ---------------------------------------------------------------------------

#: Colour of the plane-sweep marker, chosen to be absent from real scenes.
PROBE_MARKER = (1.0, 0.0, 1.0)


def _probe_wrapper(scene_path: Path, camera: PovCamera, aspect: float, distance: float) -> str:
    """Scene, camera, and an opaque marker plane *distance* units out.

    The plane is perpendicular to the view axis, so everything beyond it is
    hidden and the frame's remaining non-marker pixels are exactly the
    geometry in front of it.  ``ambient 1 diffuse 0`` keeps it self-lit --
    the scene's own lights must not tint the thing being measured -- and
    ``no_shadow`` keeps it from darkening what it is meant to reveal.

    :param scene_path: Absolute path to the scene, pulled in by ``#include``.
    :param camera: Camera to probe through.
    :param aspect: Frame aspect ratio (width / height).
    :param distance: Distance from the eye along the view axis.
    :return: The wrapper scene source.
    """
    forward = camera.basis()[0]
    # Plane through eye + forward*distance, normal forward:  n.p = n.eye + d.
    offset = float(np.dot(forward, np.asarray(camera.location, dtype="d")) + distance)
    normal = ", ".join(f"{c:.17g}" for c in forward)
    return (
        f'#include "{scene_path}"\n'
        + camera_block(camera, 0.0, aspect)
        + f"plane {{ <{normal}>, {offset:.17g}\n"
        f"  pigment {{ color rgb <{PROBE_MARKER[0]}, {PROBE_MARKER[1]}, {PROBE_MARKER[2]}> }}\n"
        "  finish { ambient 1 diffuse 0 } no_shadow }\n"
    )


def depth_sweep(
    scene: str | Path,
    camera: PovCamera,
    distances: Iterable[float],
    *,
    include_paths: Sequence[str | Path] = (),
    width: int = 320,
    height: int = 180,
    quality: int = 11,
    threads: int | None = None,
    binary: str | None = None,
    extra_args: Sequence[str] = (),
    progress: bool = True,
) -> list[tuple[float, float]]:
    """Trace a scene's cumulative depth histogram by plane sweep.

    The depth budget wants two numbers from a scene -- where its nearest
    content sits and where its farthest *structured* content ends -- and
    guessing them costs a render to find out.  This measures them: an opaque,
    self-lit plane slides along the view axis at distance ``d``, hiding
    everything beyond it, so the fraction of the frame that is *not* the
    marker colour is the fraction occupied by geometry nearer than ``d``::

        d= 31   0.2%   <- nearest geometry appears
        d= 47  35.1%
        d= 96  93.9%   <- 95% of everything occludable
        d=inf  93.9%   <- the remaining 6.1% is sky, at effective infinity

    Three cautions, each learned the hard way:

    *Render at the quality you will ship.*  POV-Ray disables transparency and
    refraction below ``+Q8``, so a cheap probe at ``+Q3`` reports a room with
    no windows and no sky at all.

    *Measure through the camera you will render with.*  A hologram's eye is
    usually not the scene's own; see :meth:`PovCamera.aimed`.

    *Sky is not far content.*  A backdrop at infinity never occludes, so it
    shows up as a residual that never closes.  Leave it out of the near/far
    balance -- it is low-contrast and can afford the disparity.

    :param scene: Scene to probe.  Not modified.
    :param camera: Camera to measure through.
    :param distances: Distances along the view axis to test, in scene units.
    :param include_paths: Extra ``#include`` directories.  The scene's own
        directory is always added.
    :param width: Probe frame width in pixels.  Small is fine -- this is a
        pixel *count*, not an image anyone looks at.
    :param height: Probe frame height in pixels.
    :param quality: POV-Ray ``+Q``.  Keep at 8 or above, or glass reads solid.
    :param threads: POV-Ray ``+WT``.  ``None`` applies the courtesy cap
        described in :func:`resolve_work_threads` -- a sweep is hundreds of
        small frames back to back, and taking every core for the duration is
        as rude as a quilt doing it.
    :param binary: POV-Ray executable; defaults to the usual search.
    :param extra_args: Extra POV-Ray arguments, e.g. ``["+MV3.1"]`` for a
        pre-2000 scene carrying no ``#version`` pragma of its own.
    :param progress: Print a one-line probe counter.
    :return: ``(distance, fraction_in_front)`` pairs, in the order given.
    :raises FileNotFoundError: If the scene does not exist.
    :raises RuntimeError: If POV-Ray fails, or the calibration frame is not
        uniformly the marker colour -- which means geometry is already inside
        the near plane and every reading would be measured against it.
    """
    from PIL import Image

    povray = _find_povray(binary)
    scene_path = Path(scene).expanduser().resolve()
    if not scene_path.is_file():
        raise FileNotFoundError(f"scene not found: {scene_path}")
    library_paths = [scene_path.parent, *(Path(p).expanduser().resolve() for p in include_paths)]
    aspect = width / height

    # Same courtesy cap the quilt renderers apply; an explicit +WT wins.
    if not any(str(a).startswith("+WT") for a in extra_args):
        capped = resolve_work_threads(threads)
        if capped is not None:
            extra_args = [*extra_args, f"+WT{capped}"]

    with tempfile.TemporaryDirectory(prefix="qw_depth_probe_") as tmp:
        workdir = Path(tmp)
        wrapper = workdir / "probe.pov"
        out_png = workdir / "probe.png"

        def frame(distance: float) -> np.ndarray:
            wrapper.write_text(_probe_wrapper(scene_path, camera, aspect, distance))
            out_png.unlink(missing_ok=True)
            _render_view(
                povray,
                wrapper,
                out_png,
                width,
                height,
                library_paths,
                None,  # no antialiasing: this counts pixels, it does not show them
                quality,
                extra_args,
                workdir,
            )
            return np.asarray(Image.open(out_png).convert("RGB")).astype(int)

        calibration = frame(1.0)
        if calibration.std(axis=(0, 1)).max() > 2:
            raise RuntimeError(
                "calibration frame is not uniform: something is in front of the "
                "probe plane at d=1, so the sweep would measure against it. "
                "Check the camera position."
            )
        marker = calibration.reshape(-1, 3).mean(0)

        rows = []
        distances = list(distances)
        for i, d in enumerate(distances):
            image = frame(float(d))
            fraction = float((np.abs(image - marker).sum(-1) > 30).mean())
            rows.append((float(d), fraction))
            if progress:
                print(
                    f"\r  probe {i + 1}/{len(distances)}  d={d:.0f} {fraction * 100:5.1f}%",
                    end="",
                    flush=True,
                )
        if progress:
            print()
    return rows


def summarise_depth_sweep(
    rows: Sequence[tuple[float, float]],
    *,
    appear: float = 0.001,
    structured: float = 0.95,
) -> dict[str, float]:
    """Reduce a :func:`depth_sweep` to the numbers the depth budget needs.

    *far* is taken as a share of what the sweep actually accumulated rather
    than of the whole frame, so a scene with sky in it is not penalised for
    the part that never occludes.  That share is reported as
    ``sky_fraction``: content the sweep could never hide, at effective
    infinity, which belongs outside the near/far balance.

    A backdrop that runs to the horizon needs one step more than this
    function does.  The room's walls close a plane sweep out, so the curve
    flattens and this rule lands on real content -- but a sea keeps eating a
    little more of the frame at every distance and never closes, so
    *structured* returns the end of the sweep and nothing useful.  There, fit
    the far tail (which is pure backdrop), subtract that linear creep, and
    take *structured* of what is left.

    :param rows: Output of :func:`depth_sweep`.
    :param appear: Frame fraction counting as "geometry has appeared".
    :param structured: Share of occludable content that defines *far*.
    :return: ``near``, ``far`` and ``sky_fraction``.
    :raises ValueError: If *rows* is empty.
    """
    if not rows:
        raise ValueError("no probe rows to summarise")
    d = np.array([r[0] for r in rows], dtype="d")
    f = np.array([r[1] for r in rows], dtype="d")
    saturation = float(f.max())
    return {
        "near": float(d[int(np.argmax(f > appear))]),
        "far": float(d[int(np.argmax(f >= structured * saturation))]),
        "sky_fraction": 1.0 - saturation,
    }


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _render_view(
    povray: str,
    wrapper: Path,
    out_png: Path,
    width: int,
    height: int,
    library_paths: Sequence[Path],
    antialias: float | None,
    quality: int,
    extra_args: Sequence[str],
    workdir: Path,
) -> None:
    """Run POV-Ray once for a single view.

    :raises RuntimeError: If POV-Ray exits non-zero, with its diagnostics.
    """
    cmd = [
        povray,
        f"+I{wrapper.name}",
        f"+O{out_png.name}",
        f"+W{width}",
        f"+H{height}",
        "+FN",  # PNG output
        "-D",  # no preview window
        f"+Q{quality}",
    ]
    if antialias is not None:
        cmd.append(f"+A{antialias:g}")
    cmd += [f"+L{p}" for p in library_paths]
    cmd += list(extra_args)

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=workdir)
    if result.returncode != 0:
        raise RuntimeError(
            f"POV-Ray failed ({result.returncode}) on {wrapper.name}:\n{result.stderr[-3000:]}"
        )
    if not out_png.exists():
        raise RuntimeError(
            f"POV-Ray reported success but wrote no image for {wrapper.name}.\n"
            f"{result.stderr[-2000:]}"
        )


def resolve_work_threads(requested: int | None = None) -> int | None:
    """Decide the ``+WT`` thread count for a render, or ``None`` for none.

    POV-Ray threads a single render across every core it can see, which on a
    workstation means a quilt makes the desktop unusable for the length of
    the render.  Two mechanisms already existed to stop that and neither
    covered the common case:

    * A ``Work_Threads`` line in the INI named by ``POVINI``.  This repo's
      Makefile writes one, so ``make`` renders were capped -- but calling a
      render script directly set no ``POVINI`` and took the whole machine.
    * ``jobs > 1``, which splits cores between processes.  At the documented
      ``jobs=1`` it does nothing.

    So the default here is a courtesy cap of ``cpu_count -
    COURTESY_CORES_HELD_BACK``, applied only when nothing else has spoken.
    An INI *does* speak: a command-line ``+WT`` overrides ``POVINI``
    entirely, so capping on top of a ``Work_Threads`` line would silently
    defeat ``make quilts RENDER_THREADS=$(nproc)``.

    :param requested: Explicit thread count.  ``None`` asks for the courtesy
        default; ``0`` or negative means uncapped -- let POV-Ray take
        everything.
    :return: Thread count for ``+WT``, or ``None`` to pass no ``+WT`` at all.
    """
    if requested is not None:
        return requested if requested > 0 else None

    ini = os.environ.get("POVINI", "")
    if ini:
        try:
            for line in Path(ini).read_text(errors="replace").splitlines():
                key, sep, value = line.partition("=")
                if sep and key.strip().lower() == "work_threads" and value.strip().isdigit():
                    return None  # POVINI governs; do not override it
        except OSError:
            pass

    cores = os.cpu_count()
    if not cores:
        return None
    return max(1, cores - COURTESY_CORES_HELD_BACK)


def render_pov_quilt(
    scene: str | Path,
    spec: QuiltSpec,
    camera: PovCamera,
    *,
    include_paths: Sequence[str | Path] = (),
    view_cone: float | None = None,
    antialias: float | None = 0.3,
    quality: int = 9,
    jobs: int = 1,
    threads: int | None = None,
    binary: str | None = None,
    extra_args: Sequence[str] = (),
    keep_views: str | Path | None = None,
    progress: bool = True,
    lighting: str | None = None,
    sun: tuple[float, float] | None = None,
) -> np.ndarray:
    """Render a POV-Ray scene into a Looking Glass quilt.

    Sweeps *camera* horizontally across the display's view cone using
    off-axis projections (see the module docstring), ray-traces one image
    per view, and tiles them with
    :func:`~quiltwright.lfd.assemble_quilt`.

    Cost scales linearly with the view count: a Portrait quilt is 48 full
    ray-traces.  For scenes using radiosity or photons, render one view with
    the cache saved and the rest with it loaded (via *extra_args*) -- the
    lighting is identical across a view sweep, so recomputing it per view is
    pure waste.

    :param scene: Path to the ``.pov`` scene.  Not modified.
    :param spec: Quilt specification (grid, size, aspect, cone).
    :param camera: Base camera; its ``look_at`` becomes the focal plane.
    :param include_paths: Extra directories searched for ``#include`` files.
        The scene's own directory is always searched, which is usually
        enough for scenes whose includes sit alongside them.
    :param view_cone: Override the spec's view cone in degrees.
    :param antialias: POV-Ray ``+A`` threshold; lower is higher quality
        (0.3 is a good default, 0.1 for finals).  ``None`` disables
        anti-aliasing.
    :param quality: POV-Ray ``+Q`` quality level, 0-11.
    :param jobs: Number of POV-Ray processes to run concurrently.  Views are
        independent, so one process per core is the efficient shape for a
        quilt: raising this splits the machine's cores between the jobs via
        ``+WT`` rather than letting each process claim all of them.  Pass
        your own ``+WT`` in *extra_args* to override that split.
    :param threads: POV-Ray worker threads per process.  ``None`` applies the
        courtesy cap described in :func:`resolve_work_threads`; ``0`` lets
        POV-Ray take every core, which is its own default.
    :param binary: POV-Ray executable; defaults to ``POVRAY_BINARY`` or
        ``povray`` on ``PATH``.
    :param extra_args: Additional POV-Ray command-line arguments, e.g.
        ``["+HImy.ini"]`` or radiosity cache flags.
    :param keep_views: Directory to retain the per-view PNGs and generated
        wrapper scenes in, for inspection or debugging.  Discarded if
        ``None``.
    :param progress: Print a progress line while rendering.
    :param lighting: ``"light"`` or ``"dark"`` -- append a parallel sun at
        the matching :data:`APPEARANCE_SUN` preset.  ``None`` (the default)
        leaves the scene's own lights alone.  This is appearance for a
        Dynamic Desktop still, not POV-Ray's ``clock``.
    :param sun: ``(altitude, azimuth)`` in degrees, POV-Ray Y-up (see
        :func:`sun_direction`).  Overrides the preset direction when
        *lighting* is also set.  Alone, it still appends the sun.
    :return: ``uint8`` RGB array of shape ``(quilt_height, quilt_width, 3)``.
    """
    from PIL import Image

    povray = _find_povray(binary)
    scene_path = Path(scene).expanduser().resolve()
    if not scene_path.is_file():
        raise FileNotFoundError(f"POV-Ray scene not found: {scene_path}")

    if view_cone is not None:
        spec = replace(spec, view_cone=view_cone)

    # POV-Ray threads one render across every core it can see, so N concurrent
    # processes each ask for the whole machine.  At jobs=14 on 18 cores that
    # is 336 render threads competing for 18, which buys context switching
    # and cache thrash rather than throughput.  Divide the cores between the
    # jobs instead; an explicit +WT from the caller wins.
    if not any(str(a).startswith("+WT") for a in extra_args):
        if jobs > 1:
            extra_args = [*extra_args, f"+WT{max(1, (os.cpu_count() or jobs) // jobs)}"]
        else:
            capped = resolve_work_threads(threads)
            if capped is not None:
                extra_args = [*extra_args, f"+WT{capped}"]

    # Match render_quilt: capture at the declared view aspect so the frustum
    # is undistorted, then let assemble_quilt resample into the tile.  These
    # differ only for anamorphic presets (e.g. the 27" quilts).
    render_h = spec.tile_height
    render_w = round(render_h * spec.aspect)
    render_aspect = render_w / render_h

    library_paths = [scene_path.parent, *(Path(p).expanduser().resolve() for p in include_paths)]
    offsets = view_offsets(spec, camera.focal_distance)

    with tempfile.TemporaryDirectory(prefix="pov_quilt_") as tmp:
        workdir = Path(tmp)
        views = _sweep(
            povray,
            scene_path,
            spec,
            camera,
            offsets,
            workdir,
            render_w,
            render_h,
            render_aspect,
            library_paths,
            antialias,
            quality,
            extra_args,
            jobs,
            progress,
            lighting=lighting,
            sun=sun,
        )

        quilt = assemble_quilt(
            (np.asarray(Image.open(png).convert("RGB")) for _, png in views), spec
        )

        if keep_views is not None:
            _copy_views(views, keep_views, wrappers=True)

    return quilt


def _copy_views(
    views: Sequence[tuple[Path, Path]], dest: str | Path, *, wrappers: bool
) -> list[Path]:
    """Copy rendered views out of the temporary working directory.

    :param views: ``(wrapper, png)`` pairs in view order.
    :param dest: Destination directory; created if absent.
    :param wrappers: Also copy the generated ``.pov`` wrappers.
    :return: The copied PNG paths, in view order.
    """
    out = Path(dest).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    copied = []
    for wrapper, png in views:
        if wrappers:
            shutil.copy2(wrapper, out / wrapper.name)
        copied.append(shutil.copy2(png, out / png.name))
    return [Path(p) for p in copied]


def _sweep(
    povray: str,
    scene_path: Path,
    spec: QuiltSpec,
    camera: PovCamera,
    offsets,
    workdir: Path,
    render_w: int,
    render_h: int,
    render_aspect: float,
    library_paths: Sequence[Path],
    antialias: float | None,
    quality: int,
    extra_args: Sequence[str],
    jobs: int,
    progress: bool,
    lighting: str | None = None,
    sun: tuple[float, float] | None = None,
) -> list[tuple[Path, Path]]:
    """Ray-trace one image per view into *workdir*.

    Shared by :func:`render_pov_quilt` and :func:`render_pov_views`, which
    differ only in what they do with the frames afterwards.

    :return: ``(wrapper, png)`` pairs in view order, view 0 leftmost.
    """
    # POV-Ray resolves #include against its working directory and the
    # library paths, so the wrapper lives in the working directory and
    # pulls the scene in by absolute path, with the scene's own
    # directory on the library path for its relative includes.
    prefix = lighting_declares(appearance=lighting, sun=sun)
    suffix = lighting_block(camera, appearance=lighting, sun=sun)
    views = []
    for i, offset in enumerate(offsets):
        wrapper = workdir / f"view{i:03d}.pov"
        wrapper.write_text(
            _wrapper_source(
                scene_path,
                i,
                spec.n_views,
                float(offset),
                camera,
                render_aspect,
                lighting_prefix=prefix,
                lighting_suffix=suffix,
            )
        )
        views.append((wrapper, workdir / f"view{i:03d}.png"))

    done = 0

    def run(job):
        nonlocal done
        wrapper, out_png = job
        _render_view(
            povray,
            wrapper,
            out_png,
            render_w,
            render_h,
            library_paths,
            antialias,
            quality,
            extra_args,
            workdir,
        )
        done += 1
        if progress:
            print(f"\r  pov view {done}/{spec.n_views}", end="", flush=True)

    if jobs > 1:
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            # list() forces exceptions from workers to surface here.
            list(pool.map(run, views))
    else:
        for job in views:
            run(job)
    if progress:
        print()

    return views


def render_pov_views(
    scene: str | Path,
    spec: QuiltSpec,
    camera: PovCamera,
    out_dir: str | Path,
    *,
    include_paths: Sequence[str | Path] = (),
    view_cone: float | None = None,
    antialias: float | None = 0.3,
    quality: int = 9,
    jobs: int = 1,
    threads: int | None = None,
    binary: str | None = None,
    extra_args: Sequence[str] = (),
    keep_wrappers: bool = False,
    progress: bool = True,
    lighting: str | None = None,
    sun: tuple[float, float] | None = None,
) -> list[Path]:
    """Render a POV-Ray scene as a sweep of separate view images.

    Identical camera geometry to :func:`render_pov_quilt` -- the same off-axis
    sheared frustum, the same focal plane on the ``look_at`` point -- but the
    frames are written out individually instead of being tiled into a quilt.
    That is the form consumers other than a light-field panel ask for: a
    hologram printer slicing views into hogels, or a lenticular interlacer.

    Pair it with :func:`~quiltwright.lfd.sweep_spec` when the view count is
    not a convenient rectangle::

        from quiltwright.quilt import LITIHOLO_SWEEP
        render_pov_views("risedronate.pov", LITIHOLO_SWEEP, camera, "sweep/")
        # -> sweep/view000.png ... sweep/view022.png

    The depth-budget arithmetic in :func:`format_depth_budget` still applies
    and is still worth running first: a sweep that would ghost on a
    lenticular panel is a sweep whose parallax exceeds what the medium can
    resolve, and there is no evidence that a hologram's hogels are more
    forgiving than a lens sheet.

    :param scene: Path to the ``.pov`` scene.  Not modified.
    :param spec: Sweep or quilt specification supplying view count, view
        cone, and per-view pixel size.
    :param camera: Base camera; its ``look_at`` becomes the focal plane.
    :param out_dir: Directory to write the frames into; created if absent.
    :param include_paths: Extra directories searched for ``#include`` files.
    :param view_cone: Override the spec's view cone in degrees.
    :param antialias: POV-Ray ``+A`` threshold; ``None`` disables it.
    :param quality: POV-Ray ``+Q`` quality level, 0-11.
    :param jobs: Number of POV-Ray processes to run concurrently.
    :param threads: POV-Ray worker threads per process.  ``None`` applies the
        courtesy cap described in :func:`resolve_work_threads`; ``0`` lets
        POV-Ray take every core.
    :param binary: POV-Ray executable; defaults to ``POVRAY_BINARY`` or
        ``povray`` on ``PATH``.
    :param extra_args: Additional POV-Ray command-line arguments.
    :param keep_wrappers: Also write the generated per-view ``.pov`` wrappers
        alongside the frames, for inspection.
    :param progress: Print a progress line while rendering.
    :param lighting: See :func:`render_pov_quilt`.
    :param sun: See :func:`render_pov_quilt`.
    :return: Paths to the written frames, in view order -- view 0 leftmost.
    """
    povray = _find_povray(binary)
    scene_path = Path(scene).expanduser().resolve()
    if not scene_path.is_file():
        raise FileNotFoundError(f"POV-Ray scene not found: {scene_path}")

    if view_cone is not None:
        spec = replace(spec, view_cone=view_cone)

    if not any(str(a).startswith("+WT") for a in extra_args):
        if jobs > 1:
            extra_args = [*extra_args, f"+WT{max(1, (os.cpu_count() or jobs) // jobs)}"]
        else:
            capped = resolve_work_threads(threads)
            if capped is not None:
                extra_args = [*extra_args, f"+WT{capped}"]

    render_h = spec.tile_height
    render_w = round(render_h * spec.aspect)

    library_paths = [scene_path.parent, *(Path(p).expanduser().resolve() for p in include_paths)]
    offsets = view_offsets(spec, camera.focal_distance)

    with tempfile.TemporaryDirectory(prefix="pov_sweep_") as tmp:
        views = _sweep(
            povray,
            scene_path,
            spec,
            camera,
            offsets,
            Path(tmp),
            render_w,
            render_h,
            render_w / render_h,
            library_paths,
            antialias,
            quality,
            extra_args,
            jobs,
            progress,
            lighting=lighting,
            sun=sun,
        )
        return _copy_views(views, out_dir, wrappers=keep_wrappers)
