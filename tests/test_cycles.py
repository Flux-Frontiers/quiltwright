"""Tests for the Blender Cycles quilt renderer (quiltwright.cycles).

The end-to-end tests need a way to run the driver under a real ``bpy``.  Two
routes are tried, in order:

* a ``blender`` binary (``BLENDER_BINARY``, ``PATH``, or the macOS app
  bundle) -- the normal case on a workstation;
* a Python interpreter with the ``bpy`` wheel installed, named by the
  ``QW_BPY_PYTHON`` environment variable -- the CI/container case.  A tiny
  shim translates Blender's command line onto that interpreter, so the
  production subprocess path is exercised verbatim.

With neither available the end-to-end tests skip; everything else runs on
numpy alone.
"""

import json
import math
import os
import subprocess
import sys
from dataclasses import replace

import numpy as np
import pytest

from quiltwright.cycles import (
    _DRIVER,
    CyclesCamera,
    _find_blender,
    _lighting_job,
    _scene_format,
    _view_angles,
    render_cycles_quilt,
    render_cycles_views,
    view_shift_x,
)
from quiltwright.lfd import QUILT_PRESETS, QuiltSpec, sweep_spec, view_offsets

# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def camera() -> CyclesCamera:
    """A camera looking down +y, 10 units from its focal plane, Z up."""
    return CyclesCamera(location=(0.0, -10.0, 0.0), look_at=(0.0, 0.0, 0.0), fov=30.0)


@pytest.fixture
def tiny_spec() -> QuiltSpec:
    """Minimal 2x2 quilt for fast path-tracing tests."""
    return QuiltSpec(columns=2, rows=2, quilt_width=256, quilt_height=256, aspect=1.0)


# ---------------------------------------------------------------------------
# Camera basis
# ---------------------------------------------------------------------------


class TestCyclesCamera:
    def test_focal_distance(self, camera):
        assert camera.focal_distance == pytest.approx(10.0)

    def test_basis_is_orthonormal(self):
        cam = CyclesCamera(location=(3.0, 4.0, -5.0), look_at=(1.0, 2.0, 6.0))
        forward, right, up = cam.basis()
        for v in (forward, right, up):
            assert np.linalg.norm(v) == pytest.approx(1.0)
        assert np.dot(forward, right) == pytest.approx(0.0, abs=1e-12)
        assert np.dot(forward, up) == pytest.approx(0.0, abs=1e-12)
        assert np.dot(right, up) == pytest.approx(0.0, abs=1e-12)

    def test_right_handed_convention(self, camera):
        """Blender: looking down +y with +z up must give right=+x.  Inverting
        this mirrors the sweep and turns the hologram inside out."""
        forward, right, up = camera.basis()
        np.testing.assert_allclose(forward, [0, 1, 0], atol=1e-12)
        np.testing.assert_allclose(right, [1, 0, 0], atol=1e-12)
        np.testing.assert_allclose(up, [0, 0, 1], atol=1e-12)

    def test_degenerate_camera_rejected(self):
        with pytest.raises(ValueError, match="identical"):
            CyclesCamera(location=(1, 1, 1), look_at=(1, 1, 1)).basis()

    def test_up_parallel_to_view_rejected(self):
        with pytest.raises(ValueError, match="parallel"):
            CyclesCamera(location=(0, 0, 0), look_at=(0, 0, 5)).basis()


class TestAimed:
    def test_keeps_view_direction_and_lens(self):
        cam = CyclesCamera.aimed(
            (15.0, 20.0, 6.0), (58.0, 19.0, 53.0), fov=53.13, focal_distance=48.5
        )
        base = CyclesCamera(location=(15.0, 20.0, 6.0), look_at=(58.0, 19.0, 53.0))
        np.testing.assert_allclose(cam.basis()[0], base.basis()[0], atol=1e-12)
        assert cam.fov == pytest.approx(53.13)

    def test_focal_distance_applied(self):
        cam = CyclesCamera.aimed((0, 0, 0), (0, 10, 0), fov=30.0, focal_distance=48.5)
        assert cam.focal_distance == pytest.approx(48.5)
        np.testing.assert_allclose(cam.look_at, [0, 48.5, 0], atol=1e-12)

    def test_lateral_shift_slides_eye_and_aim_together(self):
        cam = CyclesCamera.aimed((0, 0, 0), (0, 10, 0), fov=30.0, lateral_shift=-5.0)
        np.testing.assert_allclose(cam.location, [-5, 0, 0], atol=1e-12)
        np.testing.assert_allclose(cam.look_at, [-5, 10, 0], atol=1e-12)

    def test_rejects_non_positive_focal_distance(self):
        with pytest.raises(ValueError, match="focal_distance"):
            CyclesCamera.aimed((0, 0, 0), (0, 10, 0), fov=30.0, focal_distance=0.0)


# ---------------------------------------------------------------------------
# Off-axis shift + sweep angles
# ---------------------------------------------------------------------------


class TestViewShiftX:
    def test_centre_view_has_no_shift(self):
        assert view_shift_x(0.0, 10.0, 30.0, 0.75) == 0.0

    def test_matches_the_vtk_window_centre(self):
        """The PyVista backend expresses the same shear as
        ``SetWindowCenter(-offset / half_width)`` in *half*-width units;
        Blender's shift_x is the same quantity in full frame widths.  The
        two backends must agree or their quilts fuse differently."""
        offset, focal, fov, aspect = 2.4, 48.5, 14.0, 0.5625
        half_width = focal * math.tan(math.radians(fov) / 2.0) * aspect
        window_centre = -offset / half_width
        assert view_shift_x(offset, focal, fov, aspect) == pytest.approx(window_centre / 2.0)

    def test_antisymmetric_across_the_sweep(self):
        left = view_shift_x(-3.0, 10.0, 30.0, 1.0)
        right = view_shift_x(3.0, 10.0, 30.0, 1.0)
        assert left == pytest.approx(-right)

    def test_rightward_eye_shears_left(self):
        """Eye moves right, frustum window slides left to keep the focal
        point centred: positive offset, negative shift."""
        assert view_shift_x(3.0, 10.0, 30.0, 1.0) < 0


class TestViewAngles:
    def test_reproduces_view_offsets(self):
        """The driver computes ``offset = Z * tan(angle)`` because with
        ``camera=None`` the focal distance only exists inside Blender; the
        angles must therefore reproduce view_offsets exactly."""
        spec = QUILT_PRESETS["portrait"]
        for focal in (5.0, 48.5, 1000.0):
            np.testing.assert_allclose(
                focal * np.tan(_view_angles(spec)), view_offsets(spec, focal), atol=1e-12
            )

    def test_view_zero_is_leftmost(self):
        angles = _view_angles(QUILT_PRESETS["portrait"])
        assert angles[0] < 0 < angles[-1]
        assert angles == sorted(angles)

    def test_single_view(self):
        spec = QuiltSpec(columns=1, rows=1, quilt_width=64, quilt_height=64, aspect=1.0)
        assert _view_angles(spec) == [0.0]


# ---------------------------------------------------------------------------
# Scene formats + binary discovery
# ---------------------------------------------------------------------------


class TestSceneFormat:
    @pytest.mark.parametrize(
        ("name", "kind"),
        [
            ("scene.blend", "blend"),
            ("scene.glb", "gltf"),
            ("scene.GLTF", "gltf"),
            ("scene.obj", "obj"),
            ("scene.usdz", "usd"),
            ("scene.fbx", "fbx"),
        ],
    )
    def test_known_suffixes(self, tmp_path, name, kind):
        assert _scene_format(tmp_path / name) == kind

    def test_pov_scene_is_rejected_with_the_supported_list(self, tmp_path):
        """The most likely wrong turn: handing this backend a POV-Ray scene.
        The error must say what *is* supported."""
        with pytest.raises(ValueError, match=r"\.pov.*supported.*\.blend"):
            _scene_format(tmp_path / "museum.pov")


class TestFindBlender:
    def test_missing_binary_raises(self):
        with pytest.raises(RuntimeError, match="not found"):
            _find_blender("definitely-not-a-real-blender-binary")

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("BLENDER_BINARY", "definitely-not-real-either")
        with pytest.raises(RuntimeError, match="definitely-not-real-either"):
            _find_blender()


class TestDriver:
    def test_driver_is_valid_python(self):
        """The driver only ever runs inside Blender, so a syntax error would
        otherwise surface as a cryptic subprocess failure at render time."""
        compile(_DRIVER, "driver.py", "exec")


# ---------------------------------------------------------------------------
# Argument validation (no Blender involved)
# ---------------------------------------------------------------------------


@pytest.fixture
def no_blender_needed(monkeypatch):
    """Satisfy binary discovery so validation is reachable without Blender."""
    from quiltwright import cycles

    monkeypatch.setattr(cycles, "_find_blender", lambda binary=None: "/bin/true")


class TestValidation:
    def test_missing_scene_raises(self, tiny_spec, camera, tmp_path, no_blender_needed):
        with pytest.raises(FileNotFoundError):
            render_cycles_quilt(tmp_path / "nope.blend", tiny_spec, camera, progress=False)

    def test_unsupported_format_raises(self, tiny_spec, camera, tmp_path, no_blender_needed):
        scene = tmp_path / "scene.pov"
        scene.write_text("sphere { 0, 1 }\n")
        with pytest.raises(ValueError, match="unsupported scene format"):
            render_cycles_quilt(scene, tiny_spec, camera, progress=False)

    def test_scene_camera_needs_a_blend(self, tiny_spec, tmp_path, no_blender_needed):
        """camera=None means "use the scene's camera", and only a .blend can
        carry one -- an OBJ import would fail deep inside Blender instead."""
        scene = tmp_path / "mesh.obj"
        scene.write_text("v 0 0 0\n")
        with pytest.raises(ValueError, match="explicit CyclesCamera"):
            render_cycles_quilt(scene, tiny_spec, None, progress=False)

    def test_degenerate_camera_rejected_before_blender_runs(
        self, tiny_spec, tmp_path, no_blender_needed
    ):
        scene = tmp_path / "s.blend"
        scene.write_bytes(b"BLENDER")
        bad = CyclesCamera(location=(1, 1, 1), look_at=(1, 1, 1))
        with pytest.raises(ValueError, match="identical"):
            render_cycles_quilt(scene, tiny_spec, bad, progress=False)


# ---------------------------------------------------------------------------
# Orchestration, against a stub "blender"
#
# The stub honours the real contract -- parse the command line, read the job
# JSON, write one PNG per view, speak QW_ lines on stdout -- so these tests
# exercise the production subprocess path end to end without a Blender.
# ---------------------------------------------------------------------------

_STUB = """\
import json
import sys

from PIL import Image

argv = sys.argv[1:]
job_path = argv[argv.index("--") + 1]
with open(job_path) as fh:
    job = json.load(fh)

with open(job["out_dir"] + "/argv.json", "w") as fh:
    json.dump(argv, fh)

mode = job.get("_stub_mode", "ok")
if mode == "driver-error":
    print("QW_ERROR: boom", flush=True)
    sys.exit(1)
if mode == "crash":
    print("stack trace here", flush=True)
    sys.exit(11)

print("QW_DEVICE STUB", flush=True)
n = len(job["angles"])
last = n - 1 if mode == "missing-view" else n
for i in range(last):
    # Encode the view index in the red channel so tile placement is checkable.
    Image.new("RGB", (job["width"], job["height"]), (i * 20, 128, 0)).save(
        job["out_dir"] + "/view%03d.png" % i
    )
    print("QW_VIEW %d/%d" % (i + 1, n), flush=True)
print("QW_DONE", flush=True)
"""


@pytest.fixture
def stub_blender(tmp_path):
    """A fake blender executable running :data:`_STUB` under this interpreter."""
    stub_py = tmp_path / "stub.py"
    stub_py.write_text(_STUB)
    stub = tmp_path / "fake-blender"
    stub.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{stub_py}" "$@"\n')
    stub.chmod(0o755)
    return stub


@pytest.fixture
def blend_scene(tmp_path):
    """A placeholder .blend; the stub never actually opens it."""
    scene = tmp_path / "scene.blend"
    scene.write_bytes(b"BLENDER-v500")
    return scene


def _stub_mode(monkeypatch, mode: str) -> None:
    """Smuggle a failure mode to the stub through the job JSON."""
    from quiltwright import cycles

    real_run = cycles._run_blender

    def tagged(blender, workdir, job, extra_args, threads, progress):
        return real_run(
            blender, workdir, {**job, "_stub_mode": mode}, extra_args, threads, progress
        )

    monkeypatch.setattr(cycles, "_run_blender", tagged)


def _argv_spy(monkeypatch) -> dict:
    """Capture the argv the stub saw, read from the workdir before it vanishes."""
    from quiltwright import cycles

    seen: dict = {}
    real_run = cycles._run_blender

    def spy(blender, workdir, job, extra_args, threads, progress):
        views = real_run(blender, workdir, job, extra_args, threads, progress)
        seen["argv"] = json.loads((workdir / "argv.json").read_text())
        return views

    monkeypatch.setattr(cycles, "_run_blender", spy)
    return seen


class TestOrchestration:
    def test_views_come_back_in_view_order(self, blend_scene, camera, stub_blender, tmp_path):
        spec = sweep_spec(5, 45.0, 32, 32)
        paths = render_cycles_views(
            blend_scene, spec, camera, tmp_path / "sweep", binary=str(stub_blender), progress=False
        )
        assert [p.name for p in paths] == [f"view{i:03d}.png" for i in range(5)]
        from PIL import Image

        for i, p in enumerate(paths):
            assert np.asarray(Image.open(p))[0, 0, 0] == i * 20

    def test_quilt_tiles_land_in_quilt_order(self, blend_scene, camera, stub_blender, tiny_spec):
        quilt = render_cycles_quilt(
            blend_scene, tiny_spec, camera, binary=str(stub_blender), progress=False
        )
        assert quilt.shape == (256, 256, 3)
        for i in range(tiny_spec.n_views):
            x, y = tiny_spec.tile_origin(i)
            assert quilt[y, x, 0] == i * 20, f"view {i} misplaced"

    def test_job_carries_the_camera_and_geometry(
        self, blend_scene, camera, stub_blender, tiny_spec, tmp_path
    ):
        keep = tmp_path / "kept"
        render_cycles_quilt(
            blend_scene,
            tiny_spec,
            camera,
            binary=str(stub_blender),
            keep_views=keep,
            progress=False,
        )
        job = json.loads((keep / "job.json").read_text())
        assert job["format"] == "blend"
        assert job["camera"]["fov"] == pytest.approx(30.0)
        assert job["camera"]["focal_distance"] == pytest.approx(10.0)
        assert len(job["angles"]) == tiny_spec.n_views
        assert (job["width"], job["height"]) == (128, 128)
        assert job["view_transform"] == "Standard"
        assert len(list(keep.glob("view*.png"))) == tiny_spec.n_views

    def test_view_transform_override_reaches_the_job(
        self, blend_scene, camera, stub_blender, tiny_spec, tmp_path
    ):
        """Standard is the default because AgX -- Blender's own interactive
        default since 4.0 -- desaturates and flattens a render next to
        POV-Ray's; the override must still reach the driver for callers who
        want AgX's filmic highlight rolloff anyway."""
        keep = tmp_path / "kept"
        render_cycles_quilt(
            blend_scene,
            tiny_spec,
            camera,
            view_transform="AgX",
            binary=str(stub_blender),
            keep_views=keep,
            progress=False,
        )
        job = json.loads((keep / "job.json").read_text())
        assert job["view_transform"] == "AgX"

    def test_anamorphic_views_render_at_view_aspect(
        self, blend_scene, camera, stub_blender, tmp_path
    ):
        """16"-Landscape shape: 4:3 tiles hold 16:9 views; the render must
        happen at the view aspect and be resampled into the tile."""
        spec = QuiltSpec(columns=2, rows=2, quilt_width=192, quilt_height=144, aspect=1.77778)
        keep = tmp_path / "kept"
        quilt = render_cycles_quilt(
            blend_scene, spec, camera, binary=str(stub_blender), keep_views=keep, progress=False
        )
        job = json.loads((keep / "job.json").read_text())
        assert (job["width"], job["height"]) == (128, 72)
        assert quilt.shape == (144, 192, 3)

    def test_scene_camera_serialises_as_null(self, blend_scene, stub_blender, tiny_spec, tmp_path):
        render_cycles_views(
            blend_scene,
            tiny_spec,
            None,
            tmp_path / "sweep",
            binary=str(stub_blender),
            keep_job=True,
            progress=False,
        )
        job = json.loads((tmp_path / "sweep" / "job.json").read_text())
        assert job["camera"] is None

    def test_view_cone_override_reaches_the_angles(
        self, blend_scene, camera, stub_blender, tiny_spec, tmp_path
    ):
        render_cycles_views(
            blend_scene,
            tiny_spec,
            camera,
            tmp_path / "sweep",
            view_cone=20.0,
            binary=str(stub_blender),
            keep_job=True,
            progress=False,
        )
        job = json.loads((tmp_path / "sweep" / "job.json").read_text())
        assert math.degrees(job["angles"][-1] - job["angles"][0]) == pytest.approx(20.0)

    def test_driver_error_surfaces_its_message(
        self, blend_scene, camera, stub_blender, tiny_spec, monkeypatch
    ):
        _stub_mode(monkeypatch, "driver-error")
        with pytest.raises(RuntimeError, match="Cycles render failed: boom"):
            render_cycles_quilt(
                blend_scene, tiny_spec, camera, binary=str(stub_blender), progress=False
            )

    def test_crash_surfaces_the_transcript(
        self, blend_scene, camera, stub_blender, tiny_spec, monkeypatch
    ):
        _stub_mode(monkeypatch, "crash")
        with pytest.raises(RuntimeError, match=r"Blender failed \(11\)[\s\S]*stack trace here"):
            render_cycles_quilt(
                blend_scene, tiny_spec, camera, binary=str(stub_blender), progress=False
            )

    def test_missing_view_detected(self, blend_scene, camera, stub_blender, tiny_spec, monkeypatch):
        """A truncated sweep must fail loudly, not emit a half-filled quilt."""
        _stub_mode(monkeypatch, "missing-view")
        with pytest.raises(RuntimeError, match="missing"):
            render_cycles_quilt(
                blend_scene, tiny_spec, camera, binary=str(stub_blender), progress=False
            )


class TestThreads:
    """Blender takes every core it can see, same as POV-Ray; the courtesy
    cap from the POV-Ray backend applies here too, as Blender's ``-t``."""

    def _render(self, blend_scene, camera, stub_blender, tmp_path, **kwargs):
        render_cycles_views(
            blend_scene,
            sweep_spec(2, 10.0, 16, 16),
            camera,
            tmp_path / "sweep",
            binary=str(stub_blender),
            progress=False,
            **kwargs,
        )

    def test_courtesy_cap_reaches_the_command_line(
        self, blend_scene, camera, stub_blender, tmp_path, monkeypatch
    ):
        from quiltwright import cycles

        monkeypatch.setattr(cycles.os, "cpu_count", lambda: 18)
        seen = _argv_spy(monkeypatch)
        self._render(blend_scene, camera, stub_blender, tmp_path)
        argv = seen["argv"]
        assert argv[argv.index("-t") + 1] == "16"

    def test_zero_means_every_core(self, blend_scene, camera, stub_blender, tmp_path, monkeypatch):
        seen = _argv_spy(monkeypatch)
        self._render(blend_scene, camera, stub_blender, tmp_path, threads=0)
        assert "-t" not in seen["argv"]

    def test_caller_supplied_threads_not_duplicated(
        self, blend_scene, camera, stub_blender, tmp_path, monkeypatch
    ):
        seen = _argv_spy(monkeypatch)
        self._render(blend_scene, camera, stub_blender, tmp_path, extra_args=("-t", "3"))
        argv = seen["argv"]
        assert argv.count("-t") == 1
        assert argv[argv.index("-t") + 1] == "3"


# ---------------------------------------------------------------------------
# End-to-end path tracing (requires Blender, or a bpy interpreter)
# ---------------------------------------------------------------------------


def _bpy_runner(tmp_path_factory):
    """Resolve something that can act as a blender binary, or ``None``."""
    try:
        return _find_blender(None)
    except RuntimeError:
        pass
    py = os.environ.get("QW_BPY_PYTHON")
    if not py:
        return None
    probe = subprocess.run([py, "-c", "import bpy"], capture_output=True, timeout=300, check=False)
    if probe.returncode != 0:
        return None
    root = tmp_path_factory.mktemp("bpy_shim")
    shim_py = root / "shim.py"
    shim_py.write_text(
        "import runpy, sys\n"
        "argv = sys.argv[1:]\n"
        'driver = argv[argv.index("--python") + 1]\n'
        'sys.argv = [driver] + argv[argv.index("--"):]\n'
        'runpy.run_path(driver, run_name="__main__")\n'
    )
    shim = root / "fake-blender"
    shim.write_text(f'#!/bin/sh\nexec "{py}" "{shim_py}" "$@"\n')
    shim.chmod(0o755)
    return str(shim)


@pytest.fixture(scope="session")
def blender_binary(tmp_path_factory):
    runner = _bpy_runner(tmp_path_factory)
    if runner is None:
        pytest.skip("no blender binary and no QW_BPY_PYTHON with bpy")
    return runner


# Three emissive markers at different depths, right-handed Z-up.  The camera
# sits at (0,-10,0) looking at the origin: green ON the focal plane, red 4
# units nearer, blue 4 units farther, separated vertically so none occludes
# another.  The scene also carries its own camera annotated with a DoF focus
# distance of 10, for the camera=None path.
_DEPTH_SCENE_SETUP = """
import math
import sys

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene


def marker(name, color, location):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.2, location=location)
    obj = bpy.context.active_object
    obj.name = name
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    emit = mat.node_tree.nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*color, 1.0)
    emit.inputs["Strength"].default_value = 5.0
    out = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    mat.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    obj.data.materials.append(mat)


marker("green_focal", (0, 1, 0), (0.0, 0.0, 0.0))
marker("red_near", (1, 0, 0), (0.0, -4.0, -0.9))
marker("blue_far", (0, 0, 1), (0.0, 4.0, 0.9))

world = bpy.data.worlds.new("black")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0, 0, 0, 1)
bg.inputs["Strength"].default_value = 0.0
scene.view_settings.view_transform = "Standard"

data = bpy.data.cameras.new("scene_cam")
data.angle_y = math.radians(30.0)
data.dof.focus_distance = 10.0
cam = bpy.data.objects.new("scene_cam", data)
scene.collection.objects.link(cam)
scene.camera = cam
cam.location = (0.0, -10.0, 0.0)
cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])
"""


@pytest.fixture(scope="session")
def depth_blend(blender_binary, tmp_path_factory):
    root = tmp_path_factory.mktemp("depth_scene")
    setup = root / "setup.py"
    setup.write_text(_DEPTH_SCENE_SETUP)
    blend = root / "depth.blend"
    result = subprocess.run(
        [
            blender_binary,
            "--background",
            "--factory-startup",
            "--python",
            str(setup),
            "--",
            str(blend),
        ],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert blend.is_file(), f"scene setup failed:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
    return blend


def _centroid_x(tile: np.ndarray, channel: int):
    """Column centroid of the marker dominated by *channel*, or None."""
    others = [c for c in range(3) if c != channel]
    m = (tile[..., channel] > 120) & (tile[..., others[0]] < 100) & (tile[..., others[1]] < 100)
    return m.nonzero()[1].mean() if m.any() else None


def _marker_tracks(quilt: np.ndarray, spec: QuiltSpec) -> dict[int, list]:
    th, tw = spec.tile_height, spec.tile_width
    tracks = {0: [], 1: [], 2: []}
    for i in range(spec.n_views):
        x, y = spec.tile_origin(i)
        tile = quilt[y : y + th, x : x + tw].astype(float)
        for channel in tracks:
            tracks[channel].append(_centroid_x(tile, channel))
    return tracks


class TestRenderCyclesQuilt:
    def test_quilt_shape_and_parallax(self, depth_blend, tiny_spec, camera, blender_binary):
        quilt = render_cycles_quilt(
            depth_blend,
            tiny_spec,
            camera,
            samples=8,
            denoise=False,
            device="cpu",
            binary=blender_binary,
            progress=False,
        )
        assert quilt.shape == (256, 256, 3)
        assert quilt.dtype == np.uint8

        th, tw = tiny_spec.tile_height, tiny_spec.tile_width
        x0, y0 = tiny_spec.tile_origin(0)
        x3, y3 = tiny_spec.tile_origin(3)
        assert not np.array_equal(
            quilt[y0 : y0 + th, x0 : x0 + tw], quilt[y3 : y3 + th, x3 : x3 + tw]
        ), "leftmost and rightmost views identical"

    def test_focal_plane_is_pinned(self, depth_blend, tiny_spec, camera, blender_binary):
        """The on-focal-plane marker must not move between views, while the
        off-plane markers must.  This is the property that distinguishes a
        correct off-axis shear from a toe-in rotation -- and the one that
        catches a wrong shift_x unit, which pins nothing."""
        quilt = render_cycles_quilt(
            depth_blend,
            tiny_spec,
            camera,
            samples=8,
            denoise=False,
            device="cpu",
            binary=blender_binary,
            progress=False,
        )
        tracks = _marker_tracks(quilt, tiny_spec)
        green, red = tracks[1], tracks[0]
        tw = tiny_spec.tile_width

        assert all(g is not None for g in green), "focal marker missing from a view"
        assert max(green) - min(green) < 1.0, f"focal marker drifted: {green}"
        for g in green:
            assert abs(g - tw / 2) < 2.0

        assert all(r is not None for r in red)
        assert max(red) - min(red) > 5.0, f"no parallax on the near marker: {red}"

    def test_view_zero_is_leftmost_eye(self, depth_blend, tiny_spec, camera, blender_binary):
        """Moving the eye right must push nearer objects left, so the near
        marker travels right-to-left across the view order."""
        quilt = render_cycles_quilt(
            depth_blend,
            tiny_spec,
            camera,
            samples=8,
            denoise=False,
            device="cpu",
            binary=blender_binary,
            progress=False,
        )
        red = _marker_tracks(quilt, tiny_spec)[0]
        assert red[0] > red[-1], f"view order mirrored: near marker at {red}"

    def test_scene_camera_is_equivalent(self, depth_blend, blender_binary):
        """camera=None adopts the .blend's own camera -- same pose, focal
        plane from its DoF focus -- under a portrait aspect, where AUTO
        sensor fit resolves vertically.  This is the configuration whose
        shift units differ from the explicit-camera path (Blender sizes the
        AUTO sensor off sensor_width even for a vertical fit), so the focal
        pin here guards the trickiest branch of the driver."""
        spec = QuiltSpec(columns=2, rows=2, quilt_width=192, quilt_height=256, aspect=0.75)
        quilt = render_cycles_quilt(
            depth_blend,
            spec,
            None,
            samples=8,
            denoise=False,
            device="cpu",
            binary=blender_binary,
            progress=False,
        )
        tracks = _marker_tracks(quilt, spec)
        green, red = tracks[1], tracks[0]
        assert all(g is not None for g in green)
        assert max(green) - min(green) < 1.0, f"focal marker drifted: {green}"
        assert red[0] > red[-1]

    @pytest.mark.parametrize("rig", ["soft", "studio", "sky"])
    def test_unlit_import_is_not_black(self, tiny_spec, camera, blender_binary, tmp_path, rig):
        """An OBJ arrives with no lights; every lighting rig must give the
        path tracer something to see by, or the import renders black."""
        cube = tmp_path / "cube.obj"
        cube.write_text(
            "v -1 -1 -1\nv 1 -1 -1\nv 1 1 -1\nv -1 1 -1\n"
            "v -1 -1 1\nv 1 -1 1\nv 1 1 1\nv -1 1 1\n"
            "f 1 2 3 4\nf 5 8 7 6\nf 1 5 6 2\nf 2 6 7 3\nf 3 7 8 4\nf 5 1 4 8\n"
        )
        spec = replace(tiny_spec, columns=1, rows=1, quilt_width=64, quilt_height=64)
        quilt = render_cycles_quilt(
            cube,
            spec,
            camera,
            lighting=rig,
            samples=8,
            denoise=False,
            device="cpu",
            binary=blender_binary,
            progress=False,
        )
        assert quilt.mean() > 5.0, f"imported scene rendered black under {rig!r}"

    def test_bad_blend_surfaces_the_driver_error(self, tiny_spec, camera, blender_binary, tmp_path):
        bad = tmp_path / "bad.blend"
        bad.write_bytes(b"this is not a blend file")
        with pytest.raises(RuntimeError, match="could not open|Blender failed"):
            render_cycles_quilt(
                bad, tiny_spec, camera, device="cpu", binary=blender_binary, progress=False
            )


class TestRenderCyclesViews:
    def test_writes_one_frame_per_view(self, depth_blend, camera, blender_binary, tmp_path):
        spec = sweep_spec(5, 45.0, 64, 64)
        paths = render_cycles_views(
            depth_blend,
            spec,
            camera,
            tmp_path / "sweep",
            samples=8,
            denoise=False,
            device="cpu",
            binary=blender_binary,
            progress=False,
        )
        assert [p.name for p in paths] == [f"view{i:03d}.png" for i in range(5)]
        assert all(p.is_file() for p in paths)
        assert not (tmp_path / "sweep" / "job.json").exists()


# ---------------------------------------------------------------------------
# The PyVista bridge
#
# The camera and orchestration tests run on fakes -- the bridge is
# deliberately duck-typed, so no pyvista (or GL stack) is needed to pin its
# arithmetic.  The end-to-end test at the bottom drives a real plotter
# through a real Cycles render and re-asserts the focal-plane invariant,
# which is what catches a wrong coordinate hop: the scene renders fine
# either way, only the sweep geometry betrays it.
# ---------------------------------------------------------------------------

from quiltwright.cycles import (  # noqa: E402  (grouped with the tests that use them)
    _to_blender,
    cycles_camera_from_plotter,
    render_cycles_quilt_from_plotter,
)


class _FakeCamera:
    """The vtkCamera surface the bridge reads, and nothing else."""

    def __init__(self):
        self.position = (0.0, -10.0, 0.0)
        self.focal_point = (0.0, 0.0, 0.0)
        self.up = (0.0, 0.0, 1.0)
        self.view_angle = 30.0
        self.is_set = True


class _FakePlotter:
    def __init__(self, gltf_body: str = "{}"):
        self.camera = _FakeCamera()
        self.exports: list[tuple[str, dict]] = []
        self._gltf_body = gltf_body

    def export_gltf(self, path, **kwargs):
        self.exports.append((path, kwargs))
        with open(path, "w") as fh:
            fh.write(self._gltf_body)


class TestToBlender:
    def test_the_yup_rotation(self):
        """A VTK point (x, y, z) lands at (x, -z, y) after Blender's glTF
        import -- measured against imported geometry, and the single fact
        the whole bridge rests on."""
        assert _to_blender(np.array([2.0, 0.0, 5.0])) == (2.0, -5.0, 0.0)
        assert _to_blender(np.array([0.0, 0.0, 1.0])) == (0.0, -1.0, 0.0)

    def test_is_a_rotation(self):
        """Distances must survive, or the focal plane moves in the hop."""
        a, b = np.array([1.0, 2.0, 3.0]), np.array([-4.0, 0.5, 2.0])
        assert np.linalg.norm(np.subtract(_to_blender(a), _to_blender(b))) == pytest.approx(
            np.linalg.norm(a - b)
        )


class TestCyclesCameraFromPlotter:
    def test_narrows_fov_and_dollies_back(self):
        """The render_quilt convention: the lens narrows to fov and the eye
        retreats so the focal plane stays the same size in frame."""
        cam = cycles_camera_from_plotter(_FakePlotter(), fov=14.0)
        half_height = 10.0 * math.tan(math.radians(15.0))
        expected = half_height / math.tan(math.radians(7.0))
        assert cam.fov == pytest.approx(14.0)
        assert cam.focal_distance == pytest.approx(expected)

    def test_fov_none_keeps_the_plotters_view(self):
        cam = cycles_camera_from_plotter(_FakePlotter(), fov=None)
        assert cam.fov == pytest.approx(30.0)
        assert cam.focal_distance == pytest.approx(10.0)

    def test_zoom_dollies_in(self):
        base = cycles_camera_from_plotter(_FakePlotter(), fov=None)
        zoomed = cycles_camera_from_plotter(_FakePlotter(), fov=None, zoom=2.0)
        assert zoomed.focal_distance == pytest.approx(base.focal_distance / 2.0)

    def test_expressed_in_blender_world(self):
        """Everything -- eye, aim, up -- goes through the same rotation as
        the exported geometry, or the sweep tilts."""
        cam = cycles_camera_from_plotter(_FakePlotter(), fov=None)
        np.testing.assert_allclose(cam.location, [0.0, 0.0, -10.0], atol=1e-12)
        np.testing.assert_allclose(cam.look_at, [0.0, 0.0, 0.0], atol=1e-12)
        np.testing.assert_allclose(cam.up, [0.0, -1.0, 0.0], atol=1e-12)

    def test_focal_point_is_preserved(self):
        plotter = _FakePlotter()
        plotter.camera.focal_point = (1.0, 2.0, 3.0)
        cam = cycles_camera_from_plotter(plotter, fov=14.0)
        np.testing.assert_allclose(cam.look_at, _to_blender(np.array([1.0, 2.0, 3.0])), atol=1e-12)


class TestRenderFromPlotter:
    def test_exports_under_the_coordinate_contract(self, stub_blender, tiny_spec):
        """rotate_scene=False is what the camera math assumes; silently
        losing it would tilt every quilt."""
        plotter = _FakePlotter()
        quilt = render_cycles_quilt_from_plotter(
            plotter, tiny_spec, binary=str(stub_blender), progress=False
        )
        assert quilt.shape == (256, 256, 3)
        ((path, kwargs),) = plotter.exports
        assert path.endswith(".gltf")
        assert kwargs["rotate_scene"] is False
        assert kwargs["inline_data"] is True

    def test_gltf_path_retains_the_export(self, stub_blender, tiny_spec, tmp_path):
        plotter = _FakePlotter(gltf_body='{"scene": 0}')
        keep = tmp_path / "scene.gltf"
        render_cycles_quilt_from_plotter(
            plotter, tiny_spec, gltf=keep, binary=str(stub_blender), progress=False
        )
        assert keep.read_text() == '{"scene": 0}'

    def test_kwargs_reach_the_job(self, stub_blender, tiny_spec, tmp_path, monkeypatch):
        seen = _argv_spy(monkeypatch)  # proves the real _run_blender ran
        keep = tmp_path / "kept"
        render_cycles_quilt_from_plotter(
            _FakePlotter(),
            tiny_spec,
            samples=17,
            binary=str(stub_blender),
            keep_views=keep,
            progress=False,
        )
        job = json.loads((keep / "job.json").read_text())
        assert job["samples"] == 17
        assert job["format"] == "gltf"
        assert job["camera"] is not None
        assert seen["argv"]


class TestPlotterBridgeEndToEnd:
    def test_focal_plane_survives_the_hop(self, blender_binary):
        """A real plotter, through export and import, path-traced: the
        focal-plane marker must sit pinned at tile centre in every view and
        the near marker must sweep right-to-left.  A wrong rotation or a
        dropped shear renders plausible frames that fail exactly this."""
        pv = pytest.importorskip("pyvista")

        plotter = pv.Plotter(off_screen=True)
        plotter.add_mesh(pv.Sphere(radius=0.25, center=(0.0, 0.0, 0.0)), color="green")
        plotter.add_mesh(pv.Sphere(radius=0.25, center=(0.0, -4.0, -0.9)), color="red")
        plotter.add_mesh(pv.Sphere(radius=0.25, center=(0.0, 4.0, 0.9)), color="blue")
        plotter.camera_position = [(0.0, -10.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)]

        spec = QuiltSpec(columns=2, rows=2, quilt_width=256, quilt_height=256, aspect=1.0)
        quilt = render_cycles_quilt_from_plotter(
            plotter,
            spec,
            fov=30.0,
            samples=8,
            denoise=False,
            device="cpu",
            binary=blender_binary,
            progress=False,
        )

        # Lit diffuse spheres, not emissive markers: detect by channel
        # dominance rather than absolute darkness of the other channels.
        def centroid_x(tile, channel):
            others = [c for c in range(3) if c != channel]
            m = (
                (tile[..., channel] > 90)
                & (tile[..., channel] > tile[..., others[0]] + 40)
                & (tile[..., channel] > tile[..., others[1]] + 40)
            )
            return m.nonzero()[1].mean() if m.any() else None

        th, tw = spec.tile_height, spec.tile_width
        green, red = [], []
        for i in range(spec.n_views):
            x, y = spec.tile_origin(i)
            tile = quilt[y : y + th, x : x + tw].astype(float)
            green.append(centroid_x(tile, 1))
            red.append(centroid_x(tile, 0))

        assert all(g is not None for g in green), "focal marker missing from a view"
        assert max(green) - min(green) < 1.0, f"focal marker drifted: {green}"
        for g in green:
            assert abs(g - tw / 2) < 2.0

        assert all(r is not None for r in red)
        assert max(red) - min(red) > 5.0, f"no parallax on the near marker: {red}"
        assert red[0] > red[-1], f"view order mirrored: near marker at {red}"


# ---------------------------------------------------------------------------
# Lighting rigs
# ---------------------------------------------------------------------------


class TestLightingJob:
    @pytest.mark.parametrize("rig", ["soft", "studio", "sky"])
    def test_named_rigs(self, rig):
        assert _lighting_job(rig) == {"kind": rig}

    def test_none_means_no_light(self):
        assert _lighting_job(None) is None

    @pytest.mark.parametrize("suffix", [".hdr", ".exr"])
    def test_hdri_path(self, tmp_path, suffix):
        env = tmp_path / f"env{suffix}"
        env.write_bytes(b"#?RADIANCE\n")
        job = _lighting_job(env)
        assert job["kind"] == "hdri"
        assert job["path"] == str(env.resolve())

    def test_missing_hdri_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="environment map"):
            _lighting_job(tmp_path / "absent.hdr")

    def test_unknown_rig_rejected(self):
        """A typo'd rig must fail before Blender is even found -- the driver
        would otherwise render the fallback silently."""
        with pytest.raises(ValueError, match="soft.*studio.*sky"):
            _lighting_job("dramatic")


class TestLightingReachesTheJob:
    def test_named_rig(self, blend_scene, camera, stub_blender, tiny_spec, tmp_path):
        render_cycles_views(
            blend_scene,
            tiny_spec,
            camera,
            tmp_path / "sweep",
            lighting="studio",
            binary=str(stub_blender),
            keep_job=True,
            progress=False,
        )
        job = json.loads((tmp_path / "sweep" / "job.json").read_text())
        assert job["lighting"] == {"kind": "studio"}

    def test_none(self, blend_scene, camera, stub_blender, tiny_spec, tmp_path):
        render_cycles_views(
            blend_scene,
            tiny_spec,
            camera,
            tmp_path / "sweep",
            lighting=None,
            binary=str(stub_blender),
            keep_job=True,
            progress=False,
        )
        job = json.loads((tmp_path / "sweep" / "job.json").read_text())
        assert job["lighting"] is None
