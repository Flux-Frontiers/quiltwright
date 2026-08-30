"""
Looking Glass Bridge HTTP client.

Casts a saved quilt onto a connected panel, and the transport controls
(pause / resume / stop) that go with it.  Stdlib only -- importing this
module must not load VTK.

Bridge's HTTP API requires ``PUT``.  It answers ``POST`` with ``200 OK``
and an empty body, so the wrong verb fails silently.

Re-exported from :mod:`quiltwright.lfd` for one release, so
``from quiltwright.lfd import cast_quilt`` keeps working.

Part of Quiltwright -- https://github.com/suchanek/quiltwright
Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import numpy as np

from quiltwright.quilt import QuiltSpec, save_quilt

# ---------------------------------------------------------------------------
# Casting to the display via Looking Glass Bridge
# ---------------------------------------------------------------------------

#: Default address of the Looking Glass Bridge HTTP API (Bridge >= 2.2).
BRIDGE_URL = "http://localhost:33334"


def bridge_post(bridge_url: str, endpoint: str, payload: dict, timeout: float) -> dict:
    """Send a JSON payload to a Bridge endpoint and decode the response.

    Bridge's HTTP API expects ``PUT``.  It answers ``POST`` with ``200 OK``
    and an *empty* body, so using the wrong verb fails silently: the caller
    reads back no orchestration token and every later call is a no-op.
    """
    req = urllib.request.Request(
        f"{bridge_url}/{endpoint}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode()
    return json.loads(body) if body else {}


def enter_orchestration(bridge_url: str, timeout: float) -> str:
    """Enter (or rejoin) the default Bridge orchestration session.

    Bridge scopes all playback control to an orchestration session; calling
    ``enter_orchestration`` again while one is already active returns the
    *same* token rather than starting a new session, so every helper in this
    module can call this independently without stepping on the others.

    :return: The orchestration token required by every other Bridge call.
    """
    resp = bridge_post(bridge_url, "enter_orchestration", {"name": "default"}, timeout)
    token = resp.get("payload", {}).get("value", "")
    if not token:
        raise RuntimeError(
            f"Looking Glass Bridge at {bridge_url} returned no orchestration token "
            f"(response: {resp!r}).  Is Bridge running and >= 2.2?"
        )
    return token


def cast_quilt(
    quilt_path: str | Path,
    spec: QuiltSpec,
    *,
    bridge_url: str = BRIDGE_URL,
    playlist: str = "quiltwright",
    timeout: float = 10.0,
    head_index: int = -1,
) -> dict:
    """Show a saved quilt on the connected Looking Glass via Bridge.

    Requires `Looking Glass Bridge <https://lookingglassfactory.com/software/looking-glass-bridge>`_
    (>= 2.2) running on the machine the display is plugged into.  Follows
    Bridge's orchestration sequence: enter orchestration, show the display
    window, create a playlist holding the quilt, and play it.

    :param quilt_path: Path to a quilt PNG on the *Bridge host's* filesystem.
    :param spec: Quilt specification (tiling + aspect sent to Bridge).
    :param bridge_url: Base URL of the Bridge HTTP API.
    :param playlist: Name of the Bridge playlist to (re)create.
    :param timeout: HTTP timeout in seconds per request.
    :param head_index: Which Bridge output device to play on.  ``-1`` lets
        Bridge choose, which is right on a single-panel machine.  Bridge
        enumerates ordinary monitors alongside Looking Glass panels -- a
        laptop screen appears as ``hardwareVersion: thirdparty`` with no
        calibration -- so on a multi-display box the default can land the
        window somewhere that is not the glass.  ``available_output_devices``
        lists the indices; ``quiltwright cast --check`` prints them.
    :return: Decoded JSON response of the final ``play_playlist`` call.
    """
    token = enter_orchestration(bridge_url, timeout)

    bridge_post(
        bridge_url,
        "show_window",
        {"orchestration": token, "show_window": True, "head_index": head_index},
        timeout,
    )
    bridge_post(
        bridge_url,
        "instance_playlist",
        {"orchestration": token, "name": playlist, "loop": True},
        timeout,
    )
    bridge_post(
        bridge_url,
        "insert_playlist_entry",
        {
            "orchestration": token,
            "name": playlist,
            "index": 0,
            "uri": str(Path(quilt_path).resolve()),
            "rows": spec.rows,
            "cols": spec.columns,
            "aspect": spec.aspect,
            "view_count": spec.n_views,
            "durationMS": 20000,
            "isRGBD": 0,
        },
        timeout,
    )
    return bridge_post(
        bridge_url,
        "play_playlist",
        {"orchestration": token, "name": playlist, "head_index": head_index},
        timeout,
    )


def save_and_cast_quilt(
    quilt: np.ndarray,
    stem: str | Path,
    spec: QuiltSpec,
    *,
    cast: bool = True,
    bridge_url: str = BRIDGE_URL,
    timeout: float = 10.0,
) -> tuple[Path, str | None]:
    """Write a quilt to disk, then hand Bridge the **path** to it.

    The two calls this composes take different argument types, and the mistake
    is invisible until a panel is connected: :func:`save_quilt` takes the
    array, :func:`cast_quilt` takes a path.  Passing the array to the caster
    raises ``argument should be a str or an os.PathLike object ... not
    'ndarray'`` -- after the render, which for a ray-traced quilt is minutes
    later and the worst possible moment to find out.

    The file is confirmed on disk before Bridge is contacted, and a failed
    cast is *returned* rather than raised, so losing the display never costs
    the render.

    :param quilt: RGB array from :func:`render_quilt` or :func:`assemble_quilt`.
    :param stem: Output path *without* the quilt suffix or extension.
    :param spec: Quilt specification, used for both the filename and Bridge.
    :param cast: Whether to push the written file to the Looking Glass.
        ``False`` writes and returns without contacting Bridge.
    :param bridge_url: Base URL of the Bridge HTTP API.
    :param timeout: HTTP timeout in seconds per Bridge request.
    :return: ``(written path, error message or None)``.  The path is always
        real; a non-None error means the file is on disk but is not showing.
    """
    out = save_quilt(quilt, stem, spec)
    if not cast:
        return out, None
    if not out.exists():
        return out, f"{out} was not written"
    try:
        cast_quilt(out, spec, bridge_url=bridge_url, timeout=timeout)
    except Exception as exc:  # noqa: BLE001 - the quilt file is kept regardless
        return out, str(exc)
    return out, None


def pause_quilt(*, bridge_url: str = BRIDGE_URL, timeout: float = 10.0) -> dict:
    """Pause playback on the connected Looking Glass.

    Freezes the current frame; the playlist and its position are retained,
    so :func:`resume_quilt` continues from where it left off. This is
    Bridge's *transport control* group -- there is no ``stop_playlist`` or
    ``pause_playlist`` endpoint (a guessed endpoint name doesn't 404: Bridge
    answers with ``200 OK`` and an empty body, indistinguishable from a slow
    success unless you check that the response has no ``status`` field).
    Confirmed against the endpoint list in the official
    `bridge.js <https://github.com/Looking-Glass/bridge.js>`_ SDK source.

    :param bridge_url: Base URL of the Bridge HTTP API.
    :param timeout: HTTP timeout in seconds.
    :return: Decoded JSON response of the ``transport_control_pause`` call.
    """
    token = enter_orchestration(bridge_url, timeout)
    return bridge_post(bridge_url, "transport_control_pause", {"orchestration": token}, timeout)


def resume_quilt(*, bridge_url: str = BRIDGE_URL, timeout: float = 10.0) -> dict:
    """Resume playback after :func:`pause_quilt`.

    :param bridge_url: Base URL of the Bridge HTTP API.
    :param timeout: HTTP timeout in seconds.
    :return: Decoded JSON response of the ``transport_control_play`` call.
    """
    token = enter_orchestration(bridge_url, timeout)
    return bridge_post(bridge_url, "transport_control_play", {"orchestration": token}, timeout)


def stop_quilt(*, bridge_url: str = BRIDGE_URL, timeout: float = 10.0) -> dict:
    """Stop playback: pause the current frame and hide the display window.

    Bridge's own `bridge.js <https://github.com/Looking-Glass/bridge.js>`_
    SDK documents ``delete_playlist`` as *the* way to stop a playlist, and
    an earlier version of this function called it. In testing it reliably
    left Bridge unresponsive to every further HTTP call -- reproduced twice,
    once mid-video and once on a single still image, so it isn't a
    large-file decode race. This function deliberately avoids
    ``delete_playlist`` and reaches the same end state (nothing visible,
    playback halted) through calls already proven safe: the playlist from
    :func:`cast_quilt` is left instantiated but paused and hidden, rather
    than deleted, so :func:`cast_quilt` can safely replace it later.

    :param bridge_url: Base URL of the Bridge HTTP API.
    :param timeout: HTTP timeout in seconds.
    :return: Decoded JSON response of the final ``show_window`` call.
    """
    token = enter_orchestration(bridge_url, timeout)
    bridge_post(bridge_url, "transport_control_pause", {"orchestration": token}, timeout)
    return bridge_post(
        bridge_url,
        "show_window",
        {"orchestration": token, "show_window": False, "head_index": -1},
        timeout,
    )
