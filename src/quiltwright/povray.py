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
while leaving its geometry, textures and lighting untouched.  One wrapper is
written per view, each carrying that view's camera.

**Off-axis projection.**  POV-Ray builds its frustum from ``location`` (the
eye), ``direction`` (which places the centre of the image plane) and
``right``/``up`` (which span it), and it does *not* re-orthogonalise those
vectors.  Tilting ``direction`` while holding ``right`` and ``up`` fixed
therefore shears the frustum, leaving the image plane parallel to itself —
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
That warning is expected and benign — it is the shear.

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

**Requirements** — a ``povray`` binary on ``PATH`` (``brew install povray``),
plus pillow for quilt assembly (``poetry install --with viz``).

Typical usage::

    from quiltwright.lfd import QUILT_PRESETS, save_quilt
    from quiltwright.povray import PovCamera, render_pov_quilt

    camera = PovCamera(location=(35, 18.5, 0), look_at=(35, 20, 58), fov=14)
    spec = QUILT_PRESETS["portrait"]
    quilt = render_pov_quilt("museum.pov", spec, camera,
                             include_paths=["../myinclude"])
    save_quilt(quilt, "museum", spec)   # -> museum_qs8x6a0.75.png

Part of Quiltwright — https://github.com/suchanek/quiltwright
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

from quiltwright.lfd import QuiltSpec, assemble_quilt, view_disparity, view_offsets

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

    :param location: Eye position ``(x, y, z)`` in scene units.
    :param look_at: Point the camera is aimed at.  Becomes the focal plane.
    :param sky: Up-hint used to build the camera basis, matching POV-Ray's
        ``sky`` vector.  Must not be parallel to the view direction.
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

        POV-Ray is left-handed — with ``up`` at ``+y`` and ``direction`` at
        ``+z``, ``right`` is ``+x`` — which is what ``right = sky x forward``
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
        Neither survives contact with a quilt unedited — the focal plane
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
        :param fov: Vertical field of view in degrees — usually the scene's
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
        base = cls(location=tuple(location), look_at=tuple(aim), sky=sky, fov=fov)
        forward, right, _ = base.basis()
        distance = base.focal_distance if focal_distance is None else float(focal_distance)
        if distance <= 0:
            raise ValueError(f"focal_distance must be positive, got {distance}")
        eye = np.asarray(base.location, dtype="d") + right * float(lateral_shift)
        return cls(
            location=tuple(float(c) for c in eye),
            look_at=tuple(float(c) for c in eye + forward * distance),
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
    focal = camera.focal_distance
    eye = np.asarray(camera.location, dtype="d") + right * offset
    # Shear: slide the image-plane centre back onto the original view axis so
    # the focal plane stays pinned across the sweep.  Never emit `angle` here
    # — it would override |direction| and silently undo this.
    direction = forward * dist - right * (offset * dist / focal)
    return (
        "camera {\n"
        f"  location  {_vec(eye)}\n"
        f"  direction {_vec(direction)}\n"
        f"  right     {_vec(right * aspect)}\n"
        f"  up        {_vec(up)}\n"
        "}\n"
    )


# ---------------------------------------------------------------------------
# Framing: sweep extent, wall clearance, depth budget
# ---------------------------------------------------------------------------


def sweep_extent(spec: QuiltSpec, focal_distance: float) -> float:
    """Half-width of the lateral eye travel the quilt's view sweep needs.

    The outermost views sit ``focal_distance * tan(cone/2)`` to either side
    of the centre view — the largest magnitude in
    :func:`~quiltwright.lfd.view_offsets`, in closed form.  For an object on
    a turntable that space is empty; inside a room it is furniture and
    walls, so compare it against a measured :class:`Clearance` before
    committing to a render.

    :param spec: Quilt specification (supplies the view cone).
    :param focal_distance: Camera-to-focal-plane distance, in scene units.
    :return: Half the total eye sweep, in scene units.
    """
    return focal_distance * math.tan(math.radians(spec.view_cone) / 2.0)


@dataclass(frozen=True)
class Clearance:
    """The lateral corridor an interior leaves for the view sweep.

    This is the constraint peculiar to enclosed scenes, and the one that
    bites hardest.  A cone chosen without checking it does not fail loudly:
    the centre view — the one you preview — is perfect, while the outer
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
    spec: QuiltSpec, camera: PovCamera, depths: Mapping[str, float]
) -> list[tuple[str, float, float]]:
    """Adjacent-view disparity at each depth of interest.

    A thin pairing of :func:`~quiltwright.lfd.view_disparity` with the
    labelled depths measured from a scene, kept separate from
    :func:`format_depth_budget` so the numbers can be asserted on rather
    than only printed.

    :param spec: Quilt specification.
    :param camera: Centre-view camera; supplies the focal distance and FOV.
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
    camera: PovCamera,
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
    :param camera: Centre-view camera.
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
    binary: str | None = None,
    extra_args: Sequence[str] = (),
    keep_views: str | Path | None = None,
    progress: bool = True,
) -> np.ndarray:
    """Render a POV-Ray scene into a Looking Glass quilt.

    Sweeps *camera* horizontally across the display's view cone using
    off-axis projections (see the module docstring), ray-traces one image
    per view, and tiles them with
    :func:`~quiltwright.lfd.assemble_quilt`.

    Cost scales linearly with the view count: a Portrait quilt is 48 full
    ray-traces.  For scenes using radiosity or photons, render one view with
    the cache saved and the rest with it loaded (via *extra_args*) — the
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
    :param binary: POV-Ray executable; defaults to ``POVRAY_BINARY`` or
        ``povray`` on ``PATH``.
    :param extra_args: Additional POV-Ray command-line arguments, e.g.
        ``["+HImy.ini"]`` or radiosity cache flags.
    :param keep_views: Directory to retain the per-view PNGs and generated
        wrapper scenes in, for inspection or debugging.  Discarded if
        ``None``.
    :param progress: Print a progress line while rendering.
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
    if jobs > 1 and not any(str(a).startswith("+WT") for a in extra_args):
        extra_args = [*extra_args, f"+WT{max(1, (os.cpu_count() or jobs) // jobs)}"]

    # Match render_quilt: capture at the declared view aspect so the frustum
    # is undistorted, then let assemble_quilt resample into the tile.  These
    # differ only for anamorphic presets (e.g. the 27" quilts).
    render_h = spec.tile_height
    render_w = round(render_h * spec.aspect)
    render_aspect = render_w / render_h

    library_paths = [scene_path.parent, *(Path(p).expanduser().resolve() for p in include_paths)]
    offsets = view_offsets(spec, camera.focal_distance)

    with tempfile.TemporaryDirectory(prefix="pov_quilt_") as tmp:
        # POV-Ray resolves #include against its working directory and the
        # library paths, so the wrapper lives in the working directory and
        # pulls the scene in by absolute path, with the scene's own
        # directory on the library path for its relative includes.
        workdir = Path(tmp)
        views = []
        for i, offset in enumerate(offsets):
            wrapper = workdir / f"view{i:03d}.pov"
            wrapper.write_text(
                f'#include "{scene_path}"\n'
                f"// Looking Glass view {i + 1}/{spec.n_views}, "
                f"eye offset {offset:+.6g} scene units\n"
                + camera_block(camera, float(offset), render_aspect)
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

        quilt = assemble_quilt(
            (np.asarray(Image.open(png).convert("RGB")) for _, png in views), spec
        )

        if keep_views is not None:
            dest = Path(keep_views).expanduser()
            dest.mkdir(parents=True, exist_ok=True)
            for wrapper, png in views:
                shutil.copy2(wrapper, dest / wrapper.name)
                shutil.copy2(png, dest / png.name)

    return quilt
