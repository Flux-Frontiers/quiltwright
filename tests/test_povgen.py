"""Tests for the POV-Ray scene generator (quiltwright.povgen)."""

import math
import re

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
    instances_from_frames,
    lights_from_bounds,
    parse_color,
    sphere_sweeps_from_paths,
    spheres_from_points,
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
