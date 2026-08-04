#!/usr/bin/env python
"""
Render the "meek museum" POV-Ray scene as a Looking Glass hologram.

The scene is a 1994 Michael Mittelstadt interior, later extended with
molecular exhibits under bell jars.  It is close to ideal light-field
content: a foreground pedestal, mid-depth framed art and exhibits, and a
window onto terrain and sky at infinity.

The camera keeps the scene's own viewpoint, aim direction and lens, and
changes three things — each measured from the scene rather than guessed.

*Focal plane.*  The scene's ``camera_zdna3`` looks at a point 63.7 units
away, chosen for composition.  A hologram wants the focal plane placed to
balance the disparity budget instead.  The depth range was measured by
sweeping an opaque plane along the view axis (nearest geometry ~32 units,
structured far content ~100, with ~10% of the frame — sky through the window
— at effective infinity), and :func:`focal_distance_for_range` turns that
into the balanced distance.  The new look-at point sits on the *original*
aim ray, so the view direction is untouched.

*Sweep clearance.*  This is the constraint peculiar to interiors, and the
one that bites hardest.  The quilt sweeps the eye laterally by
``focal_distance * tan(cone/2)`` — at a 35-degree cone and this focal plane,
+/-15.3 units.  The room is not that wide: probing eye positions along the
right vector shows usable travel only from -18 to +8 before the camera
passes through a wall and renders its unlit back face.  A cone chosen
without checking silently blackens the outer views — 11 of 48, in the first
render of this scene.  The eye is therefore shifted to the middle of that
corridor and the cone derived from the clearance that remains.

*Aspect and cone.*  Rendered for the 16" Landscape.  The cone comes from
the clearance above (~26 degrees), which is well inside both the device's
50-degree native cone and the documented 35-degree standard, and lands
adjacent-view disparity near 3.6 px.

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

import numpy as np

from quiltwright.lfd import (
    QUILT_PRESETS,
    focal_distance_for_range,
    save_quilt,
    view_disparity,
)
from quiltwright.povray import PovCamera, render_pov_quilt

# --- Scene -----------------------------------------------------------------

POV_SCENES = Path(__file__).resolve().parents[1] / "pov-scenes"
SCENE = POV_SCENES / "museum" / "museum.pov"
INCLUDE_PATHS = [
    POV_SCENES / "myinclude",
    POV_SCENES,
]

#: Eye position of the scene's own ``camera_zdna3``.
EYE = (15.0, 20.0, 6.0)
#: Its aim point.  Used for direction only; the focal distance is recomputed.
AIM = (58.0, 19.0, 53.0)
#: Vertical FOV of the scene's ``the_lens`` (direction 1, up 1 -> 2*atan(0.5)).
FOV = 53.13

#: Depth range measured by plane-sweep probe, in scene units.
NEAR_DEPTH = 32.0
FAR_DEPTH = 100.0

#: Usable lateral eye travel along the camera's right vector, measured by
#: rendering at candidate offsets and watching for the frame to collapse to
#: the unlit back of a wall.  The corridor is asymmetric about the scene's
#: own eye position.
CLEARANCE_LEFT = -18.0
CLEARANCE_RIGHT = 8.0
#: Safety margin kept between the outermost view and the wall, in scene
#: units.  The walls are not perfectly planar and grazing them dims the
#: outer views well before the camera actually passes through.
CLEARANCE_MARGIN = 2.0


def museum_camera() -> PovCamera:
    """The scene's viewpoint, re-aimed and re-centred for the view sweep.

    The eye slides along the right vector to the middle of the measured
    lateral corridor so the sweep has symmetric room, and the look-at point
    moves to the distance that balances near/far disparity.  The view
    *direction* and lens are the scene's own.

    :return: The centre-view camera.
    """
    eye = np.asarray(EYE, dtype="d")
    forward = np.asarray(AIM, dtype="d") - eye
    forward /= np.linalg.norm(forward)
    right = np.cross((0.0, 1.0, 0.0), forward)
    right /= np.linalg.norm(right)

    eye = eye + right * ((CLEARANCE_LEFT + CLEARANCE_RIGHT) / 2.0)
    focal = focal_distance_for_range(NEAR_DEPTH, FAR_DEPTH)
    return PovCamera(location=tuple(eye), look_at=tuple(eye + forward * focal), fov=FOV)


def clearance_limited_cone(camera: PovCamera) -> float:
    """Widest view cone whose outermost eye still clears the walls.

    :param camera: The re-centred centre-view camera.
    :return: Total sweep in degrees.
    """
    half_corridor = (CLEARANCE_RIGHT - CLEARANCE_LEFT) / 2.0 - CLEARANCE_MARGIN
    return 2.0 * math.degrees(math.atan(half_corridor / camera.focal_distance))


def report_depth_budget(spec, camera: PovCamera) -> None:
    """Print the sweep extent and adjacent-view disparity at depth extremes."""
    z = camera.focal_distance
    sweep = z * math.tan(math.radians(spec.view_cone) / 2.0)
    room = (CLEARANCE_RIGHT - CLEARANCE_LEFT) / 2.0
    print(f"  focal plane      {z:.1f} units (scene's own aim was 63.7)")
    print(f"  view cone        {spec.view_cone:.1f} deg over {spec.n_views} views")
    print(f"  eye sweep        +/-{sweep:.1f} units (walls at +/-{room:.1f})")
    if sweep > room:
        print("    WARNING: sweep exceeds wall clearance; outer views will be black")
    print("  adjacent-view disparity:")
    for label, depth in (
        ("nearest geometry", NEAR_DEPTH),
        ("focal plane", z),
        ("far interior", FAR_DEPTH),
        ("sky (infinite)", math.inf),
    ):
        px = view_disparity(spec, camera.fov, z, depth)
        flag = "" if px <= 5.5 else "  <- soft"
        print(f"    {label:<18} {depth:>8.1f}  {px:5.2f} px{flag}")


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
    parser.add_argument("--out", default="out/museum", help="output stem")
    parser.add_argument("--cast", action="store_true", help="send to Looking Glass Bridge")
    parser.add_argument("--keep-views", help="directory to retain per-view PNGs in")
    args = parser.parse_args()

    if not SCENE.is_file():
        print(f"error: scene not found at {SCENE}", file=sys.stderr)
        return 1

    camera = museum_camera()
    cone = args.view_cone if args.view_cone is not None else clearance_limited_cone(camera)
    spec = replace(QUILT_PRESETS[args.device], view_cone=cone)
    if args.preview:
        spec = replace(spec, quilt_width=spec.quilt_width // 4, quilt_height=spec.quilt_height // 4)

    print(f"Museum hologram -> {args.device}{' (preview)' if args.preview else ''}")
    print(
        f"  quilt            {spec.quilt_width}x{spec.quilt_height}, "
        f"tiles {spec.tile_width}x{spec.tile_height}"
    )
    report_depth_budget(spec, camera)

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
        # mullions and bell-jar rims — the highest-contrast edges in frame.
        extra_args=() if args.preview else ("+AM2", "+R4"),
        jobs=args.jobs,
        keep_views=args.keep_views,
    )
    elapsed = time.time() - started

    out = save_quilt(quilt, args.out, spec)
    print(f"  wrote {out}  ({elapsed:.0f}s, {elapsed / spec.n_views:.1f}s/view)")

    if args.cast:
        from quiltwright.lfd import cast_quilt

        cast_quilt(out, spec)
        print("  cast to Looking Glass Bridge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
