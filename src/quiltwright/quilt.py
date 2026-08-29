"""
Quilt geometry, assembly, and save.

Renderer-agnostic half of quilt production: tiling grid, device presets,
view offsets, the assembler every backend feeds, and the Looking Glass
filename convention.  numpy and pillow only -- importing this module must
not load VTK.

Typical usage::

    from quiltwright.quilt import QUILT_PRESETS, assemble_quilt, save_quilt

    spec = QUILT_PRESETS["portrait"]
    save_quilt(assemble_quilt(views, spec), "torus", spec)

Re-exported from :mod:`quiltwright.lfd` for one release, so
``from quiltwright.lfd import QuiltSpec`` keeps working.

Part of Quiltwright -- https://github.com/suchanek/quiltwright
Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np

# ---------------------------------------------------------------------------
# Quilt specification
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuiltSpec:
    """Geometry of a quilt: tiling grid, total pixel size, and view cone.

    :param columns: Number of view tiles per quilt row.
    :param rows: Number of view tiles per quilt column.
    :param quilt_width: Total quilt width in pixels.
    :param quilt_height: Total quilt height in pixels.
    :param aspect: Aspect ratio (width / height) of a *single view*, which
        matches the target display's aspect.  Embedded in the quilt filename
        so Looking Glass software can configure playback correctly.
    :param view_cone: Total horizontal sweep of the camera in degrees.
        Looking Glass documents 35° as the standard rendering cone (the
        physical display cone is wider, ~40-58° depending on model;
        rendering slightly narrower adds apparent depth).
    """

    columns: int
    rows: int
    quilt_width: int
    quilt_height: int
    aspect: float
    view_cone: float = 35.0

    @property
    def n_views(self) -> int:
        """Total number of views in the quilt."""
        return self.columns * self.rows

    @property
    def tile_width(self) -> int:
        """Width of a single view tile in pixels."""
        return self.quilt_width // self.columns

    @property
    def tile_height(self) -> int:
        """Height of a single view tile in pixels."""
        return self.quilt_height // self.rows

    def tile_origin(self, view_index: int) -> tuple[int, int]:
        """Pixel ``(x, y)`` of a view's top-left corner within the quilt image.

        Quilt convention: view 0 at the *bottom-left*, advancing
        left-to-right then bottom-to-top.  The returned ``y`` is measured
        from the image top (numpy/PIL row order).

        :param view_index: View number in ``[0, n_views)``.
        :return: ``(x, y)`` pixel offsets of the tile.
        """
        if not 0 <= view_index < self.n_views:
            raise ValueError(f"view_index {view_index} outside [0, {self.n_views})")
        col = view_index % self.columns
        row = view_index // self.columns  # 0 = bottom row
        x = col * self.tile_width
        y = (self.rows - 1 - row) * self.tile_height
        return x, y

    def filename(self, stem: str, ext: str = "png") -> str:
        """Quilt filename with the metadata suffix Looking Glass software parses.

        :param stem: Base name without extension (e.g. ``"helix_density"``).
        :param ext: File extension without the dot.
        :return: e.g. ``"helix_density_qs8x6a0.75.png"``.
        """
        return f"{stem}_qs{self.columns}x{self.rows}a{self.aspect:g}.{ext}"

    def with_grid(self, columns: int, rows: int) -> QuiltSpec:
        """Same quilt at a different view-grid density.

        Total quilt pixels stay fixed, so more views means fewer pixels per
        view: the device's lenticular optics interpolate between views, so
        extra views give smoother look-around at the cost of per-view
        sharpness.  The official presets are the factory-calibrated balance.

        :param columns: New number of tile columns.
        :param rows: New number of tile rows.
        :return: A new :class:`QuiltSpec` with the requested grid.
        """
        return replace(self, columns=columns, rows=rows)

    def still(self, height: int = 1100) -> QuiltSpec:
        """The same view, once, as a flat image at this device's aspect.

        A one-tile "quilt" is the cheapest way to check framing, lighting and
        materials before paying for the whole sweep, and it is what the
        gallery images are: :func:`view_offsets` returns a single zero offset
        at ``n_views == 1``, so the render is the centre view and nothing
        else.  The width follows :attr:`aspect` rather than being fixed, so
        the still is framed like the panel it is standing in for -- a still
        of a landscape device is a landscape image.

        :param height: Image height in pixels.
        :return: A new 1x1 :class:`QuiltSpec` at this spec's aspect.
        :raises ValueError: If *height* is not positive.
        """
        if height <= 0:
            raise ValueError(f"still height must be positive, got {height}")
        width = max(1, round(height * self.aspect))
        return replace(self, columns=1, rows=1, quilt_width=width, quilt_height=height)

    def scaled(self, factor: float) -> QuiltSpec:
        """Same view grid at a fraction of the pixel size.

        Casting at full preset size is rarely what you want: rendering costs
        about a second, but the wait is Bridge loading the resulting PNG, and
        that scales with its area.  Halving the linear size quarters it.

        The scaled dimensions are rounded **down to a multiple of the tile
        grid**, which is the part that is easy to get wrong: scale naively and
        the quilt no longer divides evenly into tiles, so every view lands on a
        fractional pixel boundary and the whole light field smears.

        :param factor: Linear scale factor, e.g. ``0.5`` for quarter the pixels.
        :return: A new :class:`QuiltSpec` at the scaled size, tiles intact.
        :raises ValueError: If *factor* is not positive, or scales the quilt
            below one pixel per tile.
        """
        if factor <= 0:
            raise ValueError(f"scale factor must be positive, got {factor}")
        width = int(self.quilt_width * factor) // self.columns * self.columns
        height = int(self.quilt_height * factor) // self.rows * self.rows
        if width < self.columns or height < self.rows:
            raise ValueError(
                f"scale factor {factor} leaves a {width}x{height} quilt, "
                f"too small for a {self.columns}x{self.rows} tile grid"
            )
        return replace(self, quilt_width=width, quilt_height=height)


#: Standard ("ideal") quilt settings per Looking Glass device, from the
#: official docs: https://lfdocs.lookingglassfactory.com/keyconcepts/quilts
QUILT_PRESETS: dict[str, QuiltSpec] = {
    "portrait": QuiltSpec(columns=8, rows=6, quilt_width=3360, quilt_height=3360, aspect=0.75),
    "go": QuiltSpec(columns=11, rows=6, quilt_width=4092, quilt_height=4092, aspect=0.5625),
    # Gen3 16" Landscape (hardwareVersion "16_gen3_l"), verified against the
    # defaultQuilt Bridge reports for LKG-J00332.  Its native view cone is 50
    # degrees, wider than the 35-degree QuiltSpec default.
    "16-landscape": QuiltSpec(
        columns=8, rows=6, quilt_width=7680, quilt_height=4320, aspect=1.77778, view_cone=50.0
    ),
    "16-portrait": QuiltSpec(
        columns=11, rows=6, quilt_width=5995, quilt_height=6000, aspect=0.5625
    ),
    "27-landscape": QuiltSpec(columns=8, rows=6, quilt_width=7680, quilt_height=4320, aspect=1.777),
    "27-portrait": QuiltSpec(
        columns=12, rows=4, quilt_width=7680, quilt_height=4320, aspect=0.5625
    ),
    "32-landscape": QuiltSpec(columns=7, rows=7, quilt_width=8190, quilt_height=8190, aspect=1.777),
    "32-portrait": QuiltSpec(
        columns=11, rows=6, quilt_width=8184, quilt_height=8184, aspect=0.5625
    ),
    "65": QuiltSpec(columns=8, rows=9, quilt_width=8192, quilt_height=8192, aspect=1.777),
}


def sweep_spec(n_views: int, view_cone: float, tile_width: int, tile_height: int) -> QuiltSpec:
    """Geometry for a plain ordered view sweep rather than a tiled quilt.

    A quilt's view count is ``columns * rows``, so a rectangular grid cannot
    express a prime count.  A single row can express any count at all, which
    is what consumers that want the views as separate frames -- hologram
    printers, lenticular interlacers -- actually ask for.  The camera sweep is
    identical either way; only the packing differs.

    :param n_views: Number of views in the sweep.
    :param view_cone: Total horizontal camera sweep in degrees.
    :param tile_width: Pixel width of one view.
    :param tile_height: Pixel height of one view.
    :return: A single-row :class:`QuiltSpec` whose ``n_views`` is exactly
        *n_views*.
    """
    if n_views < 2:
        raise ValueError(f"a sweep needs at least 2 views, got {n_views}")
    return QuiltSpec(
        columns=n_views,
        rows=1,
        quilt_width=n_views * tile_width,
        quilt_height=tile_height,
        aspect=tile_width / tile_height,
        view_cone=view_cone,
    )


#: Sweep matching the published input specification of the LitiHolo desktop
#: 3D hologram printer: 23 viewzone images per hogel across a 45-degree
#: lateral field, horizontal parallax only -- the same off-axis sweep a
#: light-field quilt is built from, differently packed.
#:
#: The per-view pixel size is *not* published.  1600x2000 comfortably exceeds
#: the ~102x127 hogel grid of a 4x5-inch plate at 1 mm hogels and is cheap to
#: downsample, so it errs high deliberately.  Aspect 0.8 matches a 4x5 plate
#: in portrait; transpose for landscape.
LITIHOLO_SWEEP: QuiltSpec = sweep_spec(
    n_views=23, view_cone=45.0, tile_width=1600, tile_height=2000
)


# ---------------------------------------------------------------------------
# Off-axis camera math
# ---------------------------------------------------------------------------


@runtime_checkable
class QuiltCamera(Protocol):
    """Look-at camera that can feed a quilt sweep.

    :class:`~quiltwright.povray.PovCamera` and
    :class:`~quiltwright.cycles.CyclesCamera` both satisfy this.  Named
    ``QuiltCamera`` rather than ``CameraFrame`` so it does not collide with
    ``kg_utils.viz3d.layout.CameraFrame`` in the growth engine.

    Handedness is the camera's own: POV-Ray is left-handed, Cycles and VTK
    are right-handed.  :meth:`basis` returns ``(forward, right, up)`` in
    that convention.  Callers that emit a renderer-specific frustum convert
    :func:`window_shear` into the units that renderer takes.
    """

    location: tuple[float, float, float]
    look_at: tuple[float, float, float]
    fov: float

    @property
    def focal_distance(self) -> float:
        """Distance from the eye to the look-at point, in scene units."""
        ...

    def basis(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Orthonormal ``(forward, right, up)`` in this camera's handedness."""
        ...


def window_shear(offset: float, focal_distance: float, fov: float, aspect: float) -> float:
    """Dimensionless horizontal window shift that pins the look-at point.

    The eye has translated *offset* along the camera's right vector.  This
    is the shear that slides the frustum window back so the original look-at
    point stays centred -- the off-axis projection, never a toe-in.

    VTK's ``SetWindowCenter`` takes this value directly (units of half the
    image width).  Blender's ``shift_x`` is this value divided by 2
    (fractions of the full frame width).  POV-Ray slides the image-plane
    centre by ``window_shear * (aspect / 2)`` along ``right``, which is
    ``-offset * D / Z`` for image-plane distance ``D``.

    :param offset: Lateral eye offset along the camera's right vector, in
        scene units, from :func:`view_offsets`.
    :param focal_distance: Camera-to-focal-plane distance, in scene units.
    :param fov: Vertical field of view in degrees.
    :param aspect: Width / height of the rendered view.
    :return: The dimensionless window centre.  Zero at the centre view;
        negative when the eye has moved right.
    """
    return -offset / (focal_distance * math.tan(math.radians(fov) / 2.0) * aspect)


def view_offsets(spec: QuiltSpec, distance: float) -> np.ndarray:
    """Horizontal camera offsets (world units) for every view in the quilt.

    Cameras sweep a total angle of ``spec.view_cone`` centred on the base
    camera position, at constant distance from the focal plane.  Offsets are
    ordered to match quilt view order: view 0 is the leftmost camera.

    :param spec: Quilt specification (view count + cone angle).
    :param distance: Distance from camera to the focal plane.
    :return: Array of shape ``(n_views,)`` with signed offsets along the
        camera's right vector.
    """
    half_cone = math.radians(spec.view_cone) / 2.0
    n = spec.n_views
    if n == 1:
        return np.zeros(1)
    # Even angular spacing across the cone; tan() converts angle to lateral
    # shift so the focal plane is sampled like the physical display does.
    angles = np.linspace(-half_cone, half_cone, n)
    return distance * np.tan(angles)


def view_disparity(spec: QuiltSpec, fov: float, focal_distance: float, depth: float) -> float:
    """Pixel shift of a feature between *adjacent* quilt views.

    This is the number that decides whether a hologram fuses.  A lenticular
    display blends neighbouring views optically, so content that moves only
    a pixel or two between them reads as solid depth, while larger shifts
    read as ghosting or a visible stack of copies.  Rendered scenes that
    "look fine" flat routinely blow this budget.

    Derived from the off-axis projection: a point at *depth* along the view
    axis lands at image coordinate ``(D/aspect)(x/depth + s(1/Z - 1/depth))``
    for eye offset ``s``, so the shift across the whole cone is
    ``[tan(cone/2)/tan(fov/2)] * (1 - Z/depth) * tile_height`` pixels, which
    divided between ``n_views - 1`` gaps gives this.  The aspect ratio
    cancels.  Verified against ray-traced renders to within 0.5%.

    Two consequences worth internalising: content *at* the focal plane has
    zero disparity, and a *narrower* FOV increases disparity, because it
    magnifies the scene and the parallax along with it.

    :param spec: Quilt specification (view count + cone angle + tile size).
    :param fov: Vertical field of view in degrees.
    :param focal_distance: Camera-to-focal-plane distance, in scene units.
    :param depth: Distance of the content of interest from the camera, in
        scene units.  Use ``math.inf`` for sky or a backdrop at infinity.
    :return: Adjacent-view shift in pixels.  Roughly 4-5 px is the practical
        ceiling; beyond ~8 px expect visible ghosting on hard edges.
    """
    if spec.n_views < 2:
        return 0.0
    magnification = math.tan(math.radians(spec.view_cone) / 2.0) / math.tan(math.radians(fov) / 2.0)
    parallax = 1.0 if math.isinf(depth) else abs(1.0 - focal_distance / depth)
    return magnification * parallax * spec.tile_height / (spec.n_views - 1)


def focal_distance_for_range(near: float, far: float) -> float:
    """Focal distance that balances disparity between the nearest and
    farthest content -- their harmonic mean.

    Disparity grows with ``|1 - Z/depth|``, which is asymmetric in depth:
    placing the focal plane at the arithmetic midpoint leaves the near
    content far worse off than the far content.  Equalising the two,
    ``Z/near - 1 = 1 - Z/far``, gives ``Z = 2/(1/near + 1/far)``.

    With *far* at infinity this reduces to ``2 * near``.

    :param near: Distance to the nearest content, in scene units.
    :param far: Distance to the farthest content; may be ``math.inf``.
    :return: Focal distance to aim the camera at.
    :raises ValueError: If *near* is not positive or exceeds *far*.
    """
    if near <= 0:
        raise ValueError(f"near must be positive, got {near}")
    if far < near:
        raise ValueError(f"far ({far}) must be >= near ({near})")
    if math.isinf(far):
        return 2.0 * near
    return 2.0 / (1.0 / near + 1.0 / far)


def sweep_extent(spec: QuiltSpec, focal_distance: float) -> float:
    """Half-width of the lateral eye travel the quilt's view sweep needs.

    The outermost views sit ``focal_distance * tan(cone/2)`` to either side
    of the centre view -- the largest magnitude in :func:`view_offsets`, in
    closed form.  For an object on a turntable that space is empty; inside a
    room it is furniture and walls, so compare it against a measured
    :class:`~quiltwright.povray.Clearance` before committing to a render.

    :param spec: Quilt specification (supplies the view cone).
    :param focal_distance: Camera-to-focal-plane distance, in scene units.
    :return: Half the total eye sweep, in scene units.
    """
    return focal_distance * math.tan(math.radians(spec.view_cone) / 2.0)


# ---------------------------------------------------------------------------
# Quilt assembly and save
# ---------------------------------------------------------------------------


def assemble_quilt(views: Iterable[np.ndarray], spec: QuiltSpec) -> np.ndarray:
    """Tile per-view images into a single quilt image.

    This is the renderer-agnostic half of quilt production: it takes views
    that some backend already rendered -- VTK via :func:`render_quilt`, a
    ray-tracer via :mod:`quiltwright.povray` -- and lays them out in quilt
    order.  Views are consumed lazily, so a backend can stream them without
    holding all ``n_views`` frames in memory at once.

    Views whose pixel size differs from the tile size are resampled, which
    is what makes anamorphic quilts (tile pixel aspect != view aspect, e.g.
    the 27" presets) come out correctly.

    :param views: Iterable of ``uint8`` RGB (or RGBA) arrays in view order --
        view 0 is the leftmost camera.  Must yield exactly ``spec.n_views``.
    :param spec: Quilt specification (grid, size, aspect).
    :return: ``uint8`` RGB array of shape ``(quilt_height, quilt_width, 3)``.
    :raises ValueError: If the number of views does not match ``spec``.
    """
    quilt = np.zeros((spec.quilt_height, spec.quilt_width, 3), dtype=np.uint8)
    n = 0
    for i, img in enumerate(views):
        if i >= spec.n_views:
            raise ValueError(
                f"got more than {spec.n_views} views for a {spec.columns}x{spec.rows} quilt"
            )
        img = np.asarray(img)[..., :3]
        if img.shape[:2] != (spec.tile_height, spec.tile_width):
            img = _resize_view(img, spec.tile_width, spec.tile_height)
        x, y = spec.tile_origin(i)
        quilt[y : y + spec.tile_height, x : x + spec.tile_width] = img
        n = i + 1
    if n != spec.n_views:
        raise ValueError(
            f"expected {spec.n_views} views for a {spec.columns}x{spec.rows} quilt, got {n}"
        )
    return quilt


def _resize_view(img: np.ndarray, width: int, height: int) -> np.ndarray:
    """Resample a rendered view to the quilt tile size (anamorphic storage)."""
    from PIL import Image

    resized = Image.fromarray(img).resize((width, height), Image.Resampling.LANCZOS)
    return np.asarray(resized)


def save_quilt(quilt: np.ndarray, stem: str | Path, spec: QuiltSpec) -> Path:
    """Write a quilt to PNG using the Looking Glass filename convention.

    :param quilt: RGB array from :func:`render_quilt`.
    :param stem: Output path *without* the quilt suffix or extension.
        Any ``.png`` extension is stripped first.
    :param spec: Quilt specification (encodes the suffix metadata).
    :return: The path written, e.g. ``renders/quilts/helix_qs8x6a0.75.png``.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise ImportError(
            "save_quilt() requires pillow.\nInstall with:  poetry install --with viz"
        ) from exc

    stem = Path(stem)
    if stem.suffix.lower() == ".png":
        stem = stem.with_suffix("")
    out_path = stem.parent / spec.filename(stem.name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(quilt).save(out_path)
    return out_path
