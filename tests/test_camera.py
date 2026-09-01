"""Algebraic identity of the three off-axis shears.

No renderer required: VTK WindowCenter, Blender shift_x, and the POV-Ray
direction shear are unit conversions of :func:`window_shear`.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass

import numpy as np
import pytest

from quiltwright.cycles import CyclesCamera, view_shift_x
from quiltwright.povray import PovCamera, camera_block, depth_budget
from quiltwright.quilt import QUILT_PRESETS, HasLens, QuiltCamera, window_shear


@dataclass(frozen=True)
class _TinyLens:
    """Stand-in for :class:`~quiltwright.lfd._Lens` -- fov + focal_distance only."""

    fov: float
    focal_distance: float


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


class TestHasLens:
    def test_cameras_and_lens_namespace_satisfy_the_protocol(self):
        pov = PovCamera(location=(0.0, 0.0, -10.0), look_at=(0.0, 0.0, 0.0), fov=14.0)
        cyc = CyclesCamera(location=(0.0, -10.0, 0.0), look_at=(0.0, 0.0, 0.0), fov=14.0)
        lens = _TinyLens(fov=14.0, focal_distance=10.0)
        assert isinstance(pov, HasLens)
        assert isinstance(cyc, HasLens)
        assert isinstance(lens, HasLens)

    def test_depth_budget_accepts_the_lens_namespace(self):
        spec = QUILT_PRESETS["portrait"]
        lens = _TinyLens(fov=14.0, focal_distance=48.5)
        rows = depth_budget(spec, lens, {"focal": 48.5})
        assert rows[0][0] == "focal"
        assert rows[0][2] == pytest.approx(0.0, abs=1e-9)


class TestAimedParity:
    """PovCamera.aimed and CyclesCamera.aimed share one contract.

    Each backend has its own handedness and default up-hint, so the
    assertions are invariant-level: lens preserved, focal distance applied,
    view direction untouched, lateral shift slides eye and aim together.
    """

    def test_keeps_view_direction_and_lens(self):
        location, aim, fov, fd = (15.0, 20.0, 6.0), (58.0, 19.0, 53.0), 53.13, 48.5
        for aimed, Camera in (
            (PovCamera.aimed, PovCamera),
            (CyclesCamera.aimed, CyclesCamera),
        ):
            cam = aimed(location, aim, fov=fov, focal_distance=fd)
            base = Camera(location=location, look_at=aim)
            np.testing.assert_allclose(cam.basis()[0], base.basis()[0], atol=1e-12)
            assert cam.fov == pytest.approx(fov)

    def test_focal_distance_applied_without_moving_the_eye(self):
        for aimed, location, aim, look_at in (
            (PovCamera.aimed, (0.0, 0.0, 0.0), (0.0, 0.0, 10.0), (0.0, 0.0, 48.5)),
            (CyclesCamera.aimed, (0.0, 0.0, 0.0), (0.0, 10.0, 0.0), (0.0, 48.5, 0.0)),
        ):
            cam = aimed(location, aim, fov=30.0, focal_distance=48.5)
            assert cam.focal_distance == pytest.approx(48.5)
            np.testing.assert_allclose(cam.location, location, atol=1e-12)
            np.testing.assert_allclose(cam.look_at, look_at, atol=1e-12)

    def test_lateral_shift_slides_eye_and_aim_together(self):
        for aimed, location, aim, eye, look_at in (
            (
                PovCamera.aimed,
                (0.0, 0.0, 0.0),
                (0.0, 0.0, 10.0),
                (-5.0, 0.0, 0.0),
                (-5.0, 0.0, 10.0),
            ),
            (
                CyclesCamera.aimed,
                (0.0, 0.0, 0.0),
                (0.0, 10.0, 0.0),
                (-5.0, 0.0, 0.0),
                (-5.0, 10.0, 0.0),
            ),
        ):
            cam = aimed(location, aim, fov=30.0, lateral_shift=-5.0)
            np.testing.assert_allclose(cam.location, eye, atol=1e-12)
            np.testing.assert_allclose(cam.look_at, look_at, atol=1e-12)
            forward, _, _ = cam.basis()
            base_forward = np.asarray(aim, dtype="d") - location
            base_forward = base_forward / np.linalg.norm(base_forward)
            np.testing.assert_allclose(forward, base_forward, atol=1e-12)

    def test_rejects_non_positive_focal_distance(self):
        for aimed, aim in (
            (PovCamera.aimed, (0.0, 0.0, 10.0)),
            (CyclesCamera.aimed, (0.0, 10.0, 0.0)),
        ):
            with pytest.raises(ValueError, match="focal_distance"):
                aimed((0.0, 0.0, 0.0), aim, fov=30.0, focal_distance=0.0)


def test_importing_window_shear_does_not_load_pyvista() -> None:
    """The identity lives in quilt; the Cycles helper must not drag VTK in."""
    sys.modules.pop("pyvista", None)
    sys.modules.pop("quiltwright.lfd", None)
    from quiltwright.cycles import view_shift_x as vs  # noqa: F401
    from quiltwright.quilt import window_shear as ws  # noqa: F401

    assert "pyvista" not in sys.modules
    assert "quiltwright.lfd" not in sys.modules
