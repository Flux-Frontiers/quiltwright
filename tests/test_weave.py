"""Tests for the CPU lenticular weaver (quiltwright.weave)."""

import json
import math

import numpy as np
import pytest

from quiltwright.lfd import QuiltSpec
from quiltwright.weave import Calibration, _cell_for_pixel, weave_quilt

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

#: The visual.json of a real gen3 16" Landscape unit (configVersion 3.0),
#: wrappers and all, exactly as Bridge stores it on-device.
LKG_J00332 = {
    "configVersion": "3.0",
    "serial": "LKG-J00332",
    "pitch": {"value": 44.75058319896644},
    "slope": {"value": -6.874565686767793},
    "center": {"value": 0.16935753461833172},
    "viewCone": {"value": 50.0},
    "DPI": {"value": 283.0},
    "screenW": {"value": 3840.0},
    "screenH": {"value": 2160.0},
    "flipImageX": {"value": 0.0},
    "CellPatternMode": {"value": 2.0},
    "subpixelCells": [
        {
            "ROffsetX": -0.3100000023841858,
            "ROffsetY": 0.25,
            "GOffsetX": 0.2800000011920929,
            "GOffsetY": 0.25,
            "BOffsetX": 0.0,
            "BOffsetY": -0.25,
        },
        {
            "ROffsetX": -0.3100000023841858,
            "ROffsetY": -0.25,
            "GOffsetX": 0.2800000011920929,
            "GOffsetY": -0.25,
            "BOffsetX": 0.0,
            "BOffsetY": 0.25,
        },
    ],
}


@pytest.fixture
def gen3_cal() -> Calibration:
    """Calibration of the real 16" Landscape unit above."""
    return Calibration.from_dict(LKG_J00332)


@pytest.fixture
def tiny_cal() -> Calibration:
    """A small classic-layout panel for fast full-frame tests."""
    return Calibration(
        pitch=8.0,
        slope=-5.0,
        center=0.1,
        dpi=100.0,
        screen_w=96,
        screen_h=54,
        serial="TINY",
    )


@pytest.fixture
def tiny_spec() -> QuiltSpec:
    """A 4x3 = 12-view quilt matching the tiny panel's aspect."""
    return QuiltSpec(columns=4, rows=3, quilt_width=192, quilt_height=108, aspect=1.777)


def view_coded_quilt(spec: QuiltSpec) -> np.ndarray:
    """A quilt whose every pixel encodes its own view index as a gray level.

    Weaving it makes the chosen view index directly readable from the
    output, which turns the whole swizzle into a testable function.
    """
    q = np.zeros((spec.quilt_height, spec.quilt_width, 3), dtype=np.uint8)
    for view in range(spec.n_views):
        x, y = spec.tile_origin(view)
        q[y : y + spec.tile_height, x : x + spec.tile_width] = view
    return q


def reference_views(cal: Calibration, spec: QuiltSpec, xpix: int, ypix_td: int) -> list[int]:
    """Scalar transliteration of the Bridge shader for one output pixel.

    Written independently of the vectorized implementation (plain floats,
    top-down input coordinate) so the two can disagree.

    :param xpix: x pixel index.
    :param ypix_td: y pixel index in *top-down* image order.
    :return: The view index for each of R, G, B.
    """
    y_up = cal.screen_h - 1 - ypix_td  # shader works bottom-up
    u = (xpix + 0.5) / cal.screen_w
    v = (y_up + 0.5) / cal.screen_h
    views = []
    for ch in range(3):
        if cal.cells:
            if cal.cell_pattern_mode == 2:
                cell = cal.cells[xpix % 2]
            elif cal.cell_pattern_mode == 0:
                cell = cal.cells[0]
            else:
                raise NotImplementedError
            dx = [cell.r_offset_x, cell.g_offset_x, cell.b_offset_x][ch] / cal.screen_w
            dy = [cell.r_offset_y, cell.g_offset_y, cell.b_offset_y][ch] / cal.screen_h
            a = (u + dx) + (v + dy) * cal.processed_slope
        else:
            a = (u + ch / (3 * cal.screen_w)) + v * cal.processed_slope
        a = a * cal.processed_pitch - cal.center
        view = 1.0 - (a - math.floor(a))
        views.append(min(int(view * spec.n_views), spec.n_views - 1))
    return views


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------


class TestCalibration:
    def test_flattens_value_wrappers(self, gen3_cal):
        assert gen3_cal.serial == "LKG-J00332"
        assert gen3_cal.screen_w == 3840
        assert gen3_cal.screen_h == 2160
        assert gen3_cal.cell_pattern_mode == 2
        assert len(gen3_cal.cells) == 2

    def test_load_from_file(self, tmp_path, gen3_cal):
        path = tmp_path / "visual.json"
        path.write_text(json.dumps(LKG_J00332), encoding="utf-8")
        assert Calibration.load(path) == gen3_cal

    def test_processed_pitch_matches_lkg_toolkit(self, gen3_cal):
        # Calibration.ProcessPitch: pitch * screenW / dpi * cos(atan(1/slope))
        assert gen3_cal.processed_pitch == pytest.approx(600.892, abs=0.001)

    def test_processed_slope_matches_lkg_toolkit(self, gen3_cal):
        # Calibration.ProcessSlope: screenH / (screenW * slope), no flip
        assert gen3_cal.processed_slope == pytest.approx(-0.0818233, abs=1e-6)

    def test_flip_x_negates_slope(self, gen3_cal):
        from dataclasses import replace

        flipped = replace(gen3_cal, flip_x=1.0)
        assert flipped.processed_slope == pytest.approx(-gen3_cal.processed_slope)


# ---------------------------------------------------------------------------
# Cell patterns
# ---------------------------------------------------------------------------


class TestCellPattern:
    X = np.arange(4)[None, :]
    Y = np.arange(4)[:, None]

    def test_pattern_0_is_all_zero(self):
        assert not _cell_for_pixel(self.X, self.Y, 0).any()

    def test_pattern_1_is_checkerboard(self):
        cells = _cell_for_pixel(self.X, self.Y, 1)
        assert cells[0].tolist() == [0, 1, 0, 1]
        assert cells[1].tolist() == [1, 0, 1, 0]

    def test_pattern_2_is_column_parity(self):
        cells = _cell_for_pixel(self.X, self.Y, 2)
        assert (cells == [0, 1, 0, 1]).all()

    def test_pattern_4_is_row_parity(self):
        cells = _cell_for_pixel(self.X, self.Y, 4)
        assert (cells.T == [0, 1, 0, 1]).all()

    def test_unknown_pattern_raises(self):
        with pytest.raises(ValueError, match="CellPatternMode"):
            _cell_for_pixel(self.X, self.Y, 9)


# ---------------------------------------------------------------------------
# Weaving
# ---------------------------------------------------------------------------


class TestWeaveQuilt:
    def test_output_shape_and_dtype(self, tiny_cal, tiny_spec):
        native = weave_quilt(view_coded_quilt(tiny_spec), tiny_spec, tiny_cal)
        assert native.shape == (54, 96, 3)
        assert native.dtype == np.uint8

    def test_rejects_non_rgb(self, tiny_cal, tiny_spec):
        with pytest.raises(ValueError, match="RGB"):
            weave_quilt(np.zeros((108, 192)), tiny_spec, tiny_cal)

    def test_rejects_indivisible_quilt(self, tiny_cal, tiny_spec):
        with pytest.raises(ValueError, match="divide"):
            weave_quilt(np.zeros((100, 190, 3), dtype=np.uint8), tiny_spec, tiny_cal)

    def test_classic_path_matches_scalar_reference(self, tiny_cal, tiny_spec):
        native = weave_quilt(view_coded_quilt(tiny_spec), tiny_spec, tiny_cal)
        rng = np.random.default_rng(7)
        for _ in range(200):
            x = int(rng.integers(0, tiny_cal.screen_w))
            y = int(rng.integers(0, tiny_cal.screen_h))
            assert native[y, x].tolist() == reference_views(tiny_cal, tiny_spec, x, y)

    def test_gen3_path_matches_scalar_reference(self, gen3_cal):
        # Full-resolution panel, small tiles: keeps the test fast while
        # exercising the real calibration end to end.
        spec = QuiltSpec(columns=8, rows=6, quilt_width=64, quilt_height=48, aspect=1.777)
        native = weave_quilt(view_coded_quilt(spec), spec, gen3_cal)
        rng = np.random.default_rng(7)
        for _ in range(200):
            x = int(rng.integers(0, gen3_cal.screen_w))
            y = int(rng.integers(0, gen3_cal.screen_h))
            assert native[y, x].tolist() == reference_views(gen3_cal, spec, x, y)

    def test_uses_all_views(self, gen3_cal):
        spec = QuiltSpec(columns=8, rows=6, quilt_width=64, quilt_height=48, aspect=1.777)
        native = weave_quilt(view_coded_quilt(spec), spec, gen3_cal)
        assert set(np.unique(native)) == set(range(48))

    def test_invert_reverses_view_order(self, gen3_cal):
        spec = QuiltSpec(columns=8, rows=6, quilt_width=64, quilt_height=48, aspect=1.777)
        forward = weave_quilt(view_coded_quilt(spec), spec, gen3_cal).astype(int)
        backward = weave_quilt(view_coded_quilt(spec), spec, gen3_cal, invert=True).astype(int)
        # view = 1 - view before flooring, so indices reverse modulo the
        # float boundary where both round into the same tile
        assert np.abs((forward + backward) - (spec.n_views - 1)).max() <= 1
        assert (forward != backward).mean() > 0.9

    def test_gen3_channels_differ(self, gen3_cal):
        # The whole point of subpixelCells: R, G and B of one pixel radiate
        # toward different views, so the channels must not be identical.
        spec = QuiltSpec(columns=8, rows=6, quilt_width=64, quilt_height=48, aspect=1.777)
        native = weave_quilt(view_coded_quilt(spec), spec, gen3_cal)
        differs = (native[:, :, 0] != native[:, :, 1]) | (native[:, :, 1] != native[:, :, 2])
        assert differs.mean() > 0.5

    def test_subpixel_cell_offsets_shift_views(self, gen3_cal):
        # Zeroing the cells (classic path) must produce a different weave
        # than the gen3 delta layout -- otherwise the offsets are ignored.
        from dataclasses import replace

        spec = QuiltSpec(columns=8, rows=6, quilt_width=64, quilt_height=48, aspect=1.777)
        quilt = view_coded_quilt(spec)
        gen3 = weave_quilt(quilt, spec, gen3_cal)
        classic = weave_quilt(quilt, spec, replace(gen3_cal, cells=()))
        assert (gen3 != classic).any()
