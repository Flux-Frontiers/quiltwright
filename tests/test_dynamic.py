"""Tests for Apple Dynamic Desktop metadata and packing."""

from __future__ import annotations

import plistlib
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from quiltwright.dynamic import (
    AppearanceMap,
    DynamicSpec,
    SolarItem,
    TimeItem,
    appearance_plist,
    is_woven_stem,
    metadata_for,
    parse_clock_time,
    solar_plist,
    spec_from_json,
    spec_from_paths,
    time_plist,
    validate_spec,
    xmp_payload,
)


def _rgb(r: int, g: int, b: int, size: int = 8) -> np.ndarray:
    return np.full((size, size, 3), (r, g, b), dtype=np.uint8)


def test_woven_stem_matches_weave_filename():
    assert is_woven_stem("bell-jar-holo_native_LKG-J00332")
    assert not is_woven_stem("bell-jar-holo_qs8x6a1.77778")
    assert not is_woven_stem("plain")


def test_parse_clock_time_is_fraction_of_day():
    assert parse_clock_time("00:00") == 0.0
    assert parse_clock_time("12:00:00") == 0.5
    assert parse_clock_time("06:00") == pytest.approx(0.25)
    with pytest.raises(ValueError):
        parse_clock_time("25:00")
    with pytest.raises(ValueError):
        parse_clock_time("noon")


def test_appearance_plist_matches_apple_apr_shape():
    """Sonoma.heic / Iridescence.heic decode to {l: 0, d: 1}."""
    body = plistlib.loads(appearance_plist(AppearanceMap(0, 1)))
    assert body == {"l": 0, "d": 1}


def test_solar_plist_matches_the_lake_shape():
    """The Lake.heic uses ap fallbacks plus si[{i, a, z}]."""
    items = (
        SolarItem(0, 10.0, 100.0),
        SolarItem(1, -25.0, 70.0),
    )
    body = plistlib.loads(solar_plist(items, AppearanceMap(0, 1)))
    assert body["ap"] == {"l": 0, "d": 1}
    assert body["si"][0] == {"i": 0, "a": 10.0, "z": 100.0}
    assert body["si"][1]["i"] == 1


def test_time_plist_uses_fraction_of_day_not_pov_clock():
    items = (TimeItem(0, 0.25), TimeItem(1, 0.75))
    body = plistlib.loads(time_plist(items, AppearanceMap(0, 1)))
    assert body["ap"] == {"l": 0, "d": 1}
    assert body["ti"][0] == {"i": 0, "t": 0.25}


def test_xmp_embeds_base64_plist():
    xml = xmp_payload("apr", appearance_plist(AppearanceMap(0, 1))).decode()
    assert "apple_desktop:apr=" in xml
    assert "http://ns.apple.com/namespace/1.0/" in xml


def test_metadata_for_picks_solar_over_appearance():
    spec = DynamicSpec(
        frames=(_rgb(1, 1, 1), _rgb(2, 2, 2)),
        appearance=AppearanceMap(0, 1),
        solar=(SolarItem(0, 10, 90), SolarItem(1, -10, 270)),
    )
    tag, xmp = metadata_for(spec)
    assert tag == "solar"
    assert b"apple_desktop:solar" in xmp


def test_validate_rejects_mismatched_sizes():
    spec = DynamicSpec(
        frames=(_rgb(1, 1, 1, 8), _rgb(2, 2, 2, 4)),
        appearance=AppearanceMap(0, 1),
    )
    with pytest.raises(ValueError, match="expected"):
        validate_spec(spec)


def test_validate_rejects_solar_and_time_together():
    spec = DynamicSpec(
        frames=(_rgb(1, 1, 1), _rgb(2, 2, 2)),
        appearance=AppearanceMap(0, 1),
        solar=(SolarItem(0, 10, 90),),
        times=(TimeItem(1, 0.5),),
    )
    with pytest.raises(ValueError, match="cannot both"):
        validate_spec(spec)


def test_woven_paths_refuse_lossy(tmp_path: Path):
    light = tmp_path / "day_native_LKG-J00332.png"
    dark = tmp_path / "night_native_LKG-J00332.png"
    Image.fromarray(_rgb(200, 180, 80)).save(light)
    Image.fromarray(_rgb(20, 20, 40)).save(dark)
    with pytest.raises(ValueError, match="lossless"):
        spec_from_paths(
            [light, dark],
            appearance=AppearanceMap(0, 1),
            lossless=False,
        )
    spec = spec_from_paths([light, dark], appearance=AppearanceMap(0, 1))
    assert spec.lossless is True


def test_spec_from_json_remaps_primary_and_solar(tmp_path: Path):
    for i, color in enumerate([(10, 10, 10), (20, 20, 20), (30, 30, 30)]):
        Image.fromarray(_rgb(*color)).save(tmp_path / f"{i}.png")
    cfg = tmp_path / "solar.json"
    cfg.write_text(
        """
        [
          {"fileName": "0.png", "altitude": 10, "azimuth": 80},
          {"fileName": "1.png", "isPrimary": true, "isForLight": true,
           "altitude": 45, "azimuth": 180},
          {"fileName": "2.png", "isForDark": true, "altitude": -20, "azimuth": 350}
        ]
        """
    )
    spec = spec_from_json(cfg)
    assert spec.appearance.light == 0  # primary became index 0
    assert spec.appearance.dark == 2
    assert spec.solar[0].index == 0
    assert spec.solar[0].altitude == 45
    assert spec.solar[1].index == 1
    assert spec.solar[1].altitude == 10


def test_spec_from_json_time(tmp_path: Path):
    Image.fromarray(_rgb(1, 1, 1)).save(tmp_path / "a.png")
    Image.fromarray(_rgb(2, 2, 2)).save(tmp_path / "b.png")
    cfg = tmp_path / "hours.json"
    cfg.write_text(
        """
        [
          {"fileName": "a.png", "isPrimary": true, "isForLight": true, "time": "08:00"},
          {"fileName": "b.png", "isForDark": true, "time": "20:00:00"}
        ]
        """
    )
    spec = spec_from_json(cfg)
    assert spec.times[0].time == pytest.approx(8 / 24)
    assert spec.times[1].time == pytest.approx(20 / 24)


def test_save_without_pillow_heif_explains_the_extra(monkeypatch):
    import quiltwright.dynamic as dyn

    def boom(name):
        raise ImportError("nope")

    monkeypatch.setattr(dyn, "_require_heif", lambda: (_ for _ in ()).throw(RuntimeError("hint")))
    spec = DynamicSpec.from_appearance(_rgb(1, 1, 1), _rgb(2, 2, 2))
    with pytest.raises(RuntimeError, match="hint"):
        dyn.save_dynamic_heic(spec, "out.heic")


@pytest.mark.skipif(
    __import__("importlib").util.find_spec("pillow_heif") is None,
    reason="pillow-heif extra not installed",
)
def test_heic_roundtrip_keeps_apr_tag(tmp_path: Path):
    from quiltwright.dynamic import read_dynamic_metadata, save_dynamic_heic

    spec = DynamicSpec.from_appearance(_rgb(200, 200, 200), _rgb(10, 10, 10))
    out = save_dynamic_heic(spec, tmp_path / "apr.heic")
    info = read_dynamic_metadata(out)
    assert info["tag"] == "apr"
    assert info["plist"] == {"l": 0, "d": 1}
    assert info["n_images"] == 2
