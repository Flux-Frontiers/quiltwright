"""Tests for the POV-Ray scene generator (quiltwright.povgen)."""

import math
import re
import subprocess
import sys

import numpy as np
import pytest

from quiltwright.povgen import (
    SWEEP_MIN_POINTS,
    Box,
    Cylinder,
    Finish,
    Instance,
    LightSource,
    PovScene,
    Sphere,
    SphereSweep,
    Texture,
    Union,
    _frame_from_direction,
    fov_horizontal_to_vertical,
    ground_slab,
    instances_by_color,
    instances_from_frames,
    lights_from_bounds,
    parse_color,
    pov_camera_from_frame,
    pov_camera_from_plotter,
    sphere_sweeps_from_paths,
    spheres_from_points,
    swept_scene,
    to_pov,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def vectors_in(text: str) -> list[np.ndarray]:
    """Pull every ``<x, y, z>`` vector out of an SDL fragment."""
    pattern = r"<\s*(-?[\d.eE+-]+)\s*,\s*(-?[\d.eE+-]+)\s*,\s*(-?[\d.eE+-]+)\s*>"
    return [np.array([float(a), float(b), float(c)]) for a, b, c in re.findall(pattern, text)]


# ---------------------------------------------------------------------------
# Coordinates and colour
# ---------------------------------------------------------------------------


def test_to_pov_negates_z_by_default():
    assert to_pov((1.0, 2.0, 3.0)) == (1.0, 2.0, -3.0)


def test_to_pov_none_passes_through():
    assert to_pov((1.0, 2.0, 3.0), "none") == (1.0, 2.0, 3.0)


def test_to_pov_rejects_unknown_handedness():
    with pytest.raises(ValueError, match="handedness"):
        to_pov((0, 0, 0), "left")


def test_to_pov_is_an_involution():
    """Flipping twice is the identity, so a round trip cannot drift."""
    point = (1.5, -2.5, 3.5)
    assert to_pov(to_pov(point)) == point


@pytest.mark.parametrize(
    "value,expected",
    [
        ("#ffffff", (1.0, 1.0, 1.0)),
        ("#000000", (0.0, 0.0, 0.0)),
        ("ff0000", (1.0, 0.0, 0.0)),
        ("#0f0", (0.0, 1.0, 0.0)),
        ((0.25, 0.5, 0.75), (0.25, 0.5, 0.75)),
    ],
)
def test_parse_color(value, expected):
    assert parse_color(value) == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize("bad", ["#12345", "nothex", "#gggggg", (0.1, 0.2)])
def test_parse_color_rejects_junk(bad):
    with pytest.raises(ValueError):
        parse_color(bad)


# ---------------------------------------------------------------------------
# Textures
# ---------------------------------------------------------------------------


def test_texture_opaque_has_no_transmit():
    assert "transmit" not in Texture("#808080").sdl()


def test_texture_opacity_becomes_transmit_not_filter():
    """VTK alpha is uniform transparency, which is POV-Ray's ``transmit``."""
    sdl = Texture("#808080", opacity=0.25).sdl()
    assert "transmit 0.75" in sdl
    assert "filter" not in sdl


def test_finish_omits_unset_terms():
    sdl = Finish(phong=None).sdl()
    assert "phong" not in sdl
    assert "specular" not in sdl
    assert "ambient" in sdl and "diffuse" in sdl


def test_named_texture_is_referenced_not_inlined():
    sdl = Sphere((0, 0, 0), 1.0, "Bark").sdl()
    assert "texture { Bark }" in sdl
    assert "pigment" not in sdl


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------


def test_sphere_emits_flipped_centre():
    sdl = Sphere((1.0, 2.0, 3.0), 0.5).sdl()
    assert sdl.startswith("sphere {")
    assert vectors_in(sdl)[0] == pytest.approx([1.0, 2.0, -3.0])
    assert "0.5" in sdl


def test_cylinder_open_flag():
    assert " open" in Cylinder((0, 0, 0), (0, 1, 0), 0.2, open=True).sdl()
    assert " open" not in Cylinder((0, 0, 0), (0, 1, 0), 0.2).sdl()


def test_box_corners_sorted_after_flip():
    """Negating z swaps which corner is lower; POV-Ray needs corner1 <= corner2."""
    lo, hi = vectors_in(Box((0, 0, 0), (1, 1, 1)).sdl())
    assert np.all(lo <= hi)
    assert lo == pytest.approx([0.0, 0.0, -1.0])
    assert hi == pytest.approx([1.0, 1.0, 0.0])


def test_sphere_sweep_defaults_to_interpolating_spline():
    """b_spline would pull the surface off the already-smoothed path."""
    assert SphereSweep(np.zeros((4, 3)) + np.arange(4)[:, None], 1.0).kind == "linear_spline"


def test_sphere_sweep_emits_point_radius_pairs():
    points = np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 2.0, 0.0]])
    sdl = SphereSweep(points, np.array([0.3, 0.2, 0.1])).sdl()
    assert "linear_spline, 3," in sdl
    assert "tolerance" in sdl
    assert [v[1] for v in vectors_in(sdl)] == pytest.approx([0.0, 1.0, 2.0])
    assert "0.3" in sdl and "0.1" in sdl


def test_sphere_sweep_scalar_radius_broadcasts():
    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    assert "linear_spline, 2," in SphereSweep(points, 0.25).sdl()


def test_sphere_sweep_drops_duplicate_points():
    """Repeated points make POV-Ray's sweep solver degenerate."""
    points = np.array([[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    assert "linear_spline, 2," in SphereSweep(points, 0.1).sdl()


def test_sphere_sweep_rejects_unknown_kind():
    with pytest.raises(ValueError, match="unknown sphere_sweep kind"):
        SphereSweep(np.zeros((4, 3)), 1.0, kind="nurbs").sdl()


def test_sphere_sweep_rejects_mismatched_radii():
    with pytest.raises(ValueError, match="does not match"):
        SphereSweep(np.zeros((3, 3)), np.array([1.0, 2.0])).sdl()


@pytest.mark.parametrize("kind,minimum", sorted(SWEEP_MIN_POINTS.items()))
def test_sphere_sweep_enforces_minimum_points(kind, minimum):
    points = np.arange(3 * (minimum - 1), dtype=float).reshape(minimum - 1, 3)
    with pytest.raises(ValueError, match="at least"):
        SphereSweep(points, 0.1, kind=kind).sdl()


def test_union_of_nothing_is_empty():
    assert Union([]).sdl() == ""


def test_union_wraps_members_and_applies_texture():
    sdl = Union([Sphere((0, 0, 0), 1.0), Sphere((2, 0, 0), 1.0)], Texture("#ff0000")).sdl()
    assert sdl.startswith("union {") and sdl.rstrip().endswith("}")
    assert sdl.count("sphere {") == 2
    assert "pigment" in sdl


def test_instance_orders_transformations_scale_rotate_translate():
    sdl = Instance("Leaf", translate=(1, 2, 3), scale=(1, 0.5, 0.2)).sdl()
    assert sdl.index("scale") < sdl.index("translate")
    assert vectors_in(sdl)[-1] == pytest.approx([1.0, 2.0, -3.0])


def test_instance_scalar_scale():
    assert "scale 2" in Instance("Leaf", scale=2.0).sdl()


def test_light_source_area_and_shadowless():
    plain = LightSource((1, 2, 3)).sdl()
    assert plain.startswith("light_source {")
    assert "shadowless" not in plain and "area_light" not in plain
    fancy = LightSource((1, 2, 3), shadowless=True, area=((1, 0, 0), (0, 0, 1), 3, 3)).sdl()
    assert "shadowless" in fancy and "area_light" in fancy


# ---------------------------------------------------------------------------
# Orientation frames
# ---------------------------------------------------------------------------


def test_frame_from_direction_is_orthonormal_with_direction_first():
    for direction in ([1, 0, 0], [0, 0, 1], [0.3, -0.9, 0.2], [0, 0, -1]):
        frame = _frame_from_direction(np.array(direction, dtype=float))
        assert frame @ frame.T == pytest.approx(np.eye(3), abs=1e-9)
        expected = np.asarray(direction, dtype=float)
        assert frame[0] == pytest.approx(expected / np.linalg.norm(expected), abs=1e-9)


def test_frame_from_direction_handles_degenerate_input():
    assert _frame_from_direction(np.zeros(3)) == pytest.approx(np.eye(3))


def test_frame_from_direction_is_right_handed():
    frame = _frame_from_direction(np.array([0.2, 0.4, -0.9]))
    assert np.linalg.det(frame) == pytest.approx(1.0, abs=1e-9)


def test_instance_matrix_conjugated_by_the_flip():
    """A rotation must mean the same thing after the world is mirrored."""
    direction = np.array([0.0, 0.0, 1.0])
    frame = _frame_from_direction(direction)
    sdl = Instance("Leaf", matrix=frame).sdl()
    values = [float(v) for v in re.search(r"matrix <([^>]*)>", sdl).group(1).split(",")]
    emitted = np.array(values[:9]).reshape(3, 3)
    flip = np.diag([1.0, 1.0, -1.0])
    assert emitted == pytest.approx(flip @ frame @ flip, abs=1e-9)
    # The aim vector, transformed and flipped, still points along the flipped aim.
    assert (np.array([1.0, 0.0, 0.0]) @ emitted) == pytest.approx(to_pov(direction), abs=1e-9)


# ---------------------------------------------------------------------------
# Bulk constructors
# ---------------------------------------------------------------------------


def test_sphere_sweeps_from_paths_skips_degenerate_paths():
    paths = [
        (np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]), np.array([0.2, 0.1])),
        (np.array([[5.0, 5.0, 5.0]]), np.array([0.2])),  # single point
        (np.array([[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]), np.array([0.2, 0.1])),  # duplicate
    ]
    assert len(sphere_sweeps_from_paths(paths)) == 1


def test_sphere_sweeps_from_paths_raises_zero_radii():
    paths = [(np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]), np.array([0.2, 0.0]))]
    sweep = sphere_sweeps_from_paths(paths, min_radius=1e-3)[0]
    assert float(np.min(sweep.radii)) == pytest.approx(1e-3)


def test_spheres_from_points_scalar_and_per_point_radii():
    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    assert [s.radius for s in spheres_from_points(points, 0.5)] == [0.5, 0.5]
    assert [s.radius for s in spheres_from_points(points, np.array([0.1, 0.2]))] == [0.1, 0.2]
    assert spheres_from_points(np.zeros((0, 3)), 1.0) == []


def test_instances_from_frames_with_and_without_directions():
    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    plain = instances_from_frames("Leaf", points)
    assert len(plain) == 2 and all(i.matrix is None for i in plain)
    oriented = instances_from_frames("Leaf", points, np.array([[1.0, 0, 0], [0, 1.0, 0]]))
    assert all(i.matrix is not None for i in oriented)


def test_instances_from_frames_rejects_shape_mismatch():
    with pytest.raises(ValueError, match="does not match"):
        instances_from_frames("Leaf", np.zeros((3, 3)), np.zeros((2, 3)))


# ---------------------------------------------------------------------------
# Scene assembly
# ---------------------------------------------------------------------------


def test_scene_emits_no_camera():
    """render_pov_quilt appends the camera; emitting one here would be overridden."""
    scene = PovScene(background="#101018").add(Sphere((0, 0, 0), 1.0))
    statements = [ln for ln in scene.sdl().split("\n") if not ln.lstrip().startswith("//")]
    assert not any("camera" in ln for ln in statements)


def test_scene_orders_declares_before_objects():
    scene = PovScene()
    scene.declare_texture("Bark", Texture("#6b4a2f"))
    scene.add(Sphere((0, 0, 0), 1.0, "Bark"))
    sdl = scene.sdl()
    assert sdl.index("#declare Bark") < sdl.index("sphere {")


def test_scene_includes_and_background():
    scene = PovScene(background=(0.1, 0.1, 0.2), includes=["colors.inc"], ambient_light="#202020")
    sdl = scene.sdl()
    assert '#include "colors.inc"' in sdl
    assert "background {" in sdl
    assert "ambient_light" in sdl


def test_scene_add_accepts_single_and_iterable():
    scene = PovScene()
    scene.add(Sphere((0, 0, 0), 1.0))
    scene.add([Sphere((1, 0, 0), 1.0), Sphere((2, 0, 0), 1.0)])
    assert len(scene) == 3


def test_scene_add_chains():
    scene = PovScene().add(Sphere((0, 0, 0), 1.0)).add(Sphere((1, 0, 0), 1.0))
    assert len(scene) == 2


def test_scene_handedness_none_leaves_z_alone():
    scene = PovScene(handedness="none").add(Sphere((1.0, 2.0, 3.0), 0.5))
    assert vectors_in(scene.sdl())[0] == pytest.approx([1.0, 2.0, 3.0])


def test_scene_write_round_trips(tmp_path):
    scene = PovScene().add(Sphere((0, 0, 0), 1.0))
    written = scene.write(tmp_path / "nested" / "scene.pov")
    assert written.is_file()
    assert written.read_text() == scene.sdl()


def test_scene_bounds_covers_every_measurable_primitive():
    scene = PovScene()
    scene.add(Sphere((0.0, 0.0, 0.0), 1.0))
    scene.add(Box((-3.0, 0.0, 0.0), (-2.0, 1.0, 1.0)))
    scene.add(Cylinder((0.0, 0.0, 0.0), (0.0, 5.0, 0.0), 0.5))
    lo, hi = scene.bounds()
    assert lo[0] == pytest.approx(-3.0)
    assert hi[1] == pytest.approx(5.5)


def test_scene_bounds_reports_right_handed_coordinates():
    """Bounds feed camera placement, which is authored right-handed too."""
    scene = PovScene().add(Sphere((0.0, 0.0, 4.0), 1.0))
    lo, hi = scene.bounds()
    assert lo[2] == pytest.approx(3.0)
    assert hi[2] == pytest.approx(5.0)


def test_scene_bounds_includes_union_members():
    scene = PovScene().add(Union([Sphere((10.0, 0.0, 0.0), 1.0)]))
    lo, hi = scene.bounds()
    assert hi[0] == pytest.approx(11.0)


def test_scene_bounds_none_when_unmeasurable():
    assert PovScene().bounds() is None
    assert PovScene().add(Instance("Leaf", translate=(1, 1, 1))).bounds() is None


def test_instances_do_not_widen_the_bounds_they_sit_outside_of():
    """
    The trap the docstring warns about, made concrete: instancing is what this
    method cannot see and also the reason to use this module, so a scene whose
    subject *is* the instances measures as the one prop that happens to be a
    real primitive.  Lights and cameras derived from these bounds would sit
    inside the scene.

    A tree escapes this because its swept wood reaches the crown; nothing in
    the API guarantees that, so it is worth pinning rather than assuming.
    """
    scene = PovScene().add(Sphere((0.0, 0.0, 0.0), 1.0))  # the marker post
    for x in (-50.0, 50.0):
        scene.add(Instance("Boulder", translate=(x, 0.0, 0.0), scale=8.0))

    lo, hi = scene.bounds()
    assert lo[0] == pytest.approx(-1.0)
    assert hi[0] == pytest.approx(1.0)

    # The documented escape hatch: an untextured Box is invisible to a render
    # but measurable here, so it hands the bounds back their real extent.
    scene.add(Box((-58.0, -8.0, -8.0), (58.0, 8.0, 8.0)))
    lo, hi = scene.bounds()
    assert lo[0] == pytest.approx(-58.0)
    assert hi[0] == pytest.approx(58.0)


def test_lights_from_bounds_scale_with_the_scene():
    near = lights_from_bounds((-1, -1, -1), (1, 1, 1))
    far = lights_from_bounds((-10, -10, -10), (10, 10, 10))
    assert len(near) == 2 and near[1].shadowless
    assert np.linalg.norm(far[0].position) > np.linalg.norm(near[0].position)
    assert len(lights_from_bounds((-1, -1, -1), (1, 1, 1), fill=False)) == 1


# ---------------------------------------------------------------------------
# Camera arithmetic
# ---------------------------------------------------------------------------


def test_fov_horizontal_to_vertical_is_narrower_on_wide_images():
    assert fov_horizontal_to_vertical(60.0, 16 / 9) < 60.0


def test_fov_horizontal_to_vertical_is_identity_at_square():
    assert fov_horizontal_to_vertical(45.0, 1.0) == pytest.approx(45.0)


def test_fov_horizontal_to_vertical_matches_the_trig():
    expected = math.degrees(2 * math.atan(math.tan(math.radians(30.0)) / 1.5))
    assert fov_horizontal_to_vertical(60.0, 1.5) == pytest.approx(expected)


# ---------------------------------------------------------------------------
# lights_from_bounds: which way is up
# ---------------------------------------------------------------------------


def test_the_default_rig_is_unchanged():
    """The +y-up offsets are load-bearing for existing callers; `up` is additive."""
    lo, hi = np.array([-1.0, -1.0, 0.0]), np.array([1.0, 1.0, 10.0])
    centre = (lo + hi) / 2.0
    radius = float(np.linalg.norm(hi - lo)) / 2.0
    key, fill = lights_from_bounds(lo, hi)
    assert np.allclose(key.position, centre + np.array([1.4, 1.6, -1.4]) * radius)
    assert np.allclose(fill.position, centre + np.array([-1.6, 0.6, -1.2]) * radius)


@pytest.mark.parametrize(
    "up, axis",
    [((0.0, 1.0, 0.0), 1), ((0.0, 0.0, 1.0), 2), ((1.0, 0.0, 0.0), 0)],
)
def test_the_key_light_is_above_the_subject_for_any_up_axis(up, axis):
    """
    The bug this parameter exists for: a +z-up scene lit by the +y-up defaults
    puts its key light at centre - 1.4*radius along z, below the ground, so the
    subject is lit from underneath. Whatever `up` says, the key goes over it.
    """
    lo, hi = np.array([-2.0, -2.0, 0.0]), np.array([2.0, 2.0, 20.0])
    key = lights_from_bounds(lo, hi, up=up)[0]
    assert key.position[axis] > hi[axis]


def test_the_rig_rotates_rigidly_with_up():
    """Only the frame turns — distances from the subject are unchanged."""
    lo, hi = np.array([-2.0, -1.0, 0.0]), np.array([2.0, 3.0, 20.0])
    centre = (lo + hi) / 2.0
    spans = [
        np.linalg.norm(np.asarray(light.position) - centre)
        for up in ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
        for light in lights_from_bounds(lo, hi, up=up)
    ]
    assert np.allclose(spans[0::2], spans[0])  # every key at one radius
    assert np.allclose(spans[1::2], spans[1])  # every fill at one radius


def test_the_fill_crosses_to_the_other_side_and_stays_lower_than_the_key():
    """
    "Opposite" is only across the *right* axis — the fill stays on the same
    side in up and front, and lower, which is what a fill is. It is dimmer and
    shadowless besides.
    """
    lo, hi = np.array([-2.0, -2.0, 0.0]), np.array([2.0, 2.0, 20.0])
    centre = (lo + hi) / 2.0
    for up, right_axis, up_axis in (((0.0, 1.0, 0.0), 0, 1), ((0.0, 0.0, 1.0), 0, 2)):
        key, fill = lights_from_bounds(lo, hi, up=up)
        to_key = np.asarray(key.position) - centre
        to_fill = np.asarray(fill.position) - centre
        assert to_key[right_axis] * to_fill[right_axis] < 0.0, f"same side for up={up}"
        assert 0.0 < to_fill[up_axis] < to_key[up_axis], f"fill not below key for up={up}"
        assert fill.color[0] < key.color[0]
        assert fill.shadowless and not key.shadowless


def test_a_degenerate_up_is_an_error_not_a_nan():
    with pytest.raises(ValueError, match="degenerate"):
        lights_from_bounds((-1, -1, -1), (1, 1, 1), up=(0.0, 0.0, 0.0))


# ---------------------------------------------------------------------------
# povgen is reachable without a rendering stack
# ---------------------------------------------------------------------------


def test_importing_povgen_pulls_in_no_rendering_stack():
    """
    povgen is NumPy-only by design, but it used to arrive with VTK attached:
    the package __init__ re-exported lfd eagerly, and povgen imported povray
    for PovCamera, and povray imports lfd. Both links are deferred now.

    A subprocess, because sys.modules is shared across the test session.
    """
    probe = (
        "import sys;"
        "from quiltwright.povgen import PovScene, Sphere, lights_from_bounds;"
        "assert 'pyvista' not in sys.modules, 'povgen pulled in pyvista';"
        "assert 'quiltwright.lfd' not in sys.modules, 'povgen pulled in lfd';"
        "assert 'quiltwright.povray' not in sys.modules, 'povgen pulled in povray';"
        "print('OK')"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_lazy_package_still_exports_everything_it_advertises():
    import quiltwright

    missing = [name for name in quiltwright.__all__ if not hasattr(quiltwright, name)]
    assert not missing, f"__all__ names unreachable through __getattr__: {missing}"
    assert set(quiltwright.__all__) <= set(dir(quiltwright))


def test_an_unknown_attribute_still_raises_attribute_error():
    import quiltwright

    with pytest.raises(AttributeError, match="no attribute"):
        getattr(quiltwright, "definitely_not_a_real_export")  # noqa: B009


# ---------------------------------------------------------------------------
# PovCamera lives in POV-Ray coordinates
# ---------------------------------------------------------------------------


def test_pov_camera_from_plotter_is_the_thing_that_converts():
    """
    Documents the convention a consumer got wrong: PovCamera holds POV-Ray
    coordinates. The bridge converts; a hand-built camera does not, so callers
    must run to_pov themselves. Pinned here so the docstring has a test behind
    it rather than only prose.
    """
    pv = pytest.importorskip("pyvista")
    from quiltwright.povgen import pov_camera_from_plotter

    plotter = pv.Plotter(off_screen=True)
    plotter.camera.position = (1.0, -2.0, 3.0)
    plotter.camera.focal_point = (0.0, 0.0, 4.0)
    plotter.camera.up = (0.0, 0.0, 1.0)
    camera = pov_camera_from_plotter(plotter)
    plotter.close()

    # z negated on all three, exactly as to_pov does it.
    assert camera.location == pytest.approx(to_pov((1.0, -2.0, 3.0)))
    assert camera.look_at == pytest.approx(to_pov((0.0, 0.0, 4.0)))
    assert camera.sky == pytest.approx((0.0, 0.0, -1.0))


# ---------------------------------------------------------------------------
# ground_slab — a finite floor to catch a shadow
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("up, axis", [((0.0, 1.0, 0.0), 1), ((0.0, 0.0, 1.0), 2)])
def test_ground_slab_top_face_sits_at_the_subject_base(up, axis):
    """The subject stands on the floor; it does not hover over one below it."""
    lo, hi = np.array([-4.0, -4.0, 0.0]), np.array([4.0, 4.0, 30.0])
    box = ground_slab(lo, hi, up=up)
    faces = sorted((box.corner1[axis], box.corner2[axis]))
    assert faces[1] == pytest.approx(lo[axis])


def test_ground_slab_scales_with_the_subject():
    lo, hi = np.array([-4.0, -4.0, 0.0]), np.array([4.0, 4.0, 30.0])
    narrow = ground_slab(lo, hi, up=(0, 0, 1), size=2.0)
    wide = ground_slab(lo, hi, up=(0, 0, 1), size=8.0)
    assert (wide.corner2[0] - wide.corner1[0]) == pytest.approx(
        4.0 * (narrow.corner2[0] - narrow.corner1[0])
    )


def test_ground_slab_is_centred_under_an_off_centre_subject():
    lo, hi = np.array([10.0, -4.0, 0.0]), np.array([18.0, 4.0, 30.0])
    box = ground_slab(lo, hi, up=(0, 0, 1))
    assert (box.corner1[0] + box.corner2[0]) / 2 == pytest.approx(14.0)


def test_ground_slab_is_never_degenerate_for_a_flat_subject():
    """A subject with no horizontal extent still needs a floor with an area."""
    box = ground_slab((0.0, 0.0, 0.0), (0.0, 0.0, 5.0), up=(0, 0, 1))
    assert box.corner2[0] > box.corner1[0]


# ---------------------------------------------------------------------------
# pov_camera_from_frame — the sibling for callers with no plotter
# ---------------------------------------------------------------------------


class _Frame:
    """Duck-typed stand-in for kg_utils.viz3d.CameraFrame — not imported here."""

    position = (1.0, -90.0, 15.0)
    focal_point = (1.0, 0.0, 15.0)
    up = (0.0, 0.0, 1.0)


def test_pov_camera_from_frame_converts_into_pov_coordinates():
    """
    The whole point of the function. A frame computed in the right-handed world
    the scene was authored in is not a PovCamera; camera_block emits whatever it
    is handed, so an unconverted one aims at empty space while every assertion
    comparing right-handed to right-handed passes.
    """
    cam = pov_camera_from_frame(_Frame(), fov=26.0)
    assert cam.location == pytest.approx(to_pov(_Frame.position))
    assert cam.look_at == pytest.approx(to_pov(_Frame.focal_point))
    assert cam.sky == pytest.approx((0.0, 0.0, -1.0))
    assert cam.fov == 26.0


def test_pov_camera_from_frame_matches_the_plotter_bridge():
    """Both bridges must land on the same convention, or the two paths diverge."""
    pv = pytest.importorskip("pyvista")

    plotter = pv.Plotter(off_screen=True)
    plotter.camera.position = _Frame.position
    plotter.camera.focal_point = _Frame.focal_point
    plotter.camera.up = _Frame.up
    carried = pov_camera_from_plotter(plotter, fov=26.0)
    plotter.close()

    framed = pov_camera_from_frame(_Frame(), fov=26.0)
    assert framed.location == pytest.approx(carried.location)
    assert framed.look_at == pytest.approx(carried.look_at)
    assert framed.sky == pytest.approx(carried.sky)


def test_pov_camera_from_frame_accepts_bare_sequences():
    cam = pov_camera_from_frame((0.0, -8.0, 3.0), (0.0, 0.0, 3.0), (0.0, 0.0, 1.0))
    assert cam.location == pytest.approx((0.0, -8.0, -3.0))


def test_pov_camera_from_frame_needs_a_look_at_for_a_bare_position():
    with pytest.raises(ValueError, match="look_at"):
        pov_camera_from_frame((0.0, -8.0, 3.0))


def test_zoom_dollies_toward_the_focal_point_without_moving_it():
    near = pov_camera_from_frame(_Frame(), zoom=2.0)
    far = pov_camera_from_frame(_Frame(), zoom=1.0)
    assert near.focal_distance == pytest.approx(far.focal_distance / 2.0)
    assert near.look_at == pytest.approx(far.look_at)


def test_a_non_positive_zoom_is_an_error_not_a_flipped_camera():
    with pytest.raises(ValueError, match="zoom"):
        pov_camera_from_frame(_Frame(), zoom=0.0)


# ---------------------------------------------------------------------------
# swept_scene — the composer that makes a new consumer cheap
# ---------------------------------------------------------------------------


def _subject(n_glyphs=40, seed=0):
    rng = np.random.default_rng(seed)
    sweeps = [(np.array([[0.0, 0, 0], [0, 0, 10.0], [1.0, 0, 18.0]]), np.array([0.5, 0.3, 0.1]))]
    pts = rng.normal(0, 1, (n_glyphs, 3)) * np.array([2.0, 2, 3.0]) + np.array([0, 0, 16.0])
    dirs = rng.normal(0, 1, (n_glyphs, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    return sweeps, pts, dirs


def test_swept_scene_emits_each_part_once():
    sweeps, pts, dirs = _subject()
    sdl = swept_scene(
        sweeps,
        instances=(pts, dirs),
        instance_palette=["#90EE90", "#5FBF5F"],
        instance_index=np.arange(len(pts)) % 2,
        clouds=[(pts[:5], 0.3, "#FFD700", 0.4)],
        ground=3.0,
    ).sdl()
    assert sdl.count("sphere_sweep {") == 1
    assert sdl.count("object { Glyph ") == len(pts)
    assert sdl.count("#declare Glyph =") == 1  # prototype declared once
    assert sdl.count("#declare Tint") == 2  # one texture per colour
    assert sdl.count("box {") == 1


def test_swept_scene_groups_instances_by_colour_not_one_union_each():
    """The point of instancing: five colours cost five unions, not ten thousand."""
    sweeps, pts, dirs = _subject(n_glyphs=200)
    sdl = swept_scene(
        sweeps,
        instances=(pts, dirs),
        instance_palette=["#a", "#b", "#c"][:3] and ["#aa0000", "#00aa00", "#0000aa"],
        instance_index=np.arange(len(pts)) % 3,
    ).sdl()
    assert sdl.count("union {") == 1 + 3  # the sweeps, plus one per colour


def test_swept_scene_lights_the_subject_before_laying_the_floor():
    """
    Regression the composer exists to make unrepeatable. The rig is sized from
    scene bounds and the slab is wider than the subject, so measuring after
    laying it makes the scene radius the slab's half-diagonal — flattening the
    subject and shrinking its shadow to nothing.
    """
    sweeps, pts, dirs = _subject()
    lit = re.findall(
        r"light_source \{ <([^>]*)>", swept_scene(sweeps, instances=(pts, dirs), ground=8.0).sdl()
    )
    bare = re.findall(
        r"light_source \{ <([^>]*)>", swept_scene(sweeps, instances=(pts, dirs), ground=0).sdl()
    )
    assert lit == bare


def test_swept_scene_only_the_key_casts():
    sweeps, pts, dirs = _subject()
    lights = re.findall(r"light_source \{.*", swept_scene(sweeps, instances=(pts, dirs)).sdl())
    assert sum("shadowless" not in light for light in lights) == 1


def test_swept_scene_rim_light_is_opt_in():
    sweeps, pts, dirs = _subject()
    plain = swept_scene(sweeps, instances=(pts, dirs)).sdl()
    rimmed = swept_scene(sweeps, instances=(pts, dirs), rim_light=True).sdl()
    assert rimmed.count("light_source") == plain.count("light_source") + 1


def test_swept_scene_brightness_scales_the_rig():
    sweeps, pts, dirs = _subject()

    def levels(sdl):
        return [float(m) for m in re.findall(r"light_source \{ <[^>]*> color rgb <([\d.]+)", sdl)]

    dim = levels(swept_scene(sweeps, instances=(pts, dirs), brightness=1.0).sdl())
    bright = levels(swept_scene(sweeps, instances=(pts, dirs), brightness=3.0).sdl())
    assert bright == pytest.approx([v * 3.0 for v in dim])


def test_swept_scene_needs_no_instances_or_clouds():
    sweeps, _, _ = _subject()
    sdl = swept_scene(sweeps).sdl()
    assert "sphere_sweep {" in sdl
    assert "object { Glyph" not in sdl


def test_swept_scene_of_nothing_is_empty_not_a_crash():
    scene = swept_scene([])
    assert "light_source" not in scene.sdl()


def test_instances_by_color_rejects_a_mismatched_index():
    _, pts, dirs = _subject()
    with pytest.raises(ValueError, match="does not match"):
        instances_by_color("Glyph", pts, dirs, ["#fff"], [0, 1, 2])


def test_swept_scene_knows_nothing_about_any_kg_package():
    """Layer 2 must not import layer 1 or any consumer; the seam is arrays."""
    probe = (
        "import sys, quiltwright.povgen;"
        "bad = [m for m in sys.modules if m.split('.')[0] in "
        "('kg_utils', 'gutenberg_kg', 'pycode_kg', 'diary_kg', 'doc_kg')];"
        "assert not bad, bad"
    )
    result = subprocess.run(
        [sys.executable, "-c", probe], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_ground_slab_base_overrides_the_subject_minimum():
    """
    A swept tube's bounds are padded by its radius, so a trunk rooted at z = 0
    reports a minimum of -r and the floor would sit that much low. The caller
    knows where its root actually is.
    """
    lo, hi = np.array([-4.0, -4.0, -0.5]), np.array([4.0, 4.0, 30.0])
    padded = ground_slab(lo, hi, up=(0, 0, 1))
    exact = ground_slab(lo, hi, up=(0, 0, 1), base=0.0)
    assert max(padded.corner1[2], padded.corner2[2]) == pytest.approx(-0.5)
    assert max(exact.corner1[2], exact.corner2[2]) == pytest.approx(0.0)


def test_swept_scene_lights_can_be_left_out():
    sweeps, pts, dirs = _subject()
    assert "light_source" not in swept_scene(sweeps, instances=(pts, dirs), lights=False).sdl()
    assert "light_source" in swept_scene(sweeps, instances=(pts, dirs)).sdl()
