"""
Tests for the ``quiltwright`` CLI commands.

These three commands all reach outside the process -- at Bridge over HTTP, at
System Events over AppleScript, at the process table -- so the first
requirement of this module is that **no test may cast to a panel, change the
desktop picture, or signal a real process**. Every boundary is stubbed, and
the stubs record what they were asked to do so the tests can assert on it.

What is pinned here is behaviour that has already cost real debugging time:

*Bridge lies when it is broken.* It keeps answering HTTP after crashing, so
``bridge status`` has to distinguish "answered" from "usable" and say so in
its exit code. Each failure shape gets a test.

*A laptop screen is not a Looking Glass.* Bridge enumerates ordinary monitors
alongside panels, and picking the wrong one is silent. The classification is
pinned in both ``cast --check`` and ``bridge status``.

*Woven frames are registered to one panel.* Putting one on the wrong desktop
produces a screenful of noise, so matching serial to desktop is pinned, as is
the refusal to guess when the match fails.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image

from quiltwright.cli import cmd_bridge, cmd_wallpaper
from quiltwright.cli.main import cli
from quiltwright.lfd import QUILT_PRESETS

# ---------------------------------------------------------------------------
# Doubles
# ---------------------------------------------------------------------------

#: Two heads as Bridge really reports them: a laptop panel with no
#: calibration, and a 16" Landscape.  Taken from a live probe of Bridge
#: 2.6.3, so the envelope shape is the real one.
_DEVICES = {
    "payload": {
        "value": {
            "0": {"value": {"hardwareVersion": {"value": "thirdparty"}, "hwid": {"value": ""}}},
            "1": {
                "value": {
                    "hardwareVersion": {"value": "16_gen3_l"},
                    "hwid": {"value": "LKG-J00332"},
                }
            },
        }
    }
}


class _Response:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeBridge:
    """Answers Bridge's HTTP API, recording every call.

    :param token: Orchestration token to hand out; ``""`` simulates a Bridge
        that answers but refuses a session.
    :param devices: ``available_output_devices`` body.
    :param hang: Endpoints that should time out rather than answer, which is
        how a crashed-but-listening Bridge behaves.
    """

    def __init__(self, token: str = "tok-1", devices=None, hang: set[str] | None = None):
        self.token = token
        self.devices = _DEVICES if devices is None else devices
        self.hang = hang or set()
        self.calls: list[tuple[str, dict]] = []

    @property
    def endpoints(self) -> list[str]:
        return [endpoint for endpoint, _ in self.calls]

    def payload_for(self, endpoint: str) -> dict:
        matches = [p for e, p in self.calls if e == endpoint]
        assert matches, f"no call to {endpoint}"
        return matches[-1]

    def __call__(self, req, timeout=None):
        endpoint = req.full_url.rsplit("/", 1)[-1]
        self.calls.append((endpoint, json.loads(req.data.decode())))
        if endpoint in self.hang:
            raise TimeoutError("timed out")
        if endpoint == "enter_orchestration":
            body = {"payload": {"value": self.token}}
        elif endpoint == "available_output_devices":
            body = self.devices
        else:
            body = {"status": {"value": "Completion"}}
        return _Response(json.dumps(body).encode())


@pytest.fixture
def bridge(monkeypatch) -> FakeBridge:
    """A healthy Bridge with one laptop screen and one Looking Glass."""
    fake = FakeBridge()
    monkeypatch.setattr(urllib.request, "urlopen", fake)
    monkeypatch.setattr(cmd_bridge, "_port_open", lambda *a, **k: True)
    monkeypatch.setattr(cmd_bridge, "_bridge_pids", lambda: [111])
    return fake


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _quilt(tmp_path, name: str = "scene_qs8x6a1.77778.png"):
    """A tiny stand-in quilt whose filename carries the tiling suffix."""
    path = tmp_path / name
    Image.new("RGB", (16, 12), (0, 0, 0)).save(path)
    return path


class FakeDesktops:
    """Stands in for :func:`cmd_wallpaper._osascript`.

    Models just enough of System Events to answer the three queries the
    command makes, and records every ``set picture`` so a test can assert
    that the *installed* path reached the *right* desktop.
    """

    def __init__(self, desktops):
        #: ``{index: [display_name, current_picture]}``
        self.desktops = {i: list(d) for i, d in desktops.items()}
        self.sets: list[tuple[int, str]] = []

    def __call__(self, script: str, timeout: float = 20.0) -> str:
        if "count of desktops" in script:
            return str(len(self.desktops))
        index = int(script.split("desktop ")[1].split()[0].rstrip(" to"))
        if "get display name" in script:
            return self.desktops[index][0]
        if "get picture" in script:
            return self.desktops[index][1]
        if "set picture" in script:
            path = script.split('POSIX file "')[1].rstrip('"')
            self.desktops[index][1] = path
            self.sets.append((index, path))
            return ""
        raise AssertionError(f"unexpected script: {script}")


@pytest.fixture
def desktops(monkeypatch) -> FakeDesktops:
    """A laptop screen and a Looking Glass, as macOS reports them."""
    fake = FakeDesktops(
        {
            1: ["Built-in Liquid Retina XDR Display", "/System/.../Big Sur.heic"],
            2: ["LKG-J00332", "/Users/x/Pictures/LKG-wallpapers/old_native_LKG-J00332.png"],
        }
    )
    monkeypatch.setattr(cmd_wallpaper, "_osascript", fake)
    return fake


# ---------------------------------------------------------------------------
# cast
# ---------------------------------------------------------------------------


class TestCast:
    def test_grid_and_aspect_come_from_the_filename(self, runner, tmp_path, monkeypatch):
        """The _qs suffix is the whole reason a bare `cast quilt.png` works."""
        seen = {}

        def fake_cast(path, spec, **kwargs):
            seen["spec"] = spec
            seen["kwargs"] = kwargs

        monkeypatch.setattr("quiltwright.bridge.cast_quilt", fake_cast)
        result = runner.invoke(cli, ["cast", str(_quilt(tmp_path))])
        assert result.exit_code == 0, result.output
        assert (seen["spec"].columns, seen["spec"].rows) == (8, 6)
        assert seen["spec"].aspect == pytest.approx(1.77778)

    def test_head_reaches_cast_quilt(self, runner, tmp_path, monkeypatch):
        """--head is the knob for a Bridge that picks the laptop screen."""
        seen = {}
        monkeypatch.setattr("quiltwright.bridge.cast_quilt", lambda p, s, **kw: seen.update(kw))
        result = runner.invoke(cli, ["cast", str(_quilt(tmp_path)), "--head", "1"])
        assert result.exit_code == 0, result.output
        assert seen["head_index"] == 1

    def test_unsuffixed_filename_is_refused_with_advice(self, runner, tmp_path):
        """Guessing a grid would silently shuffle the views, so it refuses."""
        result = runner.invoke(cli, ["cast", str(_quilt(tmp_path, "plain.png"))])
        assert result.exit_code != 0
        assert "--preset" in result.output and "--grid" in result.output

    def test_preset_and_grid_are_mutually_exclusive(self, runner, tmp_path):
        result = runner.invoke(
            cli,
            ["cast", str(_quilt(tmp_path)), "--preset", "16-landscape", "--grid", "8x6"],
        )
        assert result.exit_code != 0
        assert "mutually exclusive" in result.output

    def test_quilt_required_unless_check(self, runner):
        result = runner.invoke(cli, ["cast"])
        assert result.exit_code != 0
        assert "--check" in result.output

    def test_check_separates_panels_from_monitors(self, runner, bridge):
        """The classification that stops a cast landing on a laptop screen."""
        result = runner.invoke(cli, ["cast", "--check"])
        assert result.exit_code == 0, result.output
        assert "head 0: thirdparty  (ordinary monitor)" in result.output
        assert "LKG-J00332" in result.output
        assert "<- Looking Glass" in result.output

    def test_check_does_not_cast(self, runner, bridge):
        """--check is a probe; it must never start playback."""
        runner.invoke(cli, ["cast", "--check"])
        assert "play_playlist" not in bridge.endpoints

    def test_unreachable_bridge_is_a_message_not_a_traceback(self, runner, monkeypatch):
        def boom(*a, **k):
            raise OSError("connection refused")

        monkeypatch.setattr(urllib.request, "urlopen", boom)
        result = runner.invoke(cli, ["cast", "--check"])
        assert result.exit_code != 0
        assert "Bridge" in result.output
        assert "Traceback" not in result.output


# ---------------------------------------------------------------------------
# wallpaper
# ---------------------------------------------------------------------------


class TestWallpaper:
    def test_matches_the_desktop_by_serial(self, runner, tmp_path, desktops):
        """The filename's serial picks the panel -- nobody counts monitors."""
        frame = tmp_path / "scene_native_LKG-J00332.png"
        Image.new("RGB", (8, 8)).save(frame)
        result = runner.invoke(cli, ["wallpaper", str(frame), "--dir", str(tmp_path / "install")])
        assert result.exit_code == 0, result.output
        assert [i for i, _ in desktops.sets] == [2]

    def test_sets_the_installed_copy_not_the_source(self, runner, tmp_path, desktops):
        """Wallpaper is stored as a path: pointing into renders/ breaks later."""
        frame = tmp_path / "scene_native_LKG-J00332.png"
        Image.new("RGB", (8, 8)).save(frame)
        install = tmp_path / "install"
        runner.invoke(cli, ["wallpaper", str(frame), "--dir", str(install)])
        _, path = desktops.sets[-1]
        assert path.startswith(str(install))
        assert (install / frame.name).is_file()

    def test_no_install_leaves_the_file_where_it_is(self, runner, tmp_path, desktops):
        frame = tmp_path / "scene_native_LKG-J00332.png"
        Image.new("RGB", (8, 8)).save(frame)
        runner.invoke(cli, ["wallpaper", str(frame), "--no-install"])
        _, path = desktops.sets[-1]
        assert path == str(frame.resolve())

    def test_resetting_the_same_path_bounces_to_refresh(
        self, runner, tmp_path, desktops, monkeypatch
    ):
        """macOS caches wallpaper by path, so a re-weave would not appear.

        Re-weaving a scene overwrites the same filename the desktop already
        points at. Without a bounce off another image the panel keeps showing
        the previous pixels, which is indistinguishable from a weave that
        silently failed.
        """
        frame = tmp_path / "scene_native_LKG-J00332.png"
        Image.new("RGB", (8, 8)).save(frame)
        bounce = tmp_path / "bounce.heic"
        bounce.write_bytes(b"x")
        monkeypatch.setattr(cmd_wallpaper, "_BOUNCE_IMAGE", str(bounce))
        # The desktop is already on the frame -- the re-weave case.
        desktops.desktops[2][1] = str(frame.resolve())

        result = runner.invoke(cli, ["wallpaper", str(frame), "--no-install"])
        assert result.exit_code == 0, result.output
        assert desktops.sets == [(2, str(bounce)), (2, str(frame.resolve()))]

    def test_a_different_path_does_not_bounce(self, runner, tmp_path, desktops, monkeypatch):
        """The bounce is only for the cache; otherwise it is a visible flicker."""
        frame = tmp_path / "scene_native_LKG-J00332.png"
        Image.new("RGB", (8, 8)).save(frame)
        bounce = tmp_path / "bounce.heic"
        bounce.write_bytes(b"x")
        monkeypatch.setattr(cmd_wallpaper, "_BOUNCE_IMAGE", str(bounce))

        runner.invoke(cli, ["wallpaper", str(frame), "--no-install"])
        assert desktops.sets == [(2, str(frame.resolve()))]

    def test_unknown_serial_refuses_rather_than_guessing(self, runner, tmp_path, desktops):
        """A frame on the wrong panel is a screenful of noise."""
        frame = tmp_path / "scene_native_LKG-NOPE.png"
        Image.new("RGB", (8, 8)).save(frame)
        result = runner.invoke(cli, ["wallpaper", str(frame), "--no-install"])
        assert result.exit_code != 0
        assert "LKG-NOPE" in result.output
        assert not desktops.sets

    def test_missing_serial_asks_for_one(self, runner, tmp_path, desktops):
        frame = tmp_path / "plain.png"
        Image.new("RGB", (8, 8)).save(frame)
        result = runner.invoke(cli, ["wallpaper", str(frame), "--no-install"])
        assert result.exit_code != 0
        assert "--display" in result.output
        assert not desktops.sets

    def test_list_changes_nothing(self, runner, desktops):
        result = runner.invoke(cli, ["wallpaper", "--list"])
        assert result.exit_code == 0, result.output
        assert "LKG-J00332" in result.output
        assert not desktops.sets


# ---------------------------------------------------------------------------
# bridge
# ---------------------------------------------------------------------------


class TestBridgeStatus:
    def test_healthy_reports_the_panel_and_exits_zero(self, runner, bridge):
        result = runner.invoke(cli, ["bridge", "status"])
        assert result.exit_code == 0, result.output
        assert "HEALTHY" in result.output
        assert "LKG-J00332" in result.output

    def test_closed_port_is_not_running(self, runner, monkeypatch):
        monkeypatch.setattr(cmd_bridge, "_port_open", lambda *a, **k: False)
        monkeypatch.setattr(cmd_bridge, "_bridge_pids", lambda: [])
        result = runner.invoke(cli, ["bridge", "status"])
        assert result.exit_code == 1
        assert "NOT RUNNING" in result.output

    def test_open_port_but_no_answer_is_wedged(self, runner, monkeypatch):
        """The failure that cost an hour: listening, crashed, still 'up'."""
        fake = FakeBridge(hang={"enter_orchestration"})
        monkeypatch.setattr(urllib.request, "urlopen", fake)
        monkeypatch.setattr(cmd_bridge, "_port_open", lambda *a, **k: True)
        monkeypatch.setattr(cmd_bridge, "_bridge_pids", lambda: [111])
        result = runner.invoke(cli, ["bridge", "status"])
        assert result.exit_code == 1
        assert "WEDGED" in result.output
        assert "bridge reset" in result.output

    def test_answering_without_a_token_is_unusable(self, runner, monkeypatch):
        monkeypatch.setattr(urllib.request, "urlopen", FakeBridge(token=""))
        monkeypatch.setattr(cmd_bridge, "_port_open", lambda *a, **k: True)
        monkeypatch.setattr(cmd_bridge, "_bridge_pids", lambda: [111])
        result = runner.invoke(cli, ["bridge", "status"])
        assert result.exit_code == 1
        assert "UNUSABLE" in result.output

    def test_no_looking_glass_among_the_heads_is_not_healthy(self, runner, monkeypatch):
        """A healthy Bridge seeing only monitors must not read as success."""
        only_monitor = {
            "payload": {
                "value": {
                    "0": {
                        "value": {
                            "hardwareVersion": {"value": "thirdparty"},
                            "hwid": {"value": ""},
                        }
                    }
                }
            }
        }
        monkeypatch.setattr(urllib.request, "urlopen", FakeBridge(devices=only_monitor))
        monkeypatch.setattr(cmd_bridge, "_port_open", lambda *a, **k: True)
        monkeypatch.setattr(cmd_bridge, "_bridge_pids", lambda: [111])
        result = runner.invoke(cli, ["bridge", "status"])
        assert result.exit_code == 1
        assert "NO PANEL" in result.output


class TestBridgeReset:
    @pytest.fixture(autouse=True)
    def _on_a_mac(self, monkeypatch):
        """Reset is macOS-only; the process logic under test is not.

        The command refuses outright off darwin, so CI on Linux would only
        ever exercise that refusal. Pretend to be a Mac and test the part
        that has behaviour.
        """
        monkeypatch.setattr(cmd_bridge.sys, "platform", "darwin")

    def test_signals_the_processes_it_found(self, runner, monkeypatch):
        killed = []
        pids = [111, 222]
        monkeypatch.setattr(cmd_bridge, "_bridge_pids", lambda: pids)
        monkeypatch.setattr(cmd_bridge.os, "kill", lambda pid, sig: killed.append((pid, sig)))
        monkeypatch.setattr(cmd_bridge.time, "sleep", lambda s: None)
        result = runner.invoke(cli, ["bridge", "reset", "--no-relaunch"])
        assert result.exit_code == 0, result.output
        assert {pid for pid, _ in killed} == {111, 222}

    def test_no_relaunch_does_not_launch(self, runner, monkeypatch):
        launched = []
        monkeypatch.setattr(cmd_bridge, "_bridge_pids", lambda: [])
        monkeypatch.setattr(
            cmd_bridge.subprocess, "run", lambda *a, **k: launched.append(a) or None
        )
        result = runner.invoke(cli, ["bridge", "reset", "--no-relaunch"])
        assert result.exit_code == 0, result.output
        assert not launched
        assert "no Bridge process was running" in result.output

    def test_refuses_off_macos(self, runner, monkeypatch):
        monkeypatch.setattr(cmd_bridge.sys, "platform", "linux")
        result = runner.invoke(cli, ["bridge", "reset"])
        assert result.exit_code == 1
        assert "macOS only" in result.output


class TestCartoon:
    """``quiltwright cartoon`` -- the shell face of the PyMOL bridge.

    PyMOL is never invoked here.  What matters at this layer is that the
    command validates before it starts a several-second subprocess, reports
    an absent PyMOL as advice rather than a traceback, and passes what it was
    given through unaltered.
    """

    def test_check_reports_the_subprocess_route_without_converting(self, runner, monkeypatch):
        """The Homebrew build is the common install and is not importable, so
        "found but not importable" is the normal answer, not a warning.
        """
        import quiltwright.pymol as mod

        monkeypatch.setattr(mod, "available", lambda: "subprocess")
        result = runner.invoke(cli, ["cartoon", "--check"])
        assert result.exit_code == 0
        assert "subprocess" in result.output
        assert "Homebrew" in result.output

    def test_check_reports_the_importable_route(self, runner, monkeypatch):
        import quiltwright.pymol as mod

        monkeypatch.setattr(mod, "available", lambda: "module")
        result = runner.invoke(cli, ["cartoon", "--check"])
        assert result.exit_code == 0
        assert "importable" in result.output

    def test_check_fails_with_install_advice_when_pymol_is_absent(self, runner, monkeypatch):
        """The failure a first-time user hits, so it carries the fix and a
        non-zero status a script can branch on.
        """
        import quiltwright.pymol as mod

        monkeypatch.setattr(mod, "available", lambda: None)
        result = runner.invoke(cli, ["cartoon", "--check"])
        assert result.exit_code != 0
        assert "brew install pymol" in result.output
        assert "conda" in result.output

    def test_an_unknown_representation_is_refused_before_pymol_starts(self, runner, tmp_path):
        """Starting PyMOL to discover a typo costs seconds; the check is free."""
        source = tmp_path / "x.pdb"
        source.write_text("ATOM\n")
        result = runner.invoke(
            cli, ["cartoon", str(source), str(tmp_path / "o.inc"), "--rep", "ballandstick"]
        )
        assert result.exit_code != 0
        assert "is not one of" in result.output

    def test_source_and_output_are_required_unless_check(self, runner):
        result = runner.invoke(cli, ["cartoon"])
        assert result.exit_code != 0
        assert "required unless --check" in result.output

    def test_options_reach_cartoon_inc_unaltered(self, runner, tmp_path, monkeypatch):
        """The command is a pass-through; anything it quietly rewrites is a
        surprise waiting to happen.
        """
        import quiltwright.pymol as mod

        seen: dict = {}

        def fake(source, out, **kwargs):
            seen["source"] = source
            seen["out"] = out
            seen.update(kwargs)
            Path(out).write_text("")
            return mod.CartoonResult(
                path=Path(out),
                identifier="thing",
                enclosing_radius=12.5,
                centre=(0.0, 0.0, 0.0),
                vertices=3,
                faces=1,
                rep=kwargs["rep"],
                backend="subprocess",
            )

        monkeypatch.setattr(mod, "cartoon_inc", fake)
        source = tmp_path / "x.cif.gz"
        source.write_text("")
        result = runner.invoke(
            cli,
            [
                "cartoon",
                str(source),
                str(tmp_path / "o.inc"),
                "--rep",
                "surface",
                "--selection",
                "chain A",
                "--assembly",
                "",
                "--transparency",
                "0.4",
                "--surface-quality",
                "-1",
                "--name",
                "custom",
                "--raw",
            ],
        )
        assert result.exit_code == 0, result.output
        assert seen["rep"] == "surface"
        assert seen["selection"] == "chain A"
        assert seen["assembly"] == ""
        assert seen["transparency"] == pytest.approx(0.4)
        assert seen["surface_quality"] == -1
        assert seen["name"] == "custom"
        # --raw is the negation of coalescing, which is on by default.
        assert seen["coalesce"] is False

    def test_colour_none_is_passed_as_none_not_the_string(self, runner, tmp_path, monkeypatch):
        """ "none" on a command line has to become Python's None, or PyMOL is
        asked to colour everything with a colour called "none".
        """
        import quiltwright.pymol as mod

        seen: dict = {}

        def fake(source, out, **kwargs):
            seen.update(kwargs)
            Path(out).write_text("")
            return mod.CartoonResult(
                path=Path(out),
                identifier="t",
                enclosing_radius=1.0,
                centre=(0.0, 0.0, 0.0),
                vertices=0,
                faces=0,
                rep="cartoon",
                backend="module",
            )

        monkeypatch.setattr(mod, "cartoon_inc", fake)
        source = tmp_path / "x.pdb"
        source.write_text("")
        result = runner.invoke(
            cli, ["cartoon", str(source), str(tmp_path / "o.inc"), "--color", "none"]
        )
        assert result.exit_code == 0, result.output
        assert seen["color"] is None

    def test_the_summary_says_how_to_mount_what_was_written(self, runner, tmp_path, monkeypatch):
        """The next thing anyone does with the file is include it, so the
        command hands over the line that does it.
        """
        import quiltwright.pymol as mod

        def fake(source, out, **kwargs):
            Path(out).write_text("x" * 2048)
            return mod.CartoonResult(
                path=Path(out),
                identifier="_2omf",
                enclosing_radius=46.97,
                centre=(0.0, 0.0, 0.0),
                vertices=38256,
                faces=75792,
                rep="cartoon",
                backend="subprocess",
            )

        monkeypatch.setattr(mod, "cartoon_inc", fake)
        source = tmp_path / "2omf.cif.gz"
        source.write_text("")
        result = runner.invoke(cli, ["cartoon", str(source), str(tmp_path / "2omf.inc")])
        assert result.exit_code == 0, result.output
        assert "Vitrine_Mount(_2omf, _2omf_enclosing_radius)" in result.output
        assert "75792 faces" in result.output
        assert "46.970" in result.output


# ---------------------------------------------------------------------------
# quiltwright mesh
# ---------------------------------------------------------------------------


class TestMesh:
    """``quiltwright mesh`` -- the auto-framed Cycles render.

    Blender is never started here.  What this layer owes the user is that the
    two decisions the command makes on its own -- the framing camera and the
    quilt geometry -- follow from what was asked for, and that a missing
    Blender reads as advice rather than a traceback.
    """

    @pytest.fixture
    def stub(self, monkeypatch, tmp_path):
        """Stand in for Blender: fixed bounds in, recorded call out."""
        import numpy as np

        from quiltwright.cli import cmd_mesh as mod

        seen: dict = {}

        def fake_bounds(source, **kwargs):
            seen["source"] = source
            return np.array([-1.0, -2.0, -3.0]), np.array([1.0, 2.0, 3.0])

        def fake_render(source, spec, camera, **kwargs):
            seen["spec"] = spec
            seen["camera"] = camera
            seen.update(kwargs)
            return np.zeros((4, 4, 3), dtype="uint8")

        def fake_save(quilt, stem, spec):
            seen["stem"] = str(stem)
            return tmp_path / spec.filename(Path(stem).name)

        monkeypatch.setattr(mod, "mesh_bounds", fake_bounds)
        monkeypatch.setattr(mod, "render_cycles_quilt", fake_render)
        monkeypatch.setattr(mod, "save_quilt", fake_save)
        return seen

    def _source(self, tmp_path, name: str = "model.glb") -> Path:
        source = tmp_path / name
        source.write_text("")
        return source

    def test_a_blend_is_refused_with_the_reason(self, runner, tmp_path):
        """A .blend carries its own camera, so there is nothing to frame --
        and the message has to say what to do instead, not just "no".
        """
        result = runner.invoke(cli, ["mesh", str(self._source(tmp_path, "scene.blend"))])
        assert result.exit_code != 0
        assert "carries its own camera" in result.output
        assert "render_cycles_quilt" in result.output

    def test_the_camera_is_framed_on_the_measured_bounds(self, runner, tmp_path, stub):
        """The whole point of the command: the eye is placed from what the
        mesh measured, aimed at its centre, which is the focal plane.
        """
        result = runner.invoke(cli, ["mesh", str(self._source(tmp_path))])
        assert result.exit_code == 0, result.output
        camera = stub["camera"]
        assert camera.look_at == (0.0, 0.0, 0.0)  # bounds centre
        assert camera.location[1] < 0  # default view direction, 0 -1 0
        assert camera.fov == 14.0

    def test_view_direction_survives_negative_components(self, runner, tmp_path, stub):
        """``--view-direction 0.5 -1 0.3`` is the documented three-quarter
        view, and a bare ``-1`` is exactly what an option parser eats.
        """
        result = runner.invoke(
            cli, ["mesh", str(self._source(tmp_path)), "--view-direction", "0.5", "-1", "0.3"]
        )
        assert result.exit_code == 0, result.output
        x, y, z = stub["camera"].location
        assert x > 0 and y < 0 and z > 0

    def test_still_is_one_view_at_the_devices_aspect(self, runner, tmp_path, stub):
        """The literal this replaced was 880x1100 whatever --device said, so
        a landscape panel's still came out portrait.
        """
        result = runner.invoke(
            cli, ["mesh", str(self._source(tmp_path)), "--device", "16-landscape", "--still"]
        )
        assert result.exit_code == 0, result.output
        spec = stub["spec"]
        assert spec.n_views == 1
        assert spec.quilt_width > spec.quilt_height
        assert "gallery/model" in stub["stem"]

    def test_preview_quarters_the_quilt_and_says_so(self, runner, tmp_path, stub):
        result = runner.invoke(cli, ["mesh", str(self._source(tmp_path)), "--preview"])
        assert result.exit_code == 0, result.output
        assert stub["spec"].quilt_width == QUILT_PRESETS["portrait"].scaled(0.25).quilt_width
        assert "-preview" in stub["stem"]

    def test_render_options_are_passed_through_unaltered(self, runner, tmp_path, stub):
        result = runner.invoke(
            cli,
            [
                "mesh",
                str(self._source(tmp_path)),
                "--samples",
                "37",
                "--compute",
                "cpu",
                "--view-transform",
                "AgX",
            ],
        )
        assert result.exit_code == 0, result.output
        assert stub["samples"] == 37
        assert stub["device"] == "cpu"
        assert stub["view_transform"] == "AgX"

    def test_a_rig_name_stays_a_name_and_a_path_becomes_a_path(self, runner, tmp_path, stub):
        """``--lighting`` is overloaded: three rig names, anything else an
        environment map.  Handing Cycles the string "sky" as a filename would
        fail deep inside Blender.
        """
        runner.invoke(cli, ["mesh", str(self._source(tmp_path)), "--lighting", "sky"])
        assert stub["lighting"] == "sky"

        hdri = tmp_path / "sunset.hdr"
        hdri.write_text("")
        runner.invoke(cli, ["mesh", str(self._source(tmp_path)), "--lighting", str(hdri)])
        assert stub["lighting"] == hdri

    def test_a_missing_blender_reads_as_advice(self, runner, tmp_path, monkeypatch):
        """The failure every first run risks; a traceback would bury the fix."""
        from quiltwright.cli import cmd_mesh as mod

        def fake_bounds(source, **kwargs):
            raise RuntimeError("No blender binary on PATH: brew install --cask blender")

        monkeypatch.setattr(mod, "mesh_bounds", fake_bounds)
        result = runner.invoke(cli, ["mesh", str(self._source(tmp_path))])
        assert result.exit_code != 0
        assert "brew install --cask blender" in result.output
        assert "Traceback" not in result.output


# ---------------------------------------------------------------------------
# quiltwright probe
# ---------------------------------------------------------------------------


class TestProbe:
    """``quiltwright probe`` -- the plane sweep, from the shell.

    POV-Ray is never started here.  What this layer owes the user is the grid
    it sweeps, the camera it sweeps through, and -- because the number is
    quietly wrong on any scene with a backdrop that runs to the horizon --
    saying so when the sweep never closed.
    """

    @pytest.fixture
    def stub(self, monkeypatch):
        """Stand in for POV-Ray: a curve that saturates, and a recorded call."""
        seen: dict = {}

        def fake_sweep(scene, camera, distances, **kwargs):
            seen["scene"] = scene
            seen["camera"] = camera
            seen["distances"] = list(distances)
            seen.update(kwargs)
            return seen.get("curve", [(10.0, 0.0), (20.0, 0.5), (30.0, 0.8), (5000.0, 0.8)])

        monkeypatch.setattr("quiltwright.povray.depth_sweep", fake_sweep)
        return seen

    def _scene(self, tmp_path) -> Path:
        scene = tmp_path / "thing.pov"
        scene.write_text("// a scene\n")
        return scene

    def _args(self, scene, *extra):
        return ["probe", str(scene), "--eye", "0", "35", "-95", "--aim", "0", "18", "0", *extra]

    def test_it_sweeps_through_the_camera_it_was_given(self, runner, tmp_path, stub):
        result = runner.invoke(cli, self._args(self._scene(tmp_path), "--fov", "55.32"))
        assert result.exit_code == 0, result.output
        assert stub["camera"].location == (0.0, 35.0, -95.0)
        assert stub["camera"].look_at == (0.0, 18.0, 0.0)
        assert stub["camera"].fov == 55.32

    def test_the_grid_ends_at_infinity(self, runner, tmp_path, stub):
        """The last plane is what separates sky from far content; without it
        the residual that never occludes is invisible.
        """
        result = runner.invoke(cli, self._args(self._scene(tmp_path), "--probes", "10"))
        assert result.exit_code == 0, result.output
        grid = stub["distances"]
        assert len(grid) == 11
        assert grid[-1] == 5000.0
        assert grid[-2] == 400.0  # --max-distance default

    def test_min_distance_moves_the_near_end(self, runner, tmp_path, stub):
        result = runner.invoke(
            cli,
            self._args(
                self._scene(tmp_path),
                "--min-distance",
                "700",
                "--max-distance",
                "1600",
                "--probes",
                "5",
            ),
        )
        assert result.exit_code == 0, result.output
        assert stub["distances"][0] == 700.0
        assert stub["distances"][-2] == 1600.0

    def test_an_inverted_range_is_refused(self, runner, tmp_path, stub):
        result = runner.invoke(
            cli, self._args(self._scene(tmp_path), "--min-distance", "900", "--max-distance", "400")
        )
        assert result.exit_code != 0
        assert "must be less than" in result.output

    def test_it_reports_the_measured_depths(self, runner, tmp_path, stub):
        result = runner.invoke(cli, self._args(self._scene(tmp_path)))
        assert "near = 20.0" in result.output
        assert "far = 30.0" in result.output

    def test_a_sweep_that_never_closed_says_so(self, runner, tmp_path, stub):
        """A sea keeps taking a little more of the frame at every distance, so
        the 95% rule returns the end of the sweep -- a number that reads like
        a measurement and is not one.
        """
        stub["curve"] = [(100.0, 0.1), (200.0, 0.2), (300.0, 0.3), (400.0, 0.4), (5000.0, 0.4)]
        result = runner.invoke(cli, self._args(self._scene(tmp_path)))
        assert result.exit_code == 0, result.output
        assert "never closed" in result.output
        assert "knee" in result.output

    def test_a_closed_sweep_stays_quiet(self, runner, tmp_path, stub):
        result = runner.invoke(cli, self._args(self._scene(tmp_path)))
        assert "never closed" not in result.output

    def test_a_low_quality_probe_is_warned_about(self, runner, tmp_path, stub):
        """Below +Q8 POV-Ray disables transparency, so glass reads solid and
        the sweep closes early on a scene that has windows.
        """
        result = runner.invoke(cli, self._args(self._scene(tmp_path), "--quality", "3"))
        assert result.exit_code == 0, result.output
        assert "disables transparency" in result.output

    def test_rows_prints_the_curve_to_fit(self, runner, tmp_path, stub):
        result = runner.invoke(cli, self._args(self._scene(tmp_path), "--rows"))
        assert "20.00   50.00%" in result.output

    def test_povray_failures_read_as_advice(self, runner, tmp_path, monkeypatch):
        def fake_sweep(*args, **kwargs):
            raise RuntimeError("calibration frame is not uniform")

        monkeypatch.setattr("quiltwright.povray.depth_sweep", fake_sweep)
        result = runner.invoke(cli, self._args(self._scene(tmp_path)))
        assert result.exit_code != 0
        assert "calibration frame is not uniform" in result.output
        assert "Traceback" not in result.output
