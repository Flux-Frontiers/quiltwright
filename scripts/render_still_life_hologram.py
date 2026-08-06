#!/usr/bin/env python
"""
Render one of the object-centric POV-Ray still lifes as a Looking Glass hologram.

Companion to ``render_museum_hologram.py``, which drives the interior.  The
difference is not cosmetic.  The museum is a room: its eye is boxed in by
walls, so the sweep is bounded by a measured lateral corridor and the view
cone is derived from what is left.  These two scenes are single subjects on
an open backdrop — there is nothing for the eye to walk into, so the sweep
uses the display's own cone and the whole job is spending the disparity
budget well.

Both scenes put a subject a short distance in front of a backdrop that runs
to the horizon.  That backdrop is where the budget goes if you let it, so the
focal plane is placed by the harmonic mean of the *measured* near and far
depths (``focal_distance_for_range``) rather than at the scene's own composed
aim point, and the sea is deliberately excluded from the balance the same way
the museum's sky is: it is a low-contrast, low-frequency surface that can
afford the disparity, and paying for it would push the subject off the glass.

Excluding it takes one extra step over the museum.  The museum's far depth is
where 95% of occludable content is accounted for, and that works because the
room's walls close the plane sweep out: the curve flattens.  A sea running to
the horizon never closes — it keeps eating a little more of the frame at every
distance — so the same rule returns the end of the sweep and nothing useful.
The fix is to read the *knee* instead: fit the far tail of the sweep, which is
pure backdrop, subtract that linear creep, and take 95% of what is left.  For
the bell jar the backdrop accumulates 0.12% of the frame per unit and the
subject is 35% of the frame; for porin, 0.02%/unit against a 13% subject.

Usage::

    python scripts/render_still_life_hologram.py bell-jar --preview
    python scripts/render_still_life_hologram.py porin --device portrait

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path

from quiltwright.lfd import QUILT_PRESETS, focal_distance_for_range, save_quilt
from quiltwright.povray import PovCamera, format_depth_budget, render_pov_quilt

POV_SCENES = Path(__file__).resolve().parents[1] / "pov-scenes"

#: Widest sweep these scenes are rendered at unless asked otherwise.
#:
#: Nothing encloses them, so unlike the museum there is no wall to bound the
#: cone — but the disparity budget bounds it anyway, and on a wide panel the
#: preset's native cone overruns it.  The 16" Landscape declares 50 degrees,
#: which on its 720 px tiles puts the sea at 14.3 px of adjacent-view
#: disparity, close to double the ~8 px where ghosting becomes obvious, and
#: the subject itself at 4.1 px, right at the practical ceiling.  At the
#: documented 35 degree standard the same scene is 2.8 px on the subject and
#: 9.7 px on the sea.  The cost is look-around, not sharpness: with the focal
#: plane at the harmonic mean, disparity at the extremes depends on the
#: physical baseline rather than on where the focal plane sits.
STANDARD_VIEW_CONE = 35.0


@dataclass(frozen=True)
class StillLife:
    """A scene, the camera it was composed with, and its measured depths.

    :param scene: Path to the ``.pov`` file, relative to ``pov-scenes/``.
    :param eye: The scene's own camera position.
    :param aim: The scene's own aim point.  Direction only — the focal
        distance is recomputed from *near* and *far*.
    :param fov: Vertical field of view of the scene's own lens, in degrees.
    :param near: Distance at which geometry first appears, in scene units.
    :param far: Distance accounting for 95% of occludable content.
    :param backdrop: Label for the residual that never occludes, and so is
        left out of the near/far balance on purpose.
    :param extra_args: POV-Ray arguments the scene needs, e.g. ``+MV3.1``.
    :param caveat: Anything in the scene that the sweep cannot serve, printed
        before the render so it is not discovered in the output.
    """

    scene: str
    eye: tuple[float, float, float]
    aim: tuple[float, float, float]
    fov: float
    near: float
    far: float
    backdrop: str
    extra_args: tuple[str, ...] = ()
    caveat: str = ""

    def camera(self) -> PovCamera:
        """The scene's viewpoint, re-focused for the view sweep.

        :return: The centre-view camera.
        """
        return PovCamera.aimed(
            self.eye,
            self.aim,
            fov=self.fov,
            focal_distance=focal_distance_for_range(self.near, self.far),
        )


#: The scenes this script knows how to aim at.  Depths are measured, not
#: guessed — ``measure_depth_range.py`` slides an opaque plane along the view
#: axis and scores each frame for how much geometry remains in front of it::
#:
#:     python scripts/measure_depth_range.py --scene pov-scenes/porin/3porin.pov \
#:         --include-path pov-scenes/myinclude --eye 0,0,-1100 --aim 0,0,0 \
#:         --min-distance 700 --max-distance 1600 --pov-arg +MV3.1
SCENES = {
    "bell-jar": StillLife(
        scene="bell_jar/bj.pov",
        # The scene's own camera: location <0,35,-95>, look_at <0,18,0>,
        # right <3/4,0,0> with the default unit direction and up, so the
        # vertical FOV is 2*atan(0.5) and the frame is 3:4 portrait.
        eye=(0.0, 35.0, -95.0),
        aim=(0.0, 18.0, 0.0),
        fov=53.13,
        # The pedestal's front rim appears at 72; the jar, the duplex and the
        # marble account for 95% of the subject by 130.  Past that the curve
        # creeps at 0.12%/unit, which is sea, not subject.
        near=72.0,
        far=130.0,
        backdrop="sea and sky",
    ),
    "porin": StillLife(
        scene="porin/3porin.pov",
        # location <0,0,-1100>, look_at origin, direction <0,0,1>, up
        # <0,1,0>, right <3/4,0,0> — same lens, same 3:4 frame, 11x the scale.
        eye=(0.0, 0.0, -1100.0),
        aim=(0.0, 0.0, 0.0),
        fov=53.13,
        # The barrel's leading loops appear at 790 and 95% of it is in by
        # 1265; the sea's own creep past that is 0.02%/unit.  These bound the
        # barrel only — see `caveat`, which is not scene content.
        near=790.0,
        far=1265.0,
        backdrop="sea and sky",
        caveat=(
            'the "Porin" title and the signature are pinned 10-12 units from '
            "the eye, not out at the barrel.  No focal plane serves both, so "
            "they leave the frame entirely during the sweep and the hologram "
            "is the barrel alone."
        ),
        # 3porin.pov carries no #version pragma, so POV-Ray 3.5+ rejects its
        # 2.x-syntax #declares.  Pinning the language version on the command
        # line leaves the scene file as it was written.
        extra_args=("+MV3.1",),
    ),
}


def main() -> int:
    """Render (and optionally cast) one still-life quilt.

    :return: Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subject", choices=sorted(SCENES), help="which still life")
    parser.add_argument(
        "--device",
        default="16-landscape",
        choices=sorted(QUILT_PRESETS),
        help="target display.  Both scenes were composed 3:4 portrait, so on "
        "a landscape panel the vertical framing is unchanged and the extra "
        "width is backdrop — use --fov to re-frame if you want the subject "
        "larger.",
    )
    parser.add_argument(
        "--view-cone",
        type=float,
        default=None,
        help="camera sweep in degrees; defaults to the display's own cone.  "
        "Nothing encloses these scenes, so there is no wall to walk into.",
    )
    parser.add_argument(
        "--fov",
        type=float,
        default=None,
        help="vertical field of view in degrees, overriding the scene's own "
        "lens.  This is the framing control: lower zooms in.  Note that a "
        "narrower lens magnifies parallax along with everything else, so "
        "re-check the depth budget it prints.",
    )
    parser.add_argument(
        "--aspect",
        type=float,
        default=None,
        help="tile aspect (width/height), overriding the device preset's.  "
        "Changes the shape of the frame rather than what is in it.  The "
        "value is encoded in the output filename, which is what Looking "
        "Glass software reads, so a value that disagrees with the panel "
        "will be letterboxed by it.",
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
        "than stills: each view aliases differently and the display "
        "interpolates between them, so edge noise reads as shimmer.",
    )
    parser.add_argument("--jobs", type=int, default=1, help="concurrent POV-Ray processes")
    parser.add_argument("--out", default=None, help="output stem; defaults to out/<subject>")
    parser.add_argument("--cast", action="store_true", help="send to Looking Glass Bridge")
    parser.add_argument("--keep-views", help="directory to retain per-view PNGs in")
    args = parser.parse_args()

    subject = SCENES[args.subject]
    scene = POV_SCENES / subject.scene
    if not scene.is_file():
        print(f"error: scene not found at {scene}", file=sys.stderr)
        return 1

    if args.fov is not None:
        subject = replace(subject, fov=args.fov)
    camera = subject.camera()
    spec = QUILT_PRESETS[args.device]
    if args.view_cone is not None:
        spec = replace(spec, view_cone=args.view_cone)
    elif spec.view_cone > STANDARD_VIEW_CONE:
        print(
            f"  view cone        {spec.view_cone:.0f} deg native -> "
            f"{STANDARD_VIEW_CONE:.0f} to keep the budget in range "
            f"(--view-cone {spec.view_cone:.0f} to override)"
        )
        spec = replace(spec, view_cone=STANDARD_VIEW_CONE)
    if args.aspect is not None:
        spec = replace(spec, aspect=args.aspect)
    if args.preview:
        spec = replace(spec, quilt_width=spec.quilt_width // 4, quilt_height=spec.quilt_height // 4)

    print(f"{args.subject} hologram -> {args.device}{' (preview)' if args.preview else ''}")
    print(
        f"  quilt            {spec.quilt_width}x{spec.quilt_height}, "
        f"tiles {spec.tile_width}x{spec.tile_height}"
    )
    print(
        format_depth_budget(
            spec,
            camera,
            {
                "nearest geometry": subject.near,
                "focal plane": camera.focal_distance,
                "structured far": subject.far,
                f"{subject.backdrop} (infinite)": math.inf,
            },
        )
    )
    if subject.caveat:
        print(f"  note: {subject.caveat}")

    started = time.time()
    quilt = render_pov_quilt(
        scene,
        spec,
        camera,
        include_paths=[POV_SCENES / "myinclude", POV_SCENES],
        antialias=None if args.preview else args.antialias,
        quality=11,
        # Recursive supersampling rather than the default adaptive single
        # pass: the bell jar's rim and the beta-barrel's ribbon edges are the
        # highest-contrast lines in either frame, and stair-stepping on them
        # is exactly what a view sweep turns into shimmer.
        extra_args=(*subject.extra_args, *(() if args.preview else ("+AM2", "+R4"))),
        jobs=args.jobs,
        keep_views=args.keep_views,
    )
    elapsed = time.time() - started

    out = save_quilt(quilt, args.out or f"out/{args.subject}", spec)
    print(f"  wrote {out}  ({elapsed:.0f}s, {elapsed / spec.n_views:.1f}s/view)")

    if args.cast:
        from quiltwright.lfd import cast_quilt

        cast_quilt(out, spec)
        print("  cast to Looking Glass Bridge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
