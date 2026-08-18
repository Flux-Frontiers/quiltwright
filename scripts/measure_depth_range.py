#!/usr/bin/env python
"""
Measure a POV-Ray scene's depth range by plane sweep.

The depth budget wants two numbers from a scene -- where its nearest content
sits and where its farthest *structured* content ends -- and guessing them
costs a render to find out.  This measures them.

An opaque, self-lit plane is slid along the view axis at distance ``d`` from
the eye, hiding everything beyond it.  The fraction of the frame that is
*not* the marker colour is then the fraction occupied by geometry nearer
than ``d``, and sweeping ``d`` traces a cumulative depth histogram of the
frame::

    d= 31   0.2%   <- nearest geometry appears
    d= 47  35.1%
    d= 96  93.9%   <- 95% of everything occludable
    d=inf  93.9%   <- the remaining 6.1% is sky, at effective infinity

Three cautions, each learned the hard way:

*Render at the quality you will ship.*  POV-Ray disables transparency and
refraction below ``+Q8``, which makes glass opaque -- a cheap probe run at
``+Q3`` reports a room with no windows and no sky at all.

*Measure through the camera you will render with.*  A hologram's eye is
usually not the scene's own; see :meth:`~quiltwright.povray.PovCamera.aimed`.

*Sky is not far content.*  A backdrop at infinity never occludes, so it
shows up as a residual that never closes.  Leave it out of the near/far
balance: it is low-contrast and can afford the disparity.

Usage::

    python scripts/measure_depth_range.py                    # the museum
    python scripts/measure_depth_range.py --scene other.pov --max-distance 800

Author: Eric G. Suchanek, PhD
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from quiltwright.povray import PovCamera, camera_block

#: Marker colour for the sweep plane, chosen to be absent from real scenes.
MARKER = (1.0, 0.0, 1.0)


def _triple(text: str) -> tuple[float, float, float]:
    """Parse an ``x,y,z`` command-line vector."""
    parts = text.replace(" ", "").split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(f"expected x,y,z -- got {text!r}")
    try:
        return tuple(float(p) for p in parts)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected three numbers -- got {text!r}") from exc


def _wrapper(scene: Path, camera: PovCamera, aspect: float, dist: float | None) -> str:
    """Scene + camera, plus the marker plane at *dist* if given."""
    body = f'#include "{scene}"\n' + camera_block(camera, 0.0, aspect)
    if dist is None:
        return body
    forward = camera.basis()[0]
    # Plane through eye + forward*dist with normal forward:  n.p = n.eye + dist
    offset = float(np.dot(forward, np.asarray(camera.location, dtype="d")) + dist)
    normal = ", ".join(f"{c:.17g}" for c in forward)
    return body + (
        f"plane {{ <{normal}>, {offset:.17g}\n"
        f"  pigment {{ color rgb <{MARKER[0]}, {MARKER[1]}, {MARKER[2]}> }}\n"
        "  finish { ambient 1 diffuse 0 } no_shadow }\n"
    )


def _render(
    workdir: Path,
    scene: Path,
    camera: PovCamera,
    include_paths,
    width: int,
    height: int,
    quality: int,
    dist: float | None,
    extra_args=(),
) -> np.ndarray:
    """Render one probe frame and return it as an RGB array."""
    from PIL import Image

    (workdir / "probe.pov").write_text(_wrapper(scene, camera, width / height, dist))
    out = workdir / "probe.png"
    out.unlink(missing_ok=True)
    cmd = [
        "povray",
        "+Iprobe.pov",
        "+Oprobe.png",
        f"+W{width}",
        f"+H{height}",
        "+FN",
        "-D",
        f"+Q{quality}",
        f"+L{scene.parent}",
        *[f"+L{Path(p)}" for p in include_paths],
        *extra_args,
    ]
    result = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True)
    if result.returncode != 0 or not out.exists():
        raise RuntimeError(f"POV-Ray failed on the probe frame:\n{result.stderr[-2000:]}")
    return np.asarray(Image.open(out).convert("RGB")).astype(int)


def sweep(
    scene: Path,
    camera: PovCamera,
    distances,
    *,
    include_paths=(),
    width: int = 320,
    height: int = 180,
    quality: int = 11,
    extra_args=(),
    progress: bool = True,
) -> list[tuple[float, float]]:
    """Fraction of the frame nearer than each distance.

    :param scene: Scene to probe.  Not modified.
    :param camera: Camera to measure through -- the one you will render with.
    :param distances: Distances along the view axis to test, in scene units.
    :param quality: POV-Ray ``+Q``.  Keep at 8 or above or glass reads solid.
    :param extra_args: Additional POV-Ray arguments, e.g. ``["+MV3.1"]`` for
        pre-2000 scenes that carry no ``#version`` pragma of their own.
    :return: ``(distance, fraction_in_front)`` pairs, in the order given.
    :raises RuntimeError: If POV-Ray fails, or the calibration frame is not
        uniformly the marker colour (something occludes the plane at d=1).
    """
    with tempfile.TemporaryDirectory(prefix="depth_probe_") as tmp:
        workdir = Path(tmp)
        opts = dict(
            scene=scene,
            camera=camera,
            include_paths=include_paths,
            width=width,
            height=height,
            quality=quality,
            extra_args=extra_args,
        )
        calib = _render(workdir, dist=1.0, **opts)
        if calib.std(axis=(0, 1)).max() > 2:
            raise RuntimeError(
                "calibration frame is not uniform; geometry is inside the near plane"
            )
        marker = calib.reshape(-1, 3).mean(0)

        rows = []
        for i, d in enumerate(distances):
            frame = _render(workdir, dist=float(d), **opts)
            frac = float((np.abs(frame - marker).sum(-1) > 30).mean())
            rows.append((float(d), frac))
            if progress:
                print(
                    f"\r  probe {i + 1}/{len(distances)}  d={d:.0f} {frac * 100:5.1f}%",
                    end="",
                    flush=True,
                )
        if progress:
            print()
    return rows


def summarise(rows, *, appear: float = 0.001, structured: float = 0.95) -> dict:
    """Reduce a sweep to the numbers the depth budget needs.

    :param rows: Output of :func:`sweep`.
    :param appear: Frame fraction counting as "geometry has appeared".
    :param structured: Fraction of occludable content defining *far*.
    :return: ``near``, ``far``, and ``sky_fraction``.
    """
    d = np.array([r[0] for r in rows])
    f = np.array([r[1] for r in rows])
    saturation = f.max()
    return {
        "near": float(d[np.argmax(f > appear)]),
        "far": float(d[np.argmax(f >= structured * saturation)]),
        "sky_fraction": float(1.0 - saturation),
    }


def main() -> int:
    """Sweep a scene and print the measured depth range."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", help="scene to probe; defaults to the museum")
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=180)
    parser.add_argument("--quality", type=int, default=11, help="POV-Ray +Q; keep >= 8")
    parser.add_argument("--max-distance", type=float, default=400.0)
    parser.add_argument(
        "--min-distance",
        type=float,
        default=None,
        help="near end of the sweep.  Given, the probes are spread evenly "
        "between it and --max-distance instead of using the museum's grid.",
    )
    parser.add_argument(
        "--include-path",
        action="append",
        default=[],
        metavar="DIR",
        help="extra #include directory; repeatable.  With --scene only.",
    )
    parser.add_argument(
        "--eye",
        type=_triple,
        metavar="X,Y,Z",
        help="camera position to probe through.  With --scene only.",
    )
    parser.add_argument(
        "--aim", type=_triple, metavar="X,Y,Z", help="camera look_at.  With --scene only."
    )
    parser.add_argument(
        "--fov",
        type=float,
        default=53.13,
        help="vertical field of view in degrees.  With --scene only.",
    )
    parser.add_argument(
        "--pov-arg",
        action="append",
        default=[],
        metavar="ARG",
        help="extra POV-Ray argument, e.g. +MV3.1 for a scene with no #version pragma; repeatable.",
    )
    args = parser.parse_args()

    if args.scene:
        scene = Path(args.scene).resolve()
        include_paths = [Path(p).resolve() for p in args.include_path]
        camera = PovCamera(
            location=args.eye or (0, 0, -10),
            look_at=args.aim or (0, 0, 0),
            fov=args.fov,
        )
        if args.eye is None or args.aim is None:
            print("note: probing with a default camera; pass --eye and --aim for your own")
    else:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import render_museum_hologram as museum

        scene, include_paths = museum.SCENE, museum.INCLUDE_PATHS
        camera = museum.museum_camera()

    if args.quality < 8:
        print(f"warning: +Q{args.quality} disables transparency; glass will read solid")

    if args.min_distance is None:
        # The museum's grid: fine through the room, coarse out to the walls.
        grid = [
            *np.arange(5.0, 62.0, 1.0),
            *np.arange(62.0, 122.0, 2.0),
            *np.arange(125.0, args.max_distance, 10.0),
            5000.0,
        ]
    else:
        # A scene composed at some other scale -- porin sits 1100 units out --
        # wants its probes where its content is, not 200 of them in front of it.
        grid = [*np.linspace(args.min_distance, args.max_distance, 200), 5000.0]
    print(f"Sweeping {scene.name} through {len(grid)} planes at {args.width}x{args.height}")
    rows = sweep(
        scene,
        camera,
        grid,
        include_paths=include_paths,
        width=args.width,
        height=args.height,
        quality=args.quality,
        extra_args=args.pov_arg,
    )
    found = summarise(rows)
    print(f"\n  nearest geometry   {found['near']:.0f} units")
    print(f"  structured far     {found['far']:.0f} units (95% of occludable content)")
    print(f"  sky at infinity    {found['sky_fraction'] * 100:.1f}% of frame")
    print(f"\n  -> NEAR_DEPTH = {found['near']:.1f}, FAR_DEPTH = {found['far']:.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
