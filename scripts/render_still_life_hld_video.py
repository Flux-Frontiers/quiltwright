#!/usr/bin/env python
"""
Render a still-life POV-Ray scene as a turntable HLD master video.

Companion to ``render_still_life_hologram.py``, which quilts these same
scenes for light-field panels.  A Hololuminescent Display -- Looking
Glass's other product line, which now includes the small consumer
*musubi* frame -- plays ordinary flat video instead of a quilt.  This
drives :func:`quiltwright.povray.render_pov_hld_video` through the same
``SCENES`` camera registry as the quilt script, so the two renderers agree
on eye/aim/lens/focal-plane without duplicating those measured numbers.

Usage::

    python scripts/render_still_life_hld_video.py bell-jar-holo-2026 --preview
    python scripts/render_still_life_hld_video.py bell-jar-holo-2026 --seconds 8

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from render_still_life_hologram import POV_SCENES, SCENES

from quiltwright.hld import HLD_DEVICES
from quiltwright.povray import render_pov_hld_video

DEFAULT_OUT_DIR = Path(__file__).resolve().parents[1] / "renders" / "hld"

#: Master resolution per the official HLD media spec -- one 4K landscape
#: master serves every panel size, players downscale.  ``--preview`` quarters
#: it, matching render_still_life_hologram.py's own --preview convention.
FULL_RESOLUTION = (3840, 2160)
PREVIEW_RESOLUTION = (960, 540)


def main() -> int:
    """Render (and time) one still-life HLD turntable.

    :return: Process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("subject", choices=sorted(SCENES), help="which still life")
    parser.add_argument(
        "--device",
        choices=sorted(HLD_DEVICES),
        default=None,
        help="known device preset -- sets resolution, fps and encode target "
        "together, measured from the device's own generated clips (see "
        "quiltwright.hld.HLD_DEVICES).  --resolution/--codec/--fps still "
        "override individual pieces when also given.",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=None,
        choices=(30, 60),
        help="default: the --device preset's fps, else 30",
    )
    parser.add_argument("--seconds", type=float, default=10.0, help="loop length at --fps")
    parser.add_argument(
        "--orbit-degrees",
        type=float,
        default=360.0,
        help="total camera revolution over the clip; 360 loops seamlessly.  "
        "Ignored if --sway-degrees is given.",
    )
    parser.add_argument(
        "--sway-degrees",
        type=float,
        default=None,
        help="oscillate the camera +/- this many degrees around the scene's "
        "own viewpoint instead of sweeping all the way around -- one full "
        "back-and-forth cycle per clip.  Suits a single-viewpoint diorama "
        "scene, or a display that itself only rocks through a limited angle "
        "(e.g. a musubi frame's own ~15 degrees -- pass a few degrees of "
        "margin over that, not the display's full range).",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="960x540, 90 frames, no anti-aliasing -- for iterating and for "
        "checking the orbit reads well before committing to a full render",
    )
    parser.add_argument(
        "--resolution",
        nargs=2,
        type=int,
        default=None,
        metavar=("W", "H"),
        help="render (width, height) directly, overriding --device/the "
        "full/preview defaults -- e.g. 1080 1920 for a portrait device.  The "
        "scene's own camera controls framing/aspect, not this: a portrait-"
        "composed scene wants a portrait resolution to match.",
    )
    parser.add_argument(
        "--antialias",
        type=float,
        default=0.05,
        help="POV-Ray +A threshold for the full render.  Ignored -- disabled "
        "entirely -- under --preview.",
    )
    parser.add_argument(
        "--codec",
        choices=("hevc", "h264-baseline"),
        default=None,
        help="hevc targets the official HLD master spec (HEVC bt709) for "
        "HLD Author and the big Portrait HLD panels.  h264-baseline targets "
        "a device that plays video directly instead of through HLD Author -- "
        "e.g. a musubi frame, whose own generated clips are H.264 Baseline, "
        "never HEVC.  Default: the --device preset's codec, else hevc.",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=18,
        help="encoder quality (lower = better; 15-20 sensible).  x265 under "
        "--codec hevc, x264 under --codec h264-baseline.",
    )
    parser.add_argument("--jobs", type=int, default=1, help="concurrent POV-Ray processes")
    parser.add_argument(
        "--threads",
        type=int,
        default=None,
        help="POV-Ray worker threads per process.  Left alone, two cores are "
        "held back so the machine stays usable during the render.",
    )
    parser.add_argument(
        "--out", default=None, help="output stem; defaults to renders/hld/<subject>"
    )
    parser.add_argument("--keep-frames", default=None, help="directory to retain per-frame PNGs")
    parser.add_argument(
        "--keep-overlays",
        action="store_true",
        help="do not set QW_HLD_Turntable -- a scene's camera-pinned title/"
        "signature (if it checks the flag) stays in and reads mirrored "
        "through the back half of the orbit",
    )
    args = parser.parse_args()

    subject = SCENES[args.subject]
    scene = POV_SCENES / subject.scene
    if not scene.is_file():
        print(f"error: scene not found at {scene}", file=sys.stderr)
        return 1

    camera = subject.camera()
    device = HLD_DEVICES[args.device] if args.device else None

    if args.resolution is not None:
        resolution = tuple(args.resolution)
    elif device is not None and not args.preview:
        resolution = device.resolution
    else:
        resolution = PREVIEW_RESOLUTION if args.preview else FULL_RESOLUTION

    fps = args.fps if args.fps is not None else (device.fps if device is not None else 30)
    n_frames = 90 if args.preview else round(args.seconds * fps)
    if device is not None and device.max_seconds is not None and args.seconds > device.max_seconds:
        print(
            f"  note: {args.seconds:.0f}s exceeds {args.device}'s own "
            f"{device.max_seconds:.0f}s import limit -- its app will prompt to trim"
        )
    # Recursive supersampling for the full pass, same reasoning as the quilt
    # script: the jar's rim and the helix ribbons are the highest-contrast
    # lines in the frame, and an adaptive single pass turns their aliasing
    # into shimmer once the video is playing.
    antialias = None if args.preview else args.antialias
    extra_args = () if args.preview else ("+AM2", "+R4")
    quality = 9 if args.preview else 11

    # A sway keeps the camera within a few degrees of the composed viewpoint,
    # so title/signature text never approaches the angle where it would read
    # mirrored -- suppressing it by default is a full-orbit-only concern.
    suppress_overlays = args.sway_degrees is None and not args.keep_overlays

    codec = args.codec
    if codec is None:
        codec = "h264-baseline" if device is not None and device.encode_args else "hevc"
    encode_args = None
    if codec == "h264-baseline":
        base = (
            device.encode_args
            if device is not None and device.encode_args
            else (
                "-vcodec",
                "libx264",
                "-profile:v",
                "baseline",
                "-pix_fmt",
                "yuv420p",
            )
        )
        encode_args = [*base, "-crf", str(args.crf)]

    print(f"{args.subject} HLD turntable" + (" (preview)" if args.preview else ""))
    print(f"  frames           {n_frames} @ {fps} fps ({n_frames / fps:.1f} s loop)")
    print(f"  resolution       {resolution[0]}x{resolution[1]}")
    print(f"  codec            {codec}")
    if args.sway_degrees is not None:
        print(f"  sway             +/-{args.sway_degrees:.0f} deg")
    else:
        print(f"  orbit            {args.orbit_degrees:.0f} deg")

    out_stem = Path(args.out) if args.out else DEFAULT_OUT_DIR / args.subject

    started = time.time()
    out = render_pov_hld_video(
        scene,
        camera,
        out_stem,
        include_paths=[POV_SCENES / "myinclude", POV_SCENES],
        n_frames=n_frames,
        fps=fps,
        orbit_degrees=args.orbit_degrees,
        sway_degrees=args.sway_degrees,
        resolution=resolution,
        antialias=antialias,
        quality=quality,
        crf=args.crf,
        jobs=args.jobs,
        threads=args.threads,
        extra_args=extra_args,
        keep_frames=args.keep_frames,
        suppress_overlays=suppress_overlays,
        encode_args=encode_args,
    )
    elapsed = time.time() - started

    print(f"  wall clock       {elapsed:.0f} s ({elapsed / max(n_frames, 1):.1f} s/frame)")
    print(f"  output           {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
