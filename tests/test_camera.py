"""Algebraic identity of the three off-axis shears.

No renderer required: VTK WindowCenter, Blender shift_x, and the POV-Ray
direction shear are unit conversions of :func:`window_shear`.
"""

from __future__ import annotations

import math
import sys

import numpy as np
import pytest

from quiltwright.cycles import CyclesCamera, view_shift_x
from quiltwright.povray import PovCamera, camera_block
from quiltwright.quilt import QuiltCamera, window_shear


def _parse_vectors(block: str) -> dict[str, np.ndarray]:
    """Pull ``location`` / ``direction`` / ``right`` / ``up`` out of a camera block."""
    out: dict[str, np.ndarray] = {}
    for line in block.splitlines():
        for name in ("location", "direction", "right", "up"):
            if name in line:
                inner = line.split("<", 1)[1].split(">", 1)[0]
                out[name] = np.fromstring(inner, sep=",")
    return out


class TestWindowShear:
    def test_centre_view_is_zero(self):
        assert window_shear(0.0, 10.0, 14.0, 0.75) == 0.0

    def test_antisymmetric(self):
        left = window_shear(-2.4, 48.5, 14.0, 0.5625)
        right = window_shear(2.4, 48.5, 14.0, 0.5625)
        assert left == pytest.approx(-right)

    def test_rightward_eye_shears_left(self):
        assert window_shear(3.0, 10.0, 30.0, 1.0) < 0

    def test_is_the_vtk_window_centre(self):
        """VTK ``SetWindowCenter`` takes this value in half-widths."""
        offset, focal, fov, aspect = 2.4, 48.5, 14.0, 0.5625
        half_width = focal * math.tan(math.radians(fov) / 2.0) * aspect
        assert window_shear(offset, focal, fov, aspect) == pytest.approx(-offset / half_width)


class TestBackendConversions:
    def test_blender_shift_x_is_half(self):
        offset, focal, fov, aspect = 2.4, 48.5, 14.0, 0.5625
        assert view_shift_x(offset, focal, fov, aspect) == pytest.approx(
            window_shear(offset, focal, fov, aspect) / 2.0
        )

    def test_povray_direction_shear_matches(self):
        """POV-Ray slides the image-plane centre by ``shear * aspect / 2``."""
        camera = PovCamera(location=(0.0, 0.0, -10.0), look_at=(0.0, 0.0, 0.0), fov=14.0)
        offset, aspect = 2.0, 0.75
        v = _parse_vectors(camera_block(camera, offset, aspect))
        _, right, _ = camera.basis()
        expected = window_shear(offset, camera.focal_distance, camera.fov, aspect) * aspect / 2.0
        assert float(v["direction"] @ right) == pytest.approx(expected)


class TestQuiltCamera:
    def test_pov_and_cycles_satisfy_the_protocol(self):
        pov = PovCamera(location=(0.0, 0.0, -10.0), look_at=(0.0, 0.0, 0.0), fov=14.0)
        cyc = CyclesCamera(location=(0.0, -10.0, 0.0), look_at=(0.0, 0.0, 0.0), fov=14.0)
        assert isinstance(pov, QuiltCamera)
        assert isinstance(cyc, QuiltCamera)
        assert pov.focal_distance == pytest.approx(10.0)
        assert cyc.focal_distance == pytest.approx(10.0)


def test_importing_window_shear_does_not_load_pyvista() -> None:
    """The identity lives in quilt; the Cycles helper must not drag VTK in."""
    sys.modules.pop("pyvista", None)
    sys.modules.pop("quiltwright.lfd", None)
    from quiltwright.cycles import view_shift_x as vs  # noqa: F401
    from quiltwright.quilt import window_shear as ws  # noqa: F401

    assert "pyvista" not in sys.modules
    assert "quiltwright.lfd" not in sys.modules
