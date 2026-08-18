#!/usr/bin/env python
"""
Render "Eric's Science Museum" as a Looking Glass hologram.

A 1995-97 POV-Ray scene: molecular exhibits under bell jars in a room
borrowed from Michael "meek" Mittelstadt.  What is in it and why is in
``docs/about-the-image.md``; the derivation of the numbers below is in
``docs/povray.md``.

The camera keeps the scene's own viewpoint, aim direction and lens.  Three
things change, each measured from the scene rather than guessed:

* **Focal plane** -- moved from the scene's composed 63.7 units to the
  harmonic mean of the measured depth range (31 to 96 units), along the
  original aim ray.
* **Eye position** -- shifted to the middle of the room's usable lateral
  corridor, measured at -18 to +8 units along the right vector.
* **View cone** -- derived from the clearance that remains, ~26 degrees.
  The default 35 blackened 11 of 48 views by sweeping through a wall.

Usage::

    python scripts/render_museum_hologram.py [--preview] [--cast]

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import replace
from pathlib import Path

from quiltwright.lfd import QUILT_PRESETS, focal_distance_for_range, save_quilt
from quiltwright.povray import Clearance, PovCamera, format_depth_budget, render_pov_quilt

# --- Scene -----------------------------------------------------------------

POV_SCENES = Path(__file__).resolve().parents[1] / "pov-scenes"
SCENE = POV_SCENES / "museum" / "museum.pov"
INCLUDE_PATHS = [
    POV_SCENES / "myinclude",
    POV_SCENES,
]

#: Eye position of the scene's own ``camera_zdna3``.  Kept in step with it by
#: hand: this script overrides the scene's camera entirely, so a dolly in the
#: scene file is invisible to the quilt until it is copied here.
EYE = (18.4, 19.9, 9.7)
#: Its aim point.  Used for direction only; the focal distance is recomputed.
AIM = (58.0, 19.0, 53.0)
#: Vertical FOV of the scene's ``the_lens`` (direction 1, up 1 -> 2*atan(0.5)).
FOV = 53.13

#: Depth range measured by plane-sweep probe, in scene units: an opaque plane
#: slides along the view axis and the frame is scored for how much geometry
#: remains in front of it.  *near* is where geometry first appears (the near
#: pedestal's tabletop, at 0.1% of frame); *far* is where 95% of everything
#: occludable is accounted for.  The remaining ~6% of the frame is sky through
#: the window, at effective infinity, and is left out of the balance on
#: purpose -- it is low-contrast and can afford the disparity.
#: Both shifted 5 units nearer with the eye's 5.03-unit dolly toward the aim
#: point, since the plane sweep measures along the view axis from the eye.
#: They were 31.0 and 96.0 when the eye sat at <15,20,6>.
NEAR_DEPTH = 26.0
FAR_DEPTH = 91.0

#: Usable lateral eye travel along the camera's right vector, measured by
#: rendering at candidate offsets and watching for the frame to collapse to
#: the unlit back of a wall.  The corridor is asymmetric about the scene's
#: own eye position, and the 2-unit margin keeps the outermost view off
#: walls that are neither planar nor evenly lit at grazing angles.
CLEARANCE = Clearance(left=-18.0, right=8.0, margin=2.0)


def museum_camera(focal_distance: float | None = None) -> PovCamera:
    """The scene's viewpoint, re-aimed and re-centred for the view sweep.

    :param focal_distance: Where to put the focal plane, in scene units.
        Defaults to the harmonic mean of the measured depths, which equalises
        near against far.  That is only optimal when the view cone is fixed,
        and here it is not: the cone is derived from this distance against a
        wall-bounded eye sweep, so pushing the plane back narrows the cone and
        pulls *everything* -- including the sky, which no focal plane reaches
        at a fixed cone -- down with it.
    :return: The centre-view camera.
    """
    return PovCamera.aimed(
        EYE,
        AIM,
        fov=FOV,
        focal_distance=focal_distance or focal_distance_for_range(NEAR_DEPTH, FAR_DEPTH),
        lateral_shift=CLEARANCE.centre,
    )


def main() -> int:
    """Render (and optionally cast) the museum quilt.

    :return: Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device", default="16-landscape", choices=sorted(QUILT_PRESETS), help="target display"
    )
    parser.add_argument(
        "--view-cone",
        type=float,
        default=None,
        help="camera sweep in degrees; defaults to the widest cone that keeps "
        "the outermost eye inside the room",
    )
    parser.add_argument(
        "--focal",
        type=float,
        default=None,
        help="focal plane distance in scene units, overriding the harmonic "
        "mean of the measured depths.  Prefer this to --view-cone when you "
        "want the disparity down without giving up look-around: the eye still "
        "travels the full corridor the walls allow, and the cone narrows as a "
        "consequence.  --view-cone instead shortens the travel itself.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="quarter-size quilt with cheaper anti-aliasing, for iterating",
    )
    parser.add_argument(
        "--antialias",
        type=float,
        default=0.05,
        help="POV-Ray +A threshold.  Quilts are worth anti-aliasing harder "
        "than stills: each view aliases differently, and the display "
        "interpolates between them, so edge noise reads as shimmer rather "
        "than grain.",
    )
    parser.add_argument("--jobs", type=int, default=1, help="concurrent POV-Ray processes")
    parser.add_argument("--out", default="renders/quilts/museum", help="output stem")
    parser.add_argument("--cast", action="store_true", help="send to Looking Glass Bridge")
    parser.add_argument("--keep-views", help="directory to retain per-view PNGs in")
    args = parser.parse_args()

    if not SCENE.is_file():
        print(f"error: scene not found at {SCENE}", file=sys.stderr)
        return 1

    camera = museum_camera(args.focal)
    cone = args.view_cone
    if cone is None:
        cone = CLEARANCE.cone(camera.focal_distance)
    spec = replace(QUILT_PRESETS[args.device], view_cone=cone)
    if args.preview:
        spec = replace(spec, quilt_width=spec.quilt_width // 4, quilt_height=spec.quilt_height // 4)

    print(f"Museum hologram -> {args.device}{' (preview)' if args.preview else ''}")
    print(
        f"  quilt            {spec.quilt_width}x{spec.quilt_height}, "
        f"tiles {spec.tile_width}x{spec.tile_height}"
    )
    print(
        format_depth_budget(
            spec,
            camera,
            {
                "nearest geometry": NEAR_DEPTH,
                "focal plane": camera.focal_distance,
                "far interior": FAR_DEPTH,
                "sky (infinite)": math.inf,
            },
            clearance=CLEARANCE,
        )
    )

    started = time.time()
    quilt = render_pov_quilt(
        SCENE,
        spec,
        camera,
        include_paths=INCLUDE_PATHS,
        antialias=None if args.preview else args.antialias,
        quality=11,
        # Recursive supersampling (+AM2) to depth 4, rather than the default
        # adaptive single pass, which leaves stair-stepping on the window
        # mullions and bell-jar rims -- the highest-contrast edges in frame.
        extra_args=() if args.preview else ("+AM2", "+R4"),
        jobs=args.jobs,
        keep_views=args.keep_views,
    )
    elapsed = time.time() - started

    # A preview is a quarter-size stand-in, not a deliverable, so it must not
    # land on the full render's filename -- iterating on one would silently
    # destroy the other.
    stem = f"{args.out}-preview" if args.preview else args.out
    out = save_quilt(quilt, stem, spec)
    print(f"  wrote {out}  ({elapsed:.0f}s, {elapsed / spec.n_views:.1f}s/view)")

    if args.cast:
        from quiltwright.lfd import cast_quilt

        cast_quilt(out, spec)
        print("  cast to Looking Glass Bridge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
