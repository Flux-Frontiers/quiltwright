"""CLI tests for ``quiltwright dynamic``.  Never writes a real wallpaper."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner
from PIL import Image

from quiltwright.cli.main import cli
from quiltwright.dynamic import AppearanceMap, DynamicSpec


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def _png(path: Path, color: tuple[int, int, int] = (1, 2, 3)) -> Path:
    Image.new("RGB", (8, 8), color).save(path)
    return path


def test_requires_exactly_one_mode(runner: CliRunner):
    result = runner.invoke(cli, ["dynamic", "-o", "out.heic"])
    assert result.exit_code != 0
    assert "--appearance" in result.output


def test_appearance_refuses_lossy_woven(runner: CliRunner, tmp_path: Path):
    light = _png(tmp_path / "day_native_LKG-J00332.png")
    dark = _png(tmp_path / "night_native_LKG-J00332.png")
    result = runner.invoke(
        cli,
        [
            "dynamic",
            "--appearance",
            str(light),
            str(dark),
            "--lossy",
            "-o",
            str(tmp_path / "x.heic"),
        ],
    )
    assert result.exit_code != 0
    assert "lossless" in result.output


def test_missing_encoder_prints_the_extra_hint(runner: CliRunner, tmp_path: Path, monkeypatch):
    import quiltwright.cli.cmd_dynamic as cmd

    light = _png(tmp_path / "a.png")
    dark = _png(tmp_path / "b.png")

    def boom(spec, path):
        raise RuntimeError("pillow-heif\npoetry install --extras heic")

    monkeypatch.setattr(cmd, "save_dynamic_heic", boom)
    result = runner.invoke(
        cli,
        ["dynamic", "--appearance", str(light), str(dark), "-o", str(tmp_path / "out.heic")],
    )
    assert result.exit_code != 0
    assert "heic" in result.output.lower()


def test_appearance_writes_when_encoder_is_stubbed(runner: CliRunner, tmp_path: Path, monkeypatch):
    import quiltwright.cli.cmd_dynamic as cmd

    light = _png(tmp_path / "a.png")
    dark = _png(tmp_path / "b.png")
    out = tmp_path / "out.heic"
    seen: list[DynamicSpec] = []

    def fake_save(spec, path):
        seen.append(spec)
        Path(path).write_bytes(b"heic")
        return Path(path)

    monkeypatch.setattr(cmd, "save_dynamic_heic", fake_save)
    result = runner.invoke(
        cli,
        ["dynamic", "--appearance", str(light), str(dark), "-o", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert seen[0].appearance == AppearanceMap(0, 1)
    assert "apr" in result.output
    assert out.is_file()


def test_solar_and_appearance_conflict(runner: CliRunner, tmp_path: Path):
    light = _png(tmp_path / "a.png")
    dark = _png(tmp_path / "b.png")
    cfg = tmp_path / "s.json"
    cfg.write_text("[]")
    result = runner.invoke(
        cli,
        [
            "dynamic",
            "--appearance",
            str(light),
            str(dark),
            "--solar",
            str(cfg),
            "-o",
            str(tmp_path / "out.heic"),
        ],
    )
    assert result.exit_code != 0
    assert "exactly one" in result.output
