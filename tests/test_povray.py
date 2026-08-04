"""Tests for the POV-Ray quilt renderer (quiltwright.povray)."""

import math
import re
import shutil

import numpy as np
import pytest

from quiltwright.lfd import QUILT_PRESETS, QuiltSpec, view_offsets
from quiltwright.povray import PovCamera, _find_povray, camera_block

# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def camera() -> PovCamera:
    """A camera looking down +z, 10 units from its focal plane."""
    return PovCamera(location=(0.0, 0.0, -10.0), look_at=(0.0, 0.0, 0.0), fov=30.0)


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
        """right/up must not rotate with offset — that is what keeps the
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
# none occludes another — an occluded marker's centroid drifts with the
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
        the leftmost eye — so the near marker travels right-to-left across
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
