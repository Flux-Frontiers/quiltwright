"""
CLI command: ``quiltwright playlist`` -- several quilts, one looping playlist.

The multi-quilt face of :func:`quiltwright.bridge.cast_playlist`.  Where
``quiltwright cast`` puts one quilt on the glass, this builds a playlist of
them that advances on a timer and loops, the way a Looking Glass shows a set
of holograms unattended.

Sources are quilt files, played in the order given, or folders.  A folder
with a ``playlist.json`` is read the way Looking Glass Studio 1.x keeps a
playlist -- a folder of media and a list of ``{"filename": ...}`` entries --
and plays in that order, so a Studio playlist folder plays unchanged.  Any
other folder plays its quilt files by name.

Each quilt's tiling comes from its ``_qs<cols>x<rows>a<aspect>`` filename
suffix, per file, so one playlist may mix grids.  A file without the suffix
is refused by name rather than guessed at: a wrong grid shuffles the views.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import json
from pathlib import Path

import click

from quiltwright.cli.main import cli
from quiltwright.cli.options import aspect_from_filename, grid_from_filename
from quiltwright.quilt import QuiltSpec


def _studio_order(folder: Path) -> list[Path] | None:
    """The quilts a Looking Glass Studio 1.x playlist folder lists, in order.

    :param folder: A directory that may hold a ``playlist.json``.
    :return: The listed paths, or ``None`` if the folder has no playlist.json.
    :raises click.UsageError: If a listed file is not in the folder.
    """
    manifest = folder / "playlist.json"
    if not manifest.is_file():
        return None
    paths = [folder / entry["filename"] for entry in json.loads(manifest.read_text())]
    missing = [path.name for path in paths if not path.is_file()]
    if missing:
        raise click.UsageError(
            f"{manifest} lists files that are not in the folder: {', '.join(missing)}"
        )
    return paths


def _expand(sources: tuple[Path, ...]) -> list[Path]:
    """Turn the command's sources into quilt files, in playing order.

    :param sources: Quilt files and folders, as given on the command line.
    :return: Quilt paths.  A folder contributes its playlist.json order if it
        has one, otherwise its suffixed quilt files sorted by name.
    """
    quilts: list[Path] = []
    for source in sources:
        if not source.is_dir():
            quilts.append(source)
            continue
        listed = _studio_order(source)
        if listed is not None:
            quilts.extend(listed)
        else:
            quilts.extend(
                sorted(p for p in source.iterdir() if p.is_file() and grid_from_filename(p.stem))
            )
    return quilts


def _spec_for(path: Path) -> QuiltSpec:
    """The tiling Bridge needs for one quilt, from its filename.

    :param path: A quilt file named with the ``_qs`` suffix.
    :return: Its quilt specification.
    :raises click.UsageError: If the name carries no tiling suffix.
    """
    grid = grid_from_filename(path.stem)
    aspect = aspect_from_filename(path.stem)
    if grid is None or aspect is None:
        raise click.UsageError(
            f"{path.name} has no _qs<cols>x<rows>a<aspect> suffix, so its tiling is "
            "unknown. Rename it, or cast it on its own with `quiltwright cast --grid`."
        )
    columns, rows = grid
    # Bridge reads the file itself and takes only tiling and aspect from the
    # entry.  The pixel size is read where the file is an image so the spec
    # still describes it; a video quilt cannot be opened this way, and gets
    # its grid as a nominal size rather than a probe it does not need.
    from PIL import Image

    try:
        with Image.open(path) as image:
            width, height = image.size
    except OSError:
        width, height = columns, rows
    return QuiltSpec(
        columns=columns, rows=rows, quilt_width=width, quilt_height=height, aspect=aspect
    )


@cli.command("playlist")
@click.argument("sources", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option(
    "--duration",
    type=float,
    default=20.0,
    show_default=True,
    help="Seconds each quilt shows before the next.",
)
@click.option(
    "--head",
    type=int,
    default=-1,
    show_default=True,
    help="Bridge head index to play on. -1 lets Bridge choose; "
    "`quiltwright cast --check` lists them.",
)
@click.option("--once", is_flag=True, help="Play through once instead of looping.")
@click.option(
    "--playlist",
    "name",
    default=None,
    help="Bridge playlist name. Defaults to a fresh name, which is what replaces "
    "whatever is showing.",
)
@click.option("--bridge-url", default=None, help="Bridge HTTP API base URL.")
def playlist_cmd(
    sources: tuple[Path, ...],
    duration: float,
    head: int,
    once: bool,
    name: str | None,
    bridge_url: str | None,
) -> None:
    """Play quilts on the connected Looking Glass as one looping playlist.

    SOURCES are quilt files, in playing order, or folders: a Looking Glass
    Studio playlist folder plays in its playlist.json order, any other folder
    plays its quilt files by name.

    \b
    Examples:
      quiltwright playlist a_qs11x6a0.5625.png b_qs11x6a0.5625.png --head 1
      quiltwright playlist ~/Documents/HoloPlayStudio/"EGS Science Go"
      quiltwright playlist renders/quilts/go --duration 10 --once
    """
    from quiltwright.bridge import BRIDGE_URL, cast_playlist

    quilts = _expand(sources)
    if not quilts:
        raise click.UsageError("no quilts to play: the sources hold no _qs-suffixed quilt files")
    entries = [(path, _spec_for(path)) for path in quilts]

    try:
        cast_playlist(
            entries,
            bridge_url=bridge_url or BRIDGE_URL,
            playlist=name,
            head_index=head,
            duration_ms=round(duration * 1000),
            loop=not once,
        )
    except Exception as exc:  # noqa: BLE001 -- surfaced verbatim, as cast does
        raise click.ClickException(
            f"playlist failed: {exc}\nRun `quiltwright cast --check` to see what Bridge can reach."
        ) from exc

    for index, (path, spec) in enumerate(entries, 1):
        click.echo(
            f"  {index:2}. {path.name}  ({spec.columns}x{spec.rows}, aspect {spec.aspect:g})"
        )
    click.echo(
        f"{len(entries)} quilt(s), {duration:g} s each, {'once' if once else 'looping'}"
        + (f", head {head}" if head >= 0 else ", Bridge's default head")
    )
