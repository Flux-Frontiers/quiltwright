#!/usr/bin/env python
"""
Render a molecule in the standard vitrine as a Looking Glass hologram.

The vitrine (``pov-scenes/vitrine/vitrine.inc``) is a museum exhibit case
built in *exhibit units*: the molecule is normalised to a unit sphere using
the enclosing radius pdb2pov writes into every scene, and the room is built
around that.  The consequence is the reason this script has no per-molecule
numbers in it -- hemoglobin (R = 40 A) and F1-ATPase (R = 79 A) arrive at the
same size on the same plinth, so **one camera and one depth budget serve every
structure**.  Compare ``render_museum_hologram.py``, which needs a measured
corridor, a measured depth range and a derived cone, all specific to that room.

The alcove is open toward -z, so the sweep-clearance trap that cost the museum
eleven of its forty-eight views cannot occur: the corridor is +-VIT_SIDE by
construction, which at the default focal distance permits a cone far wider
than any display asks for.  The numbers are still printed before the render,
because a budget you did not look at is a budget you do not have.

Usage::

    python scripts/render_vitrine.py hemoglobin [--preview] [--cast]

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from quiltwright.lfd import QUILT_PRESETS, focal_distance_for_range, save_quilt
from quiltwright.povgen import fov_vertical_to_horizontal
from quiltwright.povray import Clearance, PovCamera, format_depth_budget, render_pov_quilt
from quiltwright.runreport import RunReport, povray_parallelism

ROOT = Path(__file__).resolve().parents[1]
VITRINE = ROOT / "pov-scenes" / "vitrine"


def pdb2pov_include() -> Path:
    """Where pdb2pov's radius sets and element textures live.

    Asked of the installed package rather than guessed from a checkout path:
    the includes ship *inside* ``pypdb2pov``, so wherever it is installed is
    where they are, and a scene then renders the same from any working
    directory and on any machine.  ``pypdb2pov --include-dir`` prints the
    same answer at a shell.

    :return: The include directory.
    :raises SystemExit: With an install hint if the package is absent, which
        is a better failure than POV-Ray reporting a missing ``atoms2.inc``
        forty lines into a scene it half-parsed.
    """
    try:
        import pypdb2pov
    except ImportError:  # pragma: no cover - depends on the environment
        raise SystemExit(
            "pypdb2pov is not installed, so the atom textures cannot be found.\n"
            '  pip install "quiltwright[molecules]"\n'
            "  pip install pypdb2pov"
        ) from None
    return Path(pypdb2pov.include_dir())


# --- The vitrine's own geometry --------------------------------------------
#
# These mirror the defaults in vitrine.inc and must be kept in step with it by
# hand: the scene prints them at parse time via Vitrine_Report(), so a drift
# shows up in the render log rather than silently.

EYE = (0.0, 0.95, -6.90)
AIM = (0.0, -1.30, 0.00)
FOV_V = 44.0
ASPECT = 16 / 9

#: Nearest content: the front of the bell jar.  Farthest: the alcove's back
#: wall.  Both are analytic here, which is the whole advantage of a room you
#: built rather than one you inherited -- no plane-sweep probing.
NEAR = 5.534
FAR = 10.300

#: The alcove's side walls, in scene units either side of the eye.
ROOM = Clearance(left=-5.30, right=5.30, margin=0.50)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "exhibit",
        nargs="?",
        default="hemoglobin",
        help="exhibit stem, e.g. hemoglobin (renders exhibit_<stem>.pov)",
    )
    parser.add_argument("--device", default="16-landscape", help="quilt preset")
    parser.add_argument("--preview", action="store_true", help="quarter-scale, fast")
    parser.add_argument("--cast", action="store_true", help="send to Looking Glass Bridge")
    parser.add_argument("--jobs", type=int, default=1, help="concurrent POV-Ray processes")
    parser.add_argument("--threads", type=int, default=None, help="POV-Ray threads per job")
    parser.add_argument("--quality", type=int, default=11, help="POV-Ray +Q; keep >=8 for glass")
    parser.add_argument("--budget-only", action="store_true", help="print the budget and stop")
    args = parser.parse_args(argv)

    scene = VITRINE / f"exhibit_{args.exhibit}.pov"
    if not scene.exists():
        parser.error(f"no such exhibit: {scene}")

    focal = focal_distance_for_range(NEAR, FAR)
    camera = PovCamera.aimed(
        EYE,
        AIM,
        fov=fov_vertical_to_horizontal(FOV_V, ASPECT),
        focal_distance=focal,
    )

    spec = QUILT_PRESETS[args.device]
    if args.preview:
        spec = spec.scaled(0.25)

    print(f"\nExhibit: {args.exhibit}   scene: {scene.name}")
    print(format_depth_budget(spec, camera, {"near": NEAR, "far": FAR}, clearance=ROOM))
    print(f"  widest legal cone: {ROOM.cone(focal):.1f} deg (spec asks {spec.view_cone:.1f})")
    if args.budget_only:
        return 0

    started = time.time()
    quilt = render_pov_quilt(
        scene,
        spec,
        camera,
        include_paths=[VITRINE, pdb2pov_include()],
        quality=args.quality,
        jobs=args.jobs,
        threads=args.threads,
    )
    elapsed = time.time() - started

    stem = (
        ROOT
        / "renders"
        / "quilts"
        / (f"vitrine-{args.exhibit}" + ("-preview" if args.preview else ""))
    )
    path = save_quilt(quilt, stem, spec)
    print(f"\nwrote {path}  ({elapsed / 60:.1f} min)")

    report = RunReport(f"Vitrine: {args.exhibit}", scene=scene)
    report.table("Parallelism", povray_parallelism(args.jobs, args.threads))
    report.pre(
        "Depth budget",
        format_depth_budget(spec, camera, {"near": NEAR, "far": FAR}, clearance=ROOM),
    )
    print(f"  report {report.write(ROOT / 'renders' / 'reports' / f'{path.stem}.md', output=path)}")

    if args.cast:
        from quiltwright.lfd import cast_quilt

        result = cast_quilt(path, spec)
        print(f"cast: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
