"""Dual-render parity: a povgen scene must land where the PyVista one does.

The generator's job is *geometry and camera*, not photometry -- POV-Ray's
lighting model is not VTK's, and a scene worth ray-tracing wants its own
lights anyway.  So these tests render the same scene through both backends
with flat emissive surfaces and compare **silhouettes**, which isolates the
things a transcoder can actually get wrong: handedness, field of view, focal
plane, and the direction of the view sweep.

**The scene is deliberately asymmetric in depth.**  A scene straddling the
focal plane renders almost identically whether or not *z* was flipped, so it
cannot detect the single most damaging bug this module could have.  The
fixture therefore places one sphere well in front of the focal plane and
another well behind it, at the same radius: perspective alone decides which
looks bigger, so mirroring depth swaps them and the silhouette IoU collapses
from ~0.96 to ~0.  Verified by mutation -- reverting the flip in
:func:`~quiltwright.povgen.to_pov` fails
:func:`test_asymmetric_scene_silhouette_matches` outright.

That matters because ``povray.PovCamera.basis`` warns that getting the
cross-product ordering wrong "mirrors the view sweep and inverts the
hologram's depth" -- an error that looks perfectly fine in any single view and
only shows up as inside-out depth on the physical panel.

Both renderers must be present, so these skip on a machine with no ``povray``
binary or no GL stack for VTK.
"""

import shutil

import numpy as np
import pytest

from quiltwright.lfd import QuiltSpec, render_quilt
from quiltwright.povgen import (
    Finish,
    PovScene,
    Sphere,
    SphereSweep,
    Texture,
    pov_camera_from_plotter,
)
from quiltwright.povray import render_pov_quilt

pv = pytest.importorskip("pyvista", reason="parity needs the PyVista backend")

pytestmark = [
    pytest.mark.slow,
    pytest.mark.skipif(shutil.which("povray") is None, reason="no povray binary on PATH"),
]

TILE = 200
FOV = 40.0
CAMERA = (0.0, 0.0, -9.0)

#: Flat emissive, so a silhouette is a silhouette and not a lighting comparison.
FLAT = Finish(ambient=1.0, diffuse=0.0, phong=None)

#: Equal radii, opposite sides, opposite sides of the focal plane.  Both stay
#: clear of the frame edge across the whole sweep, so nothing clips in and out.
NEAR = ((-0.8, 0.0, -3.0), 0.45)
FAR = ((0.8, 0.0, 3.0), 0.45)


# ---------------------------------------------------------------------------
# Scene construction -- one description, two backends
# ---------------------------------------------------------------------------


def limb() -> tuple[np.ndarray, np.ndarray]:
    """A smoothed limb path with a *constant* radius.

    Constant radius on purpose: a POV-Ray ``sphere_sweep`` closes with
    hemispherical caps while a PyVista tube closes flat, so a tapered limb
    extends further past its thick end than its thin one and biases the
    silhouette's centroid by about a pixel.  Holding the radius equal makes
    that difference symmetric and keeps the centroid assertions tight enough
    to be worth making.
    """
    control = np.array([[0.0, -2.0, 1.2], [0.0, -1.0, 0.4], [0.0, 0.0, -0.4], [0.0, 1.0, -1.2]])
    spline = pv.Spline(control, 80)
    points = np.asarray(spline.points, dtype=float)
    return points, np.full(points.shape[0], 0.22)


def build_plotter(*, with_limb: bool) -> "pv.Plotter":
    """Compose the reference scene in PyVista, flat-shaded."""
    plotter = pv.Plotter(off_screen=True, window_size=(TILE, TILE))
    plotter.background_color = "black"
    flat = {"color": "white", "ambient": 1.0, "diffuse": 0.0, "specular": 0.0}
    for centre, radius in (NEAR, FAR):
        plotter.add_mesh(
            pv.Sphere(radius=radius, center=centre, theta_resolution=128, phi_resolution=128),
            **flat,
        )
    if with_limb:
        points, radii = limb()
        spline = pv.Spline(points, points.shape[0])
        spline["radius"] = radii
        plotter.add_mesh(spline.tube(scalars="radius", absolute=True, n_sides=64), **flat)
    plotter.camera.position = CAMERA
    plotter.camera.focal_point = (0.0, 0.0, 0.0)
    plotter.camera.up = (0.0, 1.0, 0.0)
    plotter.camera.view_angle = FOV
    return plotter


def build_scene(*, with_limb: bool) -> PovScene:
    """Compose the same scene analytically for POV-Ray."""
    texture = Texture("#ffffff", finish=FLAT)
    scene = PovScene(background="#000000")
    for centre, radius in (NEAR, FAR):
        scene.add(Sphere(centre, radius, texture))
    if with_limb:
        points, radii = limb()
        scene.add(SphereSweep(points, radii, texture=texture))
    return scene


def render_both(spec: QuiltSpec, tmp_path, *, with_limb: bool) -> tuple[np.ndarray, np.ndarray]:
    """Render the scene through both backends at a matched camera."""
    plotter = build_plotter(with_limb=with_limb)
    quilt_pv = render_quilt(plotter, spec, fov=None)

    path = build_scene(with_limb=with_limb).write(tmp_path / "parity.pov")
    camera = pov_camera_from_plotter(plotter, fov=None)
    quilt_pov = render_pov_quilt(path, spec, camera, progress=False, antialias=None, quality=5)
    return quilt_pv, quilt_pov


def silhouettes(quilt: np.ndarray, spec: QuiltSpec) -> list[np.ndarray]:
    """Split a quilt into one boolean foreground mask per view."""
    height = quilt.shape[0] // spec.rows
    width = quilt.shape[1] // spec.columns
    return [
        quilt[r * height : (r + 1) * height, c * width : (c + 1) * width].sum(axis=2) > 128
        for r in range(spec.rows)
        for c in range(spec.columns)
    ]


def iou(a: np.ndarray, b: np.ndarray) -> float:
    """Intersection over union of two boolean masks."""
    union = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum()) / float(max(union, 1))


def centroid(mask: np.ndarray) -> tuple[float, float]:
    """``(x, y)`` centre of mass of a mask, in pixels."""
    ys, xs = np.nonzero(mask)
    return float(xs.mean()), float(ys.mean())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def single_view() -> QuiltSpec:
    """One view, dead on axis -- isolates the lens from the sweep."""
    return QuiltSpec(columns=1, rows=1, quilt_width=TILE, quilt_height=TILE, aspect=1.0)


@pytest.fixture(scope="module")
def three_views() -> QuiltSpec:
    """Three views across the cone, enough to see which way parallax runs."""
    return QuiltSpec(columns=3, rows=1, quilt_width=TILE * 3, quilt_height=TILE, aspect=1.0)


# ---------------------------------------------------------------------------
# Geometry and handedness
# ---------------------------------------------------------------------------


def test_asymmetric_scene_silhouette_matches(single_view, tmp_path):
    """The load-bearing test: depth must survive the trip to POV-Ray intact.

    Reverting the *z* flip drives this to roughly zero, because the near and
    far spheres swap which one perspective makes larger.
    """
    quilt_pv, quilt_pov = render_both(single_view, tmp_path, with_limb=False)
    mask_pv = silhouettes(quilt_pv, single_view)[0]
    mask_pov = silhouettes(quilt_pov, single_view)[0]
    assert mask_pv.any() and mask_pov.any(), "one of the backends rendered nothing"
    assert iou(mask_pv, mask_pov) >= 0.94


def test_near_geometry_projects_larger_than_far(single_view, tmp_path):
    """Both backends must agree which sphere is in front.

    The two spheres have identical radii, so any size difference is
    perspective.  Screen right is world ``-x`` under VTK's basis, which puts
    the *near* sphere in the right half of the image.
    """
    quilt_pv, quilt_pov = render_both(single_view, tmp_path, with_limb=False)
    for quilt in (quilt_pv, quilt_pov):
        mask = silhouettes(quilt, single_view)[0]
        half = mask.shape[1] // 2
        far_area = int(mask[:, :half].sum())
        near_area = int(mask[:, half:].sum())
        assert near_area > far_area * 2, "the near sphere should dominate"


def test_silhouette_extent_is_identical(single_view, tmp_path):
    """Bounding boxes pin the lens exactly; pixel counts only differ at the edge.

    A tessellated sphere and an analytic one disagree by a fraction of a pixel
    of antialiasing around the rim, but their extents must land on the same
    rows and columns or the field of view is wrong.
    """
    quilt_pv, quilt_pov = render_both(single_view, tmp_path, with_limb=False)
    mask_pv = silhouettes(quilt_pv, single_view)[0]
    mask_pov = silhouettes(quilt_pov, single_view)[0]
    for axis in (0, 1):
        a = np.nonzero(mask_pv.any(axis=axis))[0]
        b = np.nonzero(mask_pov.any(axis=axis))[0]
        assert abs(int(a.min()) - int(b.min())) <= 1
        assert abs(int(a.max()) - int(b.max())) <= 1


def test_scene_is_not_mirrored(single_view, tmp_path):
    """Centroids must coincide, with a swept limb making the scene asymmetric."""
    quilt_pv, quilt_pov = render_both(single_view, tmp_path, with_limb=True)
    x_pv, y_pv = centroid(silhouettes(quilt_pv, single_view)[0])
    x_pov, y_pov = centroid(silhouettes(quilt_pov, single_view)[0])
    assert abs(x_pv - x_pov) <= 1.0
    assert abs(y_pv - y_pov) <= 1.0


def test_tilted_camera_up_vector_is_converted(single_view, tmp_path):
    """A camera rolled off the vertical exercises the *z* component of ``up``.

    Every other test here leaves ``up`` at ``(0, 1, 0)``, whose *z* is zero --
    so the handedness conversion applied to it is invisible and a camera
    bridge that forgot to convert ``sky`` would pass them all.  Rolling the
    camera about the view axis gives the up-vector a *z* component that has
    to survive the trip.
    """
    plotter = build_plotter(with_limb=True)
    # Roll about the view axis (z), and tilt the eye off it, so `up` is neither
    # axis-aligned nor perpendicular to the flip.
    plotter.camera.position = (2.5, 1.5, -8.5)
    plotter.camera.up = (0.35, 0.80, 0.49)
    quilt_pv = render_quilt(plotter, single_view, fov=None)

    path = build_scene(with_limb=True).write(tmp_path / "tilted.pov")
    camera = pov_camera_from_plotter(plotter, fov=None)
    assert abs(camera.sky[2]) > 0.1, "fixture no longer exercises the sky conversion"
    quilt_pov = render_pov_quilt(
        path, single_view, camera, progress=False, antialias=None, quality=5
    )

    mask_pv = silhouettes(quilt_pv, single_view)[0]
    mask_pov = silhouettes(quilt_pov, single_view)[0]
    assert mask_pv.any() and mask_pov.any(), "one of the backends rendered nothing"
    assert iou(mask_pv, mask_pov) >= 0.93


def test_mixed_scene_silhouette_matches(three_views, tmp_path):
    """Spheres plus a swept limb, across the whole view cone."""
    quilt_pv, quilt_pov = render_both(three_views, tmp_path, with_limb=True)
    for mask_pv, mask_pov in zip(
        silhouettes(quilt_pv, three_views), silhouettes(quilt_pov, three_views), strict=True
    ):
        assert iou(mask_pv, mask_pov) >= 0.93


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------


def test_parallax_runs_the_same_way_in_both_backends(three_views, tmp_path):
    """The view sweep must not be mirrored -- an inverted hologram looks fine per view."""
    quilt_pv, quilt_pov = render_both(three_views, tmp_path, with_limb=True)
    xs_pv = [centroid(m)[0] for m in silhouettes(quilt_pv, three_views)]
    xs_pov = [centroid(m)[0] for m in silhouettes(quilt_pov, three_views)]

    shift_pv = xs_pv[-1] - xs_pv[0]
    shift_pov = xs_pov[-1] - xs_pov[0]
    assert abs(shift_pv) > 0.5, "the sweep produced no parallax to compare"
    assert np.sign(shift_pv) == np.sign(shift_pov), "view sweep is mirrored"
    assert abs(shift_pv - shift_pov) <= 0.5 * abs(shift_pv)


def test_near_and_far_geometry_move_in_opposite_directions(three_views, tmp_path):
    """Depth reads as *relative* parallax, and POV-Ray must reproduce the sign.

    Geometry in front of the focal plane slides one way across the sweep and
    geometry behind it slides the other.  That opposition is what a
    light-field display turns into depth, so both backends have to show it.
    """
    quilt_pv, quilt_pov = render_both(three_views, tmp_path, with_limb=False)
    for quilt in (quilt_pv, quilt_pov):
        masks = silhouettes(quilt, three_views)
        half = masks[0].shape[1] // 2
        far_track = [centroid(m[:, :half])[0] for m in masks]
        near_track = [centroid(m[:, half:])[0] for m in masks]
        far_shift = far_track[-1] - far_track[0]
        near_shift = near_track[-1] - near_track[0]
        assert np.sign(far_shift) != np.sign(near_shift), "near and far must part company"


def test_focal_plane_is_pinned(three_views, tmp_path):
    """Geometry on the focal plane must not move across views.

    This is the property that makes a quilt fuse: the look-at point lands on
    the glass.  A toe-in camera would swing it.
    """
    plotter = build_plotter(with_limb=False)
    scene = PovScene(background="#000000")
    scene.add(Sphere((0.0, 0.0, 0.0), 0.6, Texture("#ffffff", finish=FLAT)))
    path = scene.write(tmp_path / "focal.pov")
    camera = pov_camera_from_plotter(plotter, fov=None)
    quilt = render_pov_quilt(path, three_views, camera, progress=False, antialias=None, quality=5)

    xs = [centroid(m)[0] for m in silhouettes(quilt, three_views)]
    assert max(xs) - min(xs) <= 1.0
