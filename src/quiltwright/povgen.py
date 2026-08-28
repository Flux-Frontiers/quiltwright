"""
POV-Ray Scene Generation
========================

Writes ``.pov`` scenes from *analytic* primitives, so a scene composed in
Python -- or grown by a geometry engine such as ``kg_utils.viz3d`` -- can be
ray-traced by :func:`~quiltwright.povray.render_pov_quilt` instead of
rasterised by VTK.

**Why analytic rather than a mesh dump.**  By the time geometry reaches a
``pv.Plotter`` it is already tessellated: ``pv.Sphere`` is a triangulated
ball, and a swept tube is a strip of quads.  Dumping those triangles into a
POV-Ray ``mesh2`` reproduces the scene faithfully but keeps VTK's facets and
costs a great deal of text, re-parsed once per view -- 48 times for a Portrait
quilt.  Re-emitting the *intent* instead -- a limb is a swept path of radii, a
leaf is a ball at a point -- gives POV-Ray its own exact primitives: an exact
silhouette at any zoom, and a bounding hierarchy the ray-tracer is good at.

Measured on a 3000-leaf organic tree from ``kg_utils.viz3d`` (192k triangles,
159k vertices once tessellated): **839 KB** of analytic SDL with oriented leaf
instances, or 508 KB with plain spheres, against roughly **12.5 MB** for the
equivalent ``mesh2`` -- 15x to 25x smaller, and better looking, since the
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
converted -- it holds POV-Ray coordinates, and
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
to a :class:`~quiltwright.povray.PovCamera` instead -- VTK's ``view_angle``
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

Part of Quiltwright -- https://github.com/suchanek/quiltwright

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np

if TYPE_CHECKING:  # pragma: no cover - typing only
    from quiltwright.povray import PovCamera

# ``PovCamera`` lives in :mod:`quiltwright.povray`, which imports
# :mod:`quiltwright.lfd` for the quilt assembler, which imports PyVista when it
# is installed.  Importing it at module scope would therefore drag the whole
# rendering stack into a module whose entire point is not needing one -- so it
# is imported inside :func:`pov_camera_from_plotter`, the only function here
# that constructs one, and which by definition already has a live plotter.

__author__ = "Eric G. Suchanek, PhD"

#: A vector in any accepted spelling.  A NumPy array is not a
#: ``Sequence[float]``: it is not registered with the ABC, and its elements are
#: ``np.floating``.  The geometry engines this module consumes -- ``kg_utils.viz3d``,
#: PyVista, VTK -- all emit arrays, so the signatures below accept both forms.
Vec = Sequence[float] | np.ndarray

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


def to_pov(point: Vec, handedness: str = "flip-z") -> tuple[float, float, float]:
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


def parse_color(color: str | Vec) -> tuple[float, float, float]:
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


def _vec(v: Vec) -> str:
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
    photometrically -- POV-Ray's lighting model is not VTK's, and a scene worth
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
        passes light through unchanged -- the correct analogue of VTK's alpha.
        POV-Ray's ``filter`` is *not*: it tints everything seen through the
        surface by the surface's own colour.
    :param finish: Shading parameters.
    """

    color: str | Vec = "#cccccc"
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
class Mesh2(Primitive):
    """A POV-Ray ``mesh2`` -- shared vertex, normal and texture lists.

    The fallback this module's docstring names: for geometry with no analytic
    description -- an isosurface, a volume, a molecular cartoon exported from
    somewhere else -- there is nothing to re-emit the intent of, and triangles
    are the honest representation.

    Prefer this over many separate one-triangle objects.  A generator that
    emits a ``mesh2`` per face pays for a vertex list, a normal list and a
    texture list on every triangle: PyMOL's ``cmd.get_povray()`` does exactly
    that, and an OmpF porin trimer's cartoon costs 41 MB that way against
    7.2 MB coalesced.  :func:`coalesce_mesh2` performs that merge on text
    already written; this class avoids needing it.

    **Winding.**  Negating *z* is a reflection, and a reflection reverses
    triangle orientation, so every face's indices are emitted in reverse under
    ``handedness="flip-z"``.  Without that, POV-Ray sees inward-facing normals
    and lights the mesh from behind.  ``normal_indices`` is reversed in step,
    since it is parallel to ``faces``.

    :param vertices: ``(N, 3)`` points in right-handed world coordinates.
    :param faces: Triples of indices into *vertices*.
    :param normals: ``(M, 3)`` vectors, right-handed; ``None`` for a faceted
        mesh, which POV-Ray shades flat.
    :param normal_indices: Triples of indices into *normals*, parallel to
        *faces*.  Defaults to *faces* when *normals* is given, which is right
        whenever there is one normal per vertex.
    :param textures: Textures the faces index into, for per-vertex colour.
    :param face_textures: Triples of indices into *textures*, one per face
        corner, parallel to *faces*.
    :param texture: A texture for the whole mesh.  Independent of *textures*;
        POV-Ray applies it where the per-vertex list does not reach.
    """

    vertices: Sequence[Sequence[float]]
    faces: Sequence[Sequence[int]]
    normals: Sequence[Sequence[float]] | None = None
    normal_indices: Sequence[Sequence[int]] | None = None
    textures: Sequence[Texture | str] = ()
    face_textures: Sequence[Sequence[int]] | None = None
    texture: Texture | str | None = None

    def __post_init__(self) -> None:
        if self.normal_indices is not None and self.normals is None:
            raise ValueError("normal_indices given without normals")
        if self.face_textures is not None and not self.textures:
            raise ValueError("face_textures given without textures")
        for name, seq in (
            ("normal_indices", self.normal_indices),
            ("face_textures", self.face_textures),
        ):
            if seq is not None and len(seq) != len(self.faces):
                raise ValueError(f"{name} has {len(seq)} entries, faces has {len(self.faces)}")

    def sdl(self, handedness: str = "flip-z") -> str:
        """:return: ``mesh2 { vertex_vectors {...} ... face_indices {...} }``."""
        flip = handedness == "flip-z"

        def block(keyword: str, items: Sequence[str]) -> str:
            return f"  {keyword} {{ {len(items)},\n    " + ",\n    ".join(items) + "\n  }\n"

        out = ["mesh2 {\n"]
        out.append(block("vertex_vectors", [_vec(to_pov(v, handedness)) for v in self.vertices]))

        if self.normals is not None:
            # A normal is a direction, not a position, but the reflection acts
            # on it the same way -- mirroring the world mirrors its normals.
            out.append(block("normal_vectors", [_vec(to_pov(n, handedness)) for n in self.normals]))

        if self.textures:
            out.append(block("texture_list", [_texture_suffix(t).strip() for t in self.textures]))

        def wind(triple: Sequence[int]) -> tuple[int, int, int]:
            a, b, c = (int(i) for i in triple)
            return (a, c, b) if flip else (a, b, c)

        faces: list[str] = []
        for i, face in enumerate(self.faces):
            entry = "<{}, {}, {}>".format(*wind(face))
            if self.face_textures is not None:
                entry += ", " + ", ".join(str(int(t)) for t in wind(self.face_textures[i]))
            faces.append(entry)
        out.append(block("face_indices", faces))

        if self.normals is not None:
            source = self.normal_indices if self.normal_indices is not None else self.faces
            out.append(block("normal_indices", ["<{}, {}, {}>".format(*wind(t)) for t in source]))

        suffix = _texture_suffix(self.texture)
        out.append((suffix.strip() + "\n") if suffix else "")
        out.append("}")
        return "".join(out)


def _matching_brace(text: str, open_at: int) -> int:
    """Index just past the ``}`` closing the ``{`` at *open_at*.

    Brace counting rather than a regex: ``mesh2`` blocks contain nested
    ``texture { pigment { ... } }``, which no non-recursive pattern closes
    correctly, and getting it wrong truncates geometry silently.

    :raises ValueError: If the brace is never closed.
    """
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    raise ValueError(f"unclosed brace at {open_at}")


def _named_list(body: str, keyword: str) -> str | None:
    """Contents of ``keyword { ... }`` inside *body*, or ``None`` if absent."""
    at = body.find(keyword)
    if at < 0:
        return None
    open_at = body.find("{", at)
    if open_at < 0:
        return None
    return body[open_at + 1 : _matching_brace(body, open_at) - 1]


def _top_level_items(items: str) -> list[str]:
    """Split a POV list on commas that are not inside brackets or braces."""
    out, depth, start = [], 0, 0
    for i, ch in enumerate(items):
        if ch in "{<":
            depth += 1
        elif ch in "}>":
            depth -= 1
        elif ch == "," and depth == 0:
            out.append(items[start:i].strip())
            start = i + 1
    tail = items[start:].strip()
    if tail:
        out.append(tail)
    return out


def coalesce_mesh2(text: str) -> str:
    """Merge every ``mesh2`` in *text* into one with shared lists.

    Written for generators that emit one ``mesh2`` per triangle, each carrying
    its own three-entry vertex, normal and texture lists.  PyMOL's
    ``cmd.get_povray()`` is the case in hand: a GFP cartoon arrives as 17,140
    single-face meshes and 9.3 MB, and leaves as one mesh and 1.5 MB, because
    51,420 vertices collapse to 8,654 and 51,420 textures to 215.

    The merge is exact.  Vertices, normals and textures are deduplicated on
    their emitted text, so nothing is fused that was not already identical,
    and ``normal_indices`` is carried through explicitly rather than being
    assumed parallel to the faces -- which preserves per-face normal
    assignment, so smooth shading is unchanged.

    Text that is not a ``mesh2`` is left exactly where it was; the merged mesh
    replaces the first one and the rest are dropped.  A block that does not
    parse is left alone rather than discarded, so a scene never loses geometry
    to this function.

    :param text: POV-Ray source.
    :return: The same source with its meshes merged.
    """
    blocks: list[tuple[int, int, str]] = []
    at = 0
    while True:
        found = text.find("mesh2", at)
        if found < 0:
            break
        open_at = text.find("{", found)
        if open_at < 0:
            break
        try:
            end = _matching_brace(text, open_at)
        except ValueError:
            break
        blocks.append((found, end, text[open_at + 1 : end - 1]))
        at = end

    if len(blocks) < 2:
        return text

    verts: dict[str, int] = {}
    norms: dict[str, int] = {}
    texs: dict[str, int] = {}
    faces: list[str] = []
    normal_idx: list[str] = []
    kept: list[tuple[int, int]] = []
    saw_normals = False

    def intern(store: dict[str, int], key: str) -> int:
        got = store.get(key)
        if got is None:
            got = store[key] = len(store)
        return got

    for start, end, body in blocks:
        v_raw = _named_list(body, "vertex_vectors")
        f_raw = _named_list(body, "face_indices")
        if v_raw is None or f_raw is None:
            kept.append((start, end))
            continue
        n_raw = _named_list(body, "normal_vectors")
        t_raw = _named_list(body, "texture_list")
        ni_raw = _named_list(body, "normal_indices")

        v_local = [intern(verts, t) for t in _top_level_items(v_raw)[1:]]
        n_local = [intern(norms, t) for t in _top_level_items(n_raw)[1:]] if n_raw else []
        t_local = [intern(texs, t) for t in _top_level_items(t_raw)[1:]] if t_raw else []
        saw_normals = saw_normals or bool(n_local)

        f_items = _top_level_items(f_raw)[1:]
        ni_items = _top_level_items(ni_raw)[1:] if ni_raw else []

        # face_indices entries are "<a,b,c>" optionally followed by bare
        # texture indices, one per corner.  Walk rather than zip: the trailing
        # indices are siblings of the vector, not a nested list.
        i = 0
        face_no = 0
        while i < len(f_items):
            tri = f_items[i]
            i += 1
            corners = [int(x) for x in tri.strip("<> ").split(",")]
            entry = "<{}, {}, {}>".format(*(v_local[c] for c in corners))
            picks = []
            while i < len(f_items) and not f_items[i].startswith("<"):
                picks.append(int(f_items[i]))
                i += 1
            if picks and t_local:
                entry += ", " + ", ".join(str(t_local[p]) for p in picks)
            faces.append(entry)

            if n_local:
                if face_no < len(ni_items):
                    nc = [int(x) for x in ni_items[face_no].strip("<> ").split(",")]
                else:
                    nc = corners
                normal_idx.append("<{}, {}, {}>".format(*(n_local[c] for c in nc)))
            face_no += 1

    if not faces:
        return text

    def block(keyword: str, items: Sequence[str]) -> str:
        return f"  {keyword} {{ {len(items)},\n    " + ",\n    ".join(items) + "\n  }\n"

    merged = ["mesh2 {\n", block("vertex_vectors", list(verts))]
    if saw_normals:
        merged.append(block("normal_vectors", list(norms)))
    if texs:
        merged.append(block("texture_list", list(texs)))
    merged.append(block("face_indices", faces))
    if saw_normals:
        merged.append(block("normal_indices", normal_idx))
    merged.append("}")
    mesh = "".join(merged)

    keep = set(kept)
    out, cursor, placed = [], 0, False
    for start, end, _ in blocks:
        out.append(text[cursor:start])
        if (start, end) in keep:
            out.append(text[start:end])
        elif not placed:
            out.append(mesh)
            placed = True
        cursor = end
    out.append(text[cursor:])
    return "".join(out)


@dataclass(frozen=True)
class SphereSweep(Primitive):
    """A POV-Ray ``sphere_sweep`` -- a tapered tube through a polyline.

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
    translate: Vec | None = None
    scale: Vec | float | None = None
    matrix: np.ndarray | None = None
    texture: Texture | str | None = None

    def sdl(self, handedness: str = "flip-z") -> str:
        """:return: ``object { Name scale <..> matrix <..> translate <..> }``."""
        parts = [self.name]
        if self.scale is not None:
            scale = self.scale
            # ``np.ndim`` reads 0 for a float, a NumPy scalar and a 0-d array
            # alike; ``isinstance`` does not.  No type checker follows it,
            # hence the casts.
            if np.ndim(scale) == 0:
                parts.append(f"scale {float(cast('float', scale)):.6g}")
            else:
                parts.append(f"scale {_vec(cast('Vec', scale))}")
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
    color: str | Vec = "#ffffff"
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
    deliberately generic -- it knows about polylines with radii, not about
    trees -- so any producer of swept paths can use it.

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
    deterministically, so a given input always produces the same file -- but
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
    file.  It writes **no camera** -- see the module docstring.

    :param background: Hex or ``(r, g, b)`` background colour, or ``None`` to
        leave POV-Ray's default (black).
    :param includes: ``#include`` file names, e.g. ``"colors.inc"``.
    :param handedness: ``"flip-z"`` (default) to author in right-handed world
        coordinates, ``"none"`` to author directly in POV-Ray's.
    :param ambient_light: Global ``ambient_light`` colour, or ``None``.
    :param comment: Free text written into the file header.
    """

    background: str | Vec | None = None
    includes: list[str] = field(default_factory=list)
    handedness: str = "flip-z"
    ambient_light: str | Vec | None = None
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
        out: list[str] = ["// Generated by quiltwright.povgen -- do not edit by hand."]
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

        # Without this, POV-Ray 3.7 treats every colour value in the scene as
        # already linear light and re-encodes it to sRGB on output -- a
        # colour authored as a plain 0..1 number (or via parse_color()'s hex
        # decode) comes out of the render 2-3x brighter than specified.
        # #1a1a1e (0.10, 0.10, 0.12) renders as (90, 90, 96), not (26, 26, 30).
        # `assumed_gamma 1.0` (POV-Ray's own fallback when nothing is
        # declared) does not fix this -- it is the same undeclared behaviour.
        # Nor is `2.2` exact: a pure power-law gamma overshoots the piecewise
        # sRGB curve real displays use. `srgb` is POV-Ray's name for that
        # exact curve, and round-trips a hex colour losslessly -- measured
        # against this file's own colour, #1a1a1e comes back out as
        # (26, 26, 30), pixel for pixel.
        out.append("global_settings { assumed_gamma srgb }")
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

        **Instancing is what this method cannot see, and instancing is the
        reason to use this module** -- so check that the two do not collide in
        your scene.  A tree gets away with it: its wood is swept and reaches
        the crown, so the bounds cover the subject even though every leaf is an
        instance.  A scene whose subject *is* the instances does not.  Ten
        thousand instanced boulders around one measurable marker post return
        the bounds of the post, and lights placed from that land inside the
        scene while a camera framed from it fills the tile with one prop.  An
        entirely instanced scene returns ``None``.

        Two ways out: keep one measurable primitive that spans the subject --
        a :class:`Box` with no texture is invisible to a render but visible
        here -- or track the extent as you place the instances, which the
        producer usually knows anyway, and skip this.

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


def _rig_frame(up: Vec) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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
    lo: Vec,
    hi: Vec,
    *,
    up: Vec = (0.0, 1.0, 0.0),
    key_side: Vec | None = None,
    intensity: float = 1.0,
    fill: bool = True,
    rim: bool = False,
) -> list[LightSource]:
    """A serviceable two-light rig sized to a scene's bounds.

    VTK's default is a headlight at the camera, which POV-Ray does not
    reproduce and which looks flat when ray-traced anyway.  This places a key
    light off the upper-front-right corner at roughly twice the scene radius,
    plus an optional shadowless fill opposite it -- enough that a transcoded
    scene renders legibly before anyone tunes the lighting properly.

    **"Upper" means along** *up*, **which defaults to** ``+y``.  That default
    is right for a VTK scene and wrong for a ``+z``-up one -- and ``+z``-up is
    what :mod:`kg_utils.viz3d` builds, so the mismatch is not hypothetical.
    Left unchanged there, the key light lands at ``centre_z - 1.4·radius``:
    below the ground, lighting the subject from underneath. Pass
    ``up=(0, 0, 1)`` and it goes overhead where it belongs.

    **Say which side the camera is on.**  Bounds cannot tell you: the derived
    side is whatever falls out of *up*, and for a ``+z``-up scene that is
    ``+y`` -- the far side from a :func:`kg_utils.viz3d.frame_tree` camera,
    which stands off along ``-y``.  Leave *key_side* unset and the rig lights
    the back of the subject while the lens looks at its shadow.  The scene is
    perfectly lit and the picture is dark, which is a hard failure to read
    backwards from an image.

    :param lo: Lower bound corner, right-handed.
    :param hi: Upper bound corner, right-handed.
    :param up: World up direction.  Defaults to ``+y`` for backward
        compatibility; ``(0, 0, 1)`` for a ``+z``-up scene.
    :param key_side: Direction from the subject toward the side the key should
        come from -- normally the camera's own standoff direction, so the lens
        sees the lit face.  Only its component across *up* is used, so it
        chooses a side without re-deciding the key's elevation.  ``None``
        derives one from *up*, which is the historical behaviour and is
        unlikely to be the side you want.
    :param intensity: Key light brightness multiplier.
    :param fill: Add the shadowless fill light.
    :param rim: Add a dim shadowless light behind the subject, so it separates
        from the background instead of silhouetting into it.  Worth it when the
        background is dark or the subject is intricate at its edges -- a canopy,
        a wireframe -- and wasted on a solid form against a bright ground.
    :return: The light sources, key first.
    :raises ValueError: If *up* is degenerate.
    """
    lo_a = np.asarray(lo, dtype=float)
    hi_a = np.asarray(hi, dtype=float)
    centre = (lo_a + hi_a) / 2.0
    radius = float(np.linalg.norm(hi_a - lo_a)) / 2.0 or 1.0
    right, up_hat, front = _rig_frame(up)
    if key_side is not None:
        side = np.asarray(key_side, dtype=float)
        norm = float(np.linalg.norm(side))
        if norm < 1e-9:
            raise ValueError(f"key_side is degenerate: {tuple(key_side)}")
        side = side / norm
        # Keep only the part across *up*, so the caller's vector chooses a
        # side without also re-deciding the key's elevation.
        front = side - up_hat * float(side @ up_hat)
        norm = float(np.linalg.norm(front))
        if norm < 1e-9:
            raise ValueError("key_side is parallel to up; it names a side, not a height")
        front /= norm
        right = np.cross(front, up_hat)

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
    if rim:
        rim_level = intensity * 0.25
        lights.append(
            LightSource(
                position=place(-0.3, 1.3, -1.7),
                color=(rim_level, rim_level, rim_level),
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


def fov_vertical_to_horizontal(fov_v: float, aspect: float) -> float:
    """Convert a vertical FOV to POV-Ray's horizontal ``angle``.

    The inverse of :func:`fov_horizontal_to_vertical`, and needed in the
    other direction: a scene composed from ``right``/``up`` vectors states
    its lens vertically, while :class:`PovCamera` and POV-Ray's ``angle``
    keyword both want the horizontal one.

    :param fov_v: Vertical field of view in degrees.
    :param aspect: Image width divided by height.
    :return: Horizontal field of view in degrees.
    """
    half = math.radians(fov_v) / 2.0
    return math.degrees(2.0 * math.atan(math.tan(half) * aspect))


def ground_slab(
    lo: Vec,
    hi: Vec,
    *,
    up: Vec = (0.0, 1.0, 0.0),
    size: float = 3.0,
    thickness: float = 0.4,
    base: float | None = None,
    texture: Texture | str | None = None,
) -> Box:
    """A finite floor under a subject, for it to cast a shadow onto.

    Ray-tracing gives a contact shadow, and a contact shadow is most of what
    makes a subject look *placed* rather than floating.  VTK's headlight casts
    nothing, so a transcoded scene that looked fine rasterised will look
    untethered until it has one of these.

    Deliberately finite.  An effectively infinite plane guarantees off-budget
    disparity at the horizon on a light-field panel; a slab a few subject-widths
    across catches the shadow and stops.

    Its top face sits at the subject's *base* along *up* -- the minimum of the
    bounds, not below them -- so the subject stands on the floor rather than
    hovering over one parked underneath.

    :param lo: Lower bound corner of the subject, right-handed.
    :param hi: Upper bound corner of the subject, right-handed.
    :param up: World up direction; the slab lies perpendicular to it.
    :param size: Slab edge as a multiple of the subject's widest horizontal
        extent, so one value suits subjects of any scale.
    :param thickness: Slab depth along *up*.  Only its silhouette shows, but a
        zero-thickness box is degenerate.
    :param base: Level along *up* for the top face.  ``None`` takes the
        subject's own minimum, which is right when the bounds *are* the
        subject.  Pass it when they are not: a swept tube's bounds are padded
        by its radius, so a trunk rooted at ``z = 0`` reports a minimum of
        ``-r`` and the floor would sit that much low.
    :param texture: Texture, a declared name, or ``None``.
    :return: The slab as a :class:`Box`.
    :raises ValueError: If *up* is degenerate.
    """
    lo_a = np.asarray(lo, dtype=float)
    hi_a = np.asarray(hi, dtype=float)
    _, up_hat, _ = _rig_frame(up)

    axis = int(np.argmax(np.abs(up_hat)))
    flat = [i for i in range(3) if i != axis]
    width = max(float(hi_a[i] - lo_a[i]) for i in flat) or 1.0
    half = width * size / 2.0
    level = float(lo_a[axis]) if base is None else float(base)

    corner1 = np.zeros(3)
    corner2 = np.zeros(3)
    for i in flat:
        centre = (lo_a[i] + hi_a[i]) / 2.0
        corner1[i], corner2[i] = centre - half, centre + half
    sign = 1.0 if up_hat[axis] >= 0 else -1.0
    corner1[axis], corner2[axis] = level - sign * thickness, level

    return Box(corner1=tuple(corner1), corner2=tuple(corner2), texture=texture)


def pov_camera_from_frame(
    frame,
    look_at: Sequence[float] | None = None,
    up: Sequence[float] = (0.0, 0.0, 1.0),
    *,
    fov: float = 14.0,
    zoom: float = 1.0,
    handedness: str = "flip-z",
):
    """Convert a renderer-independent camera frame into a :class:`PovCamera`.

    The sibling of :func:`pov_camera_from_plotter`, for callers that have no
    plotter -- a headless box writing ``.pov`` files with no VTK installed, which
    is the whole point of this module.

    *frame* may be either three sequences (``position, look_at, up``) or a
    single object carrying ``.position``, ``.focal_point`` and ``.up``, which is
    what ``kg_utils.viz3d.frame_tree`` returns.  It is duck-typed on purpose:
    this package does not import that one, and must not.

    **The conversion is the entire point.**  :class:`PovCamera` holds POV-Ray
    coordinates; a frame computed in the right-handed world the scene was
    authored in is not one.  Hand an unconverted camera to
    :func:`~quiltwright.povray.camera_block` and the geometry sits at negative
    *z* while the lens aims at positive *z*, and POV-Ray renders an immaculate
    picture of empty space -- with nothing wrong in the scene file and every
    assertion that compares right-handed against right-handed passing.

    :param frame: ``position`` sequence, or a frame object as described above.
    :param look_at: Focal point, when *frame* is a bare position.
    :param up: Up vector, when *frame* is a bare position.
    :param fov: Vertical field of view in degrees.
    :param zoom: Dolly factor toward the focal point applied after framing;
        ``>1`` fills more of the tile, which is what drives perceived depth.
    :param handedness: Coordinate conversion; must match the :class:`PovScene`
        the geometry was written with.
    :return: The camera, in POV-Ray coordinates.
    :raises ValueError: If *zoom* is not positive.
    """
    from quiltwright.povray import PovCamera  # deferred; see the note on imports

    if hasattr(frame, "position") and hasattr(frame, "focal_point"):
        position, look_at, up = frame.position, frame.focal_point, getattr(frame, "up", up)
    else:
        position = frame
        if look_at is None:
            raise ValueError("look_at is required when frame is a bare position")

    if zoom <= 0:
        raise ValueError(f"zoom must be positive, got {zoom}")

    eye = np.asarray(position, dtype=float)
    target = np.asarray(look_at, dtype=float)
    eye = target + (eye - target) / float(zoom)

    return PovCamera(
        location=to_pov(eye, handedness),
        look_at=to_pov(target, handedness),
        sky=to_pov(up, handedness),
        fov=float(fov),
    )


def instances_by_color(
    name: str,
    points: np.ndarray,
    directions: np.ndarray | None,
    palette: Sequence[str | Vec],
    index: Sequence[int] | np.ndarray,
    *,
    scale: Sequence[float] | float | None = None,
    finish: Finish | None = None,
    prefix: str = "Tint",
) -> tuple[list[tuple[str, Texture]], list[Union]]:
    """Group instances of one prototype into a union per colour.

    A crown of ten thousand blades in five colours is five textures and five
    unions, not ten thousand of each.  POV-Ray parses each texture once and
    every instance is then a single line.

    :param name: Declared prototype identifier the instances reference.
    :param points: ``(M, 3)`` positions, right-handed.
    :param directions: ``(M, 3)`` aim vectors, or ``None`` for unoriented.
    :param palette: Colours to declare, one texture each.
    :param index: ``(M,)`` index into *palette*, one per point.
    :param scale: Per-axis or scalar scale applied to the prototype.
    :param finish: Finish shared by every declared texture.
    :param prefix: Identifier stem for the declared textures.
    :return: ``(declarations, unions)`` -- declare each ``(name, texture)`` on
        the scene, then add the unions.
    :raises ValueError: If *index* does not match *points* in length.
    """
    pts = np.atleast_2d(np.asarray(points, dtype=float))
    if pts.size == 0:
        return [], []
    idx = np.asarray(index, dtype=int)
    if idx.shape[0] != pts.shape[0]:
        raise ValueError(f"index length {idx.shape[0]} does not match {pts.shape[0]} points")

    dirs = None if directions is None else np.atleast_2d(np.asarray(directions, dtype=float))
    # ``Texture.finish`` is non-optional with a ``default_factory``, so ``None``
    # here means "keep the default".  ``Finish()`` is what the factory builds.
    resolved = Finish() if finish is None else finish
    declarations = [
        (f"{prefix}{i}", Texture(color=colour, finish=resolved)) for i, colour in enumerate(palette)
    ]

    unions: list[Union] = []
    for i, (texture_name, _) in enumerate(declarations):
        mask = idx == i
        if not mask.any():
            continue
        members = instances_from_frames(
            name, pts[mask], None if dirs is None else dirs[mask], texture=texture_name
        )
        if scale is not None:
            members = [replace(m, scale=scale) for m in members]
        unions.append(Union(members))
    return declarations, unions


def swept_scene(
    sweeps: Iterable[tuple[np.ndarray, np.ndarray]],
    *,
    sweep_color: str | Vec = "#6b4a2f",
    sweep_finish: Finish | None = None,
    instances: tuple[np.ndarray, np.ndarray | None] | None = None,
    instance_shape: Sequence[float] = (1.0, 1.0, 1.0),
    instance_radius: float = 1.0,
    instance_palette: Sequence[str | Vec] = (),
    instance_index: Sequence[int] | None = None,
    instance_finish: Finish | None = None,
    clouds: Iterable[tuple[np.ndarray, float, str | Vec, float]] = (),
    cloud_finish: Finish | None = None,
    up: Sequence[float] = (0.0, 0.0, 1.0),
    sky: str | Vec | None = None,
    ambient: str | Vec | None = None,
    lights: bool = True,
    key_side: Sequence[float] | None = None,
    rim_light: bool = False,
    ground: float = 0.0,
    ground_base: float | None = None,
    ground_color: str | Vec = "#2d4a1e",
    ground_finish: Finish | None = None,
    brightness: float = 1.0,
    comment: str = "",
) -> PovScene:
    """Compose a lit scene from swept paths, instanced glyphs and point clouds.

    Named for its geometry rather than for any subject: it knows swept tubes,
    oriented instances and scattered spheres, and nothing about what they
    depict.  A tree is one caller -- limbs are the sweeps, leaves the instances,
    annotation clouds the spheres -- but so is any producer with the same three
    shapes.  It imports no domain package and its arguments are arrays and
    colours throughout.

    What it saves a caller is not the primitives, which are already here, but
    the assembly: prototype declaration, colour grouping, light rig, floor, and
    the order those go in.

    **Lights are placed before the ground.**  The rig is sized from the scene
    bounds and the floor is deliberately wider than the subject, so measuring
    after laying it makes the "scene radius" the slab's half-diagonal -- which
    pushes the key light far enough out to flatten the subject and shrink its
    shadow to nothing.  Getting that order wrong is silent; the scene is
    structurally perfect and looks dead.

    :param sweeps: ``[(points, radii), ...]`` swept paths.
    :param sweep_color: Colour for every sweep.
    :param sweep_finish: Finish for the sweeps.
    :param instances: ``(points, directions)``; *directions* may be ``None``.
    :param instance_shape: Per-axis shape of the instanced prototype, before
        *instance_radius* scales it.  ``(1, 1, 1)`` is a ball.
    :param instance_radius: Prototype radius.
    :param instance_palette: Colours for the instances.
    :param instance_index: Per-instance index into *instance_palette*; ``None``
        puts every instance in the first colour.
    :param instance_finish: Finish shared by the instance textures.
    :param clouds: ``[(points, radius, colour, opacity), ...]`` scattered
        spheres -- annotation, typically.
    :param cloud_finish: Finish for the clouds.
    :param up: World up direction, for the light rig and the floor.
    :param sky: Background colour, or ``None`` for POV-Ray's default black.
    :param ambient: Global ambient light colour, or ``None``.
    :param ground: Floor edge as a multiple of the subject's width; ``0`` omits
        it.  See :func:`ground_slab` for why a contact shadow matters.
    :param ground_color: Floor colour.
    :param ground_finish: Floor finish.  Remember it is multiplied by
        *brightness*: a diffuse tuned for a unit key clips at a high one.
    :param brightness: Key-light multiplier.
    :param lights: Place the rig.  ``False`` leaves the scene unlit, which
        POV-Ray renders black -- useful only when the caller supplies its own.
    :param key_side: Which side the key comes from -- pass the camera's
        standoff direction, or the lens looks at the subject's shadow.  See
        :func:`lights_from_bounds`.
    :param rim_light: Add the back light; see :func:`lights_from_bounds`.
    :param ground_base: Level along *up* for the floor's top face; see
        :func:`ground_slab`.
    :param comment: Free text for the file header.
    :return: The composed :class:`PovScene`.
    """
    scene = PovScene(background=sky, ambient_light=ambient, comment=comment)

    bark = Texture(color=sweep_color, finish=Finish() if sweep_finish is None else sweep_finish)
    scene.declare_texture("SweptTex", bark)
    swept = sphere_sweeps_from_paths(sweeps, texture="SweptTex")
    if swept:
        scene.add(Union(swept))

    if instances is not None:
        points, directions = instances
        points = np.atleast_2d(np.asarray(points, dtype=float))
        if points.size:
            scene.declare("Glyph", Sphere(centre=(0.0, 0.0, 0.0), radius=1.0))
            palette = list(instance_palette) or [sweep_color]
            index = (
                np.zeros(points.shape[0], dtype=int)
                if instance_index is None
                else np.asarray(instance_index, dtype=int)
            )
            declarations, unions = instances_by_color(
                "Glyph",
                points,
                directions,
                palette,
                index,
                scale=tuple(float(instance_radius) * a for a in instance_shape),
                finish=instance_finish,
            )
            for texture_name, texture in declarations:
                scene.declare_texture(texture_name, texture)
            scene.add(unions)

    for cloud_points, radius, colour, opacity in clouds:
        texture = Texture(
            color=colour,
            opacity=opacity,
            **({} if cloud_finish is None else {"finish": cloud_finish}),
        )
        spheres = spheres_from_points(cloud_points, radius, texture)
        if spheres:
            scene.add(Union(spheres))

    bounds = scene.bounds()
    if bounds is None:
        return scene

    if lights:
        for light in lights_from_bounds(
            *bounds, up=up, key_side=key_side, intensity=brightness, rim=rim_light
        ):
            scene.add_light(light)

    if ground > 0:
        scene.add(
            ground_slab(
                *bounds,
                up=up,
                size=ground,
                base=ground_base,
                texture=Texture(
                    color=ground_color,
                    finish=Finish() if ground_finish is None else ground_finish,
                ),
            )
        )
    return scene
