"""Apple Dynamic Desktop HEIC packer.

A Dynamic Desktop is one HEIF file holding several stills plus XMP on
image 0 that tells macOS which frame to show.  The payload is a base64
binary plist in the ``apple_desktop`` namespace:

* ``apr`` -- light/dark appearance (two frames)
* ``solar`` -- sun altitude/azimuth (any number of frames)
* ``h24`` -- fraction of the local day (any number of frames)

None of this is POV-Ray's ``clock``.  That identifier is POV-Ray's
*animation* parameter (``+K`` / ``Clock=``): it steps a scene through
an internal 0-1 (or ``Initial_Clock``-``Final_Clock``) loop.  It has
nothing to do with the Mac's wall clock or the sun.  Real time of day
lives only in this metadata, which macOS reads against Location Services
(solar) or the system clock (``h24``).

Frames are finished RGB stills -- woven ``_native_`` holograms or ordinary
2D renders.  Woven frames encode lossless with 4:4:4 chroma; photographic
HEVC 4:2:0 would mix the per-channel views and destroy the weave.

Typical usage::

    from quiltwright.dynamic import AppearanceMap, DynamicSpec, save_dynamic_heic

    spec = DynamicSpec.from_appearance(light_rgb, dark_rgb, lossless=True)
    save_dynamic_heic(spec, "scene.heic")

Part of Quiltwright -- https://github.com/Flux-Frontiers/quiltwright
Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import base64
import json
import plistlib
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

#: ``<stem>_native_<serial>``, as written by ``quiltwright weave``.
NATIVE_STEM = re.compile(r"_native_(.+)$")

_APPLE_NS = "http://ns.apple.com/namespace/1.0/"
_XMP_TAG = {
    "apr": "apple_desktop:apr",
    "solar": "apple_desktop:solar",
    "h24": "apple_desktop:h24",
}


def is_woven_stem(stem: str) -> bool:
    """Whether *stem* names a woven native frame.

    :param stem: Filename without its extension.
    :return: ``True`` if the stem ends in ``_native_<serial>``.
    """
    return NATIVE_STEM.search(stem) is not None


@dataclass(frozen=True)
class AppearanceMap:
    """Image indices for System Settings Light / Dark (static).

    :param light: Index of the light-appearance frame.
    :param dark: Index of the dark-appearance frame.
    """

    light: int = 0
    dark: int = 1


@dataclass(frozen=True)
class SolarItem:
    """One solar anchor: which frame to show at this sun position.

    :param index: Frame index in the HEIC.
    :param altitude: Sun altitude in degrees (horizon = 0, zenith = 90).
    :param azimuth: Sun azimuth in degrees, ``[0, 360)``.
    """

    index: int
    altitude: float
    azimuth: float


@dataclass(frozen=True)
class TimeItem:
    """One time-of-day anchor: which frame to show at this fraction of the day.

    :param index: Frame index in the HEIC.
    :param time: Fraction of the local day, ``[0, 1)``.  Midnight is 0,
        noon is 0.5.  This is the Mac's clock, not POV-Ray's ``clock``.
    """

    index: int
    time: float


@dataclass(frozen=True)
class DynamicSpec:
    """Frames plus the metadata that makes a HEIC a Dynamic Desktop.

    Exactly one of *solar* or *times* may be set; if both are empty this
    is appearance-only.  *appearance* is always required (solar/h24 files
    still need Light/Dark fallbacks).

    :param frames: RGB ``uint8`` arrays, identical ``(H, W, 3)``.
    :param appearance: Light/Dark fallbacks.
    :param solar: Solar anchors, or ``()``.
    :param times: Time-of-day anchors, or ``()``.
    :param lossless: Encode without HEVC 4:2:0.  Required for woven frames.
    """

    frames: tuple[np.ndarray, ...]
    appearance: AppearanceMap
    solar: tuple[SolarItem, ...] = ()
    times: tuple[TimeItem, ...] = ()
    lossless: bool = False

    @classmethod
    def from_appearance(
        cls,
        light: np.ndarray,
        dark: np.ndarray,
        *,
        lossless: bool = False,
    ) -> DynamicSpec:
        """Two-frame Light/Dark wallpaper.

        :param light: RGB frame for light appearance.
        :param dark: RGB frame for dark appearance.
        :param lossless: See the class docstring.
        :return: An appearance-only spec.
        """
        return cls(
            frames=(np.asarray(light), np.asarray(dark)),
            appearance=AppearanceMap(0, 1),
            lossless=lossless,
        )


def parse_clock_time(value: str) -> float:
    """Parse ``HH:MM`` or ``HH:MM:SS`` to a fraction of a 24-hour day.

    :param value: A wall-clock time, 24-hour.
    :return: ``seconds / 86400``.
    :raises ValueError: If the string is not a time, or is out of range.
    """
    parts = value.strip().split(":")
    if len(parts) not in (2, 3):
        raise ValueError(f"time must be HH:MM or HH:MM:SS, got {value!r}")
    try:
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = int(parts[2]) if len(parts) == 3 else 0
    except ValueError as exc:
        raise ValueError(f"time must be HH:MM or HH:MM:SS, got {value!r}") from exc
    if not (0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60):
        raise ValueError(f"time out of range: {value!r}")
    return (hours * 3600 + minutes * 60 + seconds) / 86400.0


def validate_spec(spec: DynamicSpec) -> None:
    """Raise ``ValueError`` if *spec* cannot be a Dynamic Desktop.

    :param spec: The spec to check.
    """
    frames = spec.frames
    if len(frames) < 2:
        raise ValueError(f"a Dynamic Desktop needs at least 2 frames, got {len(frames)}")
    if spec.solar and spec.times:
        raise ValueError("solar and time-of-day metadata cannot both be set")
    shape = None
    for i, frame in enumerate(frames):
        arr = np.asarray(frame)
        if arr.ndim != 3 or arr.shape[2] < 3:
            raise ValueError(f"frame {i} must be RGB (H, W, 3), got {arr.shape}")
        if shape is None:
            shape = arr.shape[:2]
        elif arr.shape[:2] != shape:
            raise ValueError(
                f"frame {i} is {arr.shape[1]}x{arr.shape[0]}, expected {shape[1]}x{shape[0]}"
            )
    n = len(frames)
    for label, idx in (("light", spec.appearance.light), ("dark", spec.appearance.dark)):
        if not 0 <= idx < n:
            raise ValueError(f"appearance {label} index {idx} is out of range 0..{n - 1}")
    for item in spec.solar:
        if not 0 <= item.index < n:
            raise ValueError(f"solar index {item.index} is out of range 0..{n - 1}")
        if not -90.0 <= item.altitude <= 90.0:
            raise ValueError(f"solar altitude {item.altitude} is not in [-90, 90]")
        if not 0.0 <= item.azimuth < 360.0:
            raise ValueError(f"solar azimuth {item.azimuth} is not in [0, 360)")
    for item in spec.times:
        if not 0 <= item.index < n:
            raise ValueError(f"time index {item.index} is out of range 0..{n - 1}")
        if not 0.0 <= item.time < 1.0:
            raise ValueError(f"time fraction {item.time} is not in [0, 1)")


def appearance_plist(mapping: AppearanceMap) -> bytes:
    """Binary plist for ``apple_desktop:apr``.

    :param mapping: Light/Dark image indices.
    :return: Apple binary property list bytes.
    """
    return plistlib.dumps({"l": mapping.light, "d": mapping.dark}, fmt=plistlib.FMT_BINARY)


def solar_plist(items: tuple[SolarItem, ...], appearance: AppearanceMap) -> bytes:
    """Binary plist for ``apple_desktop:solar``.

    Matches the decoded shape of Apple's ``The Lake.heic``: ``ap`` fallbacks
    plus ``si`` anchors with ``i`` / ``a`` / ``z``.

    :param items: Solar anchors, in any order.
    :param appearance: Light/Dark fallbacks.
    :return: Apple binary property list bytes.
    """
    body = {
        "ap": {"l": appearance.light, "d": appearance.dark},
        "si": [{"i": it.index, "a": float(it.altitude), "z": float(it.azimuth)} for it in items],
    }
    return plistlib.dumps(body, fmt=plistlib.FMT_BINARY)


def time_plist(items: tuple[TimeItem, ...], appearance: AppearanceMap) -> bytes:
    """Binary plist for ``apple_desktop:h24``.

    :param items: Time-of-day anchors.
    :param appearance: Light/Dark fallbacks.
    :return: Apple binary property list bytes.
    """
    body = {
        "ap": {"l": appearance.light, "d": appearance.dark},
        "ti": [{"i": it.index, "t": float(it.time)} for it in items],
    }
    return plistlib.dumps(body, fmt=plistlib.FMT_BINARY)


def xmp_payload(tag: str, plist_bytes: bytes) -> bytes:
    """XMP packet wrapping a base64 plist as ``apple_desktop:<tag>``.

    :param tag: ``apr``, ``solar``, or ``h24``.
    :param plist_bytes: Binary plist from the matching ``*_plist`` helper.
    :return: UTF-8 XMP packet.
    """
    if tag not in _XMP_TAG:
        raise ValueError(f"unknown apple_desktop tag {tag!r}")
    b64 = base64.b64encode(plist_bytes).decode("ascii")
    # Compact on one attribute so ImageIO and pillow-heif both see it.
    xml = (
        '<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        f'<rdf:Description xmlns:apple_desktop="{_APPLE_NS}"\n'
        f' apple_desktop:{tag}="{b64}"/>\n'
        "</rdf:RDF>\n"
        "</x:xmpmeta>\n"
        '<?xpacket end="w"?>\n'
    )
    return xml.encode("utf-8")


def metadata_for(spec: DynamicSpec) -> tuple[str, bytes]:
    """Pick the XMP tag and plist for *spec*.

    :param spec: A validated spec.
    :return: ``(tag, xmp_bytes)``.
    """
    if spec.solar:
        return "solar", xmp_payload("solar", solar_plist(spec.solar, spec.appearance))
    if spec.times:
        return "h24", xmp_payload("h24", time_plist(spec.times, spec.appearance))
    return "apr", xmp_payload("apr", appearance_plist(spec.appearance))


def _require_heif():
    """Import pillow-heif or raise the extras hint.

    :return: The ``pillow_heif`` module.
    :raises RuntimeError: If the extra is not installed.
    """
    try:
        import pillow_heif
    except ImportError as exc:
        raise RuntimeError(
            "Encoding a Dynamic Desktop HEIC needs pillow-heif.\n"
            "Install with:  pip install 'quiltwright[heic]'\n"
            "            or:  poetry install --extras heic"
        ) from exc
    return pillow_heif


def save_dynamic_heic(spec: DynamicSpec, path: str | Path) -> Path:
    """Write a Dynamic Desktop HEIC.

    :param spec: Frames and metadata.
    :param path: Output path (``.heic``).
    :return: The written path.
    :raises RuntimeError: If pillow-heif is not installed.
    :raises ValueError: If *spec* is invalid.
    """
    validate_spec(spec)
    pillow_heif = _require_heif()
    pillow_heif.register_heif_opener()
    from PIL import Image

    _, xmp = metadata_for(spec)
    images = [Image.fromarray(np.asarray(f)[..., :3].astype(np.uint8)) for f in spec.frames]
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    save_kw: dict = {
        "format": "HEIF",
        "save_all": True,
        "append_images": images[1:],
        "xmp": xmp,
    }
    if spec.lossless:
        # quality=-1 is pillow-heif's lossless HEVC; chroma 444 keeps the
        # per-channel views of a woven frame from being subsampled together.
        save_kw["quality"] = -1
        save_kw["chroma"] = 444
    else:
        save_kw["quality"] = 95
    images[0].save(out, **save_kw)
    return out


def read_dynamic_metadata(path: str | Path) -> dict:
    """Decode ``apple_desktop`` metadata from a Dynamic Desktop HEIC.

    :param path: A ``.heic`` written by :func:`save_dynamic_heic`, or one
        of Apple's.
    :return: The decoded plist as a plain dict, plus ``tag``.
    :raises RuntimeError: If pillow-heif is not installed.
    :raises ValueError: If no ``apple_desktop`` tag is present.
    """
    pillow_heif = _require_heif()
    heif = pillow_heif.open_heif(path)
    xmp = heif.info.get("xmp") or heif.info.get("XMP")
    if not xmp:
        raise ValueError(f"{path} has no XMP")
    text = xmp.decode("utf-8", "replace") if isinstance(xmp, bytes) else str(xmp)
    for tag in ("solar", "h24", "apr"):
        key = f"apple_desktop:{tag}"
        match = re.search(key + r'\s*=\s*"([^"]+)"', text)
        if match is None:
            continue
        raw = base64.b64decode(match.group(1))
        body = plistlib.loads(raw)
        return {"tag": tag, "plist": body, "n_images": len(heif)}
    raise ValueError(f"{path} has no apple_desktop metadata")


def _load_rgb(path: Path) -> np.ndarray:
    """Load one still as RGB uint8.

    :param path: An image file.
    :return: ``(H, W, 3)`` array.
    """
    from PIL import Image

    return np.asarray(Image.open(path).convert("RGB"))


def spec_from_paths(
    paths: list[Path],
    *,
    appearance: AppearanceMap,
    solar: tuple[SolarItem, ...] = (),
    times: tuple[TimeItem, ...] = (),
    lossless: bool | None = None,
) -> DynamicSpec:
    """Build a spec from still files on disk.

    :param paths: Frame files, in HEIC order.
    :param appearance: Light/Dark fallbacks.
    :param solar: Solar anchors, or empty.
    :param times: Time-of-day anchors, or empty.
    :param lossless: ``None`` means "lossless if any stem is woven".
    :return: A :class:`DynamicSpec`.
    :raises ValueError: If a woven frame would be lossy-encoded.
    """
    frames = tuple(_load_rgb(p) for p in paths)
    woven = any(is_woven_stem(p.stem) for p in paths)
    if lossless is None:
        lossless = woven
    elif woven and not lossless:
        raise ValueError(
            "woven _native_ frames must be encoded lossless (HEVC 4:2:0 "
            "mixes the per-channel views). Pass lossless=True, or drop --lossy."
        )
    spec = DynamicSpec(
        frames=frames,
        appearance=appearance,
        solar=solar,
        times=times,
        lossless=lossless,
    )
    validate_spec(spec)
    return spec


def spec_from_json(path: str | Path, *, lossless: bool | None = None) -> DynamicSpec:
    """Load a wallpapper-shaped JSON description.

    Each entry needs ``fileName``.  Solar entries add ``altitude`` and
    ``azimuth``; time entries add ``time`` (``HH:MM`` or ``HH:MM:SS``).
    ``isPrimary`` puts that frame at index 0 (Preview's still).
    ``isForLight`` / ``isForDark`` set the appearance fallbacks.

    :param path: JSON file.  Image paths are relative to its directory.
    :param lossless: See :func:`spec_from_paths`.
    :return: A :class:`DynamicSpec`.
    """
    json_path = Path(path).expanduser().resolve()
    entries = json.loads(json_path.read_text())
    if not isinstance(entries, list) or len(entries) < 2:
        raise ValueError(f"{json_path} must be a JSON array of at least 2 frames")

    primary = next((i for i, e in enumerate(entries) if e.get("isPrimary")), 0)
    order = [primary] + [i for i in range(len(entries)) if i != primary]
    remap = {old: new for new, old in enumerate(order)}

    paths: list[Path] = []
    solar: list[SolarItem] = []
    times: list[TimeItem] = []
    light_idx = 0
    dark_idx = len(entries) - 1
    has_solar = False
    has_time = False
    for old in order:
        entry = entries[old]
        name = entry.get("fileName")
        if not name:
            raise ValueError(f"entry {old} has no fileName")
        paths.append((json_path.parent / name).resolve())
        new = remap[old]
        if entry.get("isForLight"):
            light_idx = new
        if entry.get("isForDark"):
            dark_idx = new
        if "altitude" in entry or "azimuth" in entry:
            if "altitude" not in entry or "azimuth" not in entry:
                raise ValueError(
                    f"entry {old} ({name}) needs both altitude and azimuth, "
                    f"got only {'altitude' if 'altitude' in entry else 'azimuth'}"
                )
            has_solar = True
            solar.append(
                SolarItem(
                    index=new,
                    altitude=float(entry["altitude"]),
                    azimuth=float(entry["azimuth"]),
                )
            )
        if "time" in entry:
            has_time = True
            times.append(TimeItem(index=new, time=parse_clock_time(str(entry["time"]))))
    if has_solar and has_time:
        raise ValueError(f"{json_path} mixes altitude/azimuth with time")
    return spec_from_paths(
        paths,
        appearance=AppearanceMap(light=light_idx, dark=dark_idx),
        solar=tuple(solar),
        times=tuple(times),
        lossless=lossless,
    )
