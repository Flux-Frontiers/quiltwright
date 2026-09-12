"""
Tests for the ParaView backend (quiltwright.paraview).

The split mirrors ``test_pymol.py``: everything that runs in a normal
interpreter is tested without ParaView present, and the handful of tests
that need a real ``pvpython`` skip cleanly when there is none.

What is pinned here:

*The inlined sweep math is the real sweep math.*  The script that runs inside
``pvpython`` cannot import quiltwright, so :data:`_SWEEP_MATH` carries its
own copy of the offset and shear formulas.  A copy can drift; these tests
exec it and check it against :func:`view_offsets` and :func:`window_shear`,
which are the source of truth every other backend uses.

*Paths are bound as literals.*  A state path goes into a generated script,
so a quote in it must not end the string and run as code.

*The frames are the success signal.*  ``pvpython`` exits 0 on a bad state
path -- it logs and carries on -- so a run that wrote nothing has to fail
loudly here rather than as a ``FileNotFoundError`` in the assembler.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import json
import stat
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from quiltwright.paraview import (
    _SWEEP_MATH,
    PARAVIEW_ENV,
    ParaViewCamera,
    ParaViewNotAvailable,
    _literals,
    _quiet,
    _script,
    available,
    depth_report,
    find_pvpython,
    probe_paraview_state,
    render_paraview_quilt,
    render_paraview_views,
)
from quiltwright.quilt import QUILT_PRESETS, view_offsets, window_shear

# ---------------------------------------------------------------------------
# Without ParaView
# ---------------------------------------------------------------------------


def _sweep_math() -> dict:
    namespace: dict = {}
    exec(compile(_SWEEP_MATH, "<sweep-math>", "exec"), namespace)
    return namespace


@pytest.mark.parametrize("name", ["portrait", "16-landscape", "go"])
@pytest.mark.parametrize("distance", [1.0, 7.5, 250.0])
def test_inlined_offsets_match_view_offsets(name, distance):
    """The copy inside the pvpython script must agree with the original."""
    spec = QUILT_PRESETS[name]
    got = _sweep_math()["sweep_offsets"](spec.n_views, spec.view_cone, distance)
    np.testing.assert_allclose(got, view_offsets(spec, distance), rtol=1e-12, atol=1e-12)


def test_inlined_offsets_single_view_is_centre():
    spec = QUILT_PRESETS["portrait"].still()
    assert _sweep_math()["sweep_offsets"](spec.n_views, spec.view_cone, 3.0) == [0.0]


@pytest.mark.parametrize("offset", [-0.4, 0.0, 0.25])
@pytest.mark.parametrize("fov,aspect", [(14.0, 0.75), (30.0, 16 / 9)])
def test_inlined_shear_matches_window_shear(offset, fov, aspect):
    got = _sweep_math()["window_shear"](offset, 5.0, fov, aspect)
    assert got == pytest.approx(window_shear(offset, 5.0, fov, aspect), rel=1e-12, abs=1e-12)


def test_script_bindings_are_literals_not_interpolation():
    text = _literals(STATE="/tmp/it's here.pvsm", FOV=None, N_VIEWS=48)
    namespace: dict = {}
    exec(compile(text, "<t>", "exec"), namespace)
    assert namespace["STATE"] == "/tmp/it's here.pvsm"
    assert namespace["FOV"] is None
    assert namespace["N_VIEWS"] == 48


def test_script_carries_the_render_size_and_view_count(tmp_path):
    """The script renders at the view aspect, not the tile aspect, and knows
    how many views to write -- the two numbers the assembler will check.
    """
    spec = QUILT_PRESETS["portrait"]
    text = _script(
        tmp_path / "s.pvsm",
        spec,
        tmp_path,
        tmp_path / "camera.json",
        fov=14.0,
        zoom=None,
        hide_orientation_axes=True,
        probe_only=False,
    )
    assert f"N_VIEWS = {spec.n_views}" in text
    assert f"RENDER_H = {spec.tile_height}" in text
    assert f"RENDER_W = {round(spec.tile_height * spec.aspect)}" in text
    assert "PROBE_ONLY = False" in text
    assert "_DisableFirstRenderCameraReset" in text
    assert "SetWindowCenter" in text


def test_probe_script_does_not_render(tmp_path):
    text = _script(
        tmp_path / "s.pvsm",
        QUILT_PRESETS["portrait"],
        tmp_path,
        tmp_path / "camera.json",
        fov=14.0,
        zoom=None,
        hide_orientation_axes=True,
        probe_only=True,
    )
    assert "PROBE_ONLY = True" in text
    # The early exit sits before the sweep loop.
    assert text.index("if PROBE_ONLY:") < text.index("for i, off in enumerate(offsets):")


def test_quiet_drops_only_the_openvkl_noise():
    err = "[openvkl] INITIALIZATION ERROR: no module\nTraceback (most recent call last):\n  boom"
    assert _quiet(err) == "Traceback (most recent call last):\n  boom"


class TestFindPvpython:
    def test_env_var_wins(self, tmp_path, monkeypatch):
        fake = tmp_path / "pvpython"
        fake.write_text("#!/bin/sh\n")
        fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
        monkeypatch.setenv(PARAVIEW_ENV, str(fake))
        assert find_pvpython() == str(fake)

    def test_env_var_pointing_nowhere_is_an_error_not_a_fallback(self, tmp_path, monkeypatch):
        monkeypatch.setenv(PARAVIEW_ENV, str(tmp_path / "missing"))
        with pytest.raises(ParaViewNotAvailable, match="not found"):
            find_pvpython()

    def test_nothing_anywhere_says_how_to_install(self, tmp_path, monkeypatch):
        monkeypatch.delenv(PARAVIEW_ENV, raising=False)
        monkeypatch.setenv("PATH", str(tmp_path))
        monkeypatch.setattr("quiltwright.paraview._MAC_BUNDLES", str(tmp_path / "none*/pvpython"))
        with pytest.raises(ParaViewNotAvailable, match="brew install --cask paraview"):
            find_pvpython()
        assert available() is None


def test_camera_from_meta_and_depth_report():
    camera = ParaViewCamera._from_meta(
        {
            "view": "RenderView1",
            "position": [0.0, 0.0, 10.0],
            "focal_point": [0.0, 0.0, 0.0],
            "view_up": [0.0, 1.0, 0.0],
            "fov": 14.0,
            "focal_distance": 10.0,
            "depths": {"near": 8.0, "focal": 10.0, "far": 13.0},
        }
    )
    assert camera.focal_distance == 10.0
    report = depth_report(camera, QUILT_PRESETS["portrait"])
    assert "near" in report and "far" in report


def test_depth_report_tolerates_no_visible_bounds():
    camera = ParaViewCamera._from_meta(
        {
            "view": "RenderView1",
            "position": [0.0, 0.0, 10.0],
            "focal_point": [0.0, 0.0, 0.0],
            "view_up": [0.0, 1.0, 0.0],
            "fov": 14.0,
            "focal_distance": 10.0,
            "depths": {"near": None, "focal": 10.0, "far": None},
        }
    )
    report = depth_report(camera, QUILT_PRESETS["portrait"])
    assert "focal" in report


def test_a_missing_state_file_is_reported_before_pvpython_runs(tmp_path, monkeypatch):
    monkeypatch.setattr("quiltwright.paraview.find_pvpython", lambda binary=None: "/bin/true")
    with pytest.raises(FileNotFoundError, match="state file not found"):
        probe_paraview_state(tmp_path / "nope.pvsm", QUILT_PRESETS["portrait"])


def test_a_run_that_writes_nothing_fails_loudly(tmp_path, monkeypatch):
    """pvpython exits 0 on a bad state -- logged, not raised -- so missing
    frames are the failure, and the error names them.
    """
    monkeypatch.setattr("quiltwright.paraview.find_pvpython", lambda binary=None: "/bin/true")
    monkeypatch.setattr(
        "quiltwright.paraview._run_pvpython",
        lambda *a, **k: (0, "loaded nothing", ""),
    )
    state = tmp_path / "s.pvsm"
    state.write_text("<ParaView/>")
    with pytest.raises(RuntimeError, match=r"did not write \['view000.png'"):
        render_paraview_views(state, QUILT_PRESETS["portrait"].still(), tmp_path / "views")


# ---------------------------------------------------------------------------
# With a real ParaView
# ---------------------------------------------------------------------------

paraview_only = pytest.mark.skipif(available() is None, reason="no pvpython found")

#: A small state for the end-to-end tests: one coloured sphere, camera set
#: off-axis so a reset would be detectable.
_STATE_SCRIPT = """
from paraview.simple import *
s = Sphere(Radius=1.0, ThetaResolution=48, PhiResolution=48)
view = GetActiveViewOrCreate("RenderView")
d = Show(s, view)
ColorBy(d, ("POINTS", "Normals", "X"))
view.ViewSize = [300, 400]
# The first Render() resets the camera, so look first, then move -- the
# order a person in the GUI follows.
Render(view)
cam = view.GetActiveCamera()
cam.SetPosition(0.0, 1.5, 6.0)
cam.SetFocalPoint(0.0, 0.0, 0.0)
cam.SetViewUp(0.0, 1.0, 0.0)
Render(view)
SaveState(STATE_OUT)
"""


@pytest.fixture(scope="module")
def sphere_state(tmp_path_factory) -> Path:
    import subprocess

    out = tmp_path_factory.mktemp("pvsm") / "sphere.pvsm"
    script = tmp_path_factory.mktemp("pvsm") / "make.py"
    script.write_text(f"STATE_OUT = {str(out)!r}\n" + _STATE_SCRIPT)
    subprocess.run(
        [find_pvpython(), "--force-offscreen-rendering", str(script)],
        check=True,
        capture_output=True,
    )
    assert out.exists()
    return out


#: A 2x2 grid keeps the end-to-end sweep at four frames.
TINY = replace(QUILT_PRESETS["portrait"], columns=2, rows=2, quilt_width=240, quilt_height=320)


@pytest.mark.slow
@paraview_only
def test_probe_reads_the_states_own_camera(sphere_state):
    camera = probe_paraview_state(sphere_state, TINY, fov=None)
    assert camera.fov == pytest.approx(30.0)  # ParaView's default view angle, kept
    assert camera.focal_point == pytest.approx((0.0, 0.0, 0.0))
    # fov=None keeps the state's distance: |(0, 1.5, 6)| exactly.
    assert camera.focal_distance == pytest.approx(np.hypot(1.5, 6.0))
    assert camera.depths["near"] < camera.depths["focal"] < camera.depths["far"]
    # Depths come from the visible bounding box, not the surface: the corners
    # of the unit cube projected on the view axis from the eye.
    eye = np.array([0.0, 1.5, 6.0])
    forward = -eye / np.linalg.norm(eye)
    corners = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)])
    along = (corners - eye) @ forward
    assert camera.depths["near"] == pytest.approx(along.min(), abs=1e-3)
    assert camera.depths["far"] == pytest.approx(along.max(), abs=1e-3)


@pytest.mark.slow
@paraview_only
def test_fov_framing_dollies_back_like_render_quilt(sphere_state):
    kept = probe_paraview_state(sphere_state, TINY, fov=None)
    framed = probe_paraview_state(sphere_state, TINY, fov=14.0)
    assert framed.fov == 14.0
    # Same half-height at the focal plane: d' = d * tan(30/2) / tan(14/2).
    expect = kept.focal_distance * np.tan(np.radians(15.0)) / np.tan(np.radians(7.0))
    assert framed.focal_distance == pytest.approx(expect, rel=1e-6)


@pytest.mark.slow
@paraview_only
def test_a_real_sweep_makes_a_quilt_whose_views_differ(sphere_state, tmp_path):
    """The end-to-end claim: state in, quilt out, and the camera moved."""
    quilt = render_paraview_quilt(sphere_state, TINY, keep_views=tmp_path / "views", progress=False)
    assert quilt.shape == (TINY.quilt_height, TINY.quilt_width, 3)
    assert quilt.dtype == np.uint8
    views = sorted((tmp_path / "views").glob("view*.png"))
    assert len(views) == TINY.n_views
    meta = json.loads((tmp_path / "views" / "camera.json").read_text())
    assert meta["view"]
    # Leftmost and rightmost tiles are different renders, not one repeated.
    th, tw = TINY.tile_height, TINY.tile_width
    left = quilt[-th:, :tw]  # view 0: bottom-left
    right = quilt[:th, -tw:]  # view N-1: top-right
    assert not np.array_equal(left, right)
    assert np.abs(left.astype(int) - right.astype(int)).mean() > 1.0


@pytest.mark.slow
@paraview_only
def test_still_is_one_centre_view(sphere_state):
    spec = TINY.still(height=200)
    quilt = render_paraview_quilt(sphere_state, spec, progress=False)
    assert quilt.shape == (200, round(200 * spec.aspect), 3)
    # Something was drawn: not a flat background.
    assert quilt.std() > 5.0


@pytest.mark.slow
@paraview_only
def test_cli_check_reports_the_binary():
    from click.testing import CliRunner

    from quiltwright.cli.main import cli

    result = CliRunner().invoke(cli, ["paraview", "--check"])
    assert result.exit_code == 0, result.output
    assert "pvpython" in result.output


def test_cli_requires_a_state_unless_checking():
    from click.testing import CliRunner

    from quiltwright.cli.main import cli

    result = CliRunner().invoke(cli, ["paraview"])
    assert result.exit_code != 0
    assert "STATE is required" in result.output


def test_cli_missing_paraview_is_a_message_not_a_traceback(monkeypatch):
    from click.testing import CliRunner

    from quiltwright.cli.main import cli

    monkeypatch.setattr("quiltwright.paraview.available", lambda: None)
    result = CliRunner().invoke(cli, ["paraview", "--check"])
    assert result.exit_code != 0
    assert "brew install --cask paraview" in result.output
    assert "Traceback" not in result.output
