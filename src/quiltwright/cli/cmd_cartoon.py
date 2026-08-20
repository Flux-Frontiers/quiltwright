"""
CLI command: ``quiltwright cartoon`` -- a molecular cartoon, ready to mount.

The shell face of :mod:`quiltwright.pymol`.  It turns a structure into an
object-only POV-Ray include on the ``pdb2pov -o`` contract -- origin centred,
``<name>_enclosing_radius`` declared, no camera and no lights -- which is the
form every scene in ``pov-scenes/`` already knows how to mount::

    quiltwright cartoon 2omf.cif.gz ompf_cartoon.inc
    # then, in a scene:
    #   #include "ompf_cartoon.inc"
    #   Vitrine_Mount(ompf_cartoon, ompf_cartoon_enclosing_radius)

**PyMOL is optional and this command is the place that says so.**  It is not
OSI-licensed, and quiltwright is BSD-3, so it can never be a dependency; it is
also awkward to reach, because PyPI has only ever published alphas and the
Homebrew build bundles an interpreter no project virtualenv can import from.
``--check`` reports which route is available before anything is loaded, and a
missing PyMOL fails with install instructions rather than a traceback.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

from pathlib import Path

import click

from quiltwright.cli.main import cli


@cli.command()
@click.argument("source", type=click.Path(exists=True, dir_okay=False), required=False)
@click.argument("output", type=click.Path(dir_okay=False), required=False)
@click.option(
    "--rep",
    default="cartoon",
    show_default=True,
    help="Representation. cartoon and surface are what pdb2pov cannot draw; "
    "sticks and spheres duplicate its -b and -v.",
)
@click.option(
    "--color",
    default="spectrum",
    show_default=True,
    help='"spectrum" ramps rainbow along the chain; any PyMOL colour name is '
    'flat; "none" keeps PyMOL\'s own colouring.',
)
@click.option(
    "--selection",
    default="polymer",
    show_default=True,
    help="PyMOL selection to show. The default drops waters and ligands.",
)
@click.option(
    "--assembly",
    default="1",
    show_default=True,
    help='Biological assembly. "1" is the biological unit -- ferritin arrives '
    'as a 24-mer rather than a 24th of itself. "" gives the asymmetric unit.',
)
@click.option(
    "--transparency",
    type=click.FloatRange(0.0, 1.0),
    default=0.0,
    show_default=True,
    help="Exports as POV-Ray transmit, which is flat see-through rather than refractive.",
)
@click.option(
    "--surface-quality",
    type=int,
    default=None,
    help="PyMOL surface_quality; lower is coarser. Worth setting negative for "
    "a large --rep surface, which otherwise runs to millions of triangles.",
)
@click.option(
    "--name",
    default=None,
    help="POV-Ray identifier to declare. Defaults to the output stem, made "
    "legal (a leading digit gains an underscore).",
)
@click.option(
    "--raw",
    is_flag=True,
    help="Skip coalescing and keep PyMOL's one mesh per triangle. For "
    "comparing against the raw export; several times larger.",
)
@click.option(
    "--check",
    is_flag=True,
    help="Report how PyMOL can be reached and exit, converting nothing.",
)
def cartoon(
    source: str | None,
    output: str | None,
    rep: str,
    color: str,
    selection: str,
    assembly: str,
    transparency: float,
    surface_quality: int | None,
    name: str | None,
    raw: bool,
    check: bool,
) -> None:
    """Convert a structure into a POV-Ray cartoon include.

    SOURCE is anything PyMOL can load -- .pdb, .cif, .cif.gz. OUTPUT is the
    .inc to write.
    """
    # Imported here, not at module scope: the root group promises to stay
    # core-only, and this module pulls in the mesh coalescer.
    from quiltwright.pymol import REPRESENTATIONS, PyMolNotAvailable, available, cartoon_inc

    if check:
        backend = available()
        if backend == "module":
            click.echo("PyMOL: importable in this interpreter (fastest route).")
        elif backend == "subprocess":
            click.echo(
                "PyMOL: found on PATH but not importable here, so it will be "
                "driven as a subprocess.\n"
                "That is normal for the Homebrew build, which bundles its own "
                "interpreter."
            )
        else:
            click.echo(
                "PyMOL: not available.\n"
                "  brew install pymol                          # macOS, stable\n"
                "  conda install -c conda-forge pymol-open-source\n"
                "  pip install --pre pymol-open-source         # alphas only"
            )
            raise SystemExit(1)
        return

    if source is None or output is None:
        raise click.UsageError("SOURCE and OUTPUT are required unless --check is given.")
    if rep not in REPRESENTATIONS:
        raise click.BadParameter(
            f"{rep!r} is not one of {', '.join(REPRESENTATIONS)}", param_hint="--rep"
        )

    try:
        result = cartoon_inc(
            source,
            output,
            rep=rep,
            color=None if color.lower() == "none" else color,
            selection=selection,
            assembly=assembly,
            transparency=transparency,
            surface_quality=surface_quality,
            coalesce=not raw,
            name=name,
        )
    except PyMolNotAvailable as exc:
        raise click.ClickException(str(exc)) from None

    size_mb = Path(result.path).stat().st_size / 1e6
    click.echo(f"wrote {result.path}  ({size_mb:.1f} MB, via {result.backend})")
    click.echo(f"  {result.rep}: {result.faces} faces, {result.vertices} vertices")
    click.echo(f"  enclosing radius {result.enclosing_radius:.3f}")
    click.echo(
        f"  mount with: Vitrine_Mount({result.identifier}, {result.identifier}_enclosing_radius)"
    )
