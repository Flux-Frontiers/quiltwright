"""CLI command: ``quiltwright dynamic`` -- pack stills into a Dynamic Desktop HEIC.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

from pathlib import Path

import click

from quiltwright.cli.main import cli
from quiltwright.dynamic import (
    AppearanceMap,
    read_dynamic_metadata,
    save_dynamic_heic,
    spec_from_json,
    spec_from_paths,
)


@cli.command("dynamic")
@click.option(
    "--appearance",
    nargs=2,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    metavar="LIGHT DARK",
    help="Two stills: light appearance, then dark.",
)
@click.option(
    "--solar",
    "solar_json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="JSON array of stills with altitude/azimuth (wallpapper shape).",
)
@click.option(
    "--time",
    "time_json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="JSON array of stills with time (HH:MM or HH:MM:SS). Mac wall clock, not POV-Ray clock.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Output .heic path. Required unless --dump.",
)
@click.option(
    "--lossless",
    "lossless_flag",
    is_flag=True,
    default=False,
    help="Force lossless 4:4:4 (implied for woven _native_ frames).",
)
@click.option(
    "--lossy",
    "lossy_flag",
    is_flag=True,
    default=False,
    help="Force lossy HEVC. Refused for woven _native_ frames.",
)
@click.option(
    "--dump",
    "dump_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Print apple_desktop metadata from an existing HEIC and exit.",
)
def dynamic_cmd(
    appearance: tuple[Path, Path] | None,
    solar_json: Path | None,
    time_json: Path | None,
    output: Path | None,
    lossless_flag: bool,
    lossy_flag: bool,
    dump_path: Path | None,
) -> None:
    """Pack stills into a macOS Dynamic Desktop HEIC.

    LIGHT/DARK, a solar JSON, or a time JSON. Woven `_native_` frames are
    always lossless. Install the result with `quiltwright wallpaper`.

    \b
    Examples:
      quiltwright dynamic --appearance day.png night.png -o scene.heic
      quiltwright dynamic --solar solar.json -o scene.heic
      quiltwright dynamic --time hours.json -o scene.heic
      quiltwright dynamic --dump scene.heic
    """
    if dump_path is not None:
        try:
            info = read_dynamic_metadata(dump_path)
        except (RuntimeError, ValueError) as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo(f"{dump_path.name}: {info['n_images']} images, apple_desktop:{info['tag']}")
        click.echo(info["plist"])
        return

    modes = [appearance is not None, solar_json is not None, time_json is not None]
    if sum(modes) != 1:
        raise click.UsageError("give exactly one of --appearance, --solar, or --time")
    if output is None:
        raise click.UsageError("--output is required unless --dump is given")
    if lossless_flag and lossy_flag:
        raise click.UsageError("--lossless and --lossy are mutually exclusive")

    lossless: bool | None
    if lossless_flag:
        lossless = True
    elif lossy_flag:
        lossless = False
    else:
        lossless = None

    try:
        if appearance is not None:
            light, dark = appearance
            spec = spec_from_paths(
                [light, dark],
                appearance=AppearanceMap(0, 1),
                lossless=lossless,
            )
        else:
            json_path = solar_json or time_json
            assert json_path is not None
            spec = spec_from_json(json_path, lossless=lossless)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc

    try:
        written = save_dynamic_heic(spec, output)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
    kind = "solar" if spec.solar else ("h24" if spec.times else "apr")
    click.echo(
        f"{written}  ({len(spec.frames)} frames, apple_desktop:{kind}"
        f"{', lossless' if spec.lossless else ''})"
    )
