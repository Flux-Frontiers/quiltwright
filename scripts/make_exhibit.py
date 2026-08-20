#!/usr/bin/env python
"""
One structure, one command, one exhibit -- the whole pipeline end to end.

    python scripts/make_exhibit.py 7AHL --label "ALPHA-HEMOLYSIN"

Five steps, each of which prints what it did and why, because every one of
them has a trap that is silent when you get it wrong:

  1. **Fetch** the biological assembly from the RCSB into ``$PDB``.
  2. **Convert** it -- ribbons through PyMOL, atoms through pypdb2pov.
  3. **Compose** a four-line exhibit scene, if one does not exist.
  4. **Render** a still at the vitrine's own aspect.
  5. **Sweep** it into a light-field quilt, with ``--quilt``.

Structures land in ``$PDB`` (default ``~/pdb``), the same convention
proteusPy uses, so a file downloaded for one tool is there for the next.
Nothing is re-downloaded that is already present.

The traps, all of which this script handles and all of which have cost time:

*The asymmetric unit is not the molecule.* Ferritin's deposited entry is a
24th of a ferritin. Assembly 1 is the biological unit, and is what gets
fetched unless ``--asymmetric`` says otherwise.

*Below +Q8 POV-Ray disables refraction*, so a cheap probe of a bell jar
reports a solid dome. Stills here are +Q11.

*The enclosing sphere circumscribes.* An elongated structure normalised by it
reads small, which is what ``--fill`` is for.

*A surface is not a cartoon in cost.* A trimeric porin surface runs to
millions of triangles; ``--rep surface`` therefore forces a coarser
``surface_quality`` unless you override it.

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VITRINE = ROOT / "pov-scenes" / "vitrine"
STILLS = ROOT / "renders" / "stills"

#: Where structures live.  ``$PDB`` if set, else ``~/pdb`` -- the convention
#: proteusPy already follows, so one download serves both.
PDB_DIR = Path(os.getenv("PDB", Path.home() / "pdb"))

RCSB = "https://files.rcsb.org/download"


def say(step: str, message: str) -> None:
    """Print a step banner with its reasoning wrapped underneath."""
    print(f"\n[{step}] {message}")


def note(text: str) -> None:
    print(textwrap.indent(textwrap.fill(text, 74), "      "))


def fetch(pdb_id: str, *, assembly: bool = True, force: bool = False) -> Path:
    """Download a structure into :data:`PDB_DIR`, or reuse what is there.

    :param pdb_id: Four-character PDB identifier, case-insensitive.
    :param assembly: Fetch assembly 1 -- the biological unit -- rather than
        the deposited asymmetric unit.
    :param force: Re-download even when the file is already present.
    :return: Path to the local file.
    :raises SystemExit: If the RCSB has no such file.
    """
    ident = pdb_id.lower()
    name = f"{ident}-assembly1.cif.gz" if assembly else f"{ident}.cif.gz"
    target = PDB_DIR / name

    if target.exists() and not force:
        size = target.stat().st_size / 1e3
        say("1/5 fetch", f"{name} already in {PDB_DIR} ({size:.0f} kB)")
        return target

    PDB_DIR.mkdir(parents=True, exist_ok=True)
    url = f"{RCSB}/{name}"
    say("1/5 fetch", f"{url}\n      -> {target}")
    try:
        urllib.request.urlopen(url, timeout=60)  # noqa: S310 - fixed https host
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and assembly:
            raise SystemExit(
                f"the RCSB has no assembly 1 for {pdb_id.upper()}.\n"
                "Some entries have none -- retry with --asymmetric."
            ) from None
        raise SystemExit(f"could not fetch {url}: {exc}") from None
    urllib.request.urlretrieve(url, target)  # noqa: S310
    note(
        "Assembly 1 is the biological unit. The deposited asymmetric unit can "
        "be a fraction of the molecule -- ferritin's is a 24th of a ferritin -- "
        "so fetching it by mistake gives a structure that is simply wrong, "
        "with nothing to say so."
        if assembly
        else "Asymmetric unit, as asked. This is the deposited coordinates and "
        "may be a fraction of the biological molecule."
    )
    return target


def convert(
    source: Path, stem: str, *, rep: str, color: str, fill_args: dict
) -> tuple[Path, float]:
    """Turn a structure into an object-only include.

    Two geometry sources, one contract: whichever writes the file, what comes
    out is origin-centred with its enclosing radius declared, so the scene in
    step 3 does not care which was used.

    :return: ``(include path, enclosing radius)``.
    """
    if rep == "atoms":
        try:
            from pypdb2pov import (
                ParseOptions,
                SceneOptions,
                find_bonds,
                prepare_structure,
                read_structure,
                write_scene,
            )
        except ImportError:
            raise SystemExit(
                "pypdb2pov is not installed, so atoms cannot be converted.\n"
                "  pip install git+https://github.com/Flux-Frontiers/pypdb2pov"
            ) from None
        out = VITRINE / f"{stem}.inc"
        say("2/5 convert", f"pypdb2pov -o -v  ->  {out.name}")
        structure, _ = read_structure(str(source), ParseOptions())
        options = SceneOptions(name=stem, object_only=True)
        prepare_structure(structure, options)
        write_scene(structure, options, str(out), find_bonds(structure, options.bond_threshold))
        radius = structure.enclosing_radius()
        note(
            "Space-filling spheres at van der Waals radii. This is what "
            "pdb2pov has drawn since 1993, and at exhibit scale it reads as a "
            "solid object rather than as confetti -- ball-and-stick does not."
        )
    else:
        from quiltwright.pymol import cartoon_inc

        # A cartoon include is gitignored by the *_cartoon.inc pattern, which
        # is deliberate: one porin trimer is 8.9 MB and three seconds to remake.
        out = VITRINE / f"{stem}_cartoon.inc"
        say("2/5 convert", f"PyMOL {rep}  ->  {out.name}")
        result = cartoon_inc(source, out, rep=rep, color=color, **fill_args)
        radius = result.enclosing_radius
        note(
            f"{result.faces} faces from {result.backend}. PyMOL emits one mesh "
            "per triangle; these were coalesced into one with shared vertex, "
            "normal and texture lists, which is several times smaller and gets "
            "re-parsed once per view in a 48-view quilt."
        )
    print(f"      enclosing radius {radius:.3f} A")
    return out, radius


def compose(stem: str, include: Path, label: str, fill: float) -> Path:
    """Write the exhibit scene, unless one is already there to keep."""
    scene = VITRINE / f"exhibit_{stem}.pov"
    if scene.exists():
        say("3/5 compose", f"{scene.name} exists, keeping it")
        note("Delete it to regenerate, or edit it -- hand edits survive reruns.")
        return scene

    identifier = include.stem
    if identifier[0].isdigit():
        identifier = "_" + identifier
    atoms = not include.name.endswith("_cartoon.inc")
    say("3/5 compose", f"writing {scene.name}")
    scene.write_text(
        f'''// {label} in the standard vitrine.  Written by scripts/make_exhibit.py.
//
// Regenerate the geometry with:
//   python scripts/make_exhibit.py {stem.upper()}

#version 3.7;
global_settings {{ assumed_gamma 1.0 }}

#include "colors.inc"
#include "textures.inc"
{'#include "atoms_vdw.inc"' + chr(10) + '#include "atoms2.inc"' if atoms else "// A cartoon carries its own textures; no atom includes needed."}

#declare VIT_LABEL = "{label}";
#declare VIT_FILL = {fill};
#include "vitrine.inc"
#include "{include.name}"

Vitrine_Report()

Vitrine_Mount({identifier}, {identifier}_enclosing_radius)
Vitrine_Case()
Vitrine_Plinth()
Vitrine_Room()
Vitrine_Lights()
Vitrine_Camera()
'''
    )
    note(
        "Four working lines. Vitrine_Mount asks nothing about how the geometry "
        "was made, so atoms, ribbons and a 1994 mesh all mount identically."
    )
    return scene


def render(scene: Path, stem: str, width: int, height: int) -> Path:
    """Ray-trace the still at the vitrine's own aspect."""
    out = STILLS / f"vitrine_{stem}.png"
    STILLS.mkdir(parents=True, exist_ok=True)
    say("4/5 render", f"{width}x{height} +Q11  ->  renders/stills/{out.name}")

    includes = ["-L."]
    try:
        import pypdb2pov

        includes.append(f"-L{pypdb2pov.include_dir()}")
    except ImportError:
        pass

    proc = subprocess.run(
        [
            "povray",
            f"+I{scene.name}",
            f"+O{out}",
            f"+W{width}",
            f"+H{height}",
            "+Q11",
            "+A0.2",
            "-D",
            "+FN",
            "-WT16",
            *includes,
        ],
        cwd=scene.parent,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not out.exists():
        tail = "\n".join(proc.stderr.strip().splitlines()[-12:])
        raise SystemExit(f"POV-Ray failed:\n{tail}")
    note(
        "+Q11 is not caution: below +Q8 POV-Ray disables refraction, so a "
        "cheap probe reports the bell jar as a solid dome and the glass you "
        "are trying to judge is not being simulated at all."
    )
    for line in proc.stderr.splitlines():
        if "vitrine]" in line:
            print("     ", line.split("vitrine]", 1)[1].strip())
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("pdb_id", help="four-character PDB ID, e.g. 7AHL")
    parser.add_argument("--label", default=None, help="plaque text (default: the ID)")
    parser.add_argument("--name", default=None, help="file stem (default: the lowercased ID)")
    parser.add_argument(
        "--rep",
        default="cartoon",
        choices=["cartoon", "surface", "ribbon", "sticks", "spheres", "atoms"],
        help="'atoms' goes through pypdb2pov; everything else through PyMOL",
    )
    parser.add_argument("--color", default="spectrum", help="PyMOL colour, or 'spectrum'")
    parser.add_argument("--fill", type=float, default=1.12, help="VIT_FILL in the scene")
    parser.add_argument("--asymmetric", action="store_true", help="deposited unit, not assembly 1")
    parser.add_argument("--force", action="store_true", help="re-download even if cached")
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--quilt", action="store_true", help="also sweep a light-field quilt")
    parser.add_argument("--surface-quality", type=int, default=None)
    args = parser.parse_args(argv)

    stem = args.name or args.pdb_id.lower()
    label = args.label or args.pdb_id.upper()

    print(f"Building an exhibit for {args.pdb_id.upper()}  ({args.rep})")
    print(
        f"Structures: {PDB_DIR}"
        + ("" if os.getenv("PDB") else "   ($PDB unset, using the default)")
    )

    source = fetch(args.pdb_id, assembly=not args.asymmetric, force=args.force)

    fill_args: dict = {}
    if args.rep in {"surface", "ribbon", "cartoon", "sticks", "spheres"}:
        quality = args.surface_quality
        if quality is None and args.rep == "surface":
            quality = -1
            print("      --rep surface: defaulting surface_quality to -1")
        fill_args["surface_quality"] = quality

    include, _ = convert(source, stem, rep=args.rep, color=args.color, fill_args=fill_args)
    scene = compose(stem, include, label, args.fill)
    still = render(scene, stem, args.width, args.height)
    print(f"\n      {still}")

    if args.quilt:
        say("5/5 quilt", "sweeping 48 views -- this is the expensive step")
        note(
            "One ray-trace per view. The scene is unchanged; only the camera "
            "moves, off-axis, along its right vector."
        )
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "render_vitrine.py"), stem, "--threads", "16"],
            check=False,
        )
    else:
        say("5/5 quilt", "skipped -- pass --quilt to sweep 48 views")

    print("\nDone. Next:")
    print(f"  open {still}")
    print(f"  python scripts/render_vitrine.py {stem} --preview   # quick quilt")
    print(f"  python scripts/render_vitrine.py {stem} --cast      # onto the panel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
