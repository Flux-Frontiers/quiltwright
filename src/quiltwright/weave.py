"""
Weaving quilts into native pre-lensed frames on the CPU.

A Looking Glass panel is a passive lenticular optic over an ordinary LCD:
it does not care *who* put the pixels behind it.  Bridge normally runs the
"lenticular" shader on the GPU every frame, interleaving quilt views per
subpixel according to the device's factory calibration.  This module runs
the same shader once, in NumPy, and writes the result out as an ordinary
image at the panel's exact native resolution.

Displayed 1:1 on the panel — most usefully as the macOS desktop wallpaper
of the Looking Glass display — that image reconstructs as a static hologram
with full parallax, no Bridge process required.

The math is a port of Bridge's ``Lenticular_RGBA_With_Aspect`` shader (via
the Unity plugin's HLSL conversion) together with LKG-Toolkit's
``Calibration.ProcessPitch`` / ``ProcessSlope``.  It implements both
calibration generations:

* classic (Portrait-era): flat one-third-pixel RGB stride, and
* gen3 (configVersion 3.0): explicit per-channel ``subpixelCells`` offsets,
  selected per pixel by ``CellPatternMode``.  These panels put R and G on
  one row and B on the other — a 2-over-1 delta, ordered R, B, G left to
  right — mirrored vertically on alternate columns.  The classic formula
  assumes all three emitters share a row at a flat third-pixel stride, so
  it gets this path badly wrong rather than slightly: on LKG-J00332 every
  pixel picks a different view, by up to 47 of 48.

Two things break the effect completely and neither is detectable from code:
the panel must run at its **true native resolution** (no HiDPI scaling — one
resample destroys the subpixel registration), and nothing may mix the RGB
channels after weaving (Night Shift, True Tone, matrix ICC profiles), since
each channel of each pixel carries a *different view*.

Typical usage::

    from quiltwright import QUILT_PRESETS, Calibration, weave_quilt
    from PIL import Image
    import numpy as np

    cal = Calibration.load("visual.json")   # from the device / Bridge
    spec = QUILT_PRESETS["16-landscape"]
    quilt = np.asarray(Image.open("scene_qs8x6a1.77778.png").convert("RGB"))
    native = weave_quilt(quilt, spec, cal)
    Image.fromarray(native).save("scene_native.png")

Part of Quiltwright — https://github.com/suchanek/quiltwright
Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from quiltwright.lfd import QuiltSpec

__all__ = ["Calibration", "SubpixelCell", "weave_quilt"]


@dataclass(frozen=True)
class SubpixelCell:
    """Physical offsets of one pixel's R, G and B emitters, in pixel units.

    Gen3 panels do not lay their subpixels out in the classic vertical
    R|G|B stripe: R and G sit on one row with B alone on the other, and the
    arrangement mirrors vertically between neighbouring pixel columns.  Each
    cell describes one variant; ``CellPatternMode`` decides which cell a
    given screen pixel uses.
    """

    r_offset_x: float
    r_offset_y: float
    g_offset_x: float
    g_offset_y: float
    b_offset_x: float
    b_offset_y: float


@dataclass(frozen=True)
class Calibration:
    """Per-unit optical calibration of a Looking Glass panel.

    Every panel is calibrated at the factory — lens pitch, slant and phase
    differ unit to unit, which is why a woven frame is registered to one
    specific display.  The values live in the device's ``visual.json``
    (readable via Looking Glass Bridge); :meth:`load` accepts that file
    directly, ``{"value": ...}`` wrappers and all.

    :param pitch: Raw lens pitch in lenticules per inch.
    :param slope: Raw lens slant (run over rise, sign carries direction).
    :param center: Phase offset of the lens array, in view-cycle units.
    :param dpi: Panel pixel density.
    :param screen_w: Native panel width in pixels.
    :param screen_h: Native panel height in pixels.
    :param flip_x: ``flipImageX`` — mirrors the tilt when >= 0.5.
    :param cell_pattern_mode: Subpixel-cell selection pattern (0-4).
    :param cells: Per-cell subpixel offsets; empty means the classic
        one-third-pixel RGB stripe layout.
    :param serial: Device serial, kept for provenance in filenames/logs.
    """

    pitch: float
    slope: float
    center: float
    dpi: float
    screen_w: int
    screen_h: int
    flip_x: float = 0.0
    cell_pattern_mode: int = 0
    cells: tuple[SubpixelCell, ...] = field(default_factory=tuple)
    serial: str = ""

    @classmethod
    def from_dict(cls, raw: dict) -> Calibration:
        """Build a :class:`Calibration` from decoded ``visual.json`` data.

        :param raw: Parsed JSON dict, with or without ``{"value": x}``
            wrappers around the numeric fields.
        :return: The calibration.
        """

        def get(key: str, default=0.0):
            val = raw.get(key, default)
            return val["value"] if isinstance(val, dict) and "value" in val else val

        cells = tuple(
            SubpixelCell(
                r_offset_x=c["ROffsetX"],
                r_offset_y=c["ROffsetY"],
                g_offset_x=c["GOffsetX"],
                g_offset_y=c["GOffsetY"],
                b_offset_x=c["BOffsetX"],
                b_offset_y=c["BOffsetY"],
            )
            for c in raw.get("subpixelCells") or ()
        )
        return cls(
            pitch=get("pitch"),
            slope=get("slope"),
            center=get("center"),
            dpi=get("DPI"),
            screen_w=int(get("screenW")),
            screen_h=int(get("screenH")),
            flip_x=get("flipImageX"),
            cell_pattern_mode=int(get("CellPatternMode")),
            cells=cells,
            serial=raw.get("serial", ""),
        )

    @classmethod
    def load(cls, path: str | Path) -> Calibration:
        """Load a device ``visual.json`` calibration file.

        :param path: Path to the JSON file.
        :return: The calibration.
        """
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))

    @property
    def processed_pitch(self) -> float:
        """Shader-space pitch: view cycles across the panel width.

        LKG-Toolkit's ``Calibration.ProcessPitch`` — the raw lenticules-
        per-inch scaled to screen widths and foreshortened by the lens
        slant.
        """
        return self.pitch * self.screen_w / self.dpi * math.cos(math.atan(1.0 / self.slope))

    @property
    def processed_slope(self) -> float:
        """Shader-space tilt: view-phase change per unit of screen height.

        LKG-Toolkit's ``Calibration.ProcessSlope``, including the
        ``flipImageX`` sign convention.
        """
        tilt = self.screen_h / (self.screen_w * self.slope)
        return -tilt if self.flip_x >= 0.5 else tilt


def _cell_for_pixel(xpix: np.ndarray, ypix: np.ndarray, pattern: int) -> np.ndarray:
    """Which subpixel cell each screen pixel uses (Bridge ``getCellForPixel``).

    :param xpix: x pixel indices (broadcastable).
    :param ypix: y pixel indices, *bottom-up* GL convention (broadcastable).
    :param pattern: ``CellPatternMode`` from the calibration.
    :return: Integer cell indices, broadcast over the inputs.
    :raises ValueError: On an unknown pattern.
    """
    if pattern == 0:
        return np.zeros(np.broadcast(xpix, ypix).shape, dtype=np.int8)
    if pattern == 1:  # checkerboard AB / BA
        return ((xpix % 2) ^ (ypix % 2)).astype(np.int8)
    if pattern == 2:  # column parity
        return (xpix % 2).astype(np.int8)
    if pattern == 3:
        return ((ypix + (xpix % 2) * 2) % 4).astype(np.int8)
    if pattern == 4:  # row parity
        return (ypix % 2).astype(np.int8)
    raise ValueError(f"unknown CellPatternMode {pattern}")


def weave_quilt(
    quilt: np.ndarray,
    spec: QuiltSpec,
    cal: Calibration,
    *,
    invert: bool = False,
) -> np.ndarray:
    """Interleave a quilt into a native pre-lensed frame for one panel.

    CPU port of Bridge's lenticular shader at its nearest-view setting
    (``filterMode 0``).  For every subpixel of the native frame the shader
    phase ``(x + dx + (y + dy) * tilt) * pitch - center`` selects which
    quilt view that subpixel physically radiates toward, and the value is
    copied from that view.  Nearest-neighbour everywhere: when the quilt
    tile size is an integer multiple of the panel resolution (all official
    presets are) sampling is exact, and no filtering ever mixes channels —
    each channel of each output pixel carries a different view, so any
    cross-channel blur is view crosstalk.

    :param quilt: Quilt image ``(H, W, 3)``, top-down row order, view 0 at
        the bottom-left tile (the standard quilt convention).
    :param spec: Quilt tiling (``columns``/``rows`` are used; the pixel
        dimensions are taken from the array itself).
    :param cal: The target panel's :class:`Calibration`.
    :param invert: Reverse the view order.  If the parallax fuses but reads
        inside-out (relief inverted, look-around backwards), the quilt's
        view sweep runs opposite to the panel's convention; this flips it.
    :return: Native frame ``(screen_h, screen_w, 3)`` of the quilt's dtype,
        top-down row order, ready to save and display 1:1.
    :raises ValueError: If the quilt does not divide evenly into the spec's
        tile grid.
    """
    q = np.asarray(quilt)
    if q.ndim != 3 or q.shape[2] < 3:
        raise ValueError(f"quilt must be (H, W, 3) RGB, got shape {q.shape}")
    q_h, q_w = q.shape[:2]
    if q_w % spec.columns or q_h % spec.rows:
        raise ValueError(
            f"{q_w}x{q_h} quilt does not divide into a {spec.columns}x{spec.rows} grid"
        )
    tile_w, tile_h = q_w // spec.columns, q_h // spec.rows
    tiles = spec.n_views
    screen_w, screen_h = cal.screen_w, cal.screen_h

    pitch = cal.processed_pitch
    tilt = cal.processed_slope
    center = cal.center

    # The shader works in GL coordinates (v = 0 at the *bottom* of both the
    # panel and the quilt texture); flipping the quilt here and the result at
    # the end keeps the port line-for-line comparable with the original.
    q = q[::-1]

    sx = (np.arange(screen_w) + 0.5) / screen_w  # (W,) fragment centres
    ypix = np.arange(screen_h)  # bottom-up pixel rows
    sy = (ypix + 0.5) / screen_h  # (H,)

    # nearest source pixel within a tile (exact for integer-ratio presets)
    qx = np.minimum((sx * tile_w).astype(np.int32), tile_w - 1)  # (W,)
    qy = np.minimum((sy * tile_h).astype(np.int32), tile_h - 1)  # (H,)

    if cal.cells:
        cell = np.broadcast_to(
            _cell_for_pixel(np.arange(screen_w)[None, :], ypix[:, None], cal.cell_pattern_mode),
            (screen_h, screen_w),
        )
        # SubpixelCell.Normalize: raw offsets are in pixels, the shader
        # wants screen-normalized coordinates.
        off_x = np.array([[c.r_offset_x, c.g_offset_x, c.b_offset_x] for c in cal.cells]) / screen_w
        off_y = np.array([[c.r_offset_y, c.g_offset_y, c.b_offset_y] for c in cal.cells]) / screen_h

    subp = 1.0 / (3 * screen_w)  # classic path: flat 1/3-pixel RGB stripe

    out = np.empty((screen_h, screen_w, 3), dtype=q.dtype)
    for ch in range(3):
        if cal.cells:
            phase = (sx[None, :] + off_x[cell, ch]) + (sy[:, None] + off_y[cell, ch]) * tilt
        else:
            phase = (sx[None, :] + ch * subp) + sy[:, None] * tilt
        phase = phase * pitch - center
        view = 1.0 - np.mod(phase, 1.0)
        if invert:
            view = 1.0 - view
        idx = np.clip((view * tiles).astype(np.int32), 0, tiles - 1)
        out[:, :, ch] = q[
            (idx // spec.columns) * tile_h + qy[:, None],
            (idx % spec.columns) * tile_w + qx[None, :],
            ch,
        ]

    return out[::-1]
