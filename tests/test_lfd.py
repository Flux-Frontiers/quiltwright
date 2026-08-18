"""Tests for the Looking Glass quilt renderer (quiltwright.lfd)."""

import json
import math
import sys
import types
import urllib.request
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from render_probe import can_render

from quiltwright.lfd import (
    DEPTH_LABELS,
    LITIHOLO_SWEEP,
    QUILT_PRESETS,
    QuiltSpec,
    _encode_args,
    assemble_quilt,
    cast_quilt,
    depth_report,
    find_ffmpeg,
    focal_distance_for_range,
    pause_quilt,
    resume_quilt,
    save_and_cast_quilt,
    save_quilt,
    scene_depths,
    stop_quilt,
    sweep_spec,
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
# View sweeps
# ---------------------------------------------------------------------------


class TestSweepSpec:
    def test_prime_view_count(self):
        """A rectangular grid cannot express 23 views; a single row can."""
        assert sweep_spec(23, 45.0, 1600, 2000).n_views == 23

    def test_tile_size_preserved(self):
        spec = sweep_spec(23, 45.0, 1600, 2000)
        assert (spec.tile_width, spec.tile_height) == (1600, 2000)
        assert spec.aspect == pytest.approx(0.8)

    def test_carries_view_cone(self):
        assert sweep_spec(23, 45.0, 160, 200).view_cone == 45.0

    def test_rejects_degenerate_sweep(self):
        with pytest.raises(ValueError, match="at least 2 views"):
            sweep_spec(1, 45.0, 160, 200)

    def test_litiholo_matches_published_spec(self):
        """23 viewzone images per hogel across a 45-degree lateral field."""
        assert LITIHOLO_SWEEP.n_views == 23
        assert LITIHOLO_SWEEP.view_cone == 45.0

    def test_sweep_offsets_symmetric_about_centre(self):
        """An odd view count puts one camera exactly on axis."""
        offsets = view_offsets(LITIHOLO_SWEEP, 38.64)
        assert len(offsets) == 23
        assert offsets[11] == pytest.approx(0.0)
        assert offsets[0] == pytest.approx(-offsets[-1])
        # Monotonic left to right, so view 0 is leftmost.
        assert np.all(np.diff(offsets) > 0)


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

    def test_scaled_keeps_the_view_grid(self, portrait):
        half = portrait.scaled(0.5)
        assert (half.columns, half.rows) == (portrait.columns, portrait.rows)
        assert half.n_views == portrait.n_views
        assert half.aspect == portrait.aspect

    def test_scaled_stays_on_the_tile_grid(self):
        """The reason this is a method: naive scaling smears every view."""
        for name, spec in QUILT_PRESETS.items():
            for factor in (0.75, 0.5, 0.33):
                small = spec.scaled(factor)
                assert small.quilt_width % small.columns == 0, (name, factor)
                assert small.quilt_height % small.rows == 0, (name, factor)

    def test_scaled_rounds_down_never_up(self, portrait):
        small = portrait.scaled(0.5)
        assert small.quilt_width <= portrait.quilt_width * 0.5
        assert small.quilt_height <= portrait.quilt_height * 0.5

    def test_scaled_by_one_is_a_noop_on_even_grids(self, portrait):
        assert portrait.scaled(1.0) == portrait

    def test_scaled_rejects_a_nonpositive_factor(self, portrait):
        with pytest.raises(ValueError, match="must be positive"):
            portrait.scaled(0)

    def test_scaled_rejects_collapsing_the_tiles(self, portrait):
        with pytest.raises(ValueError, match="too small"):
            portrait.scaled(0.0001)


# ---------------------------------------------------------------------------
# Gen3 16" Landscape -- the device these renders target
# ---------------------------------------------------------------------------


class TestSixteenLandscape:
    """The 16" Landscape preset, end to end.

    This is the display the museum quilts are actually rendered for, and it
    is the awkward one: its tiles are stored *anamorphically*, so the pixel
    aspect of a tile is not the aspect of the view it holds.  Almost every
    property below looks like a typo until that is understood, which is
    precisely why they are pinned here -- "correcting" the preset to make the
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
        """Wider than the 35 deg QuiltSpec default -- the device's own optics,
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

        Run at 1/10 scale -- same aspects and squeeze factor, 1% of the
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

        Anchors the whole chain -- preset, cone, focal plane, tile height -- to
        the depth range measured by scripts/measure_depth_range.py: nearest
        geometry at 31 units, 95% of occludable content within 96, and the
        remaining ~6% of frame sky left out of the balance on purpose
        (docs/povray.md section 4).
        """
        spec = replace(landscape, view_cone=26.42)  # clearance-limited
        z = focal_distance_for_range(31.0, 96.0)
        assert z == pytest.approx(46.87, abs=0.01)
        assert view_disparity(spec, 53.13, z, 31.0) == pytest.approx(3.68, abs=0.01)
        assert view_disparity(spec, 53.13, z, 96.0) == pytest.approx(3.68, abs=0.01)
        assert view_disparity(spec, 53.13, z, math.inf) == pytest.approx(7.19, abs=0.01)

    def test_native_cone_costs_the_budget(self, landscape):
        """At the device's full 50 deg cone the same scene doubles its
        disparity, past the ~5 px comfort ceiling -- the trade the museum
        script makes when it narrows the cone for wall clearance."""
        z = focal_distance_for_range(31.0, 96.0)
        assert view_disparity(landscape, 53.13, z, 31.0) == pytest.approx(7.31, abs=0.01)

    def test_object_centric_fov_advice_blows_up_here(self, landscape):
        """The "~14 deg FOV" advice that circulates for Looking Glass content
        is for object-centric scenes.  On an interior it magnifies parallax:
        30 px between adjacent views, ghosting on every hard edge."""
        z = focal_distance_for_range(31.0, 96.0)
        assert view_disparity(landscape, 14.0, z, 31.0) > 25.0


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


# ---------------------------------------------------------------------------
# Looking Glass Bridge transport
#
# Bridge is HTTP, so the whole control layer is testable without hardware by
# standing in for urllib.  These tests exist because the casting layer had no
# coverage at all, and because the v0.13.0 stop_quilt() fix -- avoiding
# delete_playlist, which hangs Bridge 2.6.3 -- was verified only by hand
# against a live device.  A regression there costs a kill -9, so it gets a
# test that pins the endpoint sequence rather than the end state.
# ---------------------------------------------------------------------------


class FakeBridge:
    """Records the Bridge calls a function makes, and answers them.

    Stands in for ``urllib.request.urlopen``.  ``enter_orchestration`` gets
    the token-bearing response Bridge really sends; everything else gets a
    bare success.
    """

    def __init__(self, token: str = "tok-1", orchestration_payload=None):
        self.token = token
        self.calls: list[tuple[str, dict]] = []
        self._orchestration_payload = orchestration_payload

    @property
    def endpoints(self) -> list[str]:
        return [endpoint for endpoint, _ in self.calls]

    def payload_for(self, endpoint: str) -> dict:
        """The payload of the (single) call to ``endpoint``."""
        matches = [p for e, p in self.calls if e == endpoint]
        assert len(matches) == 1, f"expected exactly one {endpoint} call, got {len(matches)}"
        return matches[0]

    def __call__(self, req, timeout=None):
        endpoint = req.full_url.rsplit("/", 1)[-1]
        payload = json.loads(req.data.decode())
        self.calls.append((endpoint, payload))
        assert req.method == "PUT", (
            f"{endpoint} sent {req.method}; Bridge answers POST with an empty "
            "200 body, so the wrong verb fails silently"
        )

        if endpoint == "enter_orchestration":
            body = (
                self._orchestration_payload
                if self._orchestration_payload is not None
                else {"payload": {"value": self.token}}
            )
        else:
            body = {"status": 0}
        return _FakeResponse(json.dumps(body).encode())


class _FakeResponse:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def bridge(monkeypatch) -> FakeBridge:
    fake = FakeBridge()
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    return fake


class TestStopQuilt:
    """v0.13.0 regression guard: delete_playlist hangs Bridge 2.6.3."""

    def test_never_calls_delete_playlist(self, bridge):
        stop_quilt()
        assert "delete_playlist" not in bridge.endpoints, (
            "delete_playlist hung Bridge 2.6.3 twice in testing, each time "
            "requiring kill -9; stop_quilt() must not reintroduce it even "
            "though bridge.js documents it as the way to stop a playlist"
        )

    def test_pauses_then_hides_the_window(self, bridge):
        stop_quilt()
        assert bridge.endpoints == [
            "enter_orchestration",
            "transport_control_pause",
            "show_window",
        ]

    def test_hides_rather_than_shows(self, bridge):
        stop_quilt()
        assert bridge.payload_for("show_window")["show_window"] is False

    def test_returns_the_show_window_response(self, bridge):
        assert stop_quilt() == {"status": 0}


class TestTransportControls:
    def test_pause_uses_transport_control(self, bridge):
        pause_quilt()
        assert bridge.endpoints == ["enter_orchestration", "transport_control_pause"]

    def test_resume_uses_transport_control(self, bridge):
        resume_quilt()
        assert bridge.endpoints == ["enter_orchestration", "transport_control_play"]

    def test_no_guessed_playlist_endpoints(self, bridge):
        """Bridge has no pause_playlist/stop_playlist; both silently 200."""
        pause_quilt()
        resume_quilt()
        stop_quilt()
        assert not {"pause_playlist", "stop_playlist"} & set(bridge.endpoints)

    @pytest.mark.parametrize("fn", [pause_quilt, resume_quilt, stop_quilt])
    def test_every_call_carries_the_token(self, bridge, fn):
        fn()
        for endpoint, payload in bridge.calls:
            if endpoint != "enter_orchestration":
                assert payload["orchestration"] == bridge.token, (
                    f"{endpoint} sent without the orchestration token"
                )


class TestEnterOrchestration:
    def test_rejects_a_missing_token(self, monkeypatch):
        """An empty token means every later call is a silent no-op."""
        monkeypatch.setattr(
            urllib.request, "urlopen", FakeBridge(orchestration_payload={"payload": {}})
        )
        with pytest.raises(RuntimeError, match="no orchestration token"):
            pause_quilt()

    def test_rejects_an_empty_response(self, monkeypatch):
        monkeypatch.setattr(urllib.request, "urlopen", FakeBridge(orchestration_payload={}))
        with pytest.raises(RuntimeError, match="no orchestration token"):
            stop_quilt()

    def test_session_name_is_default(self, bridge):
        pause_quilt()
        assert bridge.payload_for("enter_orchestration")["name"] == "default"


class TestCastQuilt:
    def test_orchestration_sequence(self, bridge, tmp_path, tiny_spec):
        quilt = tmp_path / "q.png"
        quilt.touch()
        cast_quilt(quilt, tiny_spec)
        assert bridge.endpoints == [
            "enter_orchestration",
            "show_window",
            "instance_playlist",
            "insert_playlist_entry",
            "play_playlist",
        ]

    def test_entry_describes_the_spec(self, bridge, tmp_path, tiny_spec):
        quilt = tmp_path / "q.png"
        quilt.touch()
        cast_quilt(quilt, tiny_spec)
        entry = bridge.payload_for("insert_playlist_entry")
        assert (entry["rows"], entry["cols"]) == (tiny_spec.rows, tiny_spec.columns)
        assert entry["aspect"] == pytest.approx(tiny_spec.aspect)
        assert entry["view_count"] == tiny_spec.n_views

    def test_uri_is_absolute(self, bridge, tmp_path, tiny_spec, monkeypatch):
        """Bridge resolves the path on its own host, so relative breaks it."""
        quilt = tmp_path / "q.png"
        quilt.touch()
        monkeypatch.chdir(tmp_path)
        cast_quilt("q.png", tiny_spec)
        assert Path(bridge.payload_for("insert_playlist_entry")["uri"]).is_absolute()

    def test_playlist_name_is_used(self, bridge, tmp_path, tiny_spec):
        quilt = tmp_path / "q.png"
        quilt.touch()
        cast_quilt(quilt, tiny_spec, playlist="custom")
        assert bridge.payload_for("instance_playlist")["name"] == "custom"
        assert bridge.payload_for("play_playlist")["name"] == "custom"

    def test_shows_the_window(self, bridge, tmp_path, tiny_spec):
        quilt = tmp_path / "q.png"
        quilt.touch()
        cast_quilt(quilt, tiny_spec)
        assert bridge.payload_for("show_window")["show_window"] is True


class TestSaveAndCastQuilt:
    """The whole point is that a lost display never costs the render."""

    def test_writes_then_casts_the_path(self, bridge, tmp_path, tiny_spec):
        pytest.importorskip("PIL")
        quilt = np.zeros((128, 128, 3), dtype=np.uint8)
        out, error = save_and_cast_quilt(quilt, tmp_path / "scene", tiny_spec)
        assert error is None
        assert out.exists()
        # The caster got a path on disk, not the array it was rendered from.
        assert Path(bridge.payload_for("insert_playlist_entry")["uri"]) == out.resolve()

    def test_cast_false_never_contacts_bridge(self, bridge, tmp_path, tiny_spec):
        pytest.importorskip("PIL")
        quilt = np.zeros((128, 128, 3), dtype=np.uint8)
        out, error = save_and_cast_quilt(quilt, tmp_path / "scene", tiny_spec, cast=False)
        assert (error, bridge.endpoints) == (None, [])
        assert out.exists()

    def test_a_failed_cast_returns_the_error_and_keeps_the_file(
        self, tmp_path, tiny_spec, monkeypatch
    ):
        pytest.importorskip("PIL")

        def boom(*_args, **_kwargs):
            raise ConnectionRefusedError("Bridge is not running")

        monkeypatch.setattr(urllib.request, "urlopen", boom)
        quilt = np.zeros((128, 128, 3), dtype=np.uint8)
        out, error = save_and_cast_quilt(quilt, tmp_path / "scene", tiny_spec)
        assert error is not None and "Bridge is not running" in error
        assert out.exists(), "the render must survive a display that does not"

    def test_returns_the_convention_filename(self, bridge, tmp_path, tiny_spec):
        pytest.importorskip("PIL")
        quilt = np.zeros((128, 128, 3), dtype=np.uint8)
        out, _ = save_and_cast_quilt(quilt, tmp_path / "scene", tiny_spec)
        assert out.name == "scene_qs2x2a1.png"


class TestFindFfmpeg:
    def test_prefers_the_system_binary(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: "/usr/bin/ffmpeg")
        assert find_ffmpeg() == "/usr/bin/ffmpeg"

    def test_falls_back_to_imageio(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: None)
        module = types.ModuleType("imageio_ffmpeg")
        module.get_ffmpeg_exe = lambda: "/bundled/ffmpeg"
        monkeypatch.setitem(sys.modules, "imageio_ffmpeg", module)
        assert find_ffmpeg() == "/bundled/ffmpeg"

    def test_raises_when_neither_is_available(self, monkeypatch):
        monkeypatch.setattr("shutil.which", lambda _: None)
        monkeypatch.setitem(sys.modules, "imageio_ffmpeg", None)
        with pytest.raises(RuntimeError, match="requires ffmpeg"):
            find_ffmpeg()


# ---------------------------------------------------------------------------
# Depth reporting for PyVista scenes
# ---------------------------------------------------------------------------


class _StubCamera:
    """The four camera attributes ``scene_depths`` reads, and nothing else."""

    def __init__(self, position, focal_point, up, view_angle):
        self.position = position
        self.focal_point = focal_point
        self.up = up
        self.view_angle = view_angle


class _StubPlotter:
    """A plotter's measurable surface: a camera and a bounding box.

    Using a stub rather than a real ``pv.Plotter`` keeps these tests on the
    framing arithmetic, which is the part that was wrong in two downstream
    copies, and lets them run without a GL stack.
    """

    def __init__(self, camera, bounds):
        self.camera = camera
        self.bounds = bounds


def _stub(view_angle=30.0, distance=10.0):
    """Camera on -Y looking at the origin, with a unit cube at the focal plane.

    :param view_angle: Vertical FOV in degrees.
    :param distance: Distance from camera to focal point.
    :return: A ``_StubPlotter``.
    """
    camera = _StubCamera(
        position=(0.0, -distance, 0.0),
        focal_point=(0.0, 0.0, 0.0),
        up=(0.0, 0.0, 1.0),
        view_angle=view_angle,
    )
    return _StubPlotter(camera, (-1.0, 1.0, -1.0, 1.0, -1.0, 1.0))


class TestSceneDepths:
    def test_measures_the_scene_along_the_view_axis(self):
        """With no reframing, near/far are the bounding box projected on the axis."""
        depths = scene_depths(_stub(distance=10.0), fov=None)
        near, focal, far = (depths[label] for label in DEPTH_LABELS)

        assert focal == pytest.approx(10.0)
        assert near == pytest.approx(9.0)  # front face of the unit cube
        assert far == pytest.approx(11.0)  # back face

    def test_fov_narrowing_dollies_back(self):
        """Narrowing the FOV pushes the camera back, exactly as render_quilt does.

        new_distance = (distance * tan(view/2)) / tan(fov/2)
        """
        depths = scene_depths(_stub(view_angle=30.0, distance=10.0), fov=14.0)
        expected = 10.0 * math.tan(math.radians(15.0)) / math.tan(math.radians(7.0))

        assert depths[DEPTH_LABELS[1]] == pytest.approx(expected)
        assert expected > 10.0, "a narrower FOV must retreat, not advance"

    def test_reframing_shifts_every_depth_equally(self):
        """The camera moves, the scene does not: depth *spread* is invariant."""
        plain = scene_depths(_stub(), fov=None)
        framed = scene_depths(_stub(), fov=14.0)

        spread = lambda d: d[DEPTH_LABELS[2]] - d[DEPTH_LABELS[0]]  # noqa: E731
        assert spread(framed) == pytest.approx(spread(plain))
        shift = framed[DEPTH_LABELS[1]] - plain[DEPTH_LABELS[1]]
        assert framed[DEPTH_LABELS[0]] - plain[DEPTH_LABELS[0]] == pytest.approx(shift)

    def test_zoom_divides_the_distance(self):
        """VTK's Dolly divides the camera distance, so the focal plane closes in."""
        no_zoom = scene_depths(_stub(), fov=14.0)
        zoomed = scene_depths(_stub(), fov=14.0, zoom=2.0)

        assert zoomed[DEPTH_LABELS[1]] == pytest.approx(no_zoom[DEPTH_LABELS[1]] / 2.0)

    def test_zoom_of_one_changes_nothing(self):
        assert scene_depths(_stub(), zoom=1.0) == scene_depths(_stub(), zoom=None)

    def test_custom_labels_are_used(self):
        labels = ("front of subject", "glass", "back of subject")
        assert set(scene_depths(_stub(), labels=labels)) == set(labels)

    def test_nothing_is_mutated(self):
        """The report must not disturb a camera the caller is about to render with."""
        plotter = _stub()
        before = (plotter.camera.position, plotter.camera.view_angle)
        scene_depths(plotter, fov=14.0, zoom=1.5)

        assert (plotter.camera.position, plotter.camera.view_angle) == before


class TestDepthReport:
    def test_reports_every_depth_including_extras(self):
        report = depth_report(_stub(), QUILT_PRESETS["portrait"], extra_depths={"sky": math.inf})

        for label in DEPTH_LABELS:
            assert label in report
        assert "sky" in report

    def test_the_focal_plane_has_no_disparity(self):
        """Content on the display surface is the fixed point of the sweep."""
        report = depth_report(_stub(), QUILT_PRESETS["portrait"])
        focal_line = next(ln for ln in report.splitlines() if DEPTH_LABELS[1] in ln)

        assert "0.00" in focal_line

    def test_it_answers_for_the_render_not_the_current_camera(self):
        """Reporting the un-reframed camera describes a picture nobody will make.

        render_quilt narrows the FOV and dollies back before sweeping, so a
        budget taken from the plotter as-is is computed at the wrong FOV and
        the wrong focal distance. This is the bug the function exists to stop
        each caller from reproducing.
        """
        spec = QUILT_PRESETS["portrait"]
        as_rendered = depth_report(_stub(view_angle=30.0), spec, fov=14.0)
        as_composed = depth_report(_stub(view_angle=30.0), spec, fov=None)

        assert as_rendered != as_composed
