"""
POV-Ray Scene Generation
========================

Writes ``.pov`` scenes from *analytic* primitives, so a scene composed in
Python — or grown by a geometry engine such as ``kg_utils.viz3d`` — can be
ray-traced by :func:`~quiltwright.povray.render_pov_quilt` instead of
rasterised by VTK.

**Why analytic rather than a mesh dump.**  By the time geometry reaches a
``pv.Plotter`` it is already tessellated: ``pv.Sphere`` is a triangulated
ball, and a swept tube is a strip of quads.  Dumping those triangles into a
POV-Ray ``mesh2`` reproduces the scene faithfully but keeps VTK's facets and
costs a great deal of text, re-parsed once per view — 48 times for a Portrait
quilt.  Re-emitting the *intent* instead — a limb is a swept path of radii, a
leaf is a ball at a point — gives POV-Ray its own exact primitives: an exact
silhouette at any zoom, and a bounding hierarchy the ray-tracer is good at.

Measured on a 3000-leaf organic tree from ``kg_utils.viz3d`` (192k triangles,
159k vertices once tessellated): **839 KB** of analytic SDL with oriented leaf
instances, or 508 KB with plain spheres, against roughly **12.5 MB** for the
equivalent ``mesh2`` — 15x to 25x smaller, and better looking, since the
tessellation facets are gone.  That quality difference is the reason to leave
VTK, so this module reaches for the analytic form first and leaves ``mesh2``
as the fallback for geometry that has no analytic description (volumes,
isosurfaces, imported meshes).

**Handedness.**  PyVista, VTK and NumPy are right-handed; POV-Ray is
left-handed.  Everything here is authored in right-handed world coordinates
and converted on emission by negating *z* (:func:`to_pov`), which is the same
correction ``pypdb2pov`` applies to PDB coordinates.
:func:`pov_camera_from_plotter` applies the same conversion to the camera, so
the two agree and the rendered image matches the PyVista one rather than
mirroring it.  Pass ``handedness="none"`` to author directly in POV-Ray
coordinates.

A :class:`~quiltwright.povray.PovCamera` you build yourself is **not**
converted — it holds POV-Ray coordinates, and
:func:`~quiltwright.povray.camera_block` emits it verbatim.  Run
:func:`to_pov` over its location, look-at and sky yourself, or the geometry
lands at negative *z* while the lens aims at positive *z* and POV-Ray renders
an immaculate picture of empty space.

(The reflection also reverses triangle winding.  That does not matter for the
analytic primitives here, none of which have a winding, but a future
``mesh2`` emitter must reverse each face's index order or its normals will
point inward.)

**Cameras.**  A scene written by this module deliberately contains *no*
camera.  :func:`~quiltwright.povray.render_pov_quilt` appends one off-axis
camera per view and POV-Ray uses the last camera it parses; emitting one here
would merely be overridden with a warning.  Use
:func:`pov_camera_from_plotter` to carry a composed plotter's viewpoint over
to a :class:`~quiltwright.povray.PovCamera` instead — VTK's ``view_angle``
and ``PovCamera.fov`` are both *vertical* degrees, so that maps one-to-one.

Typical usage::

    from quiltwright.lfd import QUILT_PRESETS, save_quilt
    from quiltwright.povgen import PovScene, Sphere, Texture, sphere_sweeps_from_paths
    from quiltwright.povray import render_pov_quilt

    scene = PovScene(background="#101018")
    scene.add(sphere_sweeps_from_paths(limbs, Texture("#6b4a2f")))
    scene.add(Sphere(centre, 0.4, Texture("#3f7d3f")))
    scene.write("tree.pov")

    spec = QUILT_PRESETS["portrait"]
    quilt = render_pov_quilt("tree.pov", spec, pov_camera_from_plotter(plotter))
    save_quilt(quilt, "tree", spec)

Part of Quiltwright — https://github.com/suchanek/quiltwright

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:  # pragma: no cover - typing only
    from quiltwright.povray import PovCamera

# ``PovCamera`` lives in :mod:`quiltwright.povray`, which imports
# :mod:`quiltwright.lfd` for the quilt assembler, which imports PyVista when it
# is installed.  Importing it at module scope would therefore drag the whole
# rendering stack into a module whose entire point is not needing one — so it
# is imported inside :func:`pov_camera_from_plotter`, the only function here
# that constructs one, and which by definition already has a live plotter.

__author__ = "Eric G. Suchanek, PhD"

#: Default ``sphere_sweep`` tolerance.  POV-Ray's own default (1e-6) makes the
#: root solver miss thin sweeps at scene scale and drop segments; 0.05 is the
#: value that renders swept limbs cleanly without visible faceting.
SWEEP_TOLERANCE: float = 0.05

#: Minimum control points POV-Ray requires per ``sphere_sweep`` spline kind.
SWEEP_MIN_POINTS: dict[str, int] = {
    "linear_spline": 2,
    "b_spline": 4,
    "cubic_spline": 4,
}


# ---------------------------------------------------------------------------
# Coordinates and colour
# ---------------------------------------------------------------------------


def to_pov(point: Sequence[float], handedness: str = "flip-z") -> tuple[float, float, float]:
    """Convert a right-handed world point to POV-Ray's left-handed world.

    :param point: ``(x, y, z)`` in right-handed (PyVista/VTK/NumPy) coordinates.
    :param handedness: ``"flip-z"`` to negate *z*, ``"none"`` to pass through
        for callers already authoring in POV-Ray coordinates.
    :return: ``(x, y, z)`` for emission.
    :raises ValueError: If *handedness* is not one of the two accepted values.
    """
    x, y, z = (float(v) for v in point)
    if handedness == "flip-z":
        return (x, y, -z)
    if handedness == "none":
        return (x, y, z)
    raise ValueError(f"handedness must be 'flip-z' or 'none', got {handedness!r}")


def parse_color(color: str | Sequence[float]) -> tuple[float, float, float]:
    """Normalise a colour to an ``(r, g, b)`` triple in ``0..1``.

    :param color: ``"#rrggbb"`` (with or without the hash, 3- or 6-digit) or a
        sequence of three floats already in ``0..1``.
    :return: ``(r, g, b)`` floats.
    :raises ValueError: If the string is not a valid hex colour or the
        sequence is not three components.
    """
    if isinstance(color, str):
        text = color.strip().lstrip("#")
        if len(text) == 3:
            text = "".join(c * 2 for c in text)
        if len(text) != 6:
            raise ValueError(f"not a hex colour: {color!r}")
        try:
            value = int(text, 16)
        except ValueError as exc:
            raise ValueError(f"not a hex colour: {color!r}") from exc
        return (
            ((value >> 16) & 0xFF) / 255.0,
            ((value >> 8) & 0xFF) / 255.0,
            (value & 0xFF) / 255.0,
        )
    components = [float(c) for c in color]
    if len(components) != 3:
        raise ValueError(f"colour needs three components, got {len(components)}")
    return (components[0], components[1], components[2])


def _vec(v: Sequence[float]) -> str:
    """Format a 3-vector as POV-Ray ``<x, y, z>`` with stable precision.

    Negative zero is normalised away: negating *z* turns an honest ``0`` into
    ``-0``, which is numerically identical but makes generated scenes differ
    textually for no reason.
    """
    return "<{:.6g}, {:.6g}, {:.6g}>".format(*(float(c) + 0.0 for c in v))


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finish:
    """A POV-Ray ``finish`` block.

    Defaults approximate VTK's default actor shading closely enough that a
    transcoded scene reads as the same scene, rather than matching it
    photometrically — POV-Ray's lighting model is not VTK's, and a scene worth
    ray-tracing usually wants its own lights anyway.

    :param ambient: Light emitted regardless of the light sources.
    :param diffuse: Fraction of incident light scattered.
    :param phong: Phong highlight strength; ``None`` omits it.
    :param phong_size: Phong highlight tightness.
    :param specular: Specular highlight strength; ``None`` omits it.
    :param roughness: Specular roughness; only meaningful with *specular*.
    :param reflection: Mirror reflection fraction; ``None`` omits it.
    """

    ambient: float = 0.15
    diffuse: float = 0.75
    phong: float | None = 0.25
    phong_size: float = 40.0
    specular: float | None = None
    roughness: float | None = None
    reflection: float | None = None

    def sdl(self) -> str:
        """:return: The ``finish { ... }`` block as a single line."""
        parts = [f"ambient {self.ambient:.4g}", f"diffuse {self.diffuse:.4g}"]
        if self.phong is not None:
            parts.append(f"phong {self.phong:.4g} phong_size {self.phong_size:.4g}")
        if self.specular is not None:
            parts.append(f"specular {self.specular:.4g}")
        if self.roughness is not None:
            parts.append(f"roughness {self.roughness:.4g}")
        if self.reflection is not None:
            parts.append(f"reflection {self.reflection:.4g}")
        return "finish { " + " ".join(parts) + " }"


@dataclass(frozen=True)
class Texture:
    """A POV-Ray ``texture`` block: one pigment plus one finish.

    :param color: Hex string or ``(r, g, b)`` in ``0..1``.
    :param opacity: ``1.0`` is opaque.  Emitted as POV-Ray ``transmit``, which
        passes light through unchanged — the correct analogue of VTK's alpha.
        POV-Ray's ``filter`` is *not*: it tints everything seen through the
        surface by the surface's own colour.
    :param finish: Shading parameters.
    """

    color: str | Sequence[float] = "#cccccc"
    opacity: float = 1.0
    finish: Finish = field(default_factory=Finish)

    def sdl(self) -> str:
        """:return: The ``texture { ... }`` block as a single line."""
        r, g, b = parse_color(self.color)
        pigment = f"color rgb <{r:.5g}, {g:.5g}, {b:.5g}>"
        transmit = 1.0 - float(self.opacity)
        if transmit > 1e-9:
            pigment += f" transmit {transmit:.4g}"
        return f"texture {{ pigment {{ {pigment} }} {self.finish.sdl()} }}"


def _texture_suffix(texture: Texture | str | None) -> str:
    """Render a texture, a bare ``#declare``d texture name, or nothing."""
    if texture is None:
        return ""
    if isinstance(texture, str):
        return f" texture {{ {texture} }}"
    return " " + texture.sdl()


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


class Primitive:
    """Base class for anything that can emit a POV-Ray object statement."""

    def sdl(self, handedness: str = "flip-z") -> str:
        """:return: This object as POV-Ray SDL.

        :param handedness: Passed to :func:`to_pov` for every point.
        """
        raise NotImplementedError


@dataclass(frozen=True)
class Sphere(Primitive):
    """A POV-Ray ``sphere``.

    :param centre: Centre in right-handed world coordinates.
    :param radius: Radius in scene units.
    :param texture: Texture, a ``#declare``d texture name, or ``None``.
    """

    centre: Sequence[float]
    radius: float
    texture: Texture | str | None = None

    def sdl(self, handedness: str = "flip-z") -> str:
        """:return: ``sphere { <c>, r texture { ... } }``."""
        c = to_pov(self.centre, handedness)
        return f"sphere {{ {_vec(c)}, {float(self.radius):.6g}{_texture_suffix(self.texture)} }}"


@dataclass(frozen=True)
class Cylinder(Primitive):
    """A POV-Ray ``cylinder``.

    :param base: Centre of the base cap, right-handed.
    :param cap: Centre of the top cap, right-handed.
    :param radius: Radius in scene units.
    :param open: Omit the end caps.
    :param texture: Texture, a ``#declare``d texture name, or ``None``.
    """

    base: Sequence[float]
    cap: Sequence[float]
    radius: float
    open: bool = False
    texture: Texture | str | None = None

    def sdl(self, handedness: str = "flip-z") -> str:
        """:return: ``cylinder { <b>, <c>, r [open] texture { ... } }``."""
        b = to_pov(self.base, handedness)
        c = to_pov(self.cap, handedness)
        body = f"{_vec(b)}, {_vec(c)}, {float(self.radius):.6g}"
        if self.open:
            body += " open"
        return f"cylinder {{ {body}{_texture_suffix(self.texture)} }}"


@dataclass(frozen=True)
class Box(Primitive):
    """A POV-Ray axis-aligned ``box``.

    The two corners are sorted componentwise after the handedness conversion,
    because negating *z* swaps which corner is the lower one and POV-Ray
    requires ``corner1 <= corner2``.

    :param corner1: One corner, right-handed.
    :param corner2: The opposite corner, right-handed.
    :param texture: Texture, a ``#declare``d texture name, or ``None``.
    """

    corner1: Sequence[float]
    corner2: Sequence[float]
    texture: Texture | str | None = None

    def sdl(self, handedness: str = "flip-z") -> str:
        """:return: ``box { <lo>, <hi> texture { ... } }``."""
        a = np.asarray(to_pov(self.corner1, handedness), dtype=float)
        b = np.asarray(to_pov(self.corner2, handedness), dtype=float)
        lo, hi = np.minimum(a, b), np.maximum(a, b)
        return f"box {{ {_vec(lo)}, {_vec(hi)}{_texture_suffix(self.texture)} }}"


@dataclass(frozen=True)
class SphereSweep(Primitive):
    """A POV-Ray ``sphere_sweep`` — a tapered tube through a polyline.

    This is the analytic replacement for a PyVista ``spline.tube(...)``: one
    statement instead of a few thousand triangles, with an exact silhouette.

    ``linear_spline`` is the default rather than ``b_spline`` because it
    *interpolates* its control points.  Callers generally hand over a path
    that has already been smoothed (``kg_utils.viz3d.smooth_paths`` splines
    each limb before this ever sees it), so a further approximating spline
    would pull the surface off the geometry PyVista tubed and cost the
    parity that makes a dual render comparable.

    :param points: ``(K, 3)`` polyline, right-handed.
    :param radii: ``(K,)`` radius per point, or a single float for all.
    :param kind: ``"linear_spline"``, ``"b_spline"`` or ``"cubic_spline"``.
    :param tolerance: POV-Ray sweep solver tolerance; see
        :data:`SWEEP_TOLERANCE`.
    :param texture: Texture, a ``#declare``d texture name, or ``None``.
    """

    points: np.ndarray
    radii: np.ndarray | float
    kind: str = "linear_spline"
    tolerance: float = SWEEP_TOLERANCE
    texture: Texture | str | None = None

    def sdl(self, handedness: str = "flip-z") -> str:
        """:return: ``sphere_sweep { kind, N, <p>, r, ... }``.

        :raises ValueError: If *kind* is unknown, or too few points survive
            de-duplication for that spline kind.
        """
        if self.kind not in SWEEP_MIN_POINTS:
            raise ValueError(
                f"unknown sphere_sweep kind {self.kind!r}; "
                f"expected one of {sorted(SWEEP_MIN_POINTS)}"
            )
        pts = np.atleast_2d(np.asarray(self.points, dtype=float))
        radii = np.asarray(self.radii, dtype=float)
        if radii.ndim == 0:
            radii = np.full(pts.shape[0], float(radii))
        if radii.shape[0] != pts.shape[0]:
            raise ValueError(f"radii length {radii.shape[0]} does not match {pts.shape[0]} points")

        pts, radii = _dedupe_path(pts, radii)
        minimum = SWEEP_MIN_POINTS[self.kind]
        if pts.shape[0] < minimum:
            raise ValueError(
                f"{self.kind} needs at least {minimum} distinct points, got {pts.shape[0]}"
            )

        entries = ",\n    ".join(
            f"{_vec(to_pov(p, handedness))}, {r:.6g}" for p, r in zip(pts, radii, strict=True)
        )
        return (
            f"sphere_sweep {{\n"
            f"    {self.kind}, {pts.shape[0]},\n"
            f"    {entries}\n"
            f"    tolerance {self.tolerance:.6g}"
            f"{_texture_suffix(self.texture)}\n"
            f"}}"
        )


@dataclass(frozen=True)
class Union(Primitive):
    """A POV-Ray ``union`` of other primitives.

    Grouping keeps the SDL readable and lets one texture cover many members,
    which is how a whole tree's foliage becomes a single material.

    :param members: Primitives to gather.
    :param texture: Texture applied to the union as a whole, or ``None`` to
        let the members keep their own.
    """

    members: Sequence[Primitive]
    texture: Texture | str | None = None

    def sdl(self, handedness: str = "flip-z") -> str:
        """:return: ``union { ... }``, or an empty string when it has no members."""
        if not self.members:
            return ""
        lines = [_indent(m.sdl(handedness), 2) for m in self.members if m.sdl(handedness)]
        suffix = _texture_suffix(self.texture).strip()
        if suffix:
            lines.append(_indent(suffix, 2))
        body = "\n".join(lines)
        return f"union {{\n{body}\n}}"


@dataclass(frozen=True)
class Instance(Primitive):
    """An ``object { Name ... }`` reference to a ``#declare``d primitive.

    Instancing is what keeps a large crown small: POV-Ray parses the prototype
    once and the canopy becomes one short line per leaf.

    :param name: The declared identifier.
    :param translate: Optional translation, right-handed.
    :param scale: Optional per-axis scale, applied before the translation.
    :param matrix: Optional 3x3 rotation as row vectors (row-vector
        convention, matching POV-Ray's ``matrix``).  It composes with *scale*
        rather than replacing it: POV-Ray applies the transformations in the
        order written, so the prototype is scaled, then rotated, then moved.
    :param texture: Texture override, or ``None`` to keep the prototype's.
    """

    name: str
    translate: Sequence[float] | None = None
    scale: Sequence[float] | float | None = None
    matrix: np.ndarray | None = None
    texture: Texture | str | None = None

    def sdl(self, handedness: str = "flip-z") -> str:
        """:return: ``object { Name scale <..> matrix <..> translate <..> }``."""
        parts = [self.name]
        if self.scale is not None:
            scale = self.scale
            if np.ndim(scale) == 0:
                parts.append(f"scale {float(scale):.6g}")
            else:
                parts.append(f"scale {_vec(scale)}")
        if self.matrix is not None:
            m = np.asarray(self.matrix, dtype=float).reshape(3, 3)
            if handedness == "flip-z":
                # Conjugate the rotation by the reflection diag(1, 1, -1) so it
                # means the same thing in the mirrored world: negate the z
                # component of each row and the z row as a whole.
                flip = np.diag([1.0, 1.0, -1.0])
                m = flip @ m @ flip
            rows = ", ".join(f"{v:.6g}" for v in m.reshape(-1))
            parts.append(f"matrix <{rows}, 0, 0, 0>")
        if self.translate is not None:
            parts.append(f"translate {_vec(to_pov(self.translate, handedness))}")
        suffix = _texture_suffix(self.texture)
        return f"object {{ {' '.join(parts)}{suffix} }}"


@dataclass(frozen=True)
class LightSource:
    """A POV-Ray ``light_source``.

    :param position: Position in right-handed world coordinates.
    :param color: Hex string or ``(r, g, b)``; values above 1 brighten.
    :param shadowless: Emit ``shadowless``, for fill light that must not
        double the shadows of the key.
    :param area: ``(width_vector, height_vector, u, v)`` for an area light, or
        ``None`` for a point light.  Area lights are what make ray-tracing
        visibly better than VTK, and what make it slow.
    """

    position: Sequence[float]
    color: str | Sequence[float] = "#ffffff"
    shadowless: bool = False
    area: tuple[Sequence[float], Sequence[float], int, int] | None = None

    def sdl(self, handedness: str = "flip-z") -> str:
        """:return: ``light_source { <p> color rgb <c> ... }``."""
        r, g, b = parse_color(self.color)
        parts = [
            _vec(to_pov(self.position, handedness)),
            f"color rgb <{r:.5g}, {g:.5g}, {b:.5g}>",
        ]
        if self.area is not None:
            width, height, u, v = self.area
            parts.append(
                f"area_light {_vec(to_pov(width, handedness))}, "
                f"{_vec(to_pov(height, handedness))}, {int(u)}, {int(v)} adaptive 1 jitter"
            )
        if self.shadowless:
            parts.append("shadowless")
        return "light_source { " + " ".join(parts) + " }"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _indent(text: str, spaces: int) -> str:
    """Indent every non-empty line of *text* by *spaces*."""
    pad = " " * spaces
    return "\n".join(pad + line if line.strip() else line for line in text.split("\n"))


def _dedupe_path(points: np.ndarray, radii: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Drop consecutive duplicate points, which make ``sphere_sweep`` degenerate.

    :param points: ``(K, 3)`` polyline.
    :param radii: ``(K,)`` radius per point.
    :return: The filtered ``(points, radii)``.
    """
    if points.shape[0] < 2:
        return points, radii
    steps = np.linalg.norm(np.diff(points, axis=0), axis=1)
    keep = np.concatenate([[True], steps > 1e-9])
    return points[keep], radii[keep]


def sphere_sweeps_from_paths(
    paths: Iterable[tuple[np.ndarray, np.ndarray]],
    texture: Texture | str | None = None,
    *,
    kind: str = "linear_spline",
    tolerance: float = SWEEP_TOLERANCE,
    min_radius: float = 1e-4,
) -> list[SphereSweep]:
    """Turn ``[(points, radii), ...]`` paths into sweeps, skipping degenerate ones.

    This is the analytic counterpart of tubing each path in PyVista.  It is
    deliberately generic — it knows about polylines with radii, not about
    trees — so any producer of swept paths can use it.

    :param paths: Pairs of ``(K, 3)`` points and ``(K,)`` radii, such as
        ``kg_utils.viz3d.smooth_paths`` returns.
    :param texture: Texture applied to every sweep.
    :param kind: Spline kind; see :class:`SphereSweep`.
    :param tolerance: POV-Ray sweep solver tolerance.
    :param min_radius: Radii below this are raised to it.  A zero radius makes
        POV-Ray's sweep solver produce artifacts rather than a sharp tip.
    :return: One :class:`SphereSweep` per usable path.
    """
    minimum = SWEEP_MIN_POINTS.get(kind, 2)
    sweeps: list[SphereSweep] = []
    for points, radii in paths:
        pts = np.atleast_2d(np.asarray(points, dtype=float))
        rad = np.asarray(radii, dtype=float)
        if rad.ndim == 0:
            rad = np.full(pts.shape[0], float(rad))
        pts, rad = _dedupe_path(pts, rad)
        if pts.shape[0] < minimum:
            continue
        sweeps.append(
            SphereSweep(
                points=pts,
                radii=np.maximum(rad, min_radius),
                kind=kind,
                tolerance=tolerance,
                texture=texture,
            )
        )
    return sweeps


def spheres_from_points(
    points: np.ndarray,
    radius: float | np.ndarray,
    texture: Texture | str | None = None,
) -> list[Sphere]:
    """Turn a point cloud into one :class:`Sphere` each.

    :param points: ``(M, 3)`` positions, right-handed.
    :param radius: Scalar radius, or ``(M,)`` radii.
    :param texture: Texture applied to every sphere.
    :return: One :class:`Sphere` per point.
    """
    pts = np.atleast_2d(np.asarray(points, dtype=float))
    if pts.size == 0:
        return []
    radii = np.asarray(radius, dtype=float)
    if radii.ndim == 0:
        radii = np.full(pts.shape[0], float(radii))
    return [Sphere(tuple(p), float(r), texture) for p, r in zip(pts, radii, strict=True)]


def instances_from_frames(
    name: str,
    points: np.ndarray,
    directions: np.ndarray | None = None,
    texture: Texture | str | None = None,
) -> list[Instance]:
    """Instance a ``#declare``d prototype once per point, optionally oriented.

    Orientation matches VTK's glyph convention: the prototype's **+x** axis is
    aligned to each direction vector.  The remaining two axes are completed
    deterministically, so a given input always produces the same file — but
    that completion is not VTK's, so glyph *roll* will differ from a PyVista
    render even though position, aim and silhouette agree.

    :param name: Declared prototype identifier.
    :param points: ``(M, 3)`` positions, right-handed.
    :param directions: ``(M, 3)`` aim vectors, or ``None`` for no rotation.
    :param texture: Texture override applied to every instance.
    :return: One :class:`Instance` per point.
    """
    pts = np.atleast_2d(np.asarray(points, dtype=float))
    if pts.size == 0:
        return []
    if directions is None:
        return [Instance(name, translate=tuple(p), texture=texture) for p in pts]

    dirs = np.atleast_2d(np.asarray(directions, dtype=float))
    if dirs.shape != pts.shape:
        raise ValueError(f"directions {dirs.shape} does not match points {pts.shape}")

    out: list[Instance] = []
    for point, direction in zip(pts, dirs, strict=True):
        out.append(
            Instance(
                name,
                translate=tuple(point),
                matrix=_frame_from_direction(direction),
                texture=texture,
            )
        )
    return out


def _frame_from_direction(direction: np.ndarray) -> np.ndarray:
    """Build a right-handed orthonormal frame whose **first row** is *direction*.

    Rows are the images of the local x, y and z axes, which is the row-vector
    convention POV-Ray's ``matrix`` uses.  The up-hint switches away from
    ``+z`` when the direction is nearly parallel to it, so the frame never
    degenerates.

    :param direction: Aim vector; need not be normalised.
    :return: ``(3, 3)`` rotation with orthonormal rows.
    """
    x = np.asarray(direction, dtype=float)
    norm = np.linalg.norm(x)
    if norm < 1e-12:
        return np.eye(3)
    x = x / norm
    hint = np.array([0.0, 0.0, 1.0]) if abs(x[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    y = np.cross(hint, x)
    y /= np.linalg.norm(y)
    return np.stack([x, y, np.cross(x, y)])


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------


@dataclass
class PovScene:
    """A POV-Ray scene under construction.

    Holds includes, ``#declare``s, lights and objects, and emits a ``.pov``
    file.  It writes **no camera** — see the module docstring.

    :param background: Hex or ``(r, g, b)`` background colour, or ``None`` to
        leave POV-Ray's default (black).
    :param includes: ``#include`` file names, e.g. ``"colors.inc"``.
    :param handedness: ``"flip-z"`` (default) to author in right-handed world
        coordinates, ``"none"`` to author directly in POV-Ray's.
    :param ambient_light: Global ``ambient_light`` colour, or ``None``.
    :param comment: Free text written into the file header.
    """

    background: str | Sequence[float] | None = None
    includes: list[str] = field(default_factory=list)
    handedness: str = "flip-z"
    ambient_light: str | Sequence[float] | None = None
    comment: str = ""
    _declares: list[tuple[str, str]] = field(default_factory=list, repr=False)
    _lights: list[LightSource] = field(default_factory=list, repr=False)
    _objects: list[Primitive] = field(default_factory=list, repr=False)

    def add(self, item: Primitive | Iterable[Primitive]) -> PovScene:
        """Add one primitive, or an iterable of them.

        :param item: A :class:`Primitive` or any iterable of them.
        :return: ``self``, so calls chain.
        """
        if isinstance(item, Primitive):
            self._objects.append(item)
        else:
            self._objects.extend(item)
        return self

    def add_light(self, light: LightSource) -> PovScene:
        """Add a light source.

        :param light: The light.
        :return: ``self``, so calls chain.
        """
        self._lights.append(light)
        return self

    def declare(self, name: str, body: Primitive | str) -> PovScene:
        """Add a ``#declare``, for prototypes instanced by :class:`Instance`.

        :param name: Identifier, e.g. ``"Leaf"``.
        :param body: A primitive, or raw SDL such as a texture block.
        :return: ``self``, so calls chain.
        """
        text = body.sdl(self.handedness) if isinstance(body, Primitive) else str(body)
        self._declares.append((name, text))
        return self

    def declare_texture(self, name: str, texture: Texture) -> PovScene:
        """Declare a named texture, so many objects can share one definition.

        :param name: Identifier, e.g. ``"Bark"``.
        :param texture: The texture to declare.
        :return: ``self``, so calls chain.
        """
        return self.declare(name, texture.sdl())

    def __len__(self) -> int:
        """:return: Number of top-level objects."""
        return len(self._objects)

    def sdl(self) -> str:
        """:return: The whole scene as POV-Ray SDL."""
        out: list[str] = ["// Generated by quiltwright.povgen — do not edit by hand."]
        if self.comment:
            out += [f"// {line}" for line in self.comment.strip().split("\n")]
        out.append(
            "// Authored right-handed, emitted left-handed (z negated)."
            if self.handedness == "flip-z"
            else "// Authored directly in POV-Ray coordinates."
        )
        out.append("// No camera: render_pov_quilt appends one off-axis camera per view.")
        out.append("")

        for name in self.includes:
            out.append(f'#include "{name}"')
        if self.includes:
            out.append("")

        if self.background is not None:
            r, g, b = parse_color(self.background)
            out.append(f"background {{ color rgb <{r:.5g}, {g:.5g}, {b:.5g}> }}")
        if self.ambient_light is not None:
            r, g, b = parse_color(self.ambient_light)
            out.append(f"global_settings {{ ambient_light rgb <{r:.5g}, {g:.5g}, {b:.5g}> }}")
        if self.background is not None or self.ambient_light is not None:
            out.append("")

        for name, text in self._declares:
            out.append(f"#declare {name} = {text}")
        if self._declares:
            out.append("")

        for light in self._lights:
            out.append(light.sdl(self.handedness))
        if self._lights:
            out.append("")

        for obj in self._objects:
            text = obj.sdl(self.handedness)
            if text:
                out.append(text)

        return "\n".join(out) + "\n"

    def write(self, path: str | Path) -> Path:
        """Write the scene to *path*.

        :param path: Destination ``.pov`` file; parent directories are created.
        :return: The resolved path written.
        """
        target = Path(path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.sdl(), encoding="utf-8")
        return target.resolve()

    def bounds(self) -> tuple[np.ndarray, np.ndarray] | None:
        """Axis-aligned bounds of the scene, in **right-handed** coordinates.

        Only the primitives with an obvious extent contribute
        (:class:`Sphere`, :class:`Cylinder`, :class:`Box`,
        :class:`SphereSweep`, and the members of a :class:`Union`);
        :class:`Instance` cannot be measured without resolving its prototype
        and is skipped.  Useful for placing lights and for handing
        ``focal_distance_for_range`` a real depth range.

        :return: ``(lo, hi)`` as ``(3,)`` arrays, or ``None`` if nothing
            measurable is in the scene.
        """
        los: list[np.ndarray] = []
        his: list[np.ndarray] = []

        def visit(obj: Primitive) -> None:
            if isinstance(obj, Sphere):
                c = np.asarray(obj.centre, dtype=float)
                los.append(c - obj.radius)
                his.append(c + obj.radius)
            elif isinstance(obj, Cylinder):
                a = np.asarray(obj.base, dtype=float)
                b = np.asarray(obj.cap, dtype=float)
                los.append(np.minimum(a, b) - obj.radius)
                his.append(np.maximum(a, b) + obj.radius)
            elif isinstance(obj, Box):
                a = np.asarray(obj.corner1, dtype=float)
                b = np.asarray(obj.corner2, dtype=float)
                los.append(np.minimum(a, b))
                his.append(np.maximum(a, b))
            elif isinstance(obj, SphereSweep):
                pts = np.atleast_2d(np.asarray(obj.points, dtype=float))
                rad = np.asarray(obj.radii, dtype=float)
                pad = float(rad.max()) if rad.size else 0.0
                los.append(pts.min(axis=0) - pad)
                his.append(pts.max(axis=0) + pad)
            elif isinstance(obj, Union):
                for member in obj.members:
                    visit(member)

        for obj in self._objects:
            visit(obj)
        if not los:
            return None
        return np.min(np.stack(los), axis=0), np.max(np.stack(his), axis=0)


# ---------------------------------------------------------------------------
# Camera bridge
# ---------------------------------------------------------------------------


def pov_camera_from_plotter(
    plotter,
    *,
    fov: float | None = None,
    handedness: str = "flip-z",
) -> PovCamera:
    """Carry a composed PyVista plotter's viewpoint over to a POV-Ray camera.

    VTK's ``camera.view_angle`` and :attr:`PovCamera.fov` are both *vertical*
    field of view in degrees, so the lens transfers one-to-one and the two
    renderers frame the scene identically.  Both quilt paths then apply the
    same dolly arithmetic, so passing the same *fov* to
    :func:`~quiltwright.lfd.render_quilt` and using this camera with
    :func:`~quiltwright.povray.render_pov_quilt` produces a matched sweep.

    :param plotter: A ``pv.Plotter`` whose camera is already placed.
    :param fov: Vertical FOV override in degrees; ``None`` keeps the
        plotter's own ``view_angle``, which is what you want when comparing
        the two backends.
    :param handedness: Coordinate conversion; must match the
        :class:`PovScene` the geometry was written with.
    :return: A camera whose ``look_at`` is the plotter's focal point, so the
        holographic focal plane lands where PyVista's does.
    """
    from quiltwright.povray import PovCamera  # deferred; see the note on imports

    camera = plotter.camera
    return PovCamera(
        location=to_pov(camera.position, handedness),
        look_at=to_pov(camera.focal_point, handedness),
        sky=to_pov(camera.up, handedness),
        fov=float(camera.view_angle) if fov is None else float(fov),
    )


def _rig_frame(up: Sequence[float]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build the ``(right, up, front)`` frame the light rig is placed in.

    *front* is ``cross(up, right)``, which reproduces the historical ``+y``-up
    offsets exactly when *up* is ``(0, 1, 0)``.

    :param up: World up direction; need not be normalised.
    :return: Three orthonormal ``(3,)`` vectors.
    :raises ValueError: If *up* is degenerate.
    """
    up_hat = np.asarray(up, dtype=float)
    norm = float(np.linalg.norm(up_hat))
    if norm < 1e-9:
        raise ValueError(f"up vector is degenerate: {tuple(up)}")
    up_hat = up_hat / norm

    # Prefer +x for "right"; fall back to +y when up is (nearly) the x axis.
    seed = np.array([1.0, 0.0, 0.0]) if abs(up_hat[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
    right = seed - up_hat * float(seed @ up_hat)
    right /= np.linalg.norm(right)
    return right, up_hat, np.cross(up_hat, right)


def lights_from_bounds(
    lo: Sequence[float],
    hi: Sequence[float],
    *,
    up: Sequence[float] = (0.0, 1.0, 0.0),
    intensity: float = 1.0,
    fill: bool = True,
) -> list[LightSource]:
    """A serviceable two-light rig sized to a scene's bounds.

    VTK's default is a headlight at the camera, which POV-Ray does not
    reproduce and which looks flat when ray-traced anyway.  This places a key
    light off the upper-front-right corner at roughly twice the scene radius,
    plus an optional shadowless fill opposite it — enough that a transcoded
    scene renders legibly before anyone tunes the lighting properly.

    **"Upper" means along** *up*, **which defaults to** ``+y``.  That default
    is right for a VTK scene and wrong for a ``+z``-up one — and ``+z``-up is
    what :mod:`kg_utils.viz3d` builds, so the mismatch is not hypothetical.
    Left unchanged there, the key light lands at ``centre_z - 1.4·radius``:
    below the ground, lighting the subject from underneath. Pass
    ``up=(0, 0, 1)`` and it goes overhead where it belongs.

    Only the up axis is inferred.  Which side of the subject counts as "front"
    follows from *up* and cannot know where your camera is, so a scene that
    needs the key on a particular side should place its own lights rather than
    lean on this.

    :param lo: Lower bound corner, right-handed.
    :param hi: Upper bound corner, right-handed.
    :param up: World up direction.  Defaults to ``+y`` for backward
        compatibility; ``(0, 0, 1)`` for a ``+z``-up scene.
    :param intensity: Key light brightness multiplier.
    :param fill: Add the shadowless fill light.
    :return: The light sources, key first.
    :raises ValueError: If *up* is degenerate.
    """
    lo_a = np.asarray(lo, dtype=float)
    hi_a = np.asarray(hi, dtype=float)
    centre = (lo_a + hi_a) / 2.0
    radius = float(np.linalg.norm(hi_a - lo_a)) / 2.0 or 1.0
    right, up_hat, front = _rig_frame(up)

    def place(r: float, u: float, f: float) -> tuple[float, ...]:
        return tuple(centre + (right * r + up_hat * u + front * f) * radius)

    key_level = intensity
    lights = [LightSource(position=place(1.4, 1.6, 1.4), color=(key_level, key_level, key_level))]
    if fill:
        fill_level = intensity * 0.35
        lights.append(
            LightSource(
                position=place(-1.6, 0.6, 1.2),
                color=(fill_level, fill_level, fill_level),
                shadowless=True,
            )
        )
    return lights


def fov_horizontal_to_vertical(fov_h: float, aspect: float) -> float:
    """Convert a horizontal FOV to the vertical one this package uses.

    POV-Ray's own ``angle`` keyword is *horizontal*, so a FOV lifted from a
    hand-written ``.pov`` file needs converting before it can be handed to
    :class:`PovCamera`, whose ``fov`` is vertical.

    :param fov_h: Horizontal field of view in degrees.
    :param aspect: Image width divided by height.
    :return: Vertical field of view in degrees.
    """
    half = math.radians(fov_h) / 2.0
    return math.degrees(2.0 * math.atan(math.tan(half) / aspect))
