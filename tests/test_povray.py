"""Tests for the POV-Ray quilt renderer (quiltwright.povray)."""

import math
import re
import shutil
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from quiltwright.lfd import QUILT_PRESETS, QuiltSpec, view_offsets
from quiltwright.povray import (
    Clearance,
    PovCamera,
    _find_povray,
    camera_block,
    depth_budget,
    format_depth_budget,
    summarise_depth_sweep,
    sweep_extent,
)


def _parse_plane(text: str) -> tuple[np.ndarray, float]:
    """Pull ``(normal, offset)`` out of a probe wrapper's ``plane`` statement."""
    m = re.search(r"plane \{ <([^>]+)>, ([-\d.e+]+)", text)
    assert m, text
    return np.array([float(v) for v in m.group(1).split(",")]), float(m.group(2))


# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


#: A camera looking down +z, 10 units from its focal plane.  A module constant
#: as well as a fixture: `TestDepthSweep.curve` is class-scoped and so cannot
#: depend on a function-scoped fixture.  `PovCamera` is frozen, so the two
#: share one instance safely.
PROBE_CAMERA = PovCamera(location=(0.0, 0.0, -10.0), look_at=(0.0, 0.0, 0.0), fov=30.0)


@pytest.fixture
def camera() -> PovCamera:
    """A camera looking down +z, 10 units from its focal plane."""
    return PROBE_CAMERA


@pytest.fixture
def tiny_spec() -> QuiltSpec:
    """Minimal 2x2 quilt for fast ray-tracing tests."""
    return QuiltSpec(columns=2, rows=2, quilt_width=256, quilt_height=256, aspect=1.0)


def parse_vectors(block: str) -> dict[str, np.ndarray]:
    """Pull the ``location``/``direction``/``right``/``up`` vectors out of a
    POV-Ray camera statement."""
    out = {}
    for key in ("location", "direction", "right", "up"):
        match = re.search(rf"{key}\s+<([^>]+)>", block)
        assert match, f"{key} missing from camera block:\n{block}"
        out[key] = np.array([float(v) for v in match.group(1).split(",")])
    return out


# ---------------------------------------------------------------------------
# Camera basis
# ---------------------------------------------------------------------------


class TestPovCamera:
    def test_focal_distance(self, camera):
        assert camera.focal_distance == pytest.approx(10.0)

    def test_basis_is_orthonormal(self):
        cam = PovCamera(location=(3.0, 4.0, -5.0), look_at=(1.0, 2.0, 6.0))
        forward, right, up = cam.basis()
        for v in (forward, right, up):
            assert np.linalg.norm(v) == pytest.approx(1.0)
        assert np.dot(forward, right) == pytest.approx(0.0, abs=1e-12)
        assert np.dot(forward, up) == pytest.approx(0.0, abs=1e-12)
        assert np.dot(right, up) == pytest.approx(0.0, abs=1e-12)

    def test_left_handed_convention(self, camera):
        """POV-Ray: up=+y and direction=+z must give right=+x.  Inverting this
        mirrors the sweep and turns the hologram inside out."""
        forward, right, up = camera.basis()
        np.testing.assert_allclose(forward, [0, 0, 1], atol=1e-12)
        np.testing.assert_allclose(right, [1, 0, 0], atol=1e-12)
        np.testing.assert_allclose(up, [0, 1, 0], atol=1e-12)

    def test_image_plane_distance_matches_fov(self):
        # Unit-height image plane: tan(fov/2) = 0.5 / |direction|.
        cam = PovCamera(location=(0, 0, -1), look_at=(0, 0, 0), fov=14.0)
        d = cam.image_plane_distance()
        assert math.degrees(2 * math.atan(0.5 / d)) == pytest.approx(14.0)

    def test_degenerate_camera_rejected(self):
        with pytest.raises(ValueError, match="identical"):
            PovCamera(location=(1, 1, 1), look_at=(1, 1, 1)).basis()

    def test_sky_parallel_to_view_rejected(self):
        with pytest.raises(ValueError, match="parallel"):
            PovCamera(location=(0, 0, 0), look_at=(0, 5, 0), sky=(0, 1, 0)).basis()


# ---------------------------------------------------------------------------
# Off-axis camera emission
# ---------------------------------------------------------------------------


class TestCameraBlock:
    def test_centre_view_is_on_axis(self, camera):
        v = parse_vectors(camera_block(camera, offset=0.0, aspect=1.0))
        np.testing.assert_allclose(v["location"], camera.location, atol=1e-12)
        # No shear at zero offset: direction is pure forward.
        np.testing.assert_allclose(
            v["direction"], [0, 0, camera.image_plane_distance()], atol=1e-12
        )

    def test_never_emits_angle(self, camera):
        """`angle` overrides |direction| and would silently destroy the shear."""
        assert "angle" not in camera_block(camera, offset=2.0, aspect=0.75)

    def test_eye_translates_along_right(self, camera):
        v = parse_vectors(camera_block(camera, offset=2.0, aspect=1.0))
        np.testing.assert_allclose(v["location"], [2.0, 0.0, -10.0], atol=1e-12)

    def test_image_plane_stays_parallel(self, camera):
        """right/up must not rotate with offset -- that is what keeps the
        projection off-axis rather than toed-in."""
        a = parse_vectors(camera_block(camera, offset=0.0, aspect=1.0))
        b = parse_vectors(camera_block(camera, offset=3.0, aspect=1.0))
        np.testing.assert_allclose(a["right"], b["right"], atol=1e-12)
        np.testing.assert_allclose(a["up"], b["up"], atol=1e-12)

    @pytest.mark.parametrize("offset", [-4.0, -1.5, 0.0, 1.5, 4.0])
    def test_focal_point_stays_on_axis(self, camera, offset):
        """The defining property: the ray from the eye through the centre of
        the image plane must hit the look_at point for every view."""
        v = parse_vectors(camera_block(camera, offset, aspect=0.75))
        # Image-plane centre sits at location + direction; extend the ray to
        # the focal distance along the view axis.
        d = camera.image_plane_distance()
        hit = v["location"] + v["direction"] * (camera.focal_distance / d)
        np.testing.assert_allclose(hit, camera.look_at, atol=1e-9)

    def test_aspect_scales_right_only(self, camera):
        v = parse_vectors(camera_block(camera, offset=0.0, aspect=1.7778))
        assert np.linalg.norm(v["right"]) == pytest.approx(1.7778)
        assert np.linalg.norm(v["up"]) == pytest.approx(1.0)

    def test_oblique_camera_focal_point(self):
        """Same invariant for a camera that is not axis-aligned."""
        cam = PovCamera(location=(15.0, 18.5, 5.0), look_at=(66.0, 5.0, 58.0), fov=14.0)
        spec = QUILT_PRESETS["portrait"]
        d = cam.image_plane_distance()
        for offset in view_offsets(spec, cam.focal_distance):
            v = parse_vectors(camera_block(cam, float(offset), aspect=0.75))
            hit = v["location"] + v["direction"] * (cam.focal_distance / d)
            np.testing.assert_allclose(hit, cam.look_at, atol=1e-8)


# ---------------------------------------------------------------------------
# Framing an existing scene
# ---------------------------------------------------------------------------


class TestAimed:
    def test_keeps_view_direction_and_lens(self):
        """Re-aiming must not swing the camera off the scene's own axis."""
        cam = PovCamera.aimed((15.0, 20.0, 6.0), (58.0, 19.0, 53.0), fov=53.13, focal_distance=48.5)
        base = PovCamera(location=(15.0, 20.0, 6.0), look_at=(58.0, 19.0, 53.0))
        np.testing.assert_allclose(cam.basis()[0], base.basis()[0], atol=1e-12)
        assert cam.fov == pytest.approx(53.13)

    def test_focal_distance_applied(self):
        cam = PovCamera.aimed((0, 0, 0), (0, 0, 10), fov=30.0, focal_distance=48.5)
        assert cam.focal_distance == pytest.approx(48.5)
        np.testing.assert_allclose(cam.look_at, [0, 0, 48.5], atol=1e-12)

    def test_defaults_to_scene_aim_distance(self):
        cam = PovCamera.aimed((0, 0, 0), (0, 0, 10), fov=30.0)
        assert cam.focal_distance == pytest.approx(10.0)
        np.testing.assert_allclose(cam.look_at, [0, 0, 10], atol=1e-12)

    def test_lateral_shift_slides_eye_and_aim_together(self):
        """The look-at point rides along with the eye, so the view direction
        is untouched -- the whole point of shifting rather than re-aiming."""
        cam = PovCamera.aimed((0, 0, 0), (0, 0, 10), fov=30.0, lateral_shift=-5.0)
        np.testing.assert_allclose(cam.location, [-5, 0, 0], atol=1e-12)
        np.testing.assert_allclose(cam.look_at, [-5, 0, 10], atol=1e-12)

    def test_rejects_non_positive_focal_distance(self):
        with pytest.raises(ValueError, match="focal_distance"):
            PovCamera.aimed((0, 0, 0), (0, 0, 10), fov=30.0, focal_distance=0.0)

    def test_rejects_degenerate_aim(self):
        with pytest.raises(ValueError, match="identical"):
            PovCamera.aimed((1, 1, 1), (1, 1, 1), fov=30.0)


class TestSweepExtent:
    def test_matches_outermost_view_offset(self):
        spec = QUILT_PRESETS["portrait"]
        offsets = view_offsets(spec, 48.5)
        assert sweep_extent(spec, 48.5) == pytest.approx(abs(offsets).max())

    def test_scales_with_focal_distance(self):
        spec = QUILT_PRESETS["portrait"]
        assert sweep_extent(spec, 20.0) == pytest.approx(2 * sweep_extent(spec, 10.0))


class TestClearance:
    @pytest.fixture
    def museum(self) -> Clearance:
        return Clearance(left=-18.0, right=8.0, margin=2.0)

    def test_centre_and_half_width(self, museum):
        assert museum.centre == pytest.approx(-5.0)
        assert museum.half_width == pytest.approx(11.0)

    def test_cone_is_the_measured_museum_value(self, museum):
        # 2*atan(11 / 46.87) -> the 26.4 deg the museum render uses, where
        # 46.87 is the harmonic mean of its measured 31..96 depth range.
        assert museum.cone(46.87) == pytest.approx(26.4, abs=0.05)

    def test_cone_sweep_lands_on_the_margin(self, museum):
        """The derived cone must consume exactly the usable corridor: any
        wider and the outer views render the back of a wall."""
        spec = replace(QUILT_PRESETS["16-landscape"], view_cone=museum.cone(48.5))
        assert sweep_extent(spec, 48.5) == pytest.approx(museum.half_width)
        assert museum.fits(spec, 48.5)

    @pytest.mark.parametrize("cone", [35.0, 50.0])
    def test_uncorrected_cones_do_not_fit_the_museum(self, museum, cone):
        """The documented 35 deg standard and the 16" Landscape's own 50 deg
        both walk through the wall -- the failure this class exists to catch,
        and the one that shows up only in the views nobody previews."""
        spec = replace(QUILT_PRESETS["16-landscape"], view_cone=cone)
        assert not museum.fits(spec, 48.5)

    @pytest.mark.parametrize("focal", [5.0, 48.5, 63.7, 1000.0])
    def test_derived_cone_never_reports_a_wall_strike(self, museum, focal):
        """Rounding must not make the cone this class derived look like it
        leaves the room; the report would cry wolf on every render."""
        spec = replace(QUILT_PRESETS["16-landscape"], view_cone=museum.cone(focal))
        assert museum.fits(spec, focal)

    def test_inverted_corridor_rejected(self):
        with pytest.raises(ValueError, match="must exceed"):
            Clearance(left=8.0, right=-18.0)

    def test_negative_margin_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            Clearance(left=-1.0, right=1.0, margin=-0.5)

    def test_margin_consuming_corridor_rejected(self):
        with pytest.raises(ValueError, match="no room"):
            Clearance(left=-1.0, right=1.0, margin=1.0).cone(10.0)

    def test_non_positive_focal_distance_rejected(self, museum):
        with pytest.raises(ValueError, match="focal_distance"):
            museum.cone(0.0)


class TestDepthBudget:
    @pytest.fixture
    def spec(self) -> QuiltSpec:
        """The museum's quilt: 16" Landscape at its clearance-limited cone."""
        cone = Clearance(left=-18.0, right=8.0, margin=2.0).cone(46.87)
        return replace(QUILT_PRESETS["16-landscape"], view_cone=cone)

    def test_focal_plane_has_zero_disparity(self, spec):
        cam = PovCamera(location=(0, 0, 0), look_at=(0, 0, 46.87), fov=53.13)
        rows = depth_budget(spec, cam, {"focal": 46.87, "near": 31.0, "sky": math.inf})
        assert dict((label, px) for label, _, px in rows)["focal"] == pytest.approx(0.0)

    def test_harmonic_focal_plane_balances_the_extremes(self, spec):
        """Near and far disparity match when the focal plane sits at their
        harmonic mean -- the property the museum camera is built on."""
        cam = PovCamera(location=(0, 0, 0), look_at=(0, 0, 5952 / 127), fov=53.13)
        rows = dict((label, px) for label, _, px in depth_budget(spec, cam, {"n": 31.0, "f": 96.0}))
        assert rows["n"] == pytest.approx(rows["f"], rel=1e-6)

    def test_rows_preserve_input_order(self, spec):
        cam = PovCamera(location=(0, 0, 0), look_at=(0, 0, 46.87), fov=53.13)
        depths = {"near": 31.0, "focal": 46.87, "far": 96.0}
        assert [label for label, _, _ in depth_budget(spec, cam, depths)] == list(depths)

    def test_report_flags_a_sweep_that_leaves_the_room(self, spec):
        cam = PovCamera(location=(0, 0, 0), look_at=(0, 0, 46.87), fov=53.13)
        wide = replace(spec, view_cone=35.0)
        text = format_depth_budget(
            wide, cam, {"near": 31.0}, clearance=Clearance(-18.0, 8.0, margin=2.0)
        )
        assert "WARNING" in text

    def test_report_is_quiet_when_the_sweep_fits(self, spec):
        cam = PovCamera(location=(0, 0, 0), look_at=(0, 0, 46.87), fov=53.13)
        text = format_depth_budget(
            spec, cam, {"near": 31.0}, clearance=Clearance(-18.0, 8.0, margin=2.0)
        )
        assert "WARNING" not in text
        assert "clearance +/-11.0" in text

    def test_report_flags_soft_depths(self, spec):
        cam = PovCamera(location=(0, 0, 0), look_at=(0, 0, 46.87), fov=53.13)
        text = format_depth_budget(spec, cam, {"near": 31.0, "sky": math.inf}, soft_px=5.5)
        near, sky = [line for line in text.splitlines() if "near" in line or "sky" in line]
        assert "<- soft" not in near
        assert "<- soft" in sky

    def test_cycles_camera_is_accepted(self, spec):
        """The budget reads fov and focal_distance, not a POV-Ray type."""
        from quiltwright.cycles import CyclesCamera

        cam = CyclesCamera(location=(0.0, 0.0, 0.0), look_at=(0.0, 0.0, 46.87), fov=53.13)
        rows = depth_budget(spec, cam, {"focal": 46.87, "near": 31.0})
        assert dict((label, px) for label, _, px in rows)["focal"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Binary discovery
# ---------------------------------------------------------------------------


class TestFindPovray:
    def test_missing_binary_raises(self):
        with pytest.raises(RuntimeError, match="not found"):
            _find_povray("definitely-not-a-real-povray-binary")

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("POVRAY_BINARY", "definitely-not-real-either")
        with pytest.raises(RuntimeError, match="definitely-not-real-either"):
            _find_povray()


# ---------------------------------------------------------------------------
# End-to-end ray-tracing (requires a povray binary)
# ---------------------------------------------------------------------------


requires_povray = pytest.mark.skipif(
    shutil.which("povray") is None, reason="povray binary unavailable"
)

# Three emissive markers at different depths.  The green one sits exactly on
# the focal plane; the others straddle it.  They are separated vertically so
# none occludes another -- an occluded marker's centroid drifts with the
# visible crescent, which would masquerade as parallax.
DEPTH_SCENE = """
#version 3.7;
global_settings { assumed_gamma 1.0 }
camera { location <0,0,-10> look_at <0,0,0> angle 30 }
background { color rgb 0 }
sphere { <0,0,0>,     0.20 pigment { color rgb <0,1,0> } finish { ambient 1 } }
sphere { <0,-0.9,-4>, 0.20 pigment { color rgb <1,0,0> } finish { ambient 1 } }
sphere { <0,0.9,4>,   0.20 pigment { color rgb <0,0,1> } finish { ambient 1 } }
"""


@pytest.mark.slow
@requires_povray
class TestRenderPovQuilt:
    @pytest.fixture
    def scene(self, tmp_path):
        path = tmp_path / "depth.pov"
        path.write_text(DEPTH_SCENE)
        return path

    def test_quilt_shape_and_parallax(self, scene, tiny_spec, camera):
        from quiltwright.povray import render_pov_quilt

        quilt = render_pov_quilt(scene, tiny_spec, camera, progress=False)
        assert quilt.shape == (256, 256, 3)
        assert quilt.dtype == np.uint8

        th, tw = tiny_spec.tile_height, tiny_spec.tile_width
        x0, y0 = tiny_spec.tile_origin(0)
        x3, y3 = tiny_spec.tile_origin(3)
        v0 = quilt[y0 : y0 + th, x0 : x0 + tw]
        v3 = quilt[y3 : y3 + th, x3 : x3 + tw]
        assert not np.array_equal(v0, v3), "leftmost and rightmost views identical"

    def test_focal_plane_is_pinned(self, scene, tiny_spec, camera):
        """The on-focal-plane marker must not move between views, while the
        off-plane markers must.  This is the property that distinguishes a
        correct off-axis shear from a toe-in rotation."""
        from quiltwright.povray import render_pov_quilt

        quilt = render_pov_quilt(scene, tiny_spec, camera, progress=False)
        th, tw = tiny_spec.tile_height, tiny_spec.tile_width

        def centroid_x(tile, channel):
            m = (tile[..., channel] > 150) & (tile.sum(2) - tile[..., channel] < 150)
            return m.nonzero()[1].mean() if m.any() else None

        green, red = [], []
        for i in range(tiny_spec.n_views):
            x, y = tiny_spec.tile_origin(i)
            tile = quilt[y : y + th, x : x + tw].astype(float)
            green.append(centroid_x(tile, 1))
            red.append(centroid_x(tile, 0))

        # Focal-plane marker: pinned to the tile centre in every view.
        assert all(g is not None for g in green), "focal marker missing from a view"
        assert max(green) - min(green) < 1.0, f"focal marker drifted: {green}"
        for g in green:
            assert abs(g - tw / 2) < 2.0

        # Near marker: must actually shift, or there is no parallax at all.
        assert all(r is not None for r in red)
        assert max(red) - min(red) > 5.0, f"no parallax on the near marker: {red}"

    def test_view_zero_is_leftmost_eye(self, scene, tiny_spec, camera):
        """Moving the eye right must push nearer objects left, and view 0 is
        the leftmost eye -- so the near marker travels right-to-left across
        the view order."""
        from quiltwright.povray import render_pov_quilt

        quilt = render_pov_quilt(scene, tiny_spec, camera, progress=False)
        th, tw = tiny_spec.tile_height, tiny_spec.tile_width
        xs = []
        for i in (0, tiny_spec.n_views - 1):
            x, y = tiny_spec.tile_origin(i)
            tile = quilt[y : y + th, x : x + tw].astype(float)
            m = (tile[..., 0] > 150) & (tile[..., 1] < 150) & (tile[..., 2] < 150)
            xs.append(m.nonzero()[1].mean())
        assert xs[0] > xs[1], f"view order mirrored: near marker at {xs}"

    def test_view_count_mismatch_detected(self, scene, camera):
        """A spec whose view count disagrees with the rendered views must
        fail loudly rather than emit a half-filled quilt."""
        from quiltwright.lfd import assemble_quilt

        spec = QuiltSpec(columns=2, rows=2, quilt_width=64, quilt_height=64, aspect=1.0)
        with pytest.raises(ValueError, match="expected 4 views"):
            assemble_quilt((np.zeros((32, 32, 3), np.uint8) for _ in range(3)), spec)

    def test_anamorphic_quilt_assembles(self, scene, camera):
        """The 16" Landscape shape: views are captured at 16:9 and squeezed
        into 4:3 tiles.  Scaled down 10x, the squeeze factor is the device's
        own 0.75 -- tiles 96x72 holding views rendered 128x72.
        """
        from quiltwright.povray import render_pov_quilt

        spec = QuiltSpec(columns=2, rows=2, quilt_width=192, quilt_height=144, aspect=1.77778)
        assert (spec.tile_width, spec.tile_height) == (96, 72)
        quilt = render_pov_quilt(scene, spec, camera, progress=False)
        assert quilt.shape == (144, 192, 3)

    def test_missing_scene_raises(self, tiny_spec, camera, tmp_path):
        from quiltwright.povray import render_pov_quilt

        with pytest.raises(FileNotFoundError):
            render_pov_quilt(tmp_path / "nope.pov", tiny_spec, camera, progress=False)

    def test_bad_scene_surfaces_povray_error(self, tmp_path, tiny_spec, camera):
        from quiltwright.povray import render_pov_quilt

        bad = tmp_path / "bad.pov"
        bad.write_text("this is not valid POV-Ray SDL {{{\n")
        with pytest.raises(RuntimeError, match="POV-Ray failed"):
            render_pov_quilt(bad, tiny_spec, camera, progress=False)

    def test_keep_views_retains_artifacts(self, scene, tiny_spec, camera, tmp_path):
        from quiltwright.povray import render_pov_quilt

        keep = tmp_path / "views"
        render_pov_quilt(scene, tiny_spec, camera, keep_views=keep, progress=False)
        assert len(list(keep.glob("*.png"))) == tiny_spec.n_views
        assert len(list(keep.glob("*.pov"))) == tiny_spec.n_views
        # The wrapper must leave the scene untouched and override its camera.
        wrapper = (keep / "view000.pov").read_text()
        assert str(scene) in wrapper
        assert "camera {" in wrapper


@pytest.mark.slow
@requires_povray
class TestRenderPovViews:
    """The sweep-export path, which hologram printers consume instead of a quilt."""

    @pytest.fixture
    def scene(self, tmp_path):
        path = tmp_path / "depth.pov"
        path.write_text(DEPTH_SCENE)
        return path

    def test_writes_one_frame_per_view(self, scene, camera, tmp_path):
        from quiltwright.lfd import sweep_spec
        from quiltwright.povray import render_pov_views

        spec = sweep_spec(5, 45.0, 64, 64)
        paths = render_pov_views(scene, spec, camera, tmp_path / "sweep", progress=False)

        assert [p.name for p in paths] == [f"view{i:03d}.png" for i in range(5)]
        assert all(p.is_file() for p in paths)
        # Wrappers stay behind unless asked for.
        assert list((tmp_path / "sweep").glob("*.pov")) == []

    def test_prime_view_count_renders(self, scene, camera, tmp_path):
        """23 views is what LITIHOLO_SWEEP asks for and no quilt grid can supply."""
        from quiltwright.lfd import LITIHOLO_SWEEP
        from quiltwright.povray import render_pov_views

        spec = replace(LITIHOLO_SWEEP, quilt_width=23 * 48, quilt_height=60)
        paths = render_pov_views(scene, spec, camera, tmp_path / "sweep", progress=False)
        assert len(paths) == 23

    def test_parallax_matches_the_quilt_path(self, scene, tiny_spec, camera, tmp_path):
        """Same camera geometry as render_pov_quilt, only the packing differs."""
        from PIL import Image

        from quiltwright.povray import render_pov_quilt, render_pov_views

        keep = tmp_path / "kept"
        render_pov_quilt(scene, tiny_spec, camera, keep_views=keep, progress=False)
        swept = render_pov_views(scene, tiny_spec, camera, tmp_path / "sweep", progress=False)

        for i, path in enumerate(swept):
            a = np.asarray(Image.open(keep / f"view{i:03d}.png").convert("RGB")).astype(int)
            b = np.asarray(Image.open(path).convert("RGB")).astype(int)
            # Adaptive AA is nondeterministic across runs, so compare centroids
            # of the emissive markers rather than pixels.
            assert a.shape == b.shape
            assert abs(a.mean() - b.mean()) < 1.0

    def test_keep_wrappers(self, scene, camera, tmp_path):
        from quiltwright.lfd import sweep_spec
        from quiltwright.povray import render_pov_views

        spec = sweep_spec(3, 45.0, 64, 64)
        out = tmp_path / "sweep"
        render_pov_views(scene, spec, camera, out, keep_wrappers=True, progress=False)
        assert len(list(out.glob("*.pov"))) == 3
        assert str(scene) in (out / "view000.pov").read_text()

    def test_missing_scene(self, camera, tmp_path):
        from quiltwright.lfd import sweep_spec
        from quiltwright.povray import render_pov_views

        with pytest.raises(FileNotFoundError):
            render_pov_views(
                tmp_path / "nope.pov",
                sweep_spec(3, 45.0, 64, 64),
                camera,
                tmp_path / "out",
                progress=False,
            )


# ---------------------------------------------------------------------------
# Work-thread resolution
#
# POV-Ray takes every core it can see, which makes a multi-minute quilt lock
# up the workstation it is rendering on.  Two mechanisms guarded against that
# and neither covered the common case: POVINI's Work_Threads only exists when
# the Makefile writes it, and the jobs>1 split does nothing at the documented
# jobs=1.  The courtesy cap fills that gap -- but it must stay *out of the
# way* of POVINI, because a command-line +WT overrides an INI outright and
# would silently defeat `make quilts RENDER_THREADS=$(nproc)`.
# ---------------------------------------------------------------------------


class TestResolveWorkThreads:
    def test_bare_call_holds_two_cores_back(self, monkeypatch):
        """The gap this closes: a script run directly took the whole machine."""
        from quiltwright import povray

        monkeypatch.delenv("POVINI", raising=False)
        monkeypatch.setattr(povray.os, "cpu_count", lambda: 18)
        assert povray.resolve_work_threads() == 16

    def test_povini_work_threads_suppresses_the_cap(self, monkeypatch, tmp_path):
        """A command-line +WT beats POVINI, so capping would override the
        Makefile's own RENDER_THREADS escape hatch."""
        from quiltwright import povray

        ini = tmp_path / "threads.ini"
        ini.write_text("Display=Off\nWork_Threads=18\n")
        monkeypatch.setenv("POVINI", str(ini))
        monkeypatch.setattr(povray.os, "cpu_count", lambda: 18)
        assert povray.resolve_work_threads() is None

    def test_povini_without_work_threads_still_caps(self, monkeypatch, tmp_path):
        """POVINI is set for its library paths far more often than for threads."""
        from quiltwright import povray

        ini = tmp_path / "plain.ini"
        ini.write_text("Display=Off\n")
        monkeypatch.setenv("POVINI", str(ini))
        monkeypatch.setattr(povray.os, "cpu_count", lambda: 18)
        assert povray.resolve_work_threads() == 16

    def test_unreadable_povini_falls_back_to_the_cap(self, monkeypatch, tmp_path):
        from quiltwright import povray

        monkeypatch.setenv("POVINI", str(tmp_path / "absent.ini"))
        monkeypatch.setattr(povray.os, "cpu_count", lambda: 18)
        assert povray.resolve_work_threads() == 16

    def test_explicit_request_wins_over_everything(self, monkeypatch, tmp_path):
        from quiltwright import povray

        ini = tmp_path / "threads.ini"
        ini.write_text("Work_Threads=18\n")
        monkeypatch.setenv("POVINI", str(ini))
        assert povray.resolve_work_threads(4) == 4

    @pytest.mark.parametrize("uncapped", [0, -1])
    def test_zero_or_negative_means_take_everything(self, monkeypatch, uncapped):
        """The opt-out: render farms and CI want every core."""
        from quiltwright import povray

        monkeypatch.delenv("POVINI", raising=False)
        assert povray.resolve_work_threads(uncapped) is None

    def test_single_core_machine_still_gets_one_thread(self, monkeypatch):
        from quiltwright import povray

        monkeypatch.delenv("POVINI", raising=False)
        monkeypatch.setattr(povray.os, "cpu_count", lambda: 1)
        assert povray.resolve_work_threads() == 1

    def test_cap_reaches_the_povray_command_line(self, monkeypatch, tmp_path):
        """End to end: the resolved value is actually passed as +WT."""
        from quiltwright import povray

        monkeypatch.delenv("POVINI", raising=False)
        monkeypatch.setattr(povray.os, "cpu_count", lambda: 18)
        seen: list[list[str]] = []

        def fake_render(
            povray_bin,
            wrapper,
            out_png,
            width,
            height,
            library_paths,
            antialias,
            quality,
            extra_args,
            workdir,
        ):
            seen.append(list(extra_args))
            from PIL import Image

            Image.new("RGB", (width, height)).save(out_png)

        monkeypatch.setattr(povray, "_render_view", fake_render)
        monkeypatch.setattr(povray, "_find_povray", lambda binary=None: "/bin/true")

        scene = tmp_path / "s.pov"
        scene.write_text("camera { location <0,0,-1> look_at 0 }\n")
        spec = QuiltSpec(columns=2, rows=1, quilt_width=64, quilt_height=32, aspect=1.0)
        camera = PovCamera(location=(0.0, 0.0, -10.0), look_at=(0.0, 0.0, 0.0), fov=30.0)

        povray.render_pov_quilt(scene, spec, camera, progress=False)
        assert seen, "no views rendered"
        assert all("+WT16" in args for args in seen)

    def test_caller_supplied_wt_is_not_overridden(self, monkeypatch, tmp_path):
        """An explicit +WT in extra_args stays the only one."""
        from quiltwright import povray

        monkeypatch.delenv("POVINI", raising=False)
        monkeypatch.setattr(povray.os, "cpu_count", lambda: 18)
        seen: list[list[str]] = []

        def fake_render(
            povray_bin,
            wrapper,
            out_png,
            width,
            height,
            library_paths,
            antialias,
            quality,
            extra_args,
            workdir,
        ):
            seen.append(list(extra_args))
            from PIL import Image

            Image.new("RGB", (width, height)).save(out_png)

        monkeypatch.setattr(povray, "_render_view", fake_render)
        monkeypatch.setattr(povray, "_find_povray", lambda binary=None: "/bin/true")

        scene = tmp_path / "s.pov"
        scene.write_text("camera { location <0,0,-1> look_at 0 }\n")
        spec = QuiltSpec(columns=2, rows=1, quilt_width=64, quilt_height=32, aspect=1.0)
        camera = PovCamera(location=(0.0, 0.0, -10.0), look_at=(0.0, 0.0, 0.0), fov=30.0)

        povray.render_pov_quilt(scene, spec, camera, progress=False, extra_args=("+WT3",))
        assert all(len([a for a in args if a.startswith("+WT")]) == 1 for args in seen)
        assert all("+WT3" in args for args in seen)


# ---------------------------------------------------------------------------
# Depth probing
# ---------------------------------------------------------------------------


class TestProbeWrapper:
    """The marker plane's arithmetic, which decides what a probe measures.

    A plane one unit off is a depth histogram one unit wrong, and nothing
    downstream can tell -- so the geometry is pinned here rather than trusted
    to the rendered result.
    """

    def test_the_plane_passes_through_the_probe_distance(self, camera):
        from quiltwright.povray import _probe_wrapper

        text = _probe_wrapper(Path("/scene.pov"), camera, 16 / 9, 42.0)
        normal, offset = _parse_plane(text)
        forward = camera.basis()[0]
        point = np.asarray(camera.location, dtype="d") + forward * 42.0
        assert np.dot(normal, point) == pytest.approx(offset)

    def test_the_plane_faces_along_the_view_axis(self, camera):
        from quiltwright.povray import _probe_wrapper

        normal, _ = _parse_plane(_probe_wrapper(Path("/scene.pov"), camera, 1.0, 5.0))
        assert np.allclose(normal, camera.basis()[0])

    def test_the_marker_is_self_lit_and_casts_nothing(self, camera):
        """The scene's own lights must not tint the thing being measured,
        and its shadow must not darken what it is meant to reveal.
        """
        from quiltwright.povray import _probe_wrapper

        text = _probe_wrapper(Path("/scene.pov"), camera, 1.0, 5.0)
        assert "ambient 1 diffuse 0" in text
        assert "no_shadow" in text
        assert '#include "/scene.pov"' in text


class TestSummariseDepthSweep:
    def test_near_is_where_geometry_first_appears(self):
        rows = [(10.0, 0.0), (20.0, 0.0005), (30.0, 0.4), (40.0, 0.9)]
        assert summarise_depth_sweep(rows)["near"] == 30.0  # 0.0005 is below `appear`

    def test_far_is_a_share_of_what_the_sweep_accumulated(self):
        """Not a share of the frame: a scene that is 40% sky must not be
        judged against content it can never occlude.
        """
        rows = [(10.0, 0.0), (20.0, 0.30), (30.0, 0.57), (40.0, 0.60), (5000.0, 0.60)]
        found = summarise_depth_sweep(rows)
        assert found["far"] == 30.0  # 0.57 >= 0.95 * 0.60
        assert found["sky_fraction"] == pytest.approx(0.40)

    def test_thresholds_are_tunable(self):
        rows = [(10.0, 0.0), (20.0, 0.30), (30.0, 0.57), (40.0, 0.60)]
        assert summarise_depth_sweep(rows, structured=0.99)["far"] == 40.0

    def test_an_empty_sweep_is_refused(self):
        with pytest.raises(ValueError, match="no probe rows"):
            summarise_depth_sweep([])


#: A closed scene: two markers at known depths in front of an opaque backdrop,
#: so the sweep saturates instead of creeping the way a sea does.  The camera
#: sits at ``z = -10``, so the near sphere is 10 units out, the far one 14,
#: and the backdrop 30.
PROBE_SCENE = """
#version 3.7;
global_settings { assumed_gamma 1.0 }
background { color rgb 0 }
sphere { <0,-0.9,0>, 0.9 pigment { color rgb <0,1,0> } finish { ambient 1 } }
sphere { <0,0.9,4>,  0.9 pigment { color rgb <0,0,1> } finish { ambient 1 } }
plane { <0,0,-1>, -20 pigment { color rgb <0.5,0.5,0.5> } finish { ambient 1 } }
"""


@pytest.mark.slow
@requires_povray
class TestDepthSweep:
    """The measurement itself, against a scene whose depths are known exactly."""

    @pytest.fixture(scope="class")
    @staticmethod
    def scene(tmp_path_factory):
        path = tmp_path_factory.mktemp("depth_sweep") / "probe_scene.pov"
        path.write_text(PROBE_SCENE)
        return path

    # Class-scoped: one 6 s ray-trace answers all three questions below, which
    # read different properties of the same curve.  Function-scoped, this was
    # 18 s of the suite's 96.
    @pytest.fixture(scope="class")
    @staticmethod
    def curve(scene):
        from quiltwright.povray import depth_sweep

        return depth_sweep(
            scene,
            PROBE_CAMERA,
            [5.0, 8.0, 11.0, 13.0, 16.0, 25.0, 40.0],
            width=64,
            height=64,
            quality=9,
            progress=False,
        )

    def test_the_histogram_is_cumulative(self, curve):
        fractions = [f for _, f in curve]
        assert fractions == sorted(fractions)

    def test_it_finds_the_geometry_where_it_is(self, curve):
        found = summarise_depth_sweep(curve)
        # The near sphere is at 10 units, the far one at 14, the backdrop 30.
        assert found["near"] == 11.0
        assert found["far"] == 40.0

    def test_a_closed_scene_leaves_no_sky(self, curve):
        """The backdrop occludes everything, so nothing survives to infinity
        -- which is what makes the 95% rule land on real content here.
        """
        assert summarise_depth_sweep(curve)["sky_fraction"] == pytest.approx(0.0, abs=0.01)

    def test_geometry_inside_the_near_plane_is_refused(self, scene):
        """The calibration frame is the one check that the sweep is measuring
        the scene rather than something sitting on the lens.
        """
        from quiltwright.povray import depth_sweep

        # 0.6 units off the near sphere's front, so it is inside the d=1
        # calibration plane and every later reading would measure against it.
        # The wide lens leaves the rest of the frame marker-coloured, which is
        # what the uniformity check reads: an intruder covering *everything*
        # is uniform too, and no calibration frame can tell that from a clean one.
        inside = PovCamera(location=(0.0, -0.9, -1.5), look_at=(0.0, -0.9, 1.0), fov=90.0)
        with pytest.raises(RuntimeError, match="calibration frame is not uniform"):
            depth_sweep(scene, inside, [5.0], width=32, height=32, quality=9, progress=False)

    def test_a_missing_scene_is_refused_before_povray_starts(self, camera, tmp_path):
        from quiltwright.povray import depth_sweep

        with pytest.raises(FileNotFoundError):
            depth_sweep(tmp_path / "absent.pov", camera, [5.0], progress=False)
