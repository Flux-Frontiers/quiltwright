"""
CLI command: ``quiltwright wallpaper`` -- set a woven frame as the desktop.

The last step of the no-Bridge path. :mod:`quiltwright.weave` produces a
frame that is already interleaved for one specific panel, so displaying it
1:1 on that panel *is* the hologram -- and the simplest thing that displays
an image 1:1, forever, with no software running, is the desktop wallpaper.

Three things make this more than a file copy:

*The frame is registered to one panel, so it must land on that panel's
desktop.* macOS exposes each desktop's ``display name``, which for a Looking
Glass is its serial -- ``LKG-J00332``. Woven filenames carry the same serial
(``<stem>_native_<serial>.png``), so the right desktop can be found by
matching the two rather than by asking the user to count monitors. Where
that fails, ``--list`` prints what is there.

*Wallpaper is referenced by path, not by content.* Pointing the desktop at a
file inside ``renders/`` means the desktop breaks the next time that
directory is cleaned or the quilt re-rendered. The frame is therefore copied
into a stable pictures folder first -- the one macOS already reports as the
desktop's own ``pictures folder``.

*macOS caches wallpaper by path.* Overwrite a file the desktop already
points at and the screen keeps showing the old image, which on a light-field
panel looks exactly like a weave that did not take. When the destination is
already the current picture, this command bounces the desktop off another
image and back to force the reload.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import click

from quiltwright.cli.main import cli

#: Where woven frames are installed. macOS reports this as the Looking
#: Glass desktop's ``pictures folder``, and keeping frames here means a
#: cleaned ``renders/`` never blanks the panel.
DEFAULT_WALLPAPER_DIR = Path.home() / "Pictures" / "LKG-wallpapers"

#: ``<stem>_native_<serial>.png``, as written by ``quiltwright weave``.
_NATIVE_SUFFIX = re.compile(r"_native_(.+)$")

#: Anything macOS ships that is certain to exist, for the cache bounce.
_BOUNCE_IMAGE = "/System/Library/CoreServices/DefaultDesktop.heic"


def _osascript(script: str, timeout: float = 20.0) -> str:
    """Run one AppleScript and return its stdout.

    :param script: The script source.
    :param timeout: Seconds to wait.
    :return: Stripped stdout.
    :raises click.ClickException: On failure, timeout, or a non-macOS host.
    """
    if sys.platform != "darwin":
        raise click.ClickException(
            "setting the desktop picture is implemented for macOS only; "
            "on other platforms point your desktop environment at the woven "
            "file yourself (it must be displayed 1:1, unscaled and uncropped)"
        )
    try:
        proc = subprocess.run(
            ["osascript", "-e", script], capture_output=True, timeout=timeout, check=False
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise click.ClickException(f"osascript failed: {exc}") from exc
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", "replace").strip()
        raise click.ClickException(
            f"osascript failed: {err}\n"
            "If this mentions permissions, grant your terminal control of "
            "System Events under Privacy & Security > Automation."
        )
    return proc.stdout.decode("utf-8", "replace").strip()


def _desktops() -> list[tuple[int, str, str]]:
    """Enumerate the desktops macOS knows about.

    :return: ``(index, display_name, current_picture)``, 1-based to match
        AppleScript's own indexing.
    """
    count = int(_osascript('tell application "System Events" to get count of desktops') or 0)
    out = []
    for i in range(1, count + 1):
        name = _osascript(f'tell application "System Events" to get display name of desktop {i}')
        pic = _osascript(f'tell application "System Events" to get picture of desktop {i}')
        out.append((i, name, pic))
    return out


def _serial_from_name(stem: str) -> str | None:
    """Recover the panel serial from a woven filename.

    :param stem: Filename without its extension.
    :return: The serial, or ``None`` if the ``_native_`` suffix is absent.
    """
    m = _NATIVE_SUFFIX.search(stem)
    return m.group(1) if m else None


def _set_picture(index: int, path: Path) -> None:
    """Point one desktop at *path*, defeating the path cache if needed.

    :param index: 1-based AppleScript desktop index.
    :param path: Image to display.
    """
    current = _osascript(f'tell application "System Events" to get picture of desktop {index}')
    if Path(current) == path and Path(_BOUNCE_IMAGE).exists():
        # Same path as before: macOS keeps the cached pixels, so a re-weave
        # would silently not appear. Bounce off another image first.
        _osascript(
            f'tell application "System Events" to set picture of desktop {index} '
            f'to POSIX file "{_BOUNCE_IMAGE}"'
        )
    _osascript(
        f'tell application "System Events" to set picture of desktop {index} to POSIX file "{path}"'
    )


@cli.command("wallpaper")
@click.argument(
    "woven",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=False,
)
@click.option(
    "--display",
    "display_name",
    default=None,
    help="Panel serial to target (e.g. LKG-J00332). Defaults to the serial in the woven filename.",
)
@click.option(
    "--desktop",
    "desktop_index",
    type=int,
    default=None,
    help="Target desktop by 1-based index instead of by serial. Use --list to see them.",
)
@click.option(
    "--dir",
    "install_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=None,
    help=f"Where to install the frame (default: {DEFAULT_WALLPAPER_DIR}).",
)
@click.option(
    "--no-install",
    is_flag=True,
    default=False,
    help="Set the file where it lies instead of copying it. Convenient, but "
    "the desktop breaks if that path is later cleaned.",
)
@click.option(
    "--list",
    "list_only",
    is_flag=True,
    default=False,
    help="List the desktops and their current pictures, then exit.",
)
def wallpaper_cmd(
    woven: Path | None,
    display_name: str | None,
    desktop_index: int | None,
    install_dir: Path | None,
    no_install: bool,
    list_only: bool,
) -> None:
    """Set a woven frame as the desktop picture of its own panel.

    WOVEN is a native-resolution frame from `quiltwright weave` -- already
    interleaved for one panel, so displayed 1:1 it fuses into a hologram with
    no Looking Glass software running at all. The panel is identified from
    the `_native_<serial>` filename and matched against each desktop's
    display name.

    The frame is copied into a stable pictures folder first, because macOS
    stores wallpaper as a path: pointing the desktop into `renders/` means
    the panel goes blank the next time that directory is cleaned.

    \b
    Examples:
      # Weave, then hang it on the panel it was woven for
      quiltwright weave renders/quilts/bell-jar-holo_qs8x6a1.77778.png \\
          --cal ~/Pictures/LKG-wallpapers/visual.json
      quiltwright wallpaper bell-jar-holo_native_LKG-J00332.png

      # What is on each desktop right now?
      quiltwright wallpaper --list

      # Target explicitly, when the filename carries no serial
      quiltwright wallpaper frame.png --display LKG-J00332
      quiltwright wallpaper frame.png --desktop 2

      # Leave it where it is (it will break if renders/ is cleaned)
      quiltwright wallpaper renders/quilts/x_native_LKG-J00332.png --no-install
    """
    desktops = _desktops()

    if list_only:
        if not desktops:
            raise click.ClickException("System Events reports no desktops")
        click.echo(f"{len(desktops)} desktop(s):")
        for index, name, picture in desktops:
            click.echo(f"  desktop {index}: {name or '(unnamed)'}")
            click.echo(f"      {picture or '(none)'}")
        return

    if woven is None:
        raise click.UsageError("WOVEN is required unless --list is given")

    serial = display_name or _serial_from_name(woven.stem)

    if desktop_index is not None:
        match = next((d for d in desktops if d[0] == desktop_index), None)
        if match is None:
            raise click.ClickException(
                f"no desktop {desktop_index}; there are {len(desktops)}. "
                "Run `quiltwright wallpaper --list`."
            )
    elif serial is not None:
        match = next((d for d in desktops if d[1] == serial), None)
        if match is None:
            names = ", ".join(f"{i}:{n or '?'}" for i, n, _ in desktops) or "none"
            raise click.ClickException(
                f"no desktop is on display {serial!r} (found {names}).\n"
                "Is the panel connected and mirroring off? Pick one with "
                "--desktop N, or see `quiltwright wallpaper --list`."
            )
    else:
        raise click.ClickException(
            f"cannot tell which panel {woven.name!r} was woven for: its name "
            "carries no _native_<serial> suffix. Pass --display <serial> or "
            "--desktop <n>."
        )

    index, name, _ = match

    target = woven.resolve()
    if not no_install:
        dest_dir = (install_dir or DEFAULT_WALLPAPER_DIR).expanduser()
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / woven.name
        if dest.resolve() != target:
            shutil.copy2(target, dest)
        target = dest.resolve()

    _set_picture(index, target)

    click.echo(f"{woven.name}  ->  desktop {index} ({name or 'unnamed'})")
    click.echo(f"  {target}")
    if not no_install and target.parent != woven.resolve().parent:
        click.echo(f"  installed into {target.parent}")
