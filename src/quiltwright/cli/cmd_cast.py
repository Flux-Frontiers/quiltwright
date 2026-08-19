"""
CLI command: ``quiltwright cast`` -- show a saved quilt on the panel.

Casting is the one step in the pipeline with no artifact to inspect
afterwards: it either lights up the glass or it does not, and when it does
not, the cause is usually somewhere other than the quilt. This command is
therefore built to *fail informatively* -- it checks the file, resolves the
tiling from the filename, and asks Bridge what it can actually see before
sending anything.

Three failure modes are worth knowing, all of them observed on real
hardware:

*Bridge answers while unable to draw.* The HTTP port stays open and
``enter_orchestration`` returns a valid token even after Bridge has crashed
internally, so a cast can report success against a daemon that will never
put a pixel on the panel. ``--check`` surfaces this by listing the heads
Bridge admits to; a Looking Glass that has vanished from that list is the
tell. Restarting Bridge is the fix.

*Another app owns the display.* Looking Glass Studio (and the Slideshow
app) hold the panel exclusively. Bridge's own window then has nothing to
draw to and the glass stays black, with every HTTP call still returning
``Completion``.

*The cast lands on the wrong head.* Bridge enumerates ordinary monitors
alongside Looking Glass panels -- a laptop screen shows up as
``hardwareVersion: thirdparty`` with no calibration. ``--head`` pins the
target when the default picks wrong; ``--check`` prints the indices.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

from pathlib import Path

import click

from quiltwright.cli.main import cli
from quiltwright.cli.options import aspect_from_filename, resolve_grid
from quiltwright.lfd import QUILT_PRESETS, QuiltSpec


def _describe_heads(bridge_url: str, timeout: float) -> list[tuple[str, str, str]]:
    """Ask Bridge which output devices it can see.

    :param bridge_url: Base URL of the Bridge HTTP API.
    :param timeout: Per-request timeout, in seconds.
    :return: ``(index, hardware_version, serial)`` per head.
    :raises click.ClickException: If Bridge cannot be reached or refuses a
        session.
    """
    from quiltwright.lfd import _bridge_post, _enter_orchestration

    try:
        token = _enter_orchestration(bridge_url, timeout)
        payload = _bridge_post(
            bridge_url, "available_output_devices", {"orchestration": token}, timeout
        )
    except Exception as exc:  # noqa: BLE001 -- surfaced verbatim to the user
        raise click.ClickException(
            f"cannot reach Looking Glass Bridge at {bridge_url}: {exc}\n"
            "Is Bridge running? If it is, it may have crashed while still "
            "holding the port -- quit and relaunch it."
        ) from exc

    def _field(value: dict, name: str) -> str:
        """Unwrap Bridge's ``{"name":..., "type":..., "value":...}`` envelope."""
        if not isinstance(value, dict):
            return ""
        return str(value.get(name, {}).get("value", ""))

    heads = []
    for index, entry in (payload.get("payload", {}).get("value", {}) or {}).items():
        value = entry.get("value", {})
        heads.append((str(index), _field(value, "hardwareVersion") or "?", _field(value, "hwid")))
    return heads


@cli.command("cast")
@click.argument(
    "quilt",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=False,
)
@click.option(
    "--preset",
    type=click.Choice(sorted(QUILT_PRESETS)),
    default=None,
    help="Quilt tiling grid and aspect, by device preset name.",
)
@click.option(
    "--grid",
    "grid_str",
    metavar="COLSxROWS",
    default=None,
    help="Quilt tiling grid, explicit (e.g. 8x6); defaults to parsing the "
    "_qs<cols>x<rows>a<aspect> filename suffix.",
)
@click.option(
    "--aspect",
    type=float,
    default=None,
    help="Tile aspect, overriding the filename's. Rarely needed -- a value "
    "disagreeing with the panel is letterboxed by it.",
)
@click.option(
    "--head",
    type=int,
    default=-1,
    show_default=True,
    help="Bridge head index to play on. -1 lets Bridge choose, which is "
    "right until it picks an ordinary monitor; run --check for the list.",
)
@click.option(
    "--playlist",
    default="quiltwright",
    show_default=True,
    help="Bridge playlist name to create or replace.",
)
@click.option(
    "--bridge-url",
    default=None,
    help="Bridge HTTP API base URL (default: http://localhost:33334).",
)
@click.option(
    "--check",
    is_flag=True,
    default=False,
    help="List the output devices Bridge can see and exit without casting. "
    "The first thing to run when the glass stays black.",
)
def cast_cmd(
    quilt: Path | None,
    preset: str | None,
    grid_str: str | None,
    aspect: float | None,
    head: int,
    playlist: str,
    bridge_url: str | None,
    check: bool,
) -> None:
    """Show a saved quilt on the connected Looking Glass.

    QUILT is a quilt PNG on this machine, normally one written by
    `save_quilt()` or `make quilt-<name>`, whose `_qs<cols>x<rows>a<aspect>`
    filename suffix supplies the tiling automatically.

    Requires Looking Glass Bridge >= 2.2 running on the machine the panel is
    plugged into. Quit Looking Glass Studio first -- it holds the display
    exclusively, and Bridge will report success while the glass stays black.

    \b
    Examples:
      # Cast a rendered quilt; tiling comes from the filename
      quiltwright cast renders/quilts/bell-jar-holo_qs8x6a1.77778.png

      # Which displays can Bridge see? Run this first when nothing appears
      quiltwright cast --check

      # Pin the panel when Bridge picks an ordinary monitor
      quiltwright cast quilt.png --head 1

      # A quilt whose filename carries no _qs suffix
      quiltwright cast plain.png --grid 8x6 --aspect 1.77778
      quiltwright cast plain.png --preset 16-landscape
    """
    from quiltwright.lfd import BRIDGE_URL, cast_quilt

    url = bridge_url or BRIDGE_URL

    if check:
        heads = _describe_heads(url, 10.0)
        if not heads:
            raise click.ClickException(
                "Bridge is reachable but reports no output devices. It is "
                "most likely wedged -- quit and relaunch it."
            )
        click.echo(f"Bridge at {url} sees {len(heads)} output device(s):")
        for index, hardware, serial in heads:
            looking_glass = hardware not in {"thirdparty", "?", ""}
            mark = "  <- Looking Glass" if looking_glass else "  (ordinary monitor)"
            click.echo(f"  head {index}: {hardware}{' ' + serial if serial else ''}{mark}")
        click.echo("\nCast to one explicitly with --head <index>.")
        return

    if quilt is None:
        raise click.UsageError("QUILT is required unless --check is given")

    columns, rows = resolve_grid(preset, grid_str, quilt.stem)
    if aspect is None:
        aspect = (
            QUILT_PRESETS[preset].aspect if preset is not None else aspect_from_filename(quilt.stem)
        )
    if aspect is None:
        raise click.UsageError(
            f"cannot determine the tile aspect from {quilt.stem!r}: pass "
            "--aspect or --preset, or use a filename ending in "
            "_qs<cols>x<rows>a<aspect>"
        )

    # quilt_width/height are what Bridge ignores (it reads the file itself)
    # but a spec should still describe the quilt it names.
    from PIL import Image

    with Image.open(quilt) as im:
        q_w, q_h = im.size
    spec = QuiltSpec(columns=columns, rows=rows, quilt_width=q_w, quilt_height=q_h, aspect=aspect)

    try:
        cast_quilt(quilt, spec, bridge_url=url, playlist=playlist, head_index=head)
    except Exception as exc:  # noqa: BLE001 -- surfaced verbatim to the user
        raise click.ClickException(
            f"cast failed: {exc}\nRun `quiltwright cast --check` to see what Bridge can reach."
        ) from exc

    click.echo(
        f"{quilt.name}  ({columns}x{rows} views, aspect {aspect:g})  ->  "
        f"playlist {playlist!r}" + (f", head {head}" if head >= 0 else ", Bridge's default head")
    )
    click.echo("Glass still black? Quit Looking Glass Studio, then `cast --check`.")
