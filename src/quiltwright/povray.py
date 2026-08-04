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
from collections.abc import Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from quiltwright.lfd import QuiltSpec, assemble_quilt, view_offsets

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
    :param jobs: Number of POV-Ray processes to run concurrently.  POV-Ray
        already threads a single render across all cores, so the default of
        1 is usually right; raise it only when views are small enough that
        per-render startup dominates.
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
