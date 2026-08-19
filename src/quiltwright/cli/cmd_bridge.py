"""
CLI command: ``quiltwright bridge`` -- inspect and restart Looking Glass Bridge.

Bridge is the one component in this pipeline that fails *dishonestly*. It
keeps its HTTP port open and keeps answering ``enter_orchestration`` with a
valid token after it has crashed internally, so a cast against a dead daemon
reports success at every step and the glass stays black. Every other failure
in the stack leaves an artifact you can look at; this one leaves nothing.

``bridge status`` is therefore written to distrust a bare 200. It checks, in
order, whether the port accepts a connection, whether a session can be
opened, whether Bridge will enumerate its output devices, and whether any of
those is a Looking Glass rather than an ordinary monitor -- and it reports a
*verdict*, because "answered but listed no panels" is the signature of the
crashed-but-listening state and is easy to misread as success.

``bridge reset`` is the fix for that state, and the only one: Bridge's own
menu restart spawns a replacement that inherits the wedge. It terminates
every Bridge process, relaunches the app, and waits for the port to answer.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import glob
import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import click

from quiltwright.cli.main import cli

#: Where Bridge installs itself. Globbed rather than pinned: the version is
#: in the bundle name (``Looking Glass Bridge 2.6.3.app``).
_APP_GLOB = "/Applications/Looking Glass Bridge*.app"

#: Substring identifying Bridge's own processes, as opposed to unrelated
#: things with "bridge" in the name (``XProtectBridgeService`` among them).
_PROCESS_MATCH = "LookingGlassBridge"


def _port_open(url: str, timeout: float = 3.0) -> bool:
    """Whether something is listening on the Bridge port.

    :param url: Bridge base URL.
    :param timeout: Connect timeout, in seconds.
    :return: ``True`` if a TCP connection succeeds.
    """
    host, _, port = url.rsplit("/", 1)[-1].partition(":")
    sock = socket.socket()
    sock.settimeout(timeout)
    try:
        sock.connect((host or "localhost", int(port or 33334)))
        return True
    except OSError:
        return False
    finally:
        sock.close()


def _put(url: str, endpoint: str, payload: dict, timeout: float) -> dict | None:
    """One Bridge request, returning ``None`` rather than raising.

    Bridge answers an unrecognised endpoint, and a wrong HTTP verb, with
    ``200 OK`` and an empty body -- so an empty response is reported as an
    empty dict, distinct from ``None`` for "could not be reached at all".

    :param url: Bridge base URL.
    :param endpoint: Endpoint name.
    :param payload: JSON body.
    :param timeout: Per-request timeout, in seconds.
    :return: Decoded JSON, ``{}`` for an empty body, or ``None`` on failure.
    """
    request = urllib.request.Request(
        f"{url}/{endpoint}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError, TimeoutError):
        return None
    return json.loads(body) if body.strip() else {}


def _bridge_pids() -> list[int]:
    """PIDs of every running Bridge process.

    :return: PIDs, including the crash handlers Bridge spawns.
    """
    try:
        out = subprocess.run(
            ["ps", "-Ao", "pid,command"], capture_output=True, timeout=10, check=True
        ).stdout.decode("utf-8", "replace")
    except (subprocess.SubprocessError, OSError):
        return []
    pids = []
    for line in out.splitlines()[1:]:
        pid, _, command = line.strip().partition(" ")
        if _PROCESS_MATCH in command or (
            "Looking Glass Bridge" in command and "crashpad_handler" in command
        ):
            if pid.isdigit():
                pids.append(int(pid))
    return pids


@cli.group("bridge")
def bridge_group() -> None:
    """Inspect and restart Looking Glass Bridge.

    \b
    Examples:
      quiltwright bridge status    # is it actually able to draw?
      quiltwright bridge reset     # kill and relaunch a wedged daemon
    """


@bridge_group.command("status")
@click.option("--bridge-url", default=None, help="Bridge HTTP API base URL.")
@click.option(
    "--timeout",
    type=float,
    default=5.0,
    show_default=True,
    help="Per-request timeout. A wedged Bridge hangs rather than refusing, "
    "so this is what separates 'slow' from 'dead'.",
)
def status_cmd(bridge_url: str | None, timeout: float) -> None:
    """Report whether Bridge is running, responsive, and seeing a panel.

    Exits non-zero if Bridge is unusable, so this can gate a cast in a
    script.
    """
    from quiltwright.lfd import BRIDGE_URL

    url = bridge_url or BRIDGE_URL
    pids = _bridge_pids()
    click.echo(f"Bridge at {url}")
    click.echo(f"  processes    {len(pids)} running" + (f" (pids {pids})" if pids else ""))

    if not _port_open(url):
        click.echo("  port         closed")
        click.echo("\nVerdict: NOT RUNNING. Launch Looking Glass Bridge, or `bridge reset`.")
        raise SystemExit(1)
    click.echo("  port         open")

    session = _put(url, "enter_orchestration", {"name": "quiltwright-status"}, timeout)
    if session is None:
        click.echo(f"  session      no response within {timeout:g}s")
        click.echo(
            "\nVerdict: WEDGED. The port is open but Bridge is not answering "
            "-- it has most likely crashed while still holding the socket.\n"
            "Fix: quiltwright bridge reset"
        )
        raise SystemExit(1)

    token = session.get("payload", {}).get("value", "")
    if not token:
        click.echo("  session      refused (no orchestration token)")
        click.echo("\nVerdict: UNUSABLE. Bridge answered but would not open a session.")
        raise SystemExit(1)
    click.echo(f"  session      ok ({token[:8]}...)")

    devices = _put(url, "available_output_devices", {"orchestration": token}, timeout)
    if devices is None:
        click.echo("  devices      no response")
        click.echo("\nVerdict: WEDGED mid-session.\nFix: quiltwright bridge reset")
        raise SystemExit(1)

    heads = (devices.get("payload", {}).get("value", {}) or {}).items()
    panels = 0
    click.echo(f"  devices      {len(list(heads))}")
    for index, entry in (devices.get("payload", {}).get("value", {}) or {}).items():
        value = entry.get("value", {})
        hardware = str(value.get("hardwareVersion", {}).get("value", "?"))
        serial = str(value.get("hwid", {}).get("value", ""))
        is_panel = hardware not in {"thirdparty", "?", ""}
        panels += is_panel
        tag = "<- Looking Glass" if is_panel else "(ordinary monitor)"
        click.echo(f"    head {index}: {hardware}{' ' + serial if serial else ''}  {tag}")

    if not panels:
        click.echo(
            "\nVerdict: NO PANEL. Bridge is healthy but sees no Looking Glass. "
            "Check the cable, or reset if it was there a moment ago."
        )
        raise SystemExit(1)
    click.echo(f"\nVerdict: HEALTHY -- {panels} panel(s) reachable.")


@bridge_group.command("reset")
@click.option(
    "--no-relaunch",
    is_flag=True,
    default=False,
    help="Terminate Bridge without starting it again.",
)
@click.option(
    "--wait",
    type=float,
    default=20.0,
    show_default=True,
    help="Seconds to wait for the relaunched daemon to answer.",
)
@click.option("--bridge-url", default=None, help="Bridge HTTP API base URL.")
def reset_cmd(no_relaunch: bool, wait: float, bridge_url: str | None) -> None:
    """Terminate Bridge and start it again.

    Bridge's own menu restart spawns a replacement that inherits the wedge,
    which is why this kills the processes outright. Anything currently
    playing on the panel stops.
    """
    from quiltwright.lfd import BRIDGE_URL

    if sys.platform != "darwin":
        raise click.ClickException("bridge reset is implemented for macOS only")

    url = bridge_url or BRIDGE_URL
    pids = _bridge_pids()
    if pids:
        click.echo(f"terminating {len(pids)} Bridge process(es): {pids}")
        # SIGTERM first so Bridge can close its socket; SIGKILL only for what
        # survives, which a genuinely wedged daemon usually does.
        for sig in (signal.SIGTERM, signal.SIGKILL):
            alive = _bridge_pids()
            if not alive:
                break
            for pid in alive:
                try:
                    os.kill(pid, sig)
                except (ProcessLookupError, PermissionError):
                    pass
            time.sleep(2.0)
        remaining = _bridge_pids()
        click.echo("  stopped" if not remaining else f"  still running: {remaining}")
    else:
        click.echo("no Bridge process was running")

    if no_relaunch:
        return

    apps = sorted(glob.glob(_APP_GLOB))
    if not apps:
        raise click.ClickException(
            f"cannot find Bridge to relaunch (looked for {_APP_GLOB}). Start it by hand."
        )
    app = Path(apps[-1])
    click.echo(f"launching {app.name}")
    try:
        subprocess.run(["open", "-a", str(app)], capture_output=True, timeout=30, check=True)
    except (subprocess.SubprocessError, OSError) as exc:
        raise click.ClickException(f"could not launch {app}: {exc}") from exc

    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if _port_open(url, timeout=1.0):
            session = _put(url, "enter_orchestration", {"name": "quiltwright-reset"}, 5.0)
            if session and session.get("payload", {}).get("value", ""):
                click.echo("  ready")
                click.echo("\nCheck it with: quiltwright bridge status")
                return
        time.sleep(1.0)
    click.echo(f"  still not answering after {wait:g}s -- give it a moment, then `bridge status`")
