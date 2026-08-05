"""Tests for the Looking Glass quilt renderer (quiltwright.lfd)."""

import math
from dataclasses import replace

import numpy as np
import pytest
from render_probe import can_render

from quiltwright.lfd import (
    QUILT_PRESETS,
    QuiltSpec,
    _encode_args,
    assemble_quilt,
    focal_distance_for_range,
    save_quilt,
    view_disparity,
    view_offsets,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def portrait() -> QuiltSpec:
    """Standard Looking Glass Portrait quilt spec (48 views, 8x6)."""
    return QUILT_PRESETS["portrait"]


@pytest.fixture
def tiny_spec() -> QuiltSpec:
    """Minimal 2x2 quilt for fast rendering tests."""
    return QuiltSpec(columns=2, rows=2, quilt_width=128, quilt_height=128, aspect=1.0)


# ---------------------------------------------------------------------------
# QuiltSpec geometry
# ---------------------------------------------------------------------------


class TestQuiltSpec:
    def test_portrait_preset(self, portrait):
        assert portrait.n_views == 48
        assert (portrait.columns, portrait.rows) == (8, 6)
        assert (portrait.quilt_width, portrait.quilt_height) == (3360, 3360)
        assert portrait.aspect == 0.75

    def test_portrait_tile_size(self, portrait):
        # 3360 / 8 = 420 wide, 3360 / 6 = 560 tall -> 0.75 view aspect
        assert (portrait.tile_width, portrait.tile_height) == (420, 560)
        assert portrait.tile_width / portrait.tile_height == pytest.approx(portrait.aspect)

    def test_presets_tiles_fit(self):
        # Tile grids must fit inside the quilt; official sizes are not always
        # exact multiples (65" is 8192 px over 9 rows), so allow a sub-tile
        # remainder but never overflow.
        for name, spec in QUILT_PRESETS.items():
            assert spec.tile_width > 0 and spec.tile_height > 0, name
            assert spec.tile_width * spec.columns <= spec.quilt_width, name
            assert spec.tile_height * spec.rows <= spec.quilt_height, name

    def test_official_preset_table(self):
        # Spot-check against the official quilt settings table:
        # https://lfdocs.lookingglassfactory.com/keyconcepts/quilts
        go = QUILT_PRESETS["go"]
        assert (go.columns, go.rows, go.n_views) == (11, 6, 66)
        assert (go.quilt_width, go.quilt_height) == (4092, 4092)
        assert go.aspect == 0.5625
        l65 = QUILT_PRESETS["65"]
        assert (l65.columns, l65.rows, l65.n_views) == (8, 9, 72)
        l27 = QUILT_PRESETS["27-landscape"]
        assert (l27.quilt_width, l27.quilt_height) == (7680, 4320)
        assert l27.aspect == 1.777

    def test_view_zero_is_bottom_left(self, portrait):
        x, y = portrait.tile_origin(0)
        assert x == 0
        assert y == portrait.quilt_height - portrait.tile_height

    def test_last_view_is_top_right(self, portrait):
        x, y = portrait.tile_origin(portrait.n_views - 1)
        assert x == portrait.quilt_width - portrait.tile_width
        assert y == 0

    def test_views_advance_left_to_right(self, portrait):
        x0, y0 = portrait.tile_origin(0)
        x1, y1 = portrait.tile_origin(1)
        assert x1 == x0 + portrait.tile_width
        assert y1 == y0

    def test_rows_advance_bottom_to_top(self, portrait):
        _, y0 = portrait.tile_origin(0)
        _, y1 = portrait.tile_origin(portrait.columns)  # first view of row 1
        assert y1 == y0 - portrait.tile_height

    def test_tile_origins_unique_and_in_bounds(self, portrait):
        origins = {portrait.tile_origin(i) for i in range(portrait.n_views)}
        assert len(origins) == portrait.n_views
        for x, y in origins:
            assert 0 <= x <= portrait.quilt_width - portrait.tile_width
            assert 0 <= y <= portrait.quilt_height - portrait.tile_height

    def test_tile_origin_out_of_range(self, portrait):
        with pytest.raises(ValueError):
            portrait.tile_origin(portrait.n_views)
        with pytest.raises(ValueError):
            portrait.tile_origin(-1)

    def test_filename_convention(self, portrait):
        # Looking Glass software parses _qs<cols>x<rows>a<aspect> suffixes.
        assert portrait.filename("helix") == "helix_qs8x6a0.75.png"

    def test_filename_go(self):
        assert QUILT_PRESETS["go"].filename("x", ext="jpg") == "x_qs11x6a0.5625.jpg"

    def test_with_grid_keeps_quilt_size(self, portrait):
        dense = portrait.with_grid(11, 6)
        assert dense.n_views == 66
        assert (dense.quilt_width, dense.quilt_height) == (3360, 3360)
        assert dense.aspect == portrait.aspect
        assert dense.tile_width < portrait.tile_width  # views cost resolution
        assert dense.filename("x") == "x_qs11x6a0.75.png"


# ---------------------------------------------------------------------------
# Gen3 16" Landscape — the device these renders target
# ---------------------------------------------------------------------------


class TestSixteenLandscape:
    """The 16" Landscape preset, end to end.

    This is the display the museum quilts are actually rendered for, and it
    is the awkward one: its tiles are stored *anamorphically*, so the pixel
    aspect of a tile is not the aspect of the view it holds.  Almost every
    property below looks like a typo until that is understood, which is
    precisely why they are pinned here — "correcting" the preset to make the
    numbers agree is a plausible mistake that would distort every render.
    """

    @pytest.fixture
    def landscape(self) -> QuiltSpec:
        return QUILT_PRESETS["16-landscape"]

    # -- Preset fidelity ----------------------------------------------------

    def test_matches_bridge_default_quilt(self, landscape):
        """Verified against the defaultQuilt Bridge reports for hardware
        version "16_gen3_l" (LKG-J00332)."""
        assert (landscape.columns, landscape.rows) == (8, 6)
        assert landscape.n_views == 48
        assert (landscape.quilt_width, landscape.quilt_height) == (7680, 4320)
        assert landscape.aspect == 1.77778

    def test_native_cone_is_50_degrees(self, landscape):
        """Wider than the 35 deg QuiltSpec default — the device's own optics,
        not the rendering convention."""
        default = QuiltSpec(columns=1, rows=1, quilt_width=8, quilt_height=8, aspect=1.0)
        assert landscape.view_cone == 50.0
        assert default.view_cone == 35.0

    # -- Anamorphic tile geometry ------------------------------------------

    def test_tile_size(self, landscape):
        assert (landscape.tile_width, landscape.tile_height) == (960, 720)

    def test_tiles_are_stored_squeezed(self, landscape):
        """The tile is 4:3 while the view it holds is 16:9.  The display
        un-squeezes on playback; the quilt stores the compressed form."""
        assert landscape.tile_width / landscape.tile_height == pytest.approx(4 / 3)
        assert landscape.aspect == pytest.approx(16 / 9, rel=1e-5)
        assert landscape.tile_width / landscape.tile_height != pytest.approx(landscape.aspect)

    def test_views_are_captured_wider_than_the_tile(self, landscape):
        """Both backends render at ``tile_height * aspect`` so the frustum is
        undistorted, then let assemble_quilt squeeze it in.  Rendering at the
        tile width instead would stretch the scene horizontally by 4/3."""
        render_w = round(landscape.tile_height * landscape.aspect)
        assert render_w == 1280
        assert landscape.tile_width / render_w == pytest.approx(0.75)

    def test_tiling_covers_the_quilt_exactly(self, landscape):
        # Unlike the 65", this preset divides evenly: no unused margin.
        assert landscape.tile_width * landscape.columns == landscape.quilt_width
        assert landscape.tile_height * landscape.rows == landscape.quilt_height

    def test_corner_views(self, landscape):
        assert landscape.tile_origin(0) == (0, 3600)  # view 0: bottom-left
        assert landscape.tile_origin(47) == (6720, 0)  # view 47: top-right

    def test_filename_suffix_bridge_parses(self, landscape):
        assert landscape.filename("museum") == "museum_qs8x6a1.77778.png"

    # -- Assembly -----------------------------------------------------------

    def test_assembly_squeezes_views_into_tiles(self):
        """A 16:9 view laid into a 4:3 tile must lose width, not height.

        Run at 1/10 scale — same aspects and squeeze factor, 1% of the
        pixels.  The full-resolution equivalent is marked slow below.
        """
        spec = QuiltSpec(columns=8, rows=6, quilt_width=768, quilt_height=432, aspect=1.77778)
        assert (spec.tile_width, spec.tile_height) == (96, 72)
        views = [np.full((72, 128, 3), i * 5, dtype=np.uint8) for i in range(spec.n_views)]
        quilt = assemble_quilt(views, spec)
        assert quilt.shape == (432, 768, 3)
        for i in (0, 24, 47):
            x, y = spec.tile_origin(i)
            assert quilt[y + 36, x + 48, 0] == i * 5

    def test_assembly_preserves_view_order(self):
        """View 0 must land bottom-left and view 47 top-right: get this wrong
        and the hologram's look-around runs backwards."""
        spec = QuiltSpec(columns=8, rows=6, quilt_width=768, quilt_height=432, aspect=1.77778)
        views = [np.full((72, 128, 3), i, dtype=np.uint8) for i in range(spec.n_views)]
        quilt = assemble_quilt(views, spec)
        assert quilt[432 - 36, 48, 0] == 0
        assert quilt[36, 768 - 48, 0] == 47

    @pytest.mark.slow
    def test_full_resolution_assembly(self, landscape):
        pytest.importorskip("PIL")
        views = (np.full((720, 1280, 3), i, dtype=np.uint8) for i in range(landscape.n_views))
        quilt = assemble_quilt(views, landscape)
        assert quilt.shape == (4320, 7680, 3)
        assert quilt.dtype == np.uint8
        for i in (0, landscape.n_views - 1):
            x, y = landscape.tile_origin(i)
            assert quilt[y + 360, x + 480, 0] == i

    # -- Video --------------------------------------------------------------

    def test_video_uses_hevc_without_padding(self, landscape):
        """7680 px exceeds the 6000 px H.264 ceiling, and both dimensions are
        even, so yuv420p needs no pad filter."""
        args = _encode_args(landscape, crf=18)
        assert "libx265" in args
        assert "-vf" not in args

    # -- Camera sweep -------------------------------------------------------

    def test_sweep_spans_the_native_cone(self, landscape):
        offs = view_offsets(landscape, distance=48.5)
        assert offs.shape == (48,)
        assert offs[-1] == pytest.approx(48.5 * math.tan(math.radians(25.0)))
        np.testing.assert_allclose(offs, -offs[::-1], atol=1e-12)

    # -- Depth budget on this device ---------------------------------------

    def test_museum_depth_budget(self, landscape):
        """The published museum figures, on this device's real 720 px tiles.

        Anchors the whole chain — preset, cone, focal plane, tile height —
        to numbers measured off finished renders (docs/povray.md).
        """
        spec = replace(landscape, view_cone=25.565)  # clearance-limited
        z = focal_distance_for_range(32.0, 100.0)
        assert z == pytest.approx(48.48, abs=0.01)
        assert view_disparity(spec, 53.13, z, 32.0) == pytest.approx(3.58, abs=0.01)
        assert view_disparity(spec, 53.13, z, 100.0) == pytest.approx(3.58, abs=0.01)
        assert view_disparity(spec, 53.13, z, math.inf) == pytest.approx(6.95, abs=0.01)

    def test_native_cone_costs_the_budget(self, landscape):
        """At the device's full 50 deg cone the same scene doubles its
        disparity, past the ~5 px comfort ceiling — the trade the museum
        script makes when it narrows the cone for wall clearance."""
        z = focal_distance_for_range(32.0, 100.0)
        assert view_disparity(landscape, 53.13, z, 32.0) == pytest.approx(7.36, abs=0.01)

    def test_object_centric_fov_advice_blows_up_here(self, landscape):
        """The "~14 deg FOV" advice that circulates for Looking Glass content
        is for object-centric scenes.  On an interior it magnifies parallax:
        30 px between adjacent views, ghosting on every hard edge."""
        z = focal_distance_for_range(32.0, 100.0)
        assert view_disparity(landscape, 14.0, z, 32.0) > 25.0


# ---------------------------------------------------------------------------
# Video encoding arguments
# ---------------------------------------------------------------------------


class TestEncodeArgs:
    def test_portrait_uses_h264_yuv420p(self, portrait):
        args = _encode_args(portrait, crf=18)
        assert "libx264" in args
        assert "yuv420p" in args
        assert "-vf" not in args  # 3360 is even, no padding needed

    def test_8k_quilts_use_hevc(self):
        args = _encode_args(QUILT_PRESETS["65"], crf=18)
        assert "libx265" in args

    def test_odd_sizes_padded(self):
        # yuv420p needs even dimensions.  Built explicitly rather than taken
        # from QUILT_PRESETS: preset sizes track real hardware and change
        # when a device's spec is corrected, which is not what this asserts.
        odd = QuiltSpec(columns=7, rows=7, quilt_width=5999, quilt_height=5999, aspect=1.777)
        args = _encode_args(odd, crf=18)
        assert "-vf" in args
        assert "pad=" in args[args.index("-vf") + 1]


# ---------------------------------------------------------------------------
# Camera sweep
# ---------------------------------------------------------------------------


class TestViewOffsets:
    def test_count_and_order(self, portrait):
        offs = view_offsets(portrait, distance=10.0)
        assert offs.shape == (48,)
        assert np.all(np.diff(offs) > 0)  # strictly left -> right

    def test_symmetric_about_centre(self, portrait):
        offs = view_offsets(portrait, distance=10.0)
        np.testing.assert_allclose(offs, -offs[::-1], atol=1e-12)

    def test_cone_extent(self, portrait):
        # Extreme views sit at +/- half the view cone.
        offs = view_offsets(portrait, distance=10.0)
        expected = 10.0 * math.tan(math.radians(portrait.view_cone) / 2.0)
        assert offs[-1] == pytest.approx(expected)
        assert offs[0] == pytest.approx(-expected)

    def test_default_cone_is_35_degrees(self, portrait):
        assert portrait.view_cone == 35.0

    def test_single_view(self):
        spec = QuiltSpec(columns=1, rows=1, quilt_width=64, quilt_height=64, aspect=1.0)
        np.testing.assert_array_equal(view_offsets(spec, 5.0), [0.0])

    def test_scales_with_distance(self, portrait):
        np.testing.assert_allclose(view_offsets(portrait, 20.0), 2.0 * view_offsets(portrait, 10.0))


# ---------------------------------------------------------------------------
# Depth budget
# ---------------------------------------------------------------------------


class TestViewDisparity:
    def test_zero_at_focal_plane(self, portrait):
        assert view_disparity(portrait, fov=14.0, focal_distance=10.0, depth=10.0) == 0.0

    def test_matches_ray_traced_measurement(self):
        """Anchor the formula to real renders.

        A POV-Ray scene with markers at depths 6 and 14, focal plane at 10,
        30 deg FOV, eye offsets of +/-2 on a 256 px image measured shifts of
        128.16 px and 54.43 px between the extreme views.  A 2-view spec
        makes the adjacent-view gap the extreme gap.
        """
        cone = 2.0 * math.degrees(math.atan(2.0 / 10.0))  # offsets +/-2 at distance 10
        spec = QuiltSpec(
            columns=2, rows=1, quilt_width=512, quilt_height=256, aspect=1.0, view_cone=cone
        )
        near = view_disparity(spec, fov=30.0, focal_distance=10.0, depth=6.0)
        far = view_disparity(spec, fov=30.0, focal_distance=10.0, depth=14.0)
        assert near == pytest.approx(128.16, rel=0.02)
        assert far == pytest.approx(54.43, rel=0.02)

    def test_narrower_fov_increases_disparity(self, portrait):
        """Counterintuitive but load-bearing: narrowing the FOV magnifies the
        scene, and the parallax with it."""
        wide = view_disparity(portrait, fov=50.0, focal_distance=50.0, depth=25.0)
        narrow = view_disparity(portrait, fov=14.0, focal_distance=50.0, depth=25.0)
        assert narrow > wide

    def test_infinite_depth_saturates(self, portrait):
        far = view_disparity(portrait, fov=30.0, focal_distance=40.0, depth=1e12)
        inf = view_disparity(portrait, fov=30.0, focal_distance=40.0, depth=math.inf)
        assert inf == pytest.approx(far, rel=1e-6)

    def test_symmetric_about_harmonic_focal_plane(self):
        """The pairing with focal_distance_for_range: near and far content
        must end up with equal disparity."""
        spec = QUILT_PRESETS["16-landscape"]
        z = focal_distance_for_range(32.0, 100.0)
        assert view_disparity(spec, 53.13, z, 32.0) == pytest.approx(
            view_disparity(spec, 53.13, z, 100.0)
        )

    def test_single_view_has_no_disparity(self):
        spec = QuiltSpec(columns=1, rows=1, quilt_width=64, quilt_height=64, aspect=1.0)
        assert view_disparity(spec, fov=14.0, focal_distance=10.0, depth=1.0) == 0.0


class TestFocalDistanceForRange:
    def test_harmonic_mean(self):
        assert focal_distance_for_range(32.0, 100.0) == pytest.approx(2 / (1 / 32 + 1 / 100))

    def test_infinite_far_is_twice_near(self):
        assert focal_distance_for_range(25.0, math.inf) == pytest.approx(50.0)

    def test_degenerate_range_is_identity(self):
        assert focal_distance_for_range(7.0, 7.0) == pytest.approx(7.0)

    def test_lies_between_near_and_far(self):
        z = focal_distance_for_range(32.0, 100.0)
        assert 32.0 < z < 100.0
        # Harmonic mean sits below the arithmetic midpoint: near content is
        # the harder side of the budget, so the plane leans toward it.
        assert z < (32.0 + 100.0) / 2

    def test_rejects_invalid_range(self):
        with pytest.raises(ValueError, match="positive"):
            focal_distance_for_range(0.0, 10.0)
        with pytest.raises(ValueError, match="must be >="):
            focal_distance_for_range(10.0, 5.0)


# ---------------------------------------------------------------------------
# Quilt assembly + I/O
# ---------------------------------------------------------------------------


class TestAssembleQuilt:
    def test_places_views_in_quilt_order(self, tiny_spec):
        views = [np.full((64, 64, 3), i * 10, dtype=np.uint8) for i in range(4)]
        quilt = assemble_quilt(views, tiny_spec)
        for i in range(4):
            x, y = tiny_spec.tile_origin(i)
            assert quilt[y + 32, x + 32, 0] == i * 10

    def test_resamples_mismatched_views(self, tiny_spec):
        pytest.importorskip("PIL")
        views = [np.full((32, 48, 3), 7, dtype=np.uint8) for _ in range(4)]
        quilt = assemble_quilt(views, tiny_spec)
        assert quilt.shape == (128, 128, 3)
        assert quilt[32, 32, 0] == 7

    def test_drops_alpha_channel(self, tiny_spec):
        views = [np.full((64, 64, 4), 9, dtype=np.uint8) for _ in range(4)]
        assert assemble_quilt(views, tiny_spec).shape == (128, 128, 3)

    def test_too_few_views_rejected(self, tiny_spec):
        views = [np.zeros((64, 64, 3), np.uint8) for _ in range(3)]
        with pytest.raises(ValueError, match="expected 4 views"):
            assemble_quilt(views, tiny_spec)

    def test_too_many_views_rejected(self, tiny_spec):
        views = [np.zeros((64, 64, 3), np.uint8) for _ in range(5)]
        with pytest.raises(ValueError, match="more than 4 views"):
            assemble_quilt(views, tiny_spec)


class TestSaveQuilt:
    def test_writes_convention_filename(self, tmp_path, tiny_spec):
        pytest.importorskip("PIL")
        quilt = np.zeros((128, 128, 3), dtype=np.uint8)
        out = save_quilt(quilt, tmp_path / "scene", tiny_spec)
        assert out.name == "scene_qs2x2a1.png"
        assert out.exists()

    def test_strips_png_extension(self, tmp_path, tiny_spec):
        pytest.importorskip("PIL")
        quilt = np.zeros((128, 128, 3), dtype=np.uint8)
        out = save_quilt(quilt, tmp_path / "scene.png", tiny_spec)
        assert out.name == "scene_qs2x2a1.png"

    def test_roundtrip_pixels(self, tmp_path, tiny_spec):
        Image = pytest.importorskip("PIL.Image")
        rng = np.random.default_rng(0)
        quilt = rng.integers(0, 255, size=(128, 128, 3), dtype=np.uint8)
        out = save_quilt(quilt, tmp_path / "rt", tiny_spec)
        back = np.asarray(Image.open(out))
        np.testing.assert_array_equal(back[..., :3], quilt)


# ---------------------------------------------------------------------------
# Off-axis rendering (requires pyvista + a working render window)
# ---------------------------------------------------------------------------


requires_render = pytest.mark.skipif(
    not can_render(), reason="pyvista off-screen rendering unavailable"
)


@requires_render
class TestRenderQuilt:
    def test_shape_and_views_differ(self, tiny_spec):
        import pyvista as pv

        from quiltwright.lfd import render_quilt

        p = pv.Plotter(off_screen=True)
        p.add_mesh(pv.Cube(), color="red")
        p.add_mesh(pv.Sphere(center=(0, 0, 1.2), radius=0.3), color="blue")
        quilt = render_quilt(p, tiny_spec)
        p.close()

        assert quilt.shape == (128, 128, 3)
        assert quilt.dtype == np.uint8
        # Parallax: leftmost and rightmost views must differ.
        x0, y0 = tiny_spec.tile_origin(0)
        x3, y3 = tiny_spec.tile_origin(3)
        v0 = quilt[y0 : y0 + 64, x0 : x0 + 64]
        v3 = quilt[y3 : y3 + 64, x3 : x3 + 64]
        assert not np.array_equal(v0, v3)

    def test_focal_point_stays_centred(self, tiny_spec):
        """Off-axis shear must pin the focal plane: an object at the focal
        point should occupy the centre pixel of *every* view."""
        import pyvista as pv

        from quiltwright.lfd import render_quilt

        p = pv.Plotter(off_screen=True)
        p.add_mesh(pv.Sphere(radius=0.2), color="white")
        p.set_background("black")
        p.camera_position = [(0, -10, 0), (0, 0, 0), (0, 0, 1)]
        quilt = render_quilt(p, tiny_spec, view_cone=35.0)
        p.close()

        th, tw = tiny_spec.tile_height, tiny_spec.tile_width
        for i in range(tiny_spec.n_views):
            x, y = tiny_spec.tile_origin(i)
            centre = quilt[y + th // 2, x + tw // 2]
            assert centre.sum() > 300, f"view {i}: focal object missing at centre {centre}"

    def test_camera_restored_after_render(self, tiny_spec):
        import pyvista as pv

        from quiltwright.lfd import render_quilt

        p = pv.Plotter(off_screen=True)
        p.add_mesh(pv.Sphere())
        p.camera_position = [(0, -8, 0), (0, 0, 0), (0, 0, 1)]
        render_quilt(p, tiny_spec, fov=None)
        pos = np.asarray(p.camera.position)
        p.close()
        np.testing.assert_allclose(pos, [0, -8, 0], atol=1e-6)
        # WindowCenter reset so subsequent screenshots are on-axis.


def _have_ffmpeg() -> bool:
    try:
        from quiltwright.lfd import find_ffmpeg

        find_ffmpeg()
        return True
    except RuntimeError:
        return False


@requires_render
@pytest.mark.skipif(not _have_ffmpeg(), reason="ffmpeg unavailable")
class TestRenderQuiltVideo:
    def test_turntable_mp4(self, tmp_path, tiny_spec):
        import pyvista as pv

        from quiltwright.lfd import render_quilt_video

        p = pv.Plotter(off_screen=True)
        p.add_mesh(pv.Cube(), color="red")
        out = render_quilt_video(
            p,
            tiny_spec,
            tmp_path / "spin",
            n_frames=4,
            fps=4,
            progress=False,
        )
        p.close()
        assert out.name == "spin_qs2x2a1.mp4"
        assert out.stat().st_size > 0

    def test_on_frame_callback_runs(self, tmp_path, tiny_spec):
        import pyvista as pv

        from quiltwright.lfd import render_quilt_video

        seen = []
        p = pv.Plotter(off_screen=True)
        p.add_mesh(pv.Sphere())
        render_quilt_video(
            p,
            tiny_spec,
            tmp_path / "cb",
            n_frames=3,
            fps=3,
            orbit_degrees=0.0,
            on_frame=seen.append,
            progress=False,
        )
        p.close()
        assert seen == [0, 1, 2]
